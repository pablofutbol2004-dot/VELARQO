$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..")
$ApiDir = Join-Path $Root "api"
New-Item -ItemType Directory -Force -Path $ApiDir | Out-Null

function Sync-Repo($Name, $Url) {
    $Path = Join-Path $ApiDir $Name
    if (Test-Path (Join-Path $Path ".git")) {
        Write-Host "Updating $Name..."
        git -C $Path fetch --depth 1 origin main
        git -C $Path reset --hard origin/main
    } else {
        if (Test-Path $Path) { Remove-Item -Recurse -Force $Path }
        Write-Host "Cloning $Name..."
        git clone --depth 1 $Url $Path
    }
}

Sync-Repo "official-docs" "https://github.com/GoHighLevel/highlevel-api-docs.git"
Sync-Repo "sdk" "https://github.com/GoHighLevel/highlevel-api-sdk.git"

Write-Host "Done. Official HighLevel API docs and SDK are in $ApiDir"
