param(
    [Parameter(Mandatory = $true)]
    [string]$CompilerDir
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Compiler = Join-Path $CompilerDir "XScriptCompiler.exe"
$Data = Join-Path $CompilerDir "default_data.dat"

if (-not (Test-Path $Compiler)) { throw "XScriptCompiler.exe not found: $Compiler" }
if (-not (Test-Path $Data)) { throw "default_data.dat not found: $Data" }

$Sources = @(
    "setup.plugin.guilds.ai.chat",
    "plugin.guilds.ai.chat.comm",
    "plugin.guilds.ai.chat.export",
    "plugin.guilds.ai.chat.hotkey"
)

foreach ($Name in $Sources) {
    $Input = Join-Path $Root "scripts/working/$Name.xs"
    $Output = Join-Path $Root "scripts/$Name.xml"
    if (-not (Test-Path $Input)) { throw "XScript source not found: $Input" }
    & $Compiler --load_data $Data --compile $Input --out $Output
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Output)) {
        throw "Compilation failed: $Input"
    }
}

Write-Host "Compiled Guilds AI communication scripts into scripts/."
