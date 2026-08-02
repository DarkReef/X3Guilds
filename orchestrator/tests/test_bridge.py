from urllib.parse import quote

from x3guilds_ai.bridge import encode_chat_response, parse_chat_request
from x3guilds_ai.models import DialogueResponse


def e(value: str) -> str:
    return quote(value, safe="")


def test_line_protocol_round_trip() -> None:
    line = "|".join(
        [
            "XUGC",
            "1",
            "CHAT_REQUEST",
            e("request-0001"),
            e("conversation-7"),
            e("ship-42"),
            e("Капитан Хаалас"),
            "ship",
            e("Телади"),
            e("PTNI"),
            e("Profit Center Alpha"),
            "23",
            "18443300",
            e("Назовите вашу цену."),
        ]
    )

    request = parse_chat_request(line)
    assert request.entity.name == "Капитан Хаалас"
    assert request.message == "Назовите вашу цену."
    assert request.game_time == 18443300

    response = DialogueResponse(
        request_id=request.request_id,
        conversation_id=request.conversation_id,
        provider="mock",
        reply="Предлагаю 16 кредитов за единицу.",
        mood="calculating",
    )
    encoded = encode_chat_response(response)
    assert encoded.startswith("XUGC|1|CHAT_RESPONSE|request-0001|")
    assert "%D0" in encoded
