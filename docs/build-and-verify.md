# Build, verify and preserve Q1

The first local-session task is website quoting. It needs the existing files, not a CAD/compiler installation. No Linux binaries or old scratch tool paths are required to upload them.

## Quick integrity and portable firmware checks

```sh
python3 scripts/verify_project.py
python3 scripts/run_host_tests.py
```

The first checks stored firmware hashes, Intel HEX integrity/journal separation, exact 46-ref BOM/CPL match, Gerber ZIP versus loose files, recorded DRC status and RFQ ZIP bytes against the repository. The second compiles/runs the existing counter/journal and LCD host tests using `CC` or an available `cc`, in a temporary directory. It requires a C compiler; it does not flash hardware.

Host tests exercise bounce, no repeat, wake click, reset priority, saturation, timer wrap, blank memory, CRC fallback, ten interrupted-journal word boundaries and 100,000 commits, plus LCD digit mapping. They do not cover analog brownout, pin mux, LCD optical/bias behavior, charging, protection or enclosure fit.

## RFQ packaging

```sh
python3 scripts/package_rfq.py
python3 scripts/verify_project.py
```

This uses Python standard library only. It renders the public RFQ HTML and creates deterministic `dist/click-counter-Q1-RFQ.zip` plus checksum/member manifest. It does not regenerate Gerbers, reroute, recompile firmware, or claim a fresh DRC run. It includes the PCB-only BOM, full BOM, offboard BOM, import notes, source/HEX/checksums and drawings. Contact details come from the authenticated vendor account; do not commit personal contact information to customize the public package.

## Target firmware

Retained image target: MSP430FR4133IG48R. Original build used TI MSP430 GCC **9.3.1.11**, support files **1.212**, warnings as errors; original recorded size was 2238 text / 98 data / 68 BSS bytes. ELF/map/HEX and source remain included; original shell command history was not retained, so bit-identical rebuild is not claimed.

For a deliberate rebuild, obtain the official host-compatible TI toolchain/support package, compile `main_msp430.c`, `counter.c` and `lcd_de188.c` for `msp430fr4133` with the supplied device headers/linker script, then emit Intel HEX with the toolchain objcopy. Review optimization/linker/section settings and map, especially that application output does not initialize information FRAM `0x1800–0x181F`. Build into ignored `build/` first, compare, then intentionally promote reviewed artifacts and update the hash manifest. Do not install or invoke an old Linux executable on macOS.

`factory-display-info.hex` initializes a valid 88,888,888 journal only for factory display inspection. It is not a field update image. Program via an MSP-FET-compatible Spy-Bi-Wire fixture per the RFQ; leave security unlocked for prototype debugging and never backfeed target V3. Reset count to zero after factory tests. USB is charge-only.

## KiCad and routing

Open `electronics/click-counter-Q1.kicad_pro` / `.kicad_pcb` in KiCad 10. Existing board geometry is embedded; the project-local LCD footprint library is in `ClickCounter.pretty` with `${KIPRJMOD}` mapping. Use matching standard libraries to avoid accidental substitutions.

`electronics/build_pcb.py` needs KiCad 10's `pcbnew` Python binding and `KICAD_FP_ROOT` pointing to the standard footprint directory. Its fallback path references the old cloud tool folder; set the environment variable explicitly on another machine. **It overwrites the board and generates an unrouted DSN.** Do not run it merely to view/upload Q1. The original router log identifies Freerouting 2.4.1; DSN/SES are retained. Regenerated DSN identifiers can invalidate old SES correspondence, so route the new DSN rather than blindly reusing an old session. `finish_pcb.py` imports a matching session if needed, normalizes tracks, fills copper and stores the custom footprint. It does not replace all export/validation steps.

The retained DRC identifies KiCad **10.0.6** and includes errors/warnings under the saved configuration. It ignores `missing_courtyard`, `track_not_centered_on_via`, `tuning_profile_track_geometries`, `footprint_filters_mismatch`, and `footprint_type_mismatch`. Its schematic parity list is empty because no matching native schematic/ERC exists. The zero-result claim is limited to that configuration; review excluded checks and physical courtyards as part of engineering qualification.

For an intentional electronics change: first preserve a branch/checkpoint, make the schematic/netlist/generator changes consistently, regenerate/route, run fresh DRC, export all Gerbers/drills and both placement conventions, update BOM/importer splits and assembly drawings, then revalidate/refreeze the package. A native schematic/ERC still must be created. Do not treat packaging assertions as fresh KiCad validation.

## CAD

See `mechanical/README.md`. CadQuery source, STEP/STLs and rendered PNGs are supplied. Need CadQuery, NumPy and Pillow for the historical renderer; font paths are Linux-specific and must be adapted. Q1 mount/USB/component changes must be modeled before final printing. Solid-validity checks alone are insufficient.
