# X3 Guilds AI Orchestrator

External, testable dialogue layer for the X3: Farnham's Legacy Guilds mod.
The game remains the authority for objects and economy. The service owns dialogue,
conversation memory, provider access and idempotency.

## Run in deterministic mock mode

```bash
cd orchestrator
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'
cp .env.example .env
x3guilds-ai
```

The API listens on `127.0.0.1:8765`:

```bash
curl http://127.0.0.1:8765/health
curl -X POST http://127.0.0.1:8765/v1/chat \
  -H 'Content-Type: application/json' \
  -d @examples/chat-request.json
```

## Enable GigaChat

Set environment variables before launch:

```text
X3AI_PROVIDER=gigachat
X3AI_GIGACHAT_CREDENTIALS=<authorization key, not an access token>
X3AI_GIGACHAT_SCOPE=GIGACHAT_API_PERS
X3AI_GIGACHAT_MODEL=GigaChat-2
```

Credentials are exchanged for a short-lived OAuth token and are never written to
SQLite or the game logs.

## Safety boundary

Model output is validated against a strict schema. The only accepted action types are:

- `show_message`
- `remember_fact`
- `publish_bbs_news`
- `create_trade_offer`
- `offer_mission`

This milestone does not execute those actions in X3. It only returns typed intents for
a later game-side validator.

## Bridge protocol

`x3guilds_ai.bridge` defines a percent-encoded, one-line protocol suitable for X3 log
files. See `docs/AI_CHAT_ARCHITECTURE.md` in the repository root.

## Consume an X3 log file

The file bridge tails only new lines and stores an atomic checkpoint:

```bash
x3guilds-ai-bridge \
  --input 'C:/Users/<user>/Documents/Egosoft/X3FL/log09980.txt' \
  --output './data/x3guilds-ai-outbox.log'
```

Use `--once` in diagnostics and CI. Re-running the bridge cannot trigger another model
call for an already processed `request_id`.
