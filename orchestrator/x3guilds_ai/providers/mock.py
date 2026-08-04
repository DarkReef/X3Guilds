from __future__ import annotations

from x3guilds_ai.models import ChatRequest, ModelDialogue, StoredMessage


class MockDialogueProvider:
    name = "mock"

    async def generate(
        self,
        request: ChatRequest,
        history: list[StoredMessage],
        memories: list[str],
    ) -> ModelDialogue:
        suffix = f" Мы уже говорили {len(history) // 2} раз." if history else ""
        memory_hint = f" Я помню: {memories[-1]}." if memories else ""
        return ModelDialogue(
            reply=(
                f"{request.entity.name} принимает сообщение: «{request.message}»."
                f" Канал связи работает.{suffix}{memory_hint}"
            ),
            mood="neutral",
            memories=[f"Игрок сказал: {request.message[:240]}"],
            actions=[],
        )
