---
name: flash-clickers
description: Program (flash) Count Fidget Q5 clickers with the Q5 firmware over USB-C from a Mac or Linux machine using the STM32 ROM DFU bootloader and dfu-util, verify each unit, run the on-device commissioning check and keep a unit log. Use when the user wants to flash, reflash, update, program or commission clickers, or troubleshoot DFU / dfu-util connection problems.
---

# Flash Count Fidget clickers

The tool is `tools/clicker-flash/clicker_flash.py`: standard-library Python 3, wrapping `dfu-util`. Read `tools/clicker-flash/README.md` for the full operator procedure. Follow these steps.

## 1. Preconditions (run them, don't assume)

1. `python3 tools/clicker-flash/clicker_flash.py doctor`
   - dfu-util missing: on macOS, ask the user before running `brew install dfu-util`. On Linux, suggest the package manager. Never download dfu-util from elsewhere.
   - Image FAIL: the firmware build does not match its manifest. Do **not** flash. Check `git status firmware/q5-stm32/build`, and restore the committed build (`git checkout -- firmware/q5-stm32/build`) or rebuild per `docs/build-and-verify.md`. Never flash an image that is not listed in the manifest.
2. If the user wants the full provenance check as well: `python3 -B scripts/build_firmware_q5.py --verify-only`.

## 2. Guide the operator into DFU mode

Tell the user, per unit:
1. Connect USB-C (a data cable).
2. Hold RESET (○).
3. Click the pinhole with a paper clip.
4. Release RESET.

The display stays dark. The saved count is not affected. Confirm with `python3 tools/clicker-flash/clicker_flash.py list`.

## 3. Flash

- One unit: `python3 tools/clicker-flash/clicker_flash.py flash --check`
- Many units: `python3 tools/clicker-flash/clicker_flash.py flash --batch --check`

These commands wait for the device and prompt the operator interactively, so run them in the user's terminal; they cannot run in a non-interactive tool call. If you can only run commands non-interactively, drop `--check` and ask the user the four commissioning questions yourself (see the README table), then record the answers in your summary.

`--timeout` sets how long to wait for a device (default 120 s).

## 4. Interpret results

- **PASS:** bytes verified by read-back. It is not proof the board works; the `--check` answers are the functional test.
- **VERIFY FAILED / Download failed:** retry once on the same unit. A repeat failure means a hardware fault: tell the user to set the unit aside and note its serial.
- **More than one device:** only one clicker at a time.
- **Device not found:** data cable; RESET held while the pinhole is released; another port.
- **FLASHED_CHECK_FAIL:** flashing worked but the unit failed a functional check. Treat it as a reject for diagnosis.

At the end, summarise from the log (`~/count-fidget-flash-log.csv` unless `--log` was given): units passed, failed, and serials of rejects.

## Never

- Write option bytes, set read protection (RDP), mass-erase, or use `dfu-util` directly with `:force`, `:unprotect` or `:mass-erase`.
- Flash a non-Q5 image, or edit the image or manifest to make a check pass.
- Commit the unit log to this public repository.
- Present a PASS as hardware qualification.

The firmware provisions its own brown-out option byte on first boot. The count lives in external FRAM that DFU cannot reach, so updates keep it.
