# Guilds Living Communications architecture

## Complete runtime path

```text
X3 tracking target
  -> registered XScript hotkey
  -> XUGC CHAT_CONTEXT record in log09980.txt
  -> checkpointed Python tailer
  -> active target in Tk overlay
  -> player text submission
  -> validated ChatRequest
  -> recent dialogue + durable memories from SQLite
  -> Mock or GigaChat provider
  -> strict ModelDialogue JSON schema
  -> validated, logged response
  -> always-on-top overlay
```

The return path intentionally terminates in the overlay. Standard MSCI can reliably write logs, but no supported, low-risk real-time mechanism lets an external process inject arbitrary text into a running save. This design therefore gives a fully usable live chat without DLL injection or savegame mutation.

## Protocol

### Target selection

```text
XUGC|1|CHAT_CONTEXT|context_id|entity_id|name|kind|race|faction|sector|relation|game_time
```

### Optional direct request

```text
XUGC|1|CHAT_REQUEST|request_id|conversation_id|entity_id|name|kind|race|faction|sector|relation|game_time|message
```

Fields produced by Python are percent-encoded. X3-generated context fields are treated as untrusted and validated by Pydantic. The parser extracts an embedded record from timestamped or prefixed X3 log lines.

## Reliability

- checkpointer stores byte offset plus a hash of the immutable prefix already consumed;
- appending to a short log does not replay prior records;
- truncation or replacement resets the offset;
- request IDs are idempotent and tied to a payload fingerprint;
- duplicate IDs with different payloads fail closed;
- SQLite runs in WAL mode;
- GigaChat access tokens are cached and refreshed before expiry;
- transient HTTP failures are retried with bounded backoff;
- all provider output is parsed through a strict JSON schema;
- model action payloads use per-action Pydantic schemas.

## Security model

No GigaChat key enters X3, the savegame, diagnostics, or Git. The model can only propose an allowlisted intent. This PR does not execute model intents in X3. A later corporation/economy milestone must add a deterministic validator and explicit game-side executor for each action type.

## In-game source

The XScript source is stored under `scripts/working`. XScript Compiler 0.8 compiles it into native X3FL XML. The setup script registers one event hotkey; the hotkey exports only the current target's identity and context.

## Testing boundary

The Python runtime is fully unit-tested and runs in CI. The generated X3 XML must be compiled with the official XScript Compiler and smoke-tested in a local Guilds installation because CI has neither the proprietary game data nor a running X3FL process.
