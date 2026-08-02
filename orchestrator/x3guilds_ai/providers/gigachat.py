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
        self._token: _AccessToken | None = None
        self._token_lock = asyncio.Lock()

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        now = time.time()
        if self._token and self._token.expires_at - 60 > now:
            return self._token.value

        async with self._token_lock:
            now = time.time()
            if self._token and self._token.expires_at - 60 > now:
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
    def _system_prompt(request: ChatRequest) -> str:
        entity = request.entity
        facts = "\n".join(f"- {fact}" for fact in entity.facts) or "- Нет дополнительных фактов"
        return f"""Ты играешь роль персонажа во вселенной X3: Farnham's Legacy.
Никогда не изменяй численные факты мира и не обещай действий вне разрешённого списка.
Отвечай по-русски, кратко и в характере персонажа.

Собеседник:
- имя: {entity.name}
- тип: {entity.kind}
- раса: {entity.race or 'не указана'}
- фракция: {entity.faction or 'не указана'}
- сектор: {entity.sector or 'не указан'}
- отношение к игроку: {entity.relation}
- корпус: {entity.hull_percent if entity.hull_percent is not None else 'неизвестно'}

Известные факты:
{facts}

Разрешённые намерения: show_message, remember_fact, publish_bbs_news,
create_trade_offer, offer_mission. Не создавай иных типов действий."""

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        schema = ModelDialogue.model_json_schema()
        schema["additionalProperties"] = False
        return schema

    async def generate(
        self,
        request: ChatRequest,
        history: list[StoredMessage],
    ) -> ModelDialogue:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt(request)},
        ]
        messages.extend({"role": item.role, "content": item.content} for item in history)
        messages.append({"role": "user", "content": request.message})

        async with httpx.AsyncClient(
            verify=self._verify_ssl,
            timeout=self._timeout,
        ) as client:
            token = await self._get_token(client)
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
            payload = response.json()

        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, dict):
            return ModelDialogue.model_validate(content)
        if not isinstance(content, str):
            raise ValueError("Unexpected GigaChat response content")
        try:
            return ModelDialogue.model_validate_json(content)
        except Exception as exc:
            raise ValueError(f"Invalid structured GigaChat response: {json.dumps(content)}") from exc
