# Build, verify and preserve the submitted Q1 baseline

The first local-session task is website quoting. It needs the existing files, not a CAD/compiler installation. No Linux binaries or old scratch tool paths are required to upload them.

## Quick integrity and portable firmware checks

```sh
python3 scripts/verify_project.py
python3 scripts/run_host_tests.py
```

The first checks stored Q1 firmware hashes, Intel HEX integrity/journal separation, exact 46-ref BOM/CPL match, Gerber ZIP versus loose files, recorded DRC status and every frozen RFQ member against its manifest. It also validates Q2 source/header/build inputs and actual compiled outputs against the separate build manifest, compiled LCD register values, and application information-FRAM exclusion. Only the explicitly recorded `firmware/main_msp430.c` Q1/Q2 divergence is allowed; every other RFQ member must still match the working tree. The second compiles/runs the existing counter/journal and LCD host tests using `CC` or an available `cc`, in a temporary directory. It requires a C compiler; it does not flash hardware.

Host tests exercise bounce, no repeat, wake click, reset priority, saturation, timer wrap, blank memory, CRC fallback, ten interrupted-journal word boundaries and 100,000 commits, plus LCD digit mapping. They do not cover analog brownout, pin mux, LCD optical/bias behavior, charging, protection or enclosure fit.

## RFQ packaging

**Do not run `scripts/package_rfq.py` while shared source is the Q2 candidate.** The submitted Q1 ZIP and its manifest are frozen; this branch intentionally has newer source. That legacy packager copies working sources and could combine Q2 source with Q1 HEX. A future coordinated Q2 engineering release needs its own package revision after hardware/firmware qualification. The current archive still includes its matching Q1 source, PCB-only/full/offboard BOMs, import notes, HEX/checksums and drawings. Contact details come from the authenticated vendor account.

## Target firmware

Retained image target: MSP430FR4133IG48R. Original build used TI MSP430 GCC **9.3.1.11**, support files **1.212**, warnings as errors; size is 2238 text / 98 data / 68 BSS bytes. The original command history was not retained, but the controlled recipe documented in `review-lcd-firmware-Q2.md` reproduced the complete Q1 application HEX byte-for-byte on macOS. The full ELF file differs in non-load metadata. `LCD4MUX` includes `LCDSON` in the actual header: the alleged missing segment-enable/source drift was refuted.

The current shared source is a **Q2 LCD verification candidate**, changing only the LCD clock divider to 8 (32 Hz nominal) and making the already implied `LCDSON` explicit. Q1 hardware is missing R13/R23/R33 reservoir capacitors; no software build clears that hold. Existing charger/protection, schematic/ERC, fit and first-article gates also remain open.

Obtain the [official TI compiler](https://www.ti.com/tool/download/MSP430-GCC-OPENSOURCE), host-compatible **9.3.1.11**, and support **1.212**. Set paths to their installation roots, not their `bin`/`include` subdirectories:

```sh
python3 scripts/build_firmware.py --toolchain /path/to/msp430-gcc-9.3.1.11_macos --support /path/to/msp430-gcc-support-files
python3 scripts/verify_project.py
python3 scripts/run_host_tests.py
```

Default output is the separate `firmware/q2-lcd-check/` directory; use `--output /path/to/separate-directory` for a comparison build. The script compiles fixed source order with explicit `-mmcu=msp430fr4133 -std=c11 -Os -Wall -Wextra -Werror -ffunction-sections -fdata-sections` and links with `--gc-sections`. It records command argument arrays, hashes all source/header/build/verification inputs, resolved compiler dependencies, compiler tools and full toolchain/support trees. Temporary paths are normalized in the map/listing and recorded commands. The manifest records actual output hashes and the exact historical/new source hashes; no timestamps enter the build products.

Validation is intentionally restricted to this exact candidate: it binds the frozen Q1 application HEX hash, requires the same loaded addresses and exactly `0xc53d: 0x18 -> 0x38`, and checks the compiled `lcd_start` instructions for `LCDCTL0=0x385d` and `LCDVCTL=0xf0a0`. It checks ELF/HEX load-byte equality using ELF program-header load addresses, and excludes information FRAM `0x1800–0x19FF`. A disassembly listing is retained for review. A later register override or any other loaded-byte change is rejected; future firmware changes require a separately reviewed recipe. Repeating this recipe produced identical Q2 ELF/HEX/map/listing/manifest files locally. That does not establish byte reproducibility across hosts, different toolchain builds or uncontrolled environments. These are build checks, not MCU execution, waveform, current or brownout tests. Do not flash or promote this candidate without a controlled hardware validation plan; never overwrite Q1 outputs or the factory initializer to perform a rebuild.

`factory-display-info.hex` initializes a valid 88,888,888 journal only for factory display inspection. It is not a field update image. Program via an MSP-FET-compatible Spy-Bi-Wire fixture per the RFQ; leave security unlocked for prototype debugging and never backfeed target V3. Reset count to zero after factory tests. USB is charge-only.

## KiCad and routing

Open `electronics/click-counter-Q1.kicad_pro` / `.kicad_pcb` in KiCad 10. Existing board geometry is embedded; the project-local LCD footprint library is in `ClickCounter.pretty` with `${KIPRJMOD}` mapping. Use matching standard libraries to avoid accidental substitutions.

`electronics/build_pcb.py` needs KiCad 10's `pcbnew` Python binding and `KICAD_FP_ROOT` pointing to the standard footprint directory. Its fallback path references the old cloud tool folder; set the environment variable explicitly on another machine. **It overwrites the board and generates an unrouted DSN.** Do not run it merely to view/upload Q1. The original router log identifies Freerouting 2.4.1; DSN/SES are retained. Regenerated DSN identifiers can invalidate old SES correspondence, so route the new DSN rather than blindly reusing an old session. `finish_pcb.py` imports a matching session if needed, normalizes tracks, fills copper and stores the custom footprint. It does not replace all export/validation steps.

The retained DRC identifies KiCad **10.0.6** and includes errors/warnings under the saved configuration. It ignores `missing_courtyard`, `track_not_centered_on_via`, `tuning_profile_track_geometries`, `footprint_filters_mismatch`, and `footprint_type_mismatch`. Its schematic parity list is empty because no matching native schematic/ERC exists. The zero-result claim is limited to that configuration; review excluded checks and physical courtyards as part of engineering qualification.

For an intentional electronics change: first preserve a branch/checkpoint, make the schematic/netlist/generator changes consistently, regenerate/route, run fresh DRC, export all Gerbers/drills and both placement conventions, update BOM/importer splits and assembly drawings, then revalidate/refreeze the package. A native schematic/ERC still must be created. Do not treat packaging assertions as fresh KiCad validation.

## CAD

See `mechanical/README.md`. CadQuery source, STEP/STLs and rendered PNGs are supplied. Need CadQuery, NumPy and Pillow for the historical renderer; font paths are Linux-specific and must be adapted. Q1 mount/USB/component changes must be modeled before final printing. Solid-validity checks alone are insufficient.
