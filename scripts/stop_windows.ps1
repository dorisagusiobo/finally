# Stop and remove the running FinAlly container. Does NOT remove the db/
# volume — data persists across restarts. Idempotent. Windows PowerShell.

$ErrorActionPreference = "Stop"

$ContainerName = "finally"

$Existing = docker ps -aq -f "name=^$ContainerName`$"
if (-not [string]::IsNullOrWhiteSpace($Existing)) {
    Write-Host "Stopping and removing container '$ContainerName'..."
    docker stop $ContainerName 2>$null | Out-Null
    docker rm $ContainerName 2>$null | Out-Null
    Write-Host "Done."
} else {
    Write-Host "No container named '$ContainerName' found. Nothing to do."
}
