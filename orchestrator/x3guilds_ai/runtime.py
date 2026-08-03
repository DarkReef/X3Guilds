from __future__ import annotations

import argparse
import asyncio
import logging
import threading
import uuid
from pathlib import Path

from x3guilds_ai.config import Settings
from x3guilds_ai.factory import create_service
from x3guilds_ai.file_bridge import FileBridge
from x3guilds_ai.models import ChatRequest
from x3guilds_ai.overlay import ChatOverlay, OverlayEvent, OverlayEventQueue
from x3guilds_ai.paths import detect_request_log


logger = logging.getLogger(__name__)


def _request_path(settings: Settings) -> Path:
    return settings.request_log_path or detect_request_log()


async def _run_once(bridge: FileBridge) -> int:
    await bridge.service.initialize()
    return await bridge.run_once()


async def _run_console_worker(bridge: FileBridge, poll_interval: float) -> None:
    await bridge.service.initialize()
    stop = asyncio.Event()
    try:
        await bridge.run_forever(poll_interval=poll_interval, stop_event=stop)
    finally:
        stop.set()


async def _run_overlay_worker(
    bridge: FileBridge,
    events: OverlayEventQueue,
    *,
    poll_interval: float,
    worker_stop: threading.Event,
) -> None:
    await bridge.service.initialize()
    events.put(OverlayEvent("status", "Система", f"Слежение: {bridge.request_path}"))

    while not worker_stop.is_set():
        await bridge.run_once()
        for submission in events.drain_submissions():
            context = submission.context
            request = ChatRequest(
                request_id=str(uuid.uuid4()),
                conversation_id=f"x3:{context.entity.entity_id}",
                message=submission.message,
                entity=context.entity,
                game_time=context.game_time,
                metadata={"source": "desktop_overlay", "context_id": context.context_id},
            )
            await bridge.process_request(request)
        await asyncio.sleep(poll_interval)


def run_desktop() -> None:
    parser = argparse.ArgumentParser(description="X3 Guilds GigaChat desktop sidecar")
    parser.add_argument("--no-overlay", action="store_true", help="run without Tk overlay")
    parser.add_argument("--once", action="store_true", help="process current log tail once")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    request_path = _request_path(settings)
    service = create_service(settings)
    events = OverlayEventQueue()
    bridge = FileBridge(
        request_path=request_path,
        response_path=settings.response_log_path,
        checkpoint_path=settings.checkpoint_path,
        diagnostics_path=settings.diagnostics_path,
        service=service,
        callback=events.bridge_callback,
        context_callback=events.context_callback,
    )

    logger.info("Watching X3FL log: %s", request_path)
    logger.info("Provider: %s", settings.provider)

    if args.once:
        count = asyncio.run(_run_once(bridge))
        logger.info("Processed %s protocol record(s)", count)
        return

    overlay_enabled = settings.overlay_enabled and not args.no_overlay
    if not overlay_enabled:
        try:
            asyncio.run(_run_console_worker(bridge, settings.poll_interval_ms / 1000))
        except KeyboardInterrupt:
            return
        return

    worker_stop = threading.Event()

    def worker() -> None:
        asyncio.run(
            _run_overlay_worker(
                bridge,
                events,
                poll_interval=settings.poll_interval_ms / 1000,
                worker_stop=worker_stop,
            )
        )

    thread = threading.Thread(target=worker, name="x3guilds-ai-worker", daemon=True)
    thread.start()

    try:
        overlay = ChatOverlay(
            events=events,
            width=settings.overlay_width,
            height=settings.overlay_height,
            always_on_top=settings.overlay_always_on_top,
            on_close=worker_stop.set,
        )
        overlay.run()
    except ImportError:
        logger.warning("Tkinter is unavailable; rerun with --no-overlay")
    finally:
        worker_stop.set()
        thread.join(timeout=5)
