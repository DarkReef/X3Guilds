from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from x3guilds_ai.bridge import (
    encode_bridge_error,
    encode_chat_response,
    contains_protocol_marker,
    extract_protocol_record,
    is_context_record,
    is_request_record,
    parse_chat_request,
    parse_context_selection,
)
from x3guilds_ai.models import (
    BridgeError,
    ChatRequest,
    ContextSelection,
    DialogueResponse,
)
from x3guilds_ai.service import ChatService


logger = logging.getLogger(__name__)
BridgeCallback = Callable[[ChatRequest, DialogueResponse | BridgeError], Awaitable[None] | None]
ContextCallback = Callable[[ContextSelection], Awaitable[None] | None]


@dataclass(slots=True)
class BridgeStats:
    lines_seen: int = 0
    contexts_seen: int = 0
    requests_processed: int = 0
    cached_responses: int = 0
    invalid_lines: int = 0
    failures: int = 0


class FileBridge:
    def __init__(
        self,
        *,
        request_path: Path,
        response_path: Path,
        checkpoint_path: Path,
        diagnostics_path: Path,
        service: ChatService,
        callback: BridgeCallback | None = None,
        context_callback: ContextCallback | None = None,
    ) -> None:
        self.request_path = request_path
        self.response_path = response_path
        self.checkpoint_path = checkpoint_path
        self.diagnostics_path = diagnostics_path
        self.service = service
        self.callback = callback
        self.context_callback = context_callback
        self.stats = BridgeStats()

    def _prefix_hash(self, length: int) -> str:
        if length <= 0 or not self.request_path.exists():
            return ""
        with self.request_path.open("rb") as handle:
            return hashlib.sha256(handle.read(length)).hexdigest()

    def _load_checkpoint(self) -> tuple[int, int, str]:
        try:
            payload = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            return (
                max(0, int(payload.get("offset", 0))),
                max(0, int(payload.get("prefix_length", 0))),
                str(payload.get("prefix_hash", payload.get("head_hash", ""))),
            )
        except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError):
            return 0, 0, ""

    def _save_checkpoint(self, offset: int) -> None:
        prefix_length = min(offset, 512)
        prefix_hash = self._prefix_hash(prefix_length)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.checkpoint_path.with_suffix(self.checkpoint_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "offset": offset,
                    "prefix_length": prefix_length,
                    "prefix_hash": prefix_hash,
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        temporary.replace(self.checkpoint_path)

    def _append_response(self, line: str) -> None:
        self.response_path.parent.mkdir(parents=True, exist_ok=True)
        with self.response_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
            handle.write("\n")
            handle.flush()

    def _append_diagnostic(self, payload: dict[str, object]) -> None:
        self.diagnostics_path.mkdir(parents=True, exist_ok=True)
        path = self.diagnostics_path / "bridge-events.jsonl"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")

    @staticmethod
    async def _call_callback(callback, *args) -> None:
        if callback is None:
            return
        returned = callback(*args)
        if asyncio.iscoroutine(returned):
            await returned

    async def process_request(self, request: ChatRequest) -> DialogueResponse | BridgeError:
        """Process a validated request from X3, overlay input, HTTP or tests."""
        try:
            response = await self.service.chat(request)
            self._append_response(encode_chat_response(response))
            self._append_diagnostic(
                {
                    "event": "response",
                    "request": request.model_dump(mode="json"),
                    "response": response.model_dump(mode="json"),
                }
            )
            self.stats.requests_processed += 1
            if response.cached:
                self.stats.cached_responses += 1
            await self._call_callback(self.callback, request, response)
            return response
        except Exception as exc:
            self.stats.failures += 1
            error = BridgeError(
                request_id=request.request_id,
                code=type(exc).__name__,
                message=(str(exc) or type(exc).__name__)[:1000],
            )
            self._append_response(encode_bridge_error(error))
            self._append_diagnostic(
                {
                    "event": "failure",
                    "request": request.model_dump(mode="json"),
                    "error": error.model_dump(mode="json"),
                }
            )
            logger.exception("Failed to process X3 chat request %s", request.request_id)
            await self._call_callback(self.callback, request, error)
            return error

    async def _process_protocol_line(self, line: str) -> None:
        record = extract_protocol_record(line)
        if record is None:
            return
        try:
            if is_context_record(record):
                context = parse_context_selection(record)
                self.stats.contexts_seen += 1
                self._append_diagnostic(
                    {"event": "context", "context": context.model_dump(mode="json")}
                )
                await self._call_callback(self.context_callback, context)
                return
            if is_request_record(record):
                request = parse_chat_request(record)
                await self.process_request(request)
                return
            raise ValueError("Unknown XUGC record type")
        except Exception as exc:
            self.stats.invalid_lines += 1
            logger.warning("Ignoring invalid XUGC record: %s", exc)
            self._append_diagnostic({"event": "invalid_request", "line": record, "error": str(exc)})

    async def run_once(self) -> int:
        """Consume only complete, newline-terminated records from the X3 log.

        The checkpoint is a byte offset. A trailing partial record is deliberately
        left unread so the next poll can process it after X3 finishes the write.
        """
        if not self.request_path.exists():
            return 0

        file_size = self.request_path.stat().st_size
        offset, prefix_length, previous_prefix_hash = self._load_checkpoint()
        if offset > file_size:
            offset = 0
        elif offset and prefix_length and previous_prefix_hash:
            if prefix_length > file_size or self._prefix_hash(prefix_length) != previous_prefix_hash:
                offset = 0

        with self.request_path.open("rb") as handle:
            handle.seek(offset)
            chunk = handle.read()

        if not chunk:
            return 0

        last_newline = chunk.rfind(b"\n")
        if last_newline < 0:
            return 0

        complete = chunk[: last_newline + 1]
        next_offset = offset + len(complete)
        processed = 0

        for raw_line in complete.splitlines():
            self.stats.lines_seen += 1
            line = raw_line.decode("utf-8-sig", errors="replace")
            if not contains_protocol_marker(line):
                continue
            await self._process_protocol_line(line)
            processed += 1

        self._save_checkpoint(next_offset)
        return processed

    async def run_forever(
        self,
        *,
        poll_interval: float,
        stop_event: asyncio.Event,
    ) -> None:
        while not stop_event.is_set():
            await self.run_once()
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=poll_interval)
            except TimeoutError:
                pass
