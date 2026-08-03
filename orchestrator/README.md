# X3 Guilds · Living Communications

A testable external dialogue and long-term-memory sidecar for **X3: Farnham's Legacy — Guilds**.

The in-game script only selects a real X3 object and emits a compact context record to `log09980.txt`. The desktop sidecar tails that log, opens an always-on-top conversation overlay, calls either a deterministic mock provider or GigaChat, validates structured intents, and stores dialogue memory in SQLite.

## Authority boundary

- **X3/Guilds owns:** objects, sectors, relations, economy, inventories, combat, savegame state.
- **The sidecar owns:** natural-language dialogue, conversational memory, diagnostics, provider retries.
- **The model cannot execute arbitrary XScript.** Its optional intents are schema-validated and are not applied to the savegame in this milestone.

## Requirements

- Windows 10/11
- Python 3.11+
- X3FL with the current Guilds/Unofficial Patch installation
- XScript Compiler 0.8 to build the two `.xs` game scripts
- GigaChat authorization key only when using the real provider

## Install the sidecar

```powershell
cd orchestrator
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
```

Edit `.env`:

```env
X3AI_PROVIDER=gigachat
X3AI_GIGACHAT_CREDENTIALS=<authorization key>
```

Environment variables can be loaded in PowerShell before launch, or use `run-desktop.ps1`, which reads `.env` without adding another dependency.

## Compile and install the in-game scripts

Download XScript Compiler 0.8 and keep `XScriptCompiler.exe` and `default_data.dat` in one directory. Then:

```powershell
.\BUILD\install-ai-chat-dev.ps1 `
  -X3FLDirectory "C:\Games\X3 Farnham's Legacy" `
  -CompilerDir "C:\Tools\XScriptCompiler-0.8"
```

The script compiles:

- `scripts/working/setup.plugin.guilds.ai.chat.xs`
- `scripts/working/plugin.guilds.ai.chat.hotkey.xs`

and installs the generated XML plus text pages into `addon2`.

## Run

```powershell
cd orchestrator
.\run-desktop.ps1
```

In X3FL:

1. Open Controls and bind **Living Communications: select current target**.
2. Target an NPC ship or station.
3. Press the hotkey.
4. The overlay switches to that object.
5. Type messages in the overlay and press Enter.

Use `X3AI_PROVIDER=mock` first. It works offline and proves the complete game-log → overlay → memory → response loop without tokens.

## Other modes

```powershell
x3guilds-ai-desktop --no-overlay   # background bridge only
x3guilds-ai-desktop --once         # consume current log tail once
x3guilds-ai                       # HTTP API on 127.0.0.1:8787
```

Open `http://127.0.0.1:8787/ui` for a direct API test.

## Data files

By default:

- SQLite memory: `orchestrator/data/x3guilds-ai.sqlite3`
- processed-file checkpoint: `orchestrator/data/x3guilds-ai.checkpoint.json`
- sidecar responses: `orchestrator/data/x3guilds-ai-responses.log`
- diagnostics: `orchestrator/data/diagnostics/bridge-events.jsonl`

The X3 log is auto-detected under the user's `Documents/Egosoft/X3FL` directory. Set `X3AI_REQUEST_LOG_PATH` if the Documents folder is redirected or the game uses another path.

## Tests

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Tests cover strict action payloads, protocol escaping, X3 log prefixes, context selection, append-only checkpointing, log truncation, idempotency conflicts, memory, path discovery, and overlay queues.
