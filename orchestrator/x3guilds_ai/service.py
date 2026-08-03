from __future__ import annotations

from x3guilds_ai.memory import SQLiteMemoryStore
from x3guilds_ai.models import ChatRequest, DialogueResponse, StoredMessage
from x3guilds_ai.providers.base import DialogueProvider


class ChatService:
    def __init__(
        self,
        *,
        provider: DialogueProvider,
        memory: SQLiteMemoryStore,
        history_limit: int = 12,
        memory_limit: int = 20,
    ) -> None:
        self._provider = provider
        self._memory = memory
        self._history_limit = history_limit
        self._memory_limit = memory_limit

    async def initialize(self) -> None:
        await self._memory.initialize()

    async def chat(self, request: ChatRequest) -> DialogueResponse:
        cached = await self._memory.get_cached(request)
        if cached is not None:
            return cached

        history = await self._memory.recent(request.conversation_id, self._history_limit)
        persistent_memories = await self._memory.memories(
            request.conversation_id,
            self._memory_limit,
        )
        merged_memories = list(dict.fromkeys([*persistent_memories, *request.entity.facts]))
        generated = await self._provider.generate(request, history, merged_memories)
        response = DialogueResponse(
            request_id=request.request_id,
            conversation_id=request.conversation_id,
            provider=self._provider.name,
            **generated.model_dump(),
        )

        await self._memory.append(
            request.conversation_id,
            StoredMessage(role="user", content=request.message),
        )
        await self._memory.append(
            request.conversation_id,
            StoredMessage(role="assistant", content=response.reply),
        )
        await self._memory.add_memories(
            request.conversation_id,
            request.entity.entity_id,
            response.memories,
        )
        await self._memory.cache(request, response)
        return response
