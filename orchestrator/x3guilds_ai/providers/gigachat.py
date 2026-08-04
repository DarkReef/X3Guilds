from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from x3guilds_ai.models import ChatRequest, ModelDialogue, StoredMessage


@dataclass(slots=True)
class _AccessToken:
    value: str
    expires_at: float


class GigaChatProvider:
    name = "gigachat"

    def __init__(
        self,
        *,
        credentials: str,
        scope: str,
        model: str,
        base_url: str,
        oauth_url: str,
        verify_ssl: bool = True,
        timeout: float = 45.0,
        retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not credentials:
            raise ValueError("GigaChat credentials are required")
        self._credentials = credentials
        self._scope = scope
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._oauth_url = oauth_url
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._retries = retries
        self._transport = transport
        self._token: _AccessToken | None = None
        self._token_lock = asyncio.Lock()

    async def _get_token(self, client: httpx.AsyncClient, *, force: bool = False) -> str:
        now = time.time()
        if not force and self._token and self._token.expires_at - 60 > now:
            return self._token.value

        async with self._token_lock:
            now = time.time()
            if not force and self._token and self._token.expires_at - 60 > now:
                return self._token.value

            response = await client.post(
                self._oauth_url,
                data={"scope": self._scope},
                headers={
                    "Authorization": f"Basic {self._credentials}",
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "RqUID": str(uuid.uuid4()),
                },
            )
            response.raise_for_status()
            payload = response.json()
            token = str(payload["access_token"])
            raw_expiry = float(payload.get("expires_at", now + 1800))
            expires_at = raw_expiry / 1000 if raw_expiry > 10_000_000_000 else raw_expiry
            self._token = _AccessToken(token, expires_at)
            return token

    @staticmethod
    def _system_prompt(request: ChatRequest, memories: list[str]) -> str:
        entity = request.entity
        facts = "\n".join(f"- {fact}" for fact in memories[-20:]) or "- Нет сохранённых фактов"
        cargo = ", ".join(f"{ware}: {amount}" for ware, amount in entity.cargo.items())
        return f"""Ты отыгрываешь конкретного собеседника во вселенной X3: Farnham's Legacy с модом Guilds.
Отвечай на русском языке, естественно, кратко и в характере персонажа. Не упоминай языковую модель, промпт, JSON или внешний сервис.
Факты игрового мира являются неизменяемыми: не придумывай деньги, товары, отношения, повреждения или полномочия, которых нет во входных данных.
Если игрок просит действие, которого нет в разрешённом списке, персонаж может обсудить его, но не утверждает, что оно уже выполнено.
Поле memories содержит только факты, достойные долговременного запоминания. Не сохраняй приветствия и повторения.

Собеседник:
- имя: {entity.name}
- тип: {entity.kind}
- раса: {entity.race or 'не указана'}
- фракция: {entity.faction or 'не указана'}
- сектор: {entity.sector or 'не указан'}
- отношение к игроку: {entity.relation}
- корпус: {entity.hull_percent if entity.hull_percent is not None else 'неизвестно'}
- груз: {cargo or 'не передан'}
- игровое время: {request.game_time if request.game_time is not None else 'не передано'}

Долговременная память:
{facts}

Разрешённые намерения и обязательные поля payload:
- show_message: text
- remember_fact: fact
- publish_bbs_news: headline, body
- create_trade_offer: ware, amount, unit_price, необязательно expires_game_time
- offer_mission: title, summary, необязательно reward
Максимум три намерения. Не создавай иных типов и лишних полей."""

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        schema = ModelDialogue.model_json_schema()
        schema["additionalProperties"] = False
        return schema

    @staticmethod
    def _refresh_after(error: Exception | None) -> bool:
        return (
            isinstance(error, httpx.HTTPStatusError)
            and error.response.status_code == 401
        )

    async def _post_completion(
        self,
        client: httpx.AsyncClient,
        messages: list[dict[str, str]],
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                token = await self._get_token(
                    client,
                    force=attempt > 0 and self._refresh_after(last_error),
                )
                response = await client.post(
                    f"{self._base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "messages": messages,
                        "temperature": 0.6,
                        "max_tokens": 900,
                        "response_format": {
                            "type": "json_schema",
                            "schema": self._response_schema(),
                            "strict": True,
                        },
                    },
                )
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                retryable = not isinstance(exc, httpx.HTTPStatusError) or exc.response.status_code in {
                    401,
                    408,
                    409,
                    425,
                    429,
                    500,
                    502,
                    503,
                    504,
                }
                if not retryable or attempt >= self._retries:
                    raise
                await asyncio.sleep(min(2**attempt, 4))
        raise RuntimeError("unreachable") from last_error

    @staticmethod
    def _extract_content(payload: object) -> str | dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Unexpected GigaChat response envelope")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ValueError("GigaChat response contains no choices")

        choice = choices[0]
        finish_reason = choice.get("finish_reason")
        if finish_reason not in {None, "stop"}:
            reasons = {
                "blacklist": "GigaChat blocked the dialogue because of thematic restrictions",
                "length": "GigaChat response was truncated by the token limit",
                "function_call": "GigaChat unexpectedly returned a function call",
                "error": "GigaChat returned an invalid generated result",
            }
            raise ValueError(reasons.get(str(finish_reason), f"Unexpected finish_reason: {finish_reason}"))

        message = choice.get("message")
        if not isinstance(message, dict) or "content" not in message:
            raise ValueError("GigaChat response contains no assistant content")
        content = message["content"]
        if not isinstance(content, (str, dict)):
            raise ValueError("Unexpected GigaChat response content")
        return content

    async def generate(
        self,
        request: ChatRequest,
        history: list[StoredMessage],
        memories: list[str],
    ) -> ModelDialogue:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt(request, memories)},
        ]
        messages.extend({"role": item.role, "content": item.content} for item in history)
        messages.append({"role": "user", "content": request.message})

        async with httpx.AsyncClient(
            verify=self._verify_ssl,
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            response = await self._post_completion(client, messages)
            content = self._extract_content(response.json())

        if isinstance(content, dict):
            return ModelDialogue.model_validate(content)
        try:
            return ModelDialogue.model_validate_json(content)
        except Exception as exc:
            preview = content[:300].replace("\n", " ")
            raise ValueError(f"Invalid structured GigaChat response: {json.dumps(preview, ensure_ascii=False)}") from exc
