from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class _StrictPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ShowMessagePayload(_StrictPayload):
    text: str = Field(min_length=1, max_length=500)


class RememberFactPayload(_StrictPayload):
    fact: str = Field(min_length=1, max_length=500)


class PublishNewsPayload(_StrictPayload):
    headline: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=1200)


class TradeOfferPayload(_StrictPayload):
    ware: str = Field(min_length=1, max_length=120)
    amount: int = Field(gt=0, le=1_000_000)
    unit_price: int = Field(ge=0, le=2_000_000_000)
    expires_game_time: int | None = Field(default=None, ge=0)


class MissionOfferPayload(_StrictPayload):
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=1200)
    reward: int | None = Field(default=None, ge=0, le=2_000_000_000)


_PAYLOAD_MODELS: dict[str, type[_StrictPayload]] = {
    "show_message": ShowMessagePayload,
    "remember_fact": RememberFactPayload,
    "publish_bbs_news": PublishNewsPayload,
    "create_trade_offer": TradeOfferPayload,
    "offer_mission": MissionOfferPayload,
}


def validate_action_payload(action_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    model = _PAYLOAD_MODELS.get(action_type)
    if model is None:
        raise ValueError(f"unsupported action type: {action_type}")
    try:
        return model.model_validate(payload).model_dump(exclude_none=True)
    except ValidationError as exc:
        raise ValueError(f"invalid payload for {action_type}: {exc}") from exc
