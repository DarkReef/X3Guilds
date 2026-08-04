# X3 Guilds · Living Communications

External dialogue and long-term-memory sidecar for **X3: Farnham's Legacy — Guilds**.

## Game flow

```text
C / native communication menu
  → Free conversation / Свободный разговор
  → additive X3FL comm script
  → XUGC v2 record in log09980.txt
  → Python overlay
  → Mock or GigaChat
  → validated response and SQLite memory
```

The AI script is registered in addition to the existing Guilds communication script and does not replace `plugin.guilds.comm`. The bindable hotkey remains only as a fallback.

## Install

```powershell
cd orchestrator
.\install.ps1
```

The installer creates the private `x3guilds-ai.ini` file. Select `mock` for offline testing or `gigachat` for the real provider, and fill the corresponding provider settings. The real INI is ignored by Git and read only by Python; it is never stored in X3 scripts or the savegame.

Run the sidecar:

```powershell
.\run-desktop.ps1
```

Compile and install the game scripts:

```powershell
.\BUILD\install-ai-chat-dev.ps1 `
  -X3FLDirectory "C:\Games\X3 Farnham's Legacy" `
  -CompilerDir "C:\Tools\XScriptCompiler-0.8"
```

The build includes setup, native comm handler, context exporter and fallback hotkey. Reload external scripts through the Unofficial Patch Script Editor command or restart X3FL.

## Use

1. Start the sidecar in `mock` mode.
2. Select an NPC ship or station.
3. Press **C**.
4. Choose **Свободный разговор**.
5. Enter free text in the restored overlay.
6. Switch the INI provider after the offline path works.

Environment variables override INI values. An explicit INI can be selected with `run-desktop.ps1 -Config <path>`. The X3 log is auto-detected under `Documents\Egosoft\X3FL\log09980.txt` unless overridden in `[paths]`.

## Safety boundary

X3/Guilds remains authoritative for objects, economy, inventory, combat, relations and the savegame. Python owns dialogue, provider calls, memory and diagnostics. Model intents are allowlisted and schema-validated and are not executed in the savegame in this milestone.

## Tests

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Tests cover the native communication-event contract, additive registration, fallback hotkey arguments, XUGC v2 and legacy v1 parsing, object names containing `|`, INI loading, environment overrides, action validation, memory, log recovery and overlay queues.
