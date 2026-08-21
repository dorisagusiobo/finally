#!/usr/bin/env bash
# Stop and remove the running FinAlly container. Does NOT remove the db/
# volume — data persists across restarts. Idempotent. macOS/Linux.
set -euo pipefail

CONTAINER_NAME="finally"

if [[ -n "$(docker ps -aq -f name="^${CONTAINER_NAME}$")" ]]; then
  echo "Stopping and removing container '$CONTAINER_NAME'..."
  docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
  docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
  echo "Done."
else
  echo "No container named '$CONTAINER_NAME' found. Nothing to do."
fi
