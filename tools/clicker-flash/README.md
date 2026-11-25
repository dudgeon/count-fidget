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
3. only if they match, starts the application (an 8-byte read carrying the DfuSe *leave*; nothing is written). A unit that fails the compare stays in DFU mode for a retry;
4. appends a line to `~/count-fidget-flash-log.csv`: UTC time, the chip's unique DFU serial, result, image and read-back SHA-256, and dfu-util version.

`--check` then asks four on-device questions and records the answers. These double as the functional commissioning test:

| Step | Expected |
|---|---|
| After flashing | `0` with **ERR** (new FRAM) or the previous count |
| Hold RESET 2 s, release | **RST** appears, then `0` without ERR |
| Press COUNT three times | `3`; battery bars or **CHG** visible |
| Hold RESET 2 s, release | `0` |

**After the first flash of a board, keep USB connected for at least 5 s.** The application's first boot programs the brown-out option byte (a ~6.4 ms option-byte write, then a self-reset). Power lost during that write leaves an invalid option word; the board then shows **OPT** (see Troubleshooting). If the display is still dark 2 s after the leave, press the pinhole once: that is a clean hardware reset, and first-article test A6 records whether the ROM's jump to the application needed it.

In `--batch` mode, unplug the finished unit, connect the next one in DFU mode, and the tool continues. Ctrl-C stops.

## Step-by-step commands (agent-operated)

The `flash-clickers` skill (`.claude/skills/flash-clickers/`) has Claude run every command while the operator only handles the board. These subcommands never prompt, and each ends with one `RESULT {json}` line:

| Command | Device access |
|---|---|
| `wait [--timeout 300]` | lists devices until exactly one appears |
| `probe` | lists the device; checks the ROM's Flash layout. Read protection is **not** visible here: the ROM reports the same layout with RDP set |
| `backup [--out DIR]` | reads the real 128 KiB of Flash to `~/count-fidget-flash-backups/<serial>-<utc>.bin`, then the RDP and USER option words (read-only), and stays in DFU. A factory-blank STM32L0 reads all `0x00` (`contents: blank`). A failed read on a new board means read protection or a USB fault: stop |
| `flash --no-leave [--serial S]` | the only write: writes, reads back and compares, and stays in DFU |
| `verify-device` | a second, independent read-back compared with the image |
| `leave` | refuses unless Flash starts with an application vector table; then starts the application without writing and confirms the device left DFU |
| `record-check --serial S --checks blank=pass,reset=pass,count=pass,zero=pass` | logs the commissioning answers |
| `summary` | shows the latest result per unit from the log |

All except `record-check` and `summary` accept `--serial S`.

## What it refuses to do

- Flash an image whose size or SHA-256 differs from the build manifest, whose vector table is invalid, or that exceeds Flash Bank 1.
- Flash when more than one STM32 DFU device is connected.
- Flash a device without an `@Internal Flash` DfuSe interface at 0x08000000, or whose layout marks the image pages as not readable/erasable/writable.
- Start the application before the read-back matches, or `leave` into a blank or foreign Flash.
- Report success unless the read-back matches. After a verified read-back, a dfu-util error on the final *leave* request is logged as a note, because the ROM may drop off USB before answering.

The STM32L072CB has 128 KiB of Flash (two 64 KiB banks); the firmware image is confined to Bank 1 (0x08000000–0x0800FFFF). Its ROM bootloader is shared with the 192 KiB parts and has been reported to describe 192 KiB (`1536*128`) on 128 KiB parts, so both 128 and 192 KiB layouts are accepted, and nothing is read or written above 128 KiB. A read-protected (RDP level 1) part shows the normal layout but fails every read, erase and write with a DFU error (AN3156); the tool then stops. It never offers *read unprotect*: that mass-erases.

It never writes option bytes, never mass-erases and never touches the external FRAM, so the count survives every update. The firmware provisions its own brown-out option byte on first boot (see `docs/q5-firmware.md`). A flash that the tool reports as **PASS** proves the bytes are in flash. It does not prove the board works: that is what the `--check` questions and the first-article test plan are for.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `No STM32 DFU device found` | Data cable? RESET must be held while the pinhole is released. Try another port/hub. |
| `More than one STM32 DFU device` | Connect one clicker at a time. |
| `VERIFY FAILED` | The unit is still in DFU mode. Re-run `flash` on the same unit. A repeat failure means a hardware fault: press the pinhole, then set the unit aside. |
| `WARNING: device reports … KiB flash` | Neither the 192 KiB ROM layout nor 128 KiB: not an STM32L072CB. Check it is a Count Fidget Q5 board. |
| `backup`/`verify-device` read fails on a never-flashed board | Possibly read protection (RDP level 1) or a USB fault. Stop; do not try to unprotect (it mass-erases). |
| **OPT** with no digits after flashing | The option bytes are not the expected set (for example USB was unplugged during the first-boot option write). Not a brick: DFU and SWD still work. Set the board aside; `backup` shows the stored option words. Repair needs STM32CubeProgrammer (RDP AA, BOR_LEV 0xC "level 5", nBOOT1 1, BFB2 0), which this tool deliberately does not do. |
| A flash FAILED or you stopped mid-flash | The clicker is still in DFU mode. **Press the pinhole before unplugging it.** A clicker unplugged while in DFU stays powered (its USB pull-up back-feeds the power latch) and drains its cell until the pinhole is pressed. |
| Display blank after PASS | Press the pinhole once (normal restart). If still blank, record it as a commissioning failure. |

## Tests

```sh
python3 tools/clicker-flash/test_clicker_flash.py --output verification/q5-flasher-tests.json
```

The tests run the tool end to end against `mock_dfu_util.py`, which emulates dfu-util 0.11's command line and an STM32 DfuSe device (O_EXCL uploads, `:leave`, page erase). They cover:
- corrupted writes, download and leave errors;
- multiple devices, read-protected parts (same layout, failing reads and writes), non-writable and non-ROM layouts;
- the 128 KiB real Flash behind a 192 KiB ROM descriptor, the erased value 0x00, option-byte decoding;
- that only `flash` downloads, nothing writes option bytes, a mismatched image is never started and `leave` refuses a blank part;
- tampered or unrecorded images and bad vector tables;
- commissioning logging and batch operation.

If a real `dfu-util` is installed, the tests also confirm it accepts the tool's exact arguments.
