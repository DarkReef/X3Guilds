from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source(name: str) -> str:
    return (ROOT / "scripts" / "working" / name).read_text(encoding="utf-8")


def test_setup_registers_additive_native_communication_scripts() -> None:
    setup = source("setup.plugin.guilds.ai.chat.xs")
    assert 'commSetGlobal(OBJ_SHIP, null, "plugin.guilds.ai.chat.comm", TRUE)' in setup
    assert 'commSetGlobal(OBJ_DOCK, null, "plugin.guilds.ai.chat.comm", TRUE)' in setup
    assert 'registerEventHotkey(' in setup


def test_comm_script_matches_x3fl_event_contract() -> None:
    comm = source("plugin.guilds.ai.chat.comm.xs")
    assert "function main($a.obj, $a.event, $a.data)" in comm
    for event in ("commcheck", "text", "question", "accepted"):
        assert f'$a.event == "{event}"' in comm
    assert "Comm.Dlg.Contact" in comm
    assert "Comm.Dlg.Captain.Contact" in comm
    assert 'readText($page.id, 10)' in comm
    assert 'this->call("plugin.guilds.ai.chat.export", $a.obj)' in comm


def test_exporter_uses_append_only_v2_log_record() -> None:
    exporter = source("plugin.guilds.ai.chat.export.xs")
    assert '"XUGC|2|CHAT_CONTEXT|"' in exporter
    assert "writeLogFile(9980, TRUE, $line)" in exporter
    assert '$line = $line + "|" + $name' in exporter


def test_fallback_event_hotkey_has_required_arguments() -> None:
    hotkey = source("plugin.guilds.ai.chat.hotkey.xs")
    assert "function main($key.id, $event)" in hotkey
    assert '$event != "short"' in hotkey
