#DESCRIPTION "Guilds AI Chat: export selected target"
#VERSION 2

function main()
{
    $target = getPlayerTrackingAim();
    if (!$target || !$target->exists())
    {
        incomingMessage("Select a ship or station first.", PlayerLog::Alert, TRUE);
        return(null);
    }

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
    $owner = $target->getTrueOwner();
    $race = sprintf("%s", $owner, null, null, null, null);
    $sector = $target->getSector();
    $sector.name = sprintf("%s", $sector, null, null, null, null);
    $kind = "ship";
    if ($target->isOfClass(OBJ_STATION)) $kind = "station";

    // Protocol fields are deliberately simple. The Python parser validates all
    // values before any model call. X3 remains authoritative for the target.
    $line = "XUGC|1|CHAT_CONTEXT|" + $context.id;
    $line = $line + "|" + $entity.id;
    $line = $line + "|" + $name;
    $line = $line + "|" + $kind;
    $line = $line + "|" + $race;
    $line = $line + "|" + $race;
    $line = $line + "|" + $sector.name;
    $line = $line + "|0|" + playingTime();

    writeLogFile(9980, TRUE, $line);
    incomingMessage("AI communication channel selected: " + $name, PlayerLog::Alert, TRUE);
    return(null);
}
