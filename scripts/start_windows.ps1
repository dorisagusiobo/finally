# Build (if needed) and run the FinAlly Docker container. Idempotent — safe to
# run multiple times. Windows PowerShell. See planning/PLAN.md §11.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
$ImageName = "finally"
$ContainerName = "finally"
$Port = 8000

Set-Location $RootDir

if (-not (Test-Path (Join-Path $RootDir ".env"))) {
    Write-Error "Error: .env not found at $RootDir\.env`nCopy .env.example to .env and fill in OPENROUTER_API_KEY first."
    exit 1
}

New-Item -ItemType Directory -Force -Path (Join-Path $RootDir "db") | Out-Null

$Build = $args -contains "--build"
$ImageExists = docker images -q $ImageName
if ($Build -or [string]::IsNullOrWhiteSpace($ImageExists)) {
    Write-Host "Building Docker image '$ImageName'..."
    docker build -t $ImageName $RootDir
}

$Running = docker ps -q -f "name=^$ContainerName`$"
if (-not [string]::IsNullOrWhiteSpace($Running)) {
    Write-Host "Container '$ContainerName' is already running."
} else {
    $Existing = docker ps -aq -f "name=^$ContainerName`$"
    if (-not [string]::IsNullOrWhiteSpace($Existing)) {
        docker rm $ContainerName | Out-Null
    }

    Write-Host "Starting container '$ContainerName'..."
    docker run -d `
        --name $ContainerName `
        -p "${Port}:8000" `
        -v "${RootDir}\db:/app/db" `
        --env-file "${RootDir}\.env" `
        $ImageName
}

$Url = "http://localhost:$Port"
Write-Host "FinAlly is running at $Url"

try {
    Start-Process $Url
} catch {
    # Non-fatal if no default browser handler is available.
}
