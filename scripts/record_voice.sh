#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

cd "$WORKSPACE_DIR"

if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
fi

PROFILE_NAME="${1:-my_voice}"
DURATION="${2:-8.0}"

python "$SCRIPT_DIR/studio.py" --record-voice --voice-profile "$PROFILE_NAME" --record-seconds "$DURATION"
