import pytest
from pydantic import ValidationError

from x3guilds_ai.models import ActionIntent


def test_action_payload_is_strict() -> None:
    action = ActionIntent(type="create_trade_offer", payload={"ware": "Ore", "amount": 5, "unit_price": 12})
    assert action.payload == {"ware": "Ore", "amount": 5, "unit_price": 12}


def test_action_rejects_extra_fields() -> None:
    with pytest.raises((ValidationError, ValueError)):
        ActionIntent(type="show_message", payload={"text": "ok", "script": "destroy all"})
