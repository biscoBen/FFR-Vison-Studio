#!/usr/bin/env bash
set -euo pipefail
sync_script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
exec python3 "$sync_script_dir/Deck Mod Sync.py" --interactive "$@"
