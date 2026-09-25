# clicker-flash — program Count Fidget Q5 clickers from a Mac

`clicker_flash.py` programs the Q5 firmware over the clicker's own USB-C port. It uses the STM32's built-in ROM bootloader (USB DFU), so there is no programmer hardware, driver, or application bootloader to install. It needs only Python 3 (built into macOS) and `dfu-util`.

> Status: tested against a simulated DfuSe device, and the real `dfu-util` 0.11 accepts its exact arguments. **It has not yet programmed a physical clicker.** The first real flash is part of the first-article test plan.

## One-time setup (macOS)

```sh
xcode-select --install          # if python3 is missing
brew install dfu-util           # https://brew.sh
cd count-fidget                 # this repository
python3 tools/clicker-flash/clicker_flash.py doctor
```

`doctor` checks the dfu-util version (≥ 0.9), verifies the firmware image against `firmware/q5-stm32/build/build-manifest.json`, and lists connected DFU devices.

Use a **USB-C data cable**; charge-only cables never enumerate. Connect directly or through a powered hub.

## Put a clicker into DFU mode

1. Connect the clicker to the Mac by USB. USB powers it; a cell may or may not be fitted.
2. **Hold RESET** (the ○ key).
3. Press and release the **pinhole** in the base with a paper clip.
4. **Release RESET.** The display stays dark, because the ROM bootloader is running.

This never changes the saved count: a count reset needs a 2 s hold *and* a release while the application is running. `dfu-util -l` (or `clicker_flash.py list`) should now show `[0483:df11] … name="@Internal Flash …"`.

## Flash

```sh
python3 tools/clicker-flash/clicker_flash.py flash                   # one unit
python3 tools/clicker-flash/clicker_flash.py flash --batch --check   # production: unit after unit
```

For each unit the tool:
1. writes the image to 0x08000000;
2. reads the same range back and compares every byte;
3. starts the application;
4. appends a line to `~/count-fidget-flash-log.csv`: UTC time, the chip's unique DFU serial, result, image and read-back SHA-256, and dfu-util version.

`--check` then asks four on-device questions and records the answers. These double as the functional commissioning test:

| Step | Expected |
|---|---|
| After flashing | `0` with **ERR** (new FRAM) or the previous count |
| Hold RESET 2 s, release | **RST** appears, then `0` without ERR |
| Press COUNT three times | `3`; battery bars or **CHG** visible |
| Hold RESET 2 s, release | `0` |

In `--batch` mode, unplug the finished unit, connect the next one in DFU mode, and the tool continues. Ctrl-C stops.

## What it refuses to do

- Flash an image whose size or SHA-256 differs from the build manifest, whose vector table is invalid, or that exceeds Flash Bank 1.
- Flash when more than one STM32 DFU device is connected.
- Flash a device without an `@Internal Flash` DfuSe interface at 0x08000000, or whose flash pages are not writable (e.g. read protection).
- Report success unless the read-back matches. After a verified read-back, a dfu-util error on the final *leave* request is logged as a note, because the ROM may drop off USB before answering.

It never writes option bytes, never mass-erases and never touches the external FRAM, so the count survives every update. The firmware provisions its own brown-out option byte on first boot (see `docs/q5-firmware.md`). A flash that the tool reports as **PASS** proves the bytes are in flash. It does not prove the board works: that is what the `--check` questions and the first-article test plan are for.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `No STM32 DFU device found` | Data cable? RESET must be held while the pinhole is released. Try another port/hub. |
| `More than one STM32 DFU device` | Connect one clicker at a time. |
| `VERIFY FAILED` | Re-run `flash` on the same unit. A repeat failure means a hardware fault: set the unit aside. |
| `WARNING: device reports … KiB flash` | Not an STM32L072CB. Check it is a Count Fidget Q5 board. |
| Display blank after PASS | Press the pinhole once (normal restart). If still blank, record it as a commissioning failure. |

## Tests

```sh
python3 tools/clicker-flash/test_clicker_flash.py --output verification/q5-flasher-tests.json
```

The tests run the tool end to end against `mock_dfu_util.py`, which emulates dfu-util 0.11's command line and an STM32 DfuSe device (O_EXCL uploads, `:leave`, page erase). They cover:
- corrupted writes, download and leave errors;
- multiple devices, read-protected and non-ROM layouts;
- tampered or unrecorded images and bad vector tables;
- commissioning logging and batch operation.

If a real `dfu-util` is installed, the tests also confirm it accepts the tool's exact arguments.
