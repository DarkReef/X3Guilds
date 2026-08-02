from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from x3guilds_ai.api import build_service
from x3guilds_ai.config import Settings
from x3guilds_ai.file_bridge import FileBridge


async def _run(args: argparse.Namespace) -> None:
    settings = Settings.from_env()
    service = build_service(settings)
    await service.initialize()
    bridge = FileBridge(
        service=service,
        input_path=args.input,
        output_path=args.output,
        checkpoint_path=args.checkpoint,
    )
    if args.once:
        await bridge.process_available()
    else:
        await bridge.run_forever(args.poll_interval)


def run() -> None:
    parser = argparse.ArgumentParser(description="Tail an X3 Guilds AI bridge log")
    parser.add_argument("--input", type=Path, default=Path("./log09980.txt"))
    parser.add_argument("--output", type=Path, default=Path("./x3guilds-ai-outbox.log"))
    parser.add_argument("--checkpoint", type=Path, default=Path("./data/bridge-checkpoint.json"))
    parser.add_argument("--poll-interval", type=float, default=0.5)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    run()
