#DESCRIPTION "Guilds AI Chat: fallback target hotkey"
#VERSION 3

function main($key.id, $event)
{
    if ($event != "short") return(null);

    $target = getPlayerTrackingAim();
    if (!$target || !$target->exists())
    {
        $page.id = getGlobalData("pageid.guilds.ai.chat");
        if (!$page.id) $page.id = 9980;
        incomingMessage(readText($page.id, 13), PlayerLog::Alert, TRUE);
        return(null);
    }

    $result = this->call("plugin.guilds.ai.chat.export", $target);
    return($result);
}
