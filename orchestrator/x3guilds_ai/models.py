from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


AllowedAction = Literal[
    "show_message",
    "remember_fact",
    "publish_bbs_news",
    "create_trade_offer",
    "offer_mission",
]


class EntityContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=160)
    kind: Literal["ship", "station", "person", "corporation"]
    race: str | None = Field(default=None, max_length=80)
    faction: str | None = Field(default=None, max_length=120)
    sector: str | None = Field(default=None, max_length=120)
    relation: int = Field(default=0, ge=-1_000_000, le=1_000_000)
    hull_percent: float | None = Field(default=None, ge=0, le=100)
    cargo: dict[str, int] = Field(default_factory=dict)
    facts: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("cargo")
    @classmethod
    def validate_cargo(cls, value: dict[str, int]) -> dict[str, int]:
        if len(value) > 64:
            raise ValueError("cargo contains too many ware entries")
        if any(amount < 0 for amount in value.values()):
            raise ValueError("cargo amounts cannot be negative")
        return value


class ContextSelection(BaseModel):
    """The object selected in X3 for an external overlay conversation."""

    model_config = ConfigDict(extra="forbid")

    context_id: str = Field(min_length=1, max_length=128)
    entity: EntityContext
    game_time: int | None = Field(default=None, ge=0)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=8, max_length=128)
    conversation_id: str = Field(min_length=1, max_length=128)
    player_id: str = Field(default="player", min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=2000)
    entity: EntityContext
    game_time: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude={"request_id"})
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ActionIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: AllowedAction
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload(self) -> "ActionIntent":
        from x3guilds_ai.actions import validate_action_payload

        self.payload = validate_action_payload(self.type, self.payload)
        return self


class ModelDialogue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: str = Field(min_length=1, max_length=2500)
    mood: str = Field(default="neutral", min_length=1, max_length=64)
    memories: list[str] = Field(default_factory=list, max_length=5)
    actions: list[ActionIntent] = Field(default_factory=list, max_length=3)


class DialogueResponse(ModelDialogue):
    request_id: str
    conversation_id: str
    provider: str
    cached: bool = False


class StoredMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class BridgeError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=1000)
