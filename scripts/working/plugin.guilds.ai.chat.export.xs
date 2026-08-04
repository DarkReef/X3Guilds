#DESCRIPTION "Guilds AI Chat: export communication target"
#VERSION 1

function main($target)
{
    if (!$target || !$target->exists()) return(null);

    $page.id = getGlobalData("pageid.guilds.ai.chat");
    if (!$page.id) $page.id = 9980;

    $data = getGlobalData("guilds.ai.chat");
    if (!$data)
    {
        $data = tableAlloc();
        $data["context.counter"] = 0;
        setGlobalData("guilds.ai.chat", $data);
    }

    $counter = $data["context.counter"];
    if (!$counter) $counter = 0;
    ++$counter;
    $data["context.counter"] = $counter;

    $entity.id = $target->getIDCode();
    if (!$entity.id)
    {
        $entity.id = sprintf("fallback-%s", $counter, null, null, null, null);
    }

    $context.id = sprintf("ctx-%s-%s", playingTime(), $counter, null, null, null);
    $name = $target->name;
    if (!$name) $name = readText($page.id, 12);

    $owner = $target->getTrueOwner();
    $race = sprintf("%s", $owner, null, null, null, null);

    $sector = $target->getSector();
    $sector.name = "";
    if ($sector && $sector->exists())
    {
        $sector.name = sprintf("%s", $sector, null, null, null, null);
    }

    $kind = "ship";
    if ($target->isOfClass(OBJ_STATION)) $kind = "station";

    // Protocol v2 puts the player-editable object name last. Python uses a
    // bounded split so a literal pipe in a renamed ship does not corrupt fields.
    $line = "XUGC|2|CHAT_CONTEXT|" + $context.id;
    $line = $line + "|" + $entity.id;
    $line = $line + "|" + $kind;
    $line = $line + "|" + $race;
    $line = $line + "|" + $race;
    $line = $line + "|" + $sector.name;
    $line = $line + "|0|" + playingTime();
    $line = $line + "|" + $name;

    writeLogFile(9980, TRUE, $line);
    incomingMessage(readText($page.id, 11), PlayerLog::Alert, TRUE);
    return($context.id);
}
