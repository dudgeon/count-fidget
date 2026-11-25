#!/bin/sh
# Preflight for agent-operated Q5 flashing. Read-only: lists USB devices, checks the image, runs mock tests.
set -u
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 2
fail=0
echo "== doctor"; python3 tools/clicker-flash/clicker_flash.py doctor || fail=1
log=$(mktemp); echo "== flasher tests (mock device + real dfu-util argument check)"
python3 -B tools/clicker-flash/test_clicker_flash.py > "$log" 2>&1 || fail=1
tail -3 "$log"; rm -f "$log"
echo "== firmware build tree"
if [ -n "$(git status --porcelain -- firmware/q5-stm32/build)" ]; then
  git status --short -- firmware/q5-stm32/build; echo "FAIL: build tree differs from git"; fail=1
else echo "clean"; fi
[ $fail -eq 0 ] && echo "PREFLIGHT PASS" || echo "PREFLIGHT FAIL"
exit $fail
