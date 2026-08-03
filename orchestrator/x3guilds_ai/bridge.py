from __future__ import annotations

from urllib.parse import quote, unquote

from x3guilds_ai.models import (
    BridgeError,
    ChatRequest,
    ContextSelection,
    DialogueResponse,
    EntityContext,
)


PREFIX = "XUGC"
VERSION = "1"
REQUEST_MARKER = f"{PREFIX}|{VERSION}|CHAT_REQUEST|"
CONTEXT_MARKER = f"{PREFIX}|{VERSION}|CHAT_CONTEXT|"
RECORD_MARKERS = (REQUEST_MARKER, CONTEXT_MARKER)


def _escape(value: object) -> str:
    return quote(str(value), safe="")


def _unescape(value: str) -> str:
    return unquote(value)


def extract_protocol_record(raw_line: str) -> str | None:
    """Return the embedded XUGC record from an X3 log line, if present."""
    positions = [position for marker in RECORD_MARKERS if (position := raw_line.find(marker)) >= 0]
    if not positions:
        return None
    return raw_line[min(positions) :].strip()


def parse_context_selection(line: str) -> ContextSelection:
    """Parse an object-selection record emitted by the in-game hotkey."""
    record = extract_protocol_record(line) or line.strip()
    parts = record.split("|", 11)
    if len(parts) != 12 or parts[:3] != [PREFIX, VERSION, "CHAT_CONTEXT"]:
        raise ValueError("Invalid XUGC context record")

    (
        context_id,
        entity_id,
        name,
        kind,
        race,
        faction,
        sector,
        relation,
        game_time,
    ) = (_unescape(item) for item in parts[3:])

    return ContextSelection(
        context_id=context_id,
        game_time=int(game_time) if game_time else None,
        entity=EntityContext(
            entity_id=entity_id,
            name=name,
            kind=kind,
            race=race or None,
            faction=faction or None,
            sector=sector or None,
            relation=int(relation or 0),
        ),
    )


def parse_chat_request(line: str) -> ChatRequest:
    """Parse one X3 log line into a validated request.

    Protocol fields:
    XUGC|1|CHAT_REQUEST|request|conversation|entity_id|name|kind|race|faction|
    sector|relation|game_time|message
    """
    record = extract_protocol_record(line) or line.strip()
    parts = record.split("|", 13)
    if len(parts) != 14 or parts[:3] != [PREFIX, VERSION, "CHAT_REQUEST"]:
        raise ValueError("Invalid XUGC chat request line")

    (
        request_id,
        conversation_id,
        entity_id,
        name,
        kind,
        race,
        faction,
        sector,
        relation,
        game_time,
        message,
    ) = (_unescape(item) for item in parts[3:])

    return ChatRequest(
        request_id=request_id,
        conversation_id=conversation_id,
        message=message,
        game_time=int(game_time) if game_time else None,
        entity=EntityContext(
            entity_id=entity_id,
            name=name,
            kind=kind,
            race=race or None,
            faction=faction or None,
            sector=sector or None,
            relation=int(relation or 0),
        ),
    )


def encode_context_selection(context: ContextSelection) -> str:
    entity = context.entity
    return "|".join(
        [
            PREFIX,
            VERSION,
            "CHAT_CONTEXT",
            _escape(context.context_id),
            _escape(entity.entity_id),
            _escape(entity.name),
            _escape(entity.kind),
            _escape(entity.race or ""),
            _escape(entity.faction or ""),
            _escape(entity.sector or ""),
            _escape(entity.relation),
            _escape(context.game_time or ""),
        ]
    )


def encode_chat_request(request: ChatRequest) -> str:
    entity = request.entity
    return "|".join(
        [
            PREFIX,
            VERSION,
            "CHAT_REQUEST",
            _escape(request.request_id),
            _escape(request.conversation_id),
            _escape(entity.entity_id),
            _escape(entity.name),
            _escape(entity.kind),
            _escape(entity.race or ""),
            _escape(entity.faction or ""),
            _escape(entity.sector or ""),
            _escape(entity.relation),
            _escape(request.game_time or ""),
            _escape(request.message),
        ]
    )


def encode_chat_response(response: DialogueResponse) -> str:
    return "|".join(
        [
            PREFIX,
            VERSION,
            "CHAT_RESPONSE",
            _escape(response.request_id),
            _escape(response.conversation_id),
            _escape(response.mood),
            _escape(response.reply),
        ]
    )


def encode_bridge_error(error: BridgeError) -> str:
    return "|".join(
        [
            PREFIX,
            VERSION,
            "CHAT_ERROR",
            _escape(error.request_id),
            _escape(error.code),
            _escape(error.message),
        ]
    )
