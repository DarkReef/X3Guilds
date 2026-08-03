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
New-Item -ItemType Directory -Force -Path (Join-Path $Addon "scripts") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Addon "t") | Out-Null

Copy-Item (Join-Path $Root "scripts/setup.plugin.guilds.ai.chat.xml") (Join-Path $Addon "scripts") -Force
Copy-Item (Join-Path $Root "scripts/plugin.guilds.ai.chat.hotkey.xml") (Join-Path $Addon "scripts") -Force
Copy-Item (Join-Path $Root "t/9980-L044.xml") (Join-Path $Addon "t") -Force
Copy-Item (Join-Path $Root "t/9980-L007.xml") (Join-Path $Addon "t") -Force

Write-Host "Installed development scripts into $Addon"
Write-Host "Use the Unofficial Patch Script Editor command 'Reload external scripts' after updates."
