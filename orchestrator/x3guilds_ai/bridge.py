from __future__ import annotations

from urllib.parse import quote, unquote

from x3guilds_ai.models import ChatRequest, DialogueResponse, EntityContext


PREFIX = "XUGC"
VERSION = "1"


def _escape(value: object) -> str:
    return quote(str(value), safe="")


def _unescape(value: str) -> str:
    return unquote(value)


def parse_chat_request(line: str) -> ChatRequest:
    """Parse one X3 log line into a validated request.

    Protocol fields:
    XUGC|1|CHAT_REQUEST|request|conversation|entity_id|name|kind|race|faction|
    sector|relation|game_time|message
    """
    parts = line.strip().split("|")
    if len(parts) != 14 or parts[:3] != [PREFIX, VERSION, "CHAT_REQUEST"]:
        raise ValueError("Invalid XUGC chat request line")

    (
        request_id,
        conversation_id,
        entity_id,
        name,
        kind,
        race,
        faction,
        sector,
        relation,
        game_time,
        message,
    ) = (_unescape(item) for item in parts[3:])

    return ChatRequest(
        request_id=request_id,
        conversation_id=conversation_id,
        message=message,
        game_time=int(game_time) if game_time else None,
        entity=EntityContext(
            entity_id=entity_id,
            name=name,
            kind=kind,
            race=race or None,
            faction=faction or None,
            sector=sector or None,
            relation=int(relation),
        ),
    )


def encode_chat_response(response: DialogueResponse) -> str:
    return "|".join(
        [
            PREFIX,
            VERSION,
            "CHAT_RESPONSE",
            _escape(response.request_id),
            _escape(response.conversation_id),
            _escape(response.mood),
            _escape(response.reply),
        ]
    )
