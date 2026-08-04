import json
import time

import httpx
import pytest

from x3guilds_ai.models import ChatRequest, EntityContext
from x3guilds_ai.providers.gigachat import GigaChatProvider


def request() -> ChatRequest:
    return ChatRequest(
        request_id="request-123",
        conversation_id="npc:ship-1",
        message="На связь.",
        entity=EntityContext(
            entity_id="ship-1",
            name="Капитан Талос",
            kind="ship",
            race="Argon",
        ),
    )


def provider(transport: httpx.AsyncBaseTransport, *, retries: int = 0) -> GigaChatProvider:
    return GigaChatProvider(
        credentials="test-credentials",
        scope="GIGACHAT_API_PERS",
        model="GigaChat-2",
        base_url="https://mock.local",
        oauth_url="https://mock.local/api/v2/oauth",
        retries=retries,
        transport=transport,
    )


def successful_completion() -> dict[str, object]:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "reply": "Канал открыт.",
                            "mood": "neutral",
                            "memories": [],
                            "actions": [],
                        },
                        ensure_ascii=False,
                    ),
                },
                "finish_reason": "stop",
            }
        ]
    }


@pytest.mark.asyncio
async def test_blacklist_finish_reason_fails_closed() -> None:
    async def handler(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path == "/api/v2/oauth":
            return httpx.Response(
                200,
                json={
                    "access_token": "token",
                    "expires_at": int((time.time() + 1800) * 1000),
                },
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": ""},
                        "finish_reason": "blacklist",
                    }
                ]
            },
        )

    dialogue_provider = provider(httpx.MockTransport(handler))
    with pytest.raises(ValueError, match="thematic restrictions"):
        await dialogue_provider.generate(request(), [], [])


@pytest.mark.asyncio
async def test_429_retry_reuses_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    oauth_calls = 0
    completion_calls = 0

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("x3guilds_ai.providers.gigachat.asyncio.sleep", no_sleep)

    async def handler(http_request: httpx.Request) -> httpx.Response:
        nonlocal oauth_calls, completion_calls
        if http_request.url.path == "/api/v2/oauth":
            oauth_calls += 1
            return httpx.Response(
                200,
                json={
                    "access_token": "token",
                    "expires_at": int((time.time() + 1800) * 1000),
                },
            )

        completion_calls += 1
        if completion_calls == 1:
            return httpx.Response(429, json={"message": "rate limited"})
        return httpx.Response(200, json=successful_completion())

    dialogue_provider = provider(httpx.MockTransport(handler), retries=1)
    result = await dialogue_provider.generate(request(), [], [])

    assert result.reply == "Канал открыт."
    assert oauth_calls == 1
    assert completion_calls == 2


@pytest.mark.asyncio
async def test_401_retry_refreshes_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    oauth_calls = 0
    completion_calls = 0

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("x3guilds_ai.providers.gigachat.asyncio.sleep", no_sleep)

    async def handler(http_request: httpx.Request) -> httpx.Response:
        nonlocal oauth_calls, completion_calls
        if http_request.url.path == "/api/v2/oauth":
            oauth_calls += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"token-{oauth_calls}",
                    "expires_at": int((time.time() + 1800) * 1000),
                },
            )

        completion_calls += 1
        if completion_calls == 1:
            return httpx.Response(401, json={"message": "expired"})
        assert http_request.headers["Authorization"] == "Bearer token-2"
        return httpx.Response(200, json=successful_completion())

    dialogue_provider = provider(httpx.MockTransport(handler), retries=1)
    result = await dialogue_provider.generate(request(), [], [])

    assert result.reply == "Канал открыт."
    assert oauth_calls == 2
    assert completion_calls == 2
