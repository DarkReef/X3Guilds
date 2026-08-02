from __future__ import annotations

from fastapi import FastAPI, HTTPException

from x3guilds_ai.config import Settings
from x3guilds_ai.memory import SQLiteMemoryStore
from x3guilds_ai.models import ChatRequest, DialogueResponse
from x3guilds_ai.providers.gigachat import GigaChatProvider
from x3guilds_ai.providers.mock import MockDialogueProvider
from x3guilds_ai.service import ChatService


def build_service(settings: Settings) -> ChatService:
    memory = SQLiteMemoryStore(settings.database_path)
    if settings.provider == "mock":
        provider = MockDialogueProvider()
    elif settings.provider == "gigachat":
        if not settings.gigachat_credentials:
            raise ValueError("X3AI_GIGACHAT_CREDENTIALS is required for gigachat provider")
        provider = GigaChatProvider(
            credentials=settings.gigachat_credentials,
            scope=settings.gigachat_scope,
            model=settings.gigachat_model,
            base_url=settings.gigachat_base_url,
            oauth_url=settings.gigachat_oauth_url,
            verify_ssl=settings.gigachat_verify_ssl,
        )
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")

    return ChatService(
        provider=provider,
        memory=memory,
        history_limit=settings.history_limit,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    service = build_service(settings)
    app = FastAPI(title="X3 Guilds AI Orchestrator", version="0.1.0")

    @app.on_event("startup")
    async def startup() -> None:
        await service.initialize()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "provider": settings.provider}

    @app.post("/v1/chat", response_model=DialogueResponse)
    async def chat(request: ChatRequest) -> DialogueResponse:
        try:
            return await service.chat(request)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("x3guilds_ai.api:app", host="127.0.0.1", port=8765, reload=False)
