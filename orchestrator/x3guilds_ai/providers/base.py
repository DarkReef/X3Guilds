from __future__ import annotations

from typing import Protocol

from x3guilds_ai.models import ChatRequest, ModelDialogue, StoredMessage


class DialogueProvider(Protocol):
    name: str

    async def generate(
        self,
        request: ChatRequest,
        history: list[StoredMessage],
    ) -> ModelDialogue: ...
