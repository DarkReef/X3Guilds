#DESCRIPTION "Guilds AI Chat: setup"
#VERSION 2

function main()
{
    $page.id = 9980;
    loadText($page.id);
    setGlobalData("pageid.guilds.ai.chat", $page.id);

    $data = getGlobalData("guilds.ai.chat");
    if (!$data)
    {
        $data = tableAlloc();
        $data["version"] = 2;
        $data["context.counter"] = 0;
        setGlobalData("guilds.ai.chat", $data);
    }

    // A target is selected with the normal X3 tracking reticle. The hotkey only
    // exports immutable object context; all free-form text is entered in the
    // external overlay where it can be tested and kept out of the savegame.
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
