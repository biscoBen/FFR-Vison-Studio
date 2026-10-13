#!/usr/bin/env bash
set -euo pipefail
studio_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
exec python3 "$studio_dir/Studio Deck Launcher.py" --root "$studio_dir" "$@"
