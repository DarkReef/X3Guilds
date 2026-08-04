from x3guilds_ai.models import (
    ChatRequest,
    ContextSelection,
    DialogueResponse,
    EntityContext,
)
from x3guilds_ai.overlay import OverlayEventQueue


def entity() -> EntityContext:
    return EntityContext(entity_id="overlay", name="Captain", kind="ship")


def test_overlay_queue_receives_context_and_submission() -> None:
    events = OverlayEventQueue()
    context = ContextSelection(context_id="context-1", entity=entity(), game_time=7)
    events.context_callback(context)
    assert events.submit("Hello") is True
    submission = events.drain_submissions()[0]
    assert submission.context == context
    assert submission.message == "Hello"
    assert events.drain()[0].kind == "context"


def test_overlay_queue_receives_dialogue() -> None:
    events = OverlayEventQueue()
    request = ChatRequest(
        request_id="overlay-1",
        conversation_id="npc:overlay",
        message="Hello",
        entity=entity(),
    )
    response = DialogueResponse(
        request_id=request.request_id,
        conversation_id=request.conversation_id,
        provider="mock",
        reply="Acknowledged",
        mood="calm",
        memories=[],
        actions=[],
    )
    events.bridge_callback(request, response)
    drained = events.drain()
    assert [event.kind for event in drained] == ["request", "response"]
