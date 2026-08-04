#DESCRIPTION "Guilds AI Chat: setup"
#VERSION 3

function main()
{
    $page.id = 9980;
    loadText($page.id);
    setGlobalData("pageid.guilds.ai.chat", $page.id);

    $data = getGlobalData("guilds.ai.chat");
    if (!$data)
    {
        $data = tableAlloc();
        $data["context.counter"] = 0;
        setGlobalData("guilds.ai.chat", $data);
    }
    $data["version"] = 3;

    // The normal C/communications menu is the primary entry point.
    // X3FL permits multiple global communication scripts for the same
    // class/race pair, so this coexists with plugin.guilds.comm.
    commSetGlobal(OBJ_SHIP, null, "plugin.guilds.ai.chat.comm", TRUE);
    commSetGlobal(OBJ_DOCK, null, "plugin.guilds.ai.chat.comm", TRUE);

    // Optional fallback for cases where the vanilla comm menu is unavailable.
    $key.id = registerEventHotkey(
        "plugin.guilds.ai.chat.hotkey",
        InputType::Menus,
        $page.id,
        1,
        null
    );
    $data["hotkey.id"] = $key.id;
    return(null);
}
