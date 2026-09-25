# Build and verify Count Fidget

## Active Q5 engineering workflow

Q5 is derived from the frozen Q4 sources and changes only what the [Q5 review](REVIEW-Q5-2026-09-25.md) lists. Q1–Q4 remain frozen; never run a Q4 builder against Q5. **JLCPCB quoting of the locked design is authorized; purchases and manufacture are not.** Tools used for the recorded evidence: KiCad 10.0.6, Freerouting 2.4.1 (same jar SHA-256 as Q4) on a Temurin JRE with telemetry off, Arm GNU 14.3.Rel1 (x86_64 Linux build), CadQuery 2.8.

1. `build_q5_model.py` derives the Q5 model from `electronics/q4/netlist-Q4.json` plus the recorded Q5 deltas and `electronics/q5/placement.json`. `build_q5_schematic.py --kicad-cli ...` regenerates the sheets and deletes stale sheets. It must report ERC zero.
2. `build_q5_board.py` **discards routing**. After it: `sync_q5_board.py`, `preroute_q5.py` (locked SYS seed), `prepare_q5_route.py`, Freerouting on the DSN, `finish_q5_board.py --import-route` (SES import, collision-checked via nudge, the recorded `gnd-stitch.json` vias from `plan_q5_stitching.py`, two GND pours). DSN/SES are local exchange files and gitignored.
3. `verify_q5.py --kicad-cli ...` runs fresh native XML/ERC/DRC with parity and binds the reports to every input and builder script. `test_verify_q5.py --output verification/q5-negative-tests.json` requires that clean baseline, then checks 42 corruptions are rejected.
4. `build_firmware_q5.py --toolchain ...`, then `--verify-only`. `test_firmware_q5.py` runs the portable suites (`--sanitize` for UBSan; `--cc gcc` where clang's UBSan runtime is missing; `--image-only` for 13 image corruptions).
5. `simulation/q5-firmware-emulation/scenarios.py --check` runs the actual ELF on the instruction-level board model; `energy.py` produces the battery-life table. `simulation/q5-power/check.py` records the bounded latch/inrush/ADC/insertion/storage calculations.
6. `build_q5_enclosure.py --kicad-python ...` requires five valid solids, manifold STLs, zero static intersections and zero sampled assembly-path collisions.
7. `screen_stock_q5.py` (read-only public JLC/LCSC catalogue lookups) binds the final model hash. Then `export_q5.py --kicad-cli ...` writes the variant A (SMT) and variant B (`-FULL-ASSEMBLY`) BOM/CPL, loose-part, home and offboard lists and Gerbers to `procurement/q5/`. No Q5 exporter negative test exists yet. The exporter checks its inputs itself.
8. `estimate_q5_jlc_cost.py` (KiCad Python) prices both variants from JLC's published fee schedule, `stock.json` and the observed PCB quote, and writes `procurement/q5/jlc-cost-estimate.json`. `build_q5_coupon.py` writes the print-tolerance coupon STL.
9. `tools/clicker-flash/test_clicker_flash.py --output verification/q5-flasher-tests.json` tests the macOS flasher against the dfu-util emulator.

Routing notes from the design lock:
- `preroute_q5.py --no-seed` routes without the locked SYS seed, which the re-placed board no longer uses.
- Freerouting 2.4.1 is deterministic. A knot that stays unrouted is fixed by nudging placement (for example R10 at 270°, C39 at x −0.3), not by editing the SES.
- After any re-placement, re-plan `gnd-stitch.json` with `plan_q5_stitching.py` before `finish_q5_board.py`.

## Historical Q4 engineering workflow

Q4 uses STM32L072CBT6, a complete SPI OLED module and external SPI FRAM. Q1/Q2/Q3 remain frozen. **All vendor quote activity, purchases and manufacture are paused.** These are local engineering operations.

1. Read `Q4-implementation.md`, `q4-power-design.md`, `q4-firmware.md` and the current review entry point before editing.
2. `build_q4_model.py` combines exact circuit identities with `electronics/q4/placement.json`. `build_q4_schematic.py` generates the native sheets, symbols, XML, PDF and local provenance using KiCad10. `build_q4_board.py` **discards existing routing**; use it only for an intentional new layout. `sync_q4_board.py` synchronizes native fields, paths and explicit NCs.
3. The routing pipeline is `preroute_q4.py`, `prepare_q4_route.py`, local Freerouting2.4.1 with analytics disabled, then `finish_q4_board.py`. Preserve the USB and supply seed routes. DSN/SES are private exchange files and excluded from Git; a saved session must match its exact source DSN. Review footprint geometry and mechanical solder envelopes as well as electrical clearances.
4. Run `python3 scripts/verify_q4.py --kicad-cli /path/to/kicad-cli` against stable final sources. It runs fresh native XML export, ERC and DRC with schematic parity and binds reports to the inputs. No electrical or courtyard exception is accepted. Running without `--kicad-cli` validates a saved binding; it is **not a fresh native check**. Some macOS hosts require permission for KiCad's local GUI-service initialization even for command-line DRC.
5. Run `python3 scripts/test_verify_q4.py --output verification/q4-negative-tests.json`. It first requires a clean real baseline, then corrupts temporary copies to test rejection. `test_export_q4.py` separately checks the exporter; synthetic exporter tests do not validate the routed board.
6. Firmware uses official Arm GNU14.3 and pinned ST/CMSIS headers. `build_firmware_q4.py --toolchain /path/to/toolchain` builds the default FRAM product. `--verify-only` checks committed source, compiler provenance and actual loaded image bytes. `test_firmware_q4.py` runs bounded portable behavior/fault cases; `--image-only` checks image corruption. The optional EEPROM backend is a separate test build. Follow `q4-firmware.md` for home USB programming and preservation rules.
7. Run `python3 simulation/q4-power/check.py` and the documented `run_spice.py --library /path/to/libngspice` command. They bind conditional equations and ideal subcircuit results, including the retained cold-insertion counterexample. They do not simulate every semiconductor or prove physical operation.
8. Run `build_q4_enclosure.py` with CadQuery2.8 and `--kicad-python /path/to/KiCad/Python`. Final outputs must use the actual final board/model, exit successfully, have four valid single solids and manifold bed-aligned STL meshes, and pass modeled static and sampled assembly-path intersections. Private snapshot overrides are for experiments, not final evidence. Inspect the rendered images and complete the separate physical fit checks.
9. Refresh the final stock/model binding, then run `export_q4.py --kicad-cli /path/to/kicad-cli`. It requires current native evidence and exports the factory SMT split separately from home completion and unqualified offboard items. This generates local engineering files and does not submit anything to a vendor.
10. Preserve historical package hashes with `verify_project.py`; commit a coherent final Q4 review candidate to the existing branch/draft PR. Hardware validation, actual battery/harness qualification and explicit order approval remain separate.

## Historical Q1/Q2 workflow

The following records the older revisions. It does not authorize quoting or rebuilding their frozen packages.

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


## Separate Q3 OLED candidate

Q1/Q2 artifacts remain frozen. Q3 sources, board, schematic, mechanics, procurement exports and firmware live in their own q3 directories.

1. The controlled model generator selects exact MPNs from the recorded live-stock evidence. Any position/circuit change requires regenerating the Q3 schematic provenance and synchronizing native fields/NC nets without discarding routes.
2. Run verify_q3.py --prepare-native with the local KiCad CLI. Execute its exact native DRC (including schematic parity), ERC and netlist-export commands; use --bind-native only after all three finish and the sources remain unchanged. One exact disclosed J1/SW2 courtyard projection is permitted; no electrical violation or unconnected item is permitted.
3. Run test_verify_q3.py --full --bound for deliberate corruption rejection against final evidence. It works on temporary copies.
4. build_q3_enclosure.py requires CadQuery and --kicad-python. Its default input is the final native Q3 board/model. Require exit0 and a matching manifest, four valid/manifold print parts and zero modeled intersections; a file's existence is insufficient. Private snapshot arguments support experiments, but are not final package evidence.
5. export_q3.py requires the current native validation and explicit local KiCad tools. package_q3.py then verifies historical integrity, Q3 evidence, firmware, mechanical and export hashes before producing dist/q3/click-counter-Q3-RFQ.zip.
6. Q3 target firmware uses TI GCC9.3.1.11/support1.212. build_firmware_q3.py --verify-only checks sources, outputs and information-FRAM separation. Factory initialization now covers34bytes,0x1800–0x1821; ordinary updates preserve the entire information region.

These checks establish file consistency and bounded software/geometry review. They do not establish physical power, protection, OLED process, runtime, battery or fit qualification, and do not authorize manufacture or payment.


## Additional September22 adversarial review

Run `python3 scripts/test_q3_behavior_model.py` to compile the unchanged production counter, input and OLED modules against a separate bounded deterministic harness. The saved result is `verification/q3-behavior-model-2026-09-22.json`. It checks arbitrary destination-word tears, recovery cuts, scheduling and display faults; it does not emulate analog rails or the MSP430 peripherals.

Run `python3 scripts/analyze_q3_hardware_corners_20260922.py` for the separate conditional electrical analysis. Read its explicit assumptions and the dated hardware review; a reproduced counterexample is not a hardware pass. The native September15 artifacts remain unchanged. Rechecking their source bindings on September22 does not constitute fresh native DRC.

The negative-check script currently uses the macOS scratch directory `/private/tmp`; ensure it exists when reproducing on another platform. Do not modify a hash-bound validation input and then reuse the previous native binding as though it still applied. The September15 RFQ is an immutable snapshot and does not contain these new reviews or later status documents.
