---
name: flash-clickers
description: Program (flash) Count Fidget Q5 clickers with the Q5 firmware over USB-C from a Mac or Linux machine using the STM32 ROM DFU bootloader and dfu-util, verify each unit, run the on-device commissioning check and keep a unit log. Claude operates every command itself, one step at a time; the user only does the physical actions. Use when the user wants to flash, reflash, update, program or commission clickers, or troubleshoot DFU / dfu-util connection problems.
---

# Flash Count Fidget clickers (agent-operated)

**You run every command. The user only handles the board:** plugging it in, the RESET key, the pinhole, and reading the display. Never hand the user a command to type. The user asked for this so that they can't get it wrong. Go slowly, check each result, and stop at the first surprise.

The tool is `tools/clicker-flash/clicker_flash.py`: standard-library Python 3 wrapping `dfu-util`. Every step command is non-interactive and ends with one line `RESULT {json}`. Read that line, not the prose. Exit 0 means ok. 1 means a check failed (mismatch, still in DFU, a failed commissioning check). 2 means refused or error. 3 means a probe warning.

| Command | Touches the device? |
|---|---|
| `doctor`, `verify-image`, `list`, `wait`, `probe` | lists the USB devices only |
| `backup`, `verify-device` | reads flash; stays in DFU |
| `leave` | reads 8 bytes, then asks the ROM to start the application; no write |
| `flash [--no-leave] [--serial S]` | **the only write:** downloads the image to 0x08000000, reads it back and compares, logs |
| `record-check --serial S --checks …`, `summary` | log file only |

Shorthand below: `CF="python3 tools/clicker-flash/clicker_flash.py"`, run from the repository root.

## 0. Preflight, once per session

Run `.claude/skills/flash-clickers/preflight.sh`. It runs:
- `doctor`;
- the flasher test suite against the mock device, including the check that the real dfu-util accepts the exact arguments;
- `git status` on the firmware build.

Every line must pass.
- **dfu-util missing:** ask the user (AskUserQuestion) before you run `brew install dfu-util`. Never fetch dfu-util from anywhere else.
- **Image FAIL, or `firmware/q5-stm32/build` modified:** do not flash. Report it. Never edit the image or the manifest.

The committed BIN is bound to `build-manifest.json` (SHA-256 `17eac86b…c502`, 10,652 bytes). An Arm toolchain is **not** needed to flash. It is needed only to rebuild.

## 1. Before a board's first power-up (ask; this is the user's call)

From `docs/q5-first-article-test-plan.md`, section A, ask the user whether they have done these for this board, or want to skip them:
- **A2:** no shorts. VBUS, SYS and VLOGIC each read > 1 kΩ to GND.
- **A2b:** BT1 polarity is right.
- **A3:** the first power-up is USB only, with **no cell fitted**, ideally through a USB-C power meter. Expect < 30 mA.

Also confirm two things:
- A clicky switch is pressed into the RESET socket (SW2, the ○ key) and the COUNT socket (SW1). DFU entry needs RESET. Without a switch, bridging the socket contacts with tweezers works.
- The cable is a **data** cable. Charge-only cables never enumerate.

## 2. Get one board into DFU

Start `$CF wait --timeout 300` in the background **before** you ask, so it is already listening. Then send the user the physical steps (AskUserQuestion, or the project-thread report route when running over Remote Control):
1. Plug the board into the Mac with the USB-C data cable.
2. Press and **hold RESET** (○).
3. Press and release the pinhole in the base with a paper clip. On a bare board, short the reset pads instead.
4. **Release RESET.** The display stays dark. This is normal: the ROM bootloader is running.

The saved count is never affected by this.

When `wait` returns, note the `serial` and pass `--serial S` to every later step for this board. If it times out, re-check the cable, the order of the four steps, and another port. A **Stop** gate is DFU that never enumerates on two different cables (A4).

## 3. First board: progressive, testing each step

Run these one at a time. Report each result to the user in a short line before the next.

1. `$CF probe --serial S`. Expect `flash_kib: 192`, an option-bytes alt and no warnings.
   - A warning (exit 3), or a "read protection" refusal: **stop** and report.
2. `$CF backup --serial S`. This reads all 192 KiB into `~/count-fidget-flash-backups/` and proves that USB reads work before anything is written.
   - Expect `contents: blank` on a new board.
   - `q5-image` means it was already flashed.
   - `other` means unknown firmware from JLC's test. Keep the backup and tell the user before overwriting.
3. `$CF flash --serial S --no-leave --timeout 30`. This is the write: download, then read back and compare byte for byte. The board stays in DFU.
   - Expect `result: PASS`.
   - On FAIL: retry once. A second FAIL means a reject, which goes to step 6.
4. `$CF verify-device --serial S`. An independent second read-back. Expect `ok: true`.
5. `$CF leave --serial S`. This starts the application. Expect `ok: true`: the device disappears from DFU, and the display should show digits within 1 s (test A6).
   - `ok: false` means it is still in DFU. The board must **not** be unplugged: ask the user to press the pinhole first.
6. **Commissioning.** Ask the user each check in turn and wait for each answer. Use the four checks in `COMMISSIONING` in the tool, which match the README table:
   - `blank`: after the flash the display shows `0` with **ERR** (new FRAM) or the previous count;
   - `reset`: hold RESET 2 s, and **RST** appears; release, and the display shows `0` without ERR;
   - `count`: press COUNT three times, and the display shows `3`, with battery bars or **CHG**;
   - `zero`: hold RESET 2 s and release, and the display shows `0`.

   Then run `$CF record-check --serial S --checks blank=pass,reset=pass,count=pass,zero=pass` with the real answers. Use `fail` or `skipped` as needed, and add `--note "…"` for anything odd.
7. Tell the user it is safe to unplug: the application is running. Then run `$CF summary`.

## 4. Later boards

Once the first board has passed every step, use the compact sequence per board:
1. `wait`;
2. `probe`;
3. `backup`;
4. `flash --serial S`, with leave included;
5. `list`, to confirm it left DFU. If it is still listed, ask for the pinhole before the unplug;
6. the commissioning questions, then `record-check`.

Don't use `--batch` or `--check`: they prompt on stdin, which you can't answer.

Keep a running tally for the user, and finish with `summary`: units passed, failed, and the serials of rejects.

## Rules

- **Never unplug a board that is still in DFU**, after a FAIL, a `--no-leave` or an interrupted run. Have the user press the pinhole first. Otherwise its USB pull-up back-feeds the power latch and drains the cell.
- One board connected at a time. The tool refuses two.
- Never write option bytes, set read protection (RDP), mass-erase, or run `dfu-util` directly. That includes `:force`, `:unprotect`, `:mass-erase` and option-byte alts. Only this tool touches the device.
- Never flash a non-Q5 image, or edit the image or manifest to make a check pass.
- Never commit `~/count-fidget-flash-log.csv` or the backups. Commissioning evidence goes in `verification/first-article/` as the test plan says, without personal data.
- A flash PASS proves the bytes are in flash. The commissioning answers are the functional check. Neither one is hardware qualification.

The firmware sets its own brown-out option byte on first boot. The count lives in external FRAM, which DFU cannot reach, so updates keep it.
