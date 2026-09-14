#!/usr/bin/env bash
# Read-only repository check and handoff display. No installs, authentication,
# browser changes, vendor submissions, spending, or automatic git writes.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
git status --short --branch
python3 scripts/verify_project.py
cat LOCAL_SESSION_PROMPT.md
printf '\nFull local-session instructions: %s/HANDOFF.md\n' "$project_root"
