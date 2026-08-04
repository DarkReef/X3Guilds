$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11 or newer."
}

py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e .

$Config = Join-Path $Root "x3guilds-ai.ini"
if (-not (Test-Path $Config)) {
    Copy-Item (Join-Path $Root "x3guilds-ai.ini.example") $Config
}

Write-Host "Installed. Edit: $Config"
Write-Warning "The INI may contain a plaintext API secret. It is ignored by Git; restrict file access and do not share it."
Write-Host "Then run: .\run-desktop.ps1"
