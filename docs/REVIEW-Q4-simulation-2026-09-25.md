# Q4 simulation review — 25 September 2026

Independent review of commit `5fa88f7` (Q4 STM32L072 / SPI OLED module / FM25V02A FRAM). It asks whether the design would work as a product, measures how well it would work, and lists improvements. **Nothing here is a hardware measurement.** The quote pause and every physical gate in `REVIEW-Q4-2026-09-24.md` remain in force; no vendor activity took place.

## Verdict

The electrical architecture is sound. The native design data reproduce independently. However, **the assembled product as committed would not work in two ways a user would hit immediately**, and a third defect loses data during updates:

| # | Finding | Effect | Evidence | Issue |
|---|---|---|---|---|
| 1 | Boot-time FRAM journal scan (245–409 ms) overflows the 255-sample button queue | After any reset, the saved count shows `ERR`, increments are ignored and `fault=1` is persisted; clearing it zeroes the count | Emulation of the committed image with an M0+ cycle model; a patch passes all scenarios | [#2](https://github.com/dudgeon/count-fidget/issues/2) |
| 2 | USB-C mouth is 3.4 mm behind a 13.2 × 4.8 mm opening | Standard cables (overmold ≤ 12.35 × 6.5 mm per USB-IF) stop ~3 mm short of mating: no charging or DFU once enclosed | STL ray-cast + USB Type-C R2.0 Figs. 3-1/3-80; the enclosure checker rejects the design with a spec-size plug envelope | [#4](https://github.com/dudgeon/count-fidget/issues/4) |
| 3 | Documented DFU entry zeroes the count when the battery is attached | The update workflow destroys the value it promises to preserve | Emulation S4/S4b vs. S5 | [#3](https://github.com/dudgeon/count-fidget/issues/3) (docs corrected in the linked PR) |
| 4 | 83 µA standby, 80 % of it the TLV767 IQ plus its divider | 18–20 days on a shelf, ~2 weeks in use; a nano-IQ fixed LDO gives ~3–5× | Datasheet budget × emulated state timelines | [#5](https://github.com/dudgeon/count-fidget/issues/5) |
| 5 | Factory option bytes (`BOR_LEV = 0`) leave the board blank | Silent "dead" device after a missed or mislabelled option-byte step | Emulation S6; RM0376 §3.7.8 | [#6](https://github.com/dudgeon/count-fidget/issues/6) |
| 6 | 0.2 s press-to-display, 0.77 s from sleep | Sluggish feedback for a fidget device | Emulated latency breakdown | [#7](https://github.com/dudgeon/count-fidget/issues/7) |
| 7 | OLED module fed below its stated 3.5–4.2 V DC/DC range; QOD grounds it on hard resets | Brightness/pump margin and abrupt power-off unqualified | Module datasheet §3.2, SSD1315 §6.9.2, emulator power-order check | [#8](https://github.com/dudgeon/count-fidget/issues/8) |
| 8 | PVD5/BOR4 overlap, BQ2970 first-connection behaviour, insertion window by cell R, blind low-battery counting | Documentation and UX refinements | DS10689 Table 27, BQ2970 §8.4.1, RC sweep | [#9](https://github.com/dudgeon/count-fidget/issues/9) |

Items 1–3 are cheap fixes (a few firmware lines, one enclosure parameter pair, a documentation order). After them, the remaining risks are the physical gates the Q4 review already lists.

## What was checked, and how

| Check | Result |
|---|---|
| Native ERC/DRC/parity with KiCad 10.0.6 on Linux (`verify_q4.py --kicad-cli`) | Pass. Reports identical to the committed ones except timestamps; all 86 footprints have courtyards, so the ignored `missing_courtyard` rule hides nothing. |
| Firmware rebuild with Arm GNU 14.3.Rel1 (x86_64 Linux build of the pinned release) | BIN and HEX byte-identical to the committed outputs; ELF/map differ only in host metadata. `--verify-only` and host fault suites pass. |
| codex ngspice and analytical power checks (`simulation/q4-power`) | Reproduced with ngspice 42 (differences ~1e-12). |
| Datasheet cross-checks | TPS22917 CT-to-VIN correct; TLV767 DRV adjustable pinout correct; BQ25185 CE active-low, TS/MR 10 kΩ disable, 24 kΩ VSET = 4.2 V / ILIM100, 16.5 kΩ ISET = 18.2 mA; BQ29700 thresholds and delays as modelled; FM25V02A ID and timing; AN2606 confirms the L072 ROM (V4.x) uses only USART1/USART2/USB DFU with internal clocking and no DP pull-up, so the OLED SPI2 pins are not touched in DFU. The Stop routine's `RUN_PD` clear without re-unlocking is correct per RM0376 §3.6.4 (the lock re-arms only when RUN_PD is cleared). |
| Instruction-level emulation of the actual ELF (`simulation/q4-firmware-emulation/`) | Startup, clocks, GPIO/AF configuration, SPI framing to FRAM and OLED, both ISRs, Stop entry/exit, OLED power order and back-power rules: no contract violations in normal operation. Found finding 1 (9 scenario failures, one cause); the candidate patch passes all expectations. |
| Energy model (emulated state durations × datasheet currents) | See [#5](https://github.com/dudgeon/count-fidget/issues/5). Per display session: OLED ≈ 56 %, MCU run ≈ 24 %; standby dominates daily use. |
| Enclosure (committed STLs, `build_q4_enclosure.py` with CadQuery 2.8) | Pinhole, display window and mounts consistent after the documented Y-mirror export; USB-C mating fails (finding 2). The proposed opening passes the script's own collision checks with a USB-IF max plug envelope. |
| Cold-insertion window versus cell/contact resistance | Consistent with the existing counterexample; trip needs a short-delay unit plus low VSCC and/or derated-high capacitance ([#9](https://github.com/dudgeon/count-fidget/issues/9)). |

## Reproduce

```sh
python3 scripts/verify_q4.py --kicad-cli /path/to/kicad-cli          # fresh native checks
python3 simulation/q4-firmware-emulation/scenarios.py --output simulation/q4-firmware-emulation/results/committed-firmware-scenarios.json
python3 simulation/q4-firmware-emulation/scenarios.py --elf /path/to/candidate.elf --check
python3 simulation/q4-firmware-emulation/energy.py
```

Committed results: `simulation/q4-firmware-emulation/results/committed-firmware-scenarios.json` (image SHA-256 `9a982e4322120769…`, 9 expectation failures) and `results/energy-model.json`.

## Limits

The emulator models peripherals from reference-manual descriptions, uses Cortex-M0+ TRM cycle costs with a stated flash-wait-state assumption, and treats analog behaviour as absent. Currents in the energy model are datasheet typicals or stated estimates (module ≈ 1 mA at contrast 0x10). Enclosure conclusions depend on the USB Type-C specification's plug and receptacle dimensions and on the committed CAD. None of these results replaces first-article USB, power, battery, display, timing or fit measurements.
