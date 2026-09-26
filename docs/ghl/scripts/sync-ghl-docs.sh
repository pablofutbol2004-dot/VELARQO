#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_DIR="$ROOT/api"
mkdir -p "$API_DIR"

sync_repo() {
  local name="$1" url="$2" path="$API_DIR/$1"
  if [ -d "$path/.git" ]; then
    git -C "$path" fetch --depth 1 origin main
    git -C "$path" reset --hard origin/main
  else
    rm -rf "$path"
    git clone --depth 1 "$url" "$path"
  fi
}

sync_repo official-docs https://github.com/GoHighLevel/highlevel-api-docs.git
sync_repo sdk https://github.com/GoHighLevel/highlevel-api-sdk.git

echo "Done. Official HighLevel API docs and SDK are in $API_DIR"
