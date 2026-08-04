param([string]$Config)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run orchestrator/install.ps1 first."
}

$Arguments = @("-m", "x3guilds_ai.runtime")
if ($Config) {
    $Arguments += @("--config", (Resolve-Path $Config).Path)
}
$Arguments += $args
& $Python @Arguments
