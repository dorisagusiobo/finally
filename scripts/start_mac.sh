#!/usr/bin/env bash
# Build (if needed) and run the FinAlly Docker container. Idempotent — safe to
# run multiple times. macOS/Linux. See planning/PLAN.md §11.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE_NAME="finally"
CONTAINER_NAME="finally"
PORT="8000"

cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  echo "Error: .env not found at $ROOT_DIR/.env" >&2
  echo "Copy .env.example to .env and fill in OPENROUTER_API_KEY first." >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/db"

BUILD=false
if [[ "${1:-}" == "--build" ]]; then
  BUILD=true
fi
if [[ "$BUILD" == "true" ]] || [[ -z "$(docker images -q "$IMAGE_NAME" 2>/dev/null)" ]]; then
  echo "Building Docker image '$IMAGE_NAME'..."
  docker build -t "$IMAGE_NAME" "$ROOT_DIR"
fi

if [[ -n "$(docker ps -q -f name="^${CONTAINER_NAME}$")" ]]; then
  echo "Container '$CONTAINER_NAME' is already running."
else
  # Remove a stopped container with the same name, if any, before starting fresh.
  if [[ -n "$(docker ps -aq -f name="^${CONTAINER_NAME}$")" ]]; then
    docker rm "$CONTAINER_NAME" >/dev/null
  fi

  echo "Starting container '$CONTAINER_NAME'..."
  docker run -d \
    --name "$CONTAINER_NAME" \
    -p "${PORT}:8000" \
    -v "$ROOT_DIR/db:/app/db" \
    --env-file "$ROOT_DIR/.env" \
    "$IMAGE_NAME"
fi

URL="http://localhost:${PORT}"
echo "FinAlly is running at $URL"

if [[ "$(uname)" == "Darwin" ]]; then
  open "$URL" 2>/dev/null || true
fi
