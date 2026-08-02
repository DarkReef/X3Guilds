from __future__ import annotations

from x3guilds_ai.models import ChatRequest, ModelDialogue, StoredMessage


class MockDialogueProvider:
    """Deterministic provider for tests and offline play."""

    name = "mock"

    async def generate(
        self,
        request: ChatRequest,
        history: list[StoredMessage],
    ) -> ModelDialogue:
        entity = request.entity
        faction = entity.faction or entity.race or "независимый капитан"
        sector = f" в секторе {entity.sector}" if entity.sector else ""
        return ModelDialogue(
            reply=(
                f"{entity.name}, {faction}{sector}, на связи. "
                f"Ваш запрос принят: «{request.message}»."
            ),
            mood="professional",
            memories=[f"Игрок обратился с запросом: {request.message[:180]}"],
            actions=[],
        )
