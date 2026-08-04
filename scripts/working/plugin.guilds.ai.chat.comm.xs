#DESCRIPTION "Guilds AI Chat: communication menu"
#VERSION 1

function main($a.obj, $a.event, $a.data)
{
    $page.id = getGlobalData("pageid.guilds.ai.chat");
    if (!$page.id) $page.id = 9980;

    if ($a.event == "commcheck")
    {
        if (!$a.obj || !$a.obj->exists()) return(FALSE);

        if (
            $a.data == Comm.Dlg.Contact ||
            $a.data == Comm.Dlg.Captain.Contact ||
            $a.data == Comm.Dlg.Enemy ||
            $a.data == Comm.Dlg.Captain.Enemy
        )
        {
            return(TRUE);
        }
        return(FALSE);
    }
    else if ($a.event == "text")
    {
        return(readText($page.id, 10));
    }
    else if ($a.event == "question")
    {
        // Returning null accepts the selected communication option without
        // inserting a synthetic voiced line. The external overlay becomes the
        // free-text continuation of this native comm interaction.
        return(null);
    }
    else if ($a.event == "accepted")
    {
        $result = this->call("plugin.guilds.ai.chat.export", $a.obj);
        return(null);
    }

    return(null);
}
