# Guilds Living Communications architecture

## Native entry point

The primary entry point is the standard X3FL communication interface opened with **C**. `setup.plugin.guilds.ai.chat` registers `plugin.guilds.ai.chat.comm` as an additional global communication script for ships and docks. It coexists with the existing `plugin.guilds.comm` handler.

The event script follows the X3FL communication contract:

- `commcheck` decides whether the option is available;
- `text` supplies **Free conversation / Свободный разговор**;
- `question` returns no synthetic voiced line;
- `accepted` exports the exact contacted object.

A two-argument event hotkey remains as a fallback only.

## Bridge

```text
X3 comm handler
  -> append-only log09980.txt / XUGC v2
  -> checkpointed Python tailer
  -> overlay input
  -> validated provider response
  -> SQLite dialogue and durable memories
```

XUGC v2 puts the player-editable object name at the end of the context record. The parser uses a bounded split, so a renamed object containing `|` cannot shift structural fields. Legacy v1 records remain readable.

## Configuration

`x3guilds-ai.ini` is parsed directly by Python with interpolation disabled. This permits literal `%` characters in provider credentials. Environment variables have higher priority. Relative data paths are resolved from the INI directory.

The INI is ignored by Git and never enters X3 scripts, language files or the savegame. It is a plaintext local secret and must remain private to the Windows account.

## Authority boundary

X3/Guilds remains authoritative for objects, inventory, relations, economy, combat and savegame state. The sidecar owns natural-language dialogue, memory and diagnostics. Model actions are typed and validated and are not applied to the savegame in this milestone.

## Verification boundary

CI verifies Python installation, unit/integration tests, bytecode compilation, XML language files and static XScript contracts. A final local verification still requires XScript Compiler 0.8 plus a running Windows X3FL installation because neither proprietary game data nor the compiler binary is present in CI.
