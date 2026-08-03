from x3guilds_ai.bridge import (
    encode_chat_request,
    encode_chat_response,
    encode_context_selection,
    parse_chat_request,
    parse_context_selection,
)
from x3guilds_ai.models import (
    ChatRequest,
    ContextSelection,
    DialogueResponse,
    EntityContext,
)


def make_entity() -> EntityContext:
    return EntityContext(
        entity_id="x3-1",
        name="Капитан | Тон",
        kind="ship",
        race="Teladi",
        faction="PTNI",
        sector="Profit Center Alpha",
        relation=100,
    )


def make_request() -> ChatRequest:
    return ChatRequest(
        request_id="req-0001",
        conversation_id="npc:x3-1",
        message="Цена | и %?",
        game_time=42,
        entity=make_entity(),
    )


def test_request_round_trip() -> None:
    request = make_request()
    assert parse_chat_request(encode_chat_request(request)) == request


def test_context_round_trip() -> None:
    context = ContextSelection(context_id="ctx-1", entity=make_entity(), game_time=42)
    assert parse_context_selection(encode_context_selection(context)) == context


def test_parser_accepts_log_prefix() -> None:
    request = make_request()
    line = "2026-08-03 00:00:00 INFO " + encode_chat_request(request)
    assert parse_chat_request(line) == request


def test_response_is_one_line() -> None:
    response = DialogueResponse(
        request_id="req-0001",
        conversation_id="npc:x3-1",
        provider="mock",
        reply="Принято\nкапитан.",
        mood="calm",
        memories=[],
        actions=[],
    )
    encoded = encode_chat_response(response)
    assert encoded.startswith("XUGC|1|CHAT_RESPONSE|")
    assert "\n" not in encoded
