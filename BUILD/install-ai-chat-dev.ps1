param(
    [Parameter(Mandatory = $true)]
    [string]$X3FLDirectory,
    [Parameter(Mandatory = $true)]
    [string]$CompilerDir
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot "build-ai-chat-scripts.ps1") -CompilerDir $CompilerDir

$Addon = Join-Path $X3FLDirectory "addon2"
$ScriptDirectory = Join-Path $Addon "scripts"
$TextDirectory = Join-Path $Addon "t"
New-Item -ItemType Directory -Force -Path $ScriptDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $TextDirectory | Out-Null

$Scripts = @(
    "setup.plugin.guilds.ai.chat.xml",
    "plugin.guilds.ai.chat.comm.xml",
    "plugin.guilds.ai.chat.export.xml",
    "plugin.guilds.ai.chat.hotkey.xml"
)
foreach ($Script in $Scripts) {
    Copy-Item (Join-Path $Root "scripts/$Script") $ScriptDirectory -Force
}
Copy-Item (Join-Path $Root "t/9980-L044.xml") $TextDirectory -Force
Copy-Item (Join-Path $Root "t/9980-L007.xml") $TextDirectory -Force

Write-Host "Installed development scripts into $Addon"
Write-Host "Use 'Reload external scripts' in the Script Editor or restart X3FL."
