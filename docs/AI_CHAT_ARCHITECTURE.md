# Guilds AI Chat: architecture and bridge contract

## Authority split

- X3FL/Guilds owns ships, stations, cargo, credits, notoriety and mission state.
- The orchestrator owns dialogue generation, durable conversation history and request deduplication.
- GigaChat may propose typed intents but cannot invoke arbitrary XScript.

## Milestone 1 data flow

```text
X3 exporter -> log09980.txt -> bridge adapter -> POST /v1/chat
                                           -> SQLite memory
                                           -> Mock or GigaChat provider
                                           -> validated DialogueResponse
```

The return channel into a running X3FL process is deliberately not assumed. It must
pass a separate bridge probe before model-generated text is displayed inside the game.
An overlay or a generated command resource can consume the same response meanwhile.

## Line protocol

Requests use a single UTF-8 line. Dynamic values are URL-percent-encoded.

```text
XUGC|1|CHAT_REQUEST|request_id|conversation_id|entity_id|name|kind|race|faction|sector|relation|game_time|message
```

Responses:

```text
XUGC|1|CHAT_RESPONSE|request_id|conversation_id|mood|reply
```

Properties:

- `request_id` is globally unique and makes processing idempotent;
- an identical request is returned from SQLite without another model call;
- malformed lines are rejected before provider invocation;
- protocol version is explicit;
- no secret is ever transferred through the game log.

## Next bridge probe

The next game-side patch should prove this cycle before adding menus or economic actions:

1. X3 writes a fixed `CHAT_REQUEST` line.
2. Python parses it and produces a mock response.
3. A controlled return-channel prototype displays the response.
4. X3 writes an acknowledgement containing the same `request_id`.
5. Replaying the command does not display or execute it twice.

Only after this succeeds under normal speed, SETA, save/load and service restart should
the bridge be connected to GigaChat and Guilds actions.
