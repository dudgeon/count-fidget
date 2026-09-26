# Decisions and major findings

## Current decisions — 25 September 2026 (Q5)

| Decision | Reason and consequence | State |
|---|---|---|
| COUNT key is also the power key; U7 becomes a soft latch (PB2 hold, VBUS via D4) | Removes the ~80 µA sleep drain without replacing the reviewed TLV767 rail. Shelf life goes from 2–3 weeks to ~5 months. The power-on press counts. | Implemented; latch timing and release are physical gates |
| Keep TLV767 rather than a nano-IQ LDO (#5) | It is unpowered when off, so its IQ matters only while awake. Keeping it avoids re-opening the USB/OLED rail corners. | Implemented |
| LIR2032 in a vendor-soldered BT1 holder + onboard NTC, J2 harness removed (#13) | Every BOM line is a JLC inventory part. The user inserts an off-the-shelf rechargeable cell with USB connected. | Implemented; holder contact, thermal coupling and first-connection behaviour are physical gates |
| Increment wins over reset; reset needs a 2 s hold and a release before 10 s | Owner rule; prevents accidental and pocket resets and makes DFU entry count-safe (#3) | Implemented and emulated |
| Battery gauge (4 bars), LO below 3.55 V, storage power-off after 6 samples below 3.35 V | No blind counting (#9.4). Keeps the rail regulated and leaves ~9.5 days to the protector's 2.8 V disconnect. | Implemented; thresholds must be checked against a real discharge curve |
| USB detection by SYS ≥ 4.313 V OR either STAT low | 2.06 % worst-case ADC budget separates a full cell (≤ 4.308 V read) from USB SYS (≥ 4.319 V read). STAT covers charging/fault at any error. | Implemented |
| U6 QOD unconnected (#8) | SSD1315 §6.9.2 forbids grounding VBAT, and a hard reset previously did. The module supply stays at VLOGIC. | Implemented; module power tree is a first-article gate |
| Firmware self-provisions BOR_LEV 0xC (USER 0x807C) once; never RDP (#6) | A freshly flashed board must work without GUI option setup | Implemented and emulated |
| Printed MX keycaps; enclosure shrunk and USB opening corrected (#4) | No unsourced keycaps; standard USB-C plugs can mate | Implemented; print and cable fit are gates |
| Hot-swap MX sockets (CPG151101S11-16, vendor SMT) + loose clicky CPG151101D13 switches; PCB 1.6 mm | JLC stocks no clicky 5-pin MX switch it can place. A soft-tactile switch was rejected because the audible click is central to the product (user research). The sockets make the keys solder-free and need a 1.6 mm board. | Implemented, design lock; socket seating and retention are first-article gate G2b |
| Ten generic passives/FETs moved to JLC Basic parts | Each Extended type costs a $3.07 feeder fee; ~$31 saved per order. Precision dividers and the specified MLCC/diode parts are unchanged. | Implemented, re-verified |
| Basic parts wherever the circuit allows (26 Sep) | Each Extended type costs $3.07 per order. Nine types were moved to Basic with re-derived values (charge 16.7 mA, window 7.3–35.8 °C). The 16 remaining Extended types are justified in REVIEW-Q5 | Implemented, re-verified |
| First-order de-risking (26 Sep) | Independent pinout, footprint and dead-on-arrival checks; R39 filter on U5's supply; C40 10 nF; JLC-corrected CPLs | Implemented, re-verified |
| Two JLCPCB variants: A = user solders the display header; B = JLC fits the display | Owner request. B costs ~$30 more at JLC (estimate) and removes all home soldering. | PCB price observed; parts-matched PCBA quote needs the owner's signed-in upload ([JLC-QUOTE-Q5](../procurement/q5/JLC-QUOTE-Q5.md)) |

## Previous decisions — 23 September 2026

| Decision / finding | Reason and consequence | State |
|---|---|---|
| Two-layer OLED Q3 | Replaces the original unmatched reflective LCD; MCU LCD peripheral is unused | Implemented and preserved; electrical/assembly qualification remains open |
| Home programming and limited through-hole soldering | User permits them when materially useful; full vendor programming is no longer a fixed requirement | Authorized scope, not an approved order |
| STM32L072CBT6 preferred for the next candidate | Factory USB programming, low-power architecture, adequate live stock and built-in EEPROM | Recommended after the [options study](mcu-options-2026-09-23.md); circuit and firmware not implemented |
| Shared 3.3 V MCU domains, retained 3.0 V OLED | Avoid an under-voltage USB supply and independently powered USB-domain sequencing problem | Proposed architecture; interface, dropout and startup checks required |
| EEPROM journal must be redesigned | FRAM's two-record write strategy does not transfer directly to EEPROM wear/timing/ECC behavior | Target implementation and adversarial verification pending |
| Simulation scope is explicit | New ngspice run covers only idealized interface/inrush subcircuits | No whole-board simulation or hardware pass |
| Vendor quotation pause | User wants one settled revision before another quote | No new submissions, uploads, draft changes or vendor requests until explicit instruction |

See the dated study for component prices, model coverage and cost tradeoffs. Q3's existing firmware, native design and September15 archive are unchanged. Current user instructions supersede the historical table below.

## Historical Q1 decisions

Design reasoning, not blanket user approval. Q1 overrides Rev0; no hardware release is implied.

| Decision / finding | Reason and consequence | State |
|---|---|---|
| FRAM MCU with LCD drive | MSP430FR4133 combines display drive, retention and sleep; avoids separate driver/per-click flash strategy | Implemented |
| 48-pin TSSOP replaces 64-pin LQFP | Current IG48R has different pin mapping; old IPM schedule obsolete | Implemented |
| Reflective display baseline | Low power and daylight readability | DE188 conditional on qualification |
| DE188 response 440 ms | Fast-changing digits may blur despite accurate counting | Open; OLED fallback requires redesign/runtime budget |
| Standard MX Blue keys | Familiar click and cap choice; low-profile or smaller reset could reduce mass | Working choice, no comparative study |
| Screen kept separate from key area | Earlier notes moved screen to avoid tall keys obscuring it | Final viewing angle/fit still to check |
| 30-second LCD-off/LPM4 | Either key can wake; FRAM survives absent battery | Implemented; current unmeasured |
| Journal per accepted change | Two CRC records with previous-commit fallback | Host tested between word writes; analog brownout open |
| Saturate at 99,999,999 | Avoid rollover | Implemented; visible overflow cue missing |
| Prepared cell/NTC harness | Reduces holder bulk and avoids customer soldering | Supplier drawing/process approval pending |
| EEMB LIR2032 45 mAh | Specific manufacturer data; VARTA CP1254 considered lighter alternative | Alternative needs independent review |
| 18.2 mA charge current | Q1 16.5 kΩ ISET replaces Rev0 15 kΩ / 20 mA | Implemented; tolerance/termination open |
| Low-current compensation correction | TI EVM ISET → 2 kΩ → 4.7 nF → GND; Rev0 50 pF text obsolete | Implemented, never connected to SYS |
| Independent thermal comparator | Narrow nominal 8–36°C window; fixed TS resistor only alongside real cell sensor | Hardware verification open |
| Cell/protector endpoint mismatch | 2.8 V ±0.1 V UV can reach below 2.75 V cell endpoint | Release blocker |
| Four-layer 1 mm PCB | Compact routed board with internal ground and pogo lands | Exists; 2-layer alternative requires routing work |
| PCBWay 1 oz inner form minimum | RFQ preference is 0.5 oz inner | Price distinct stack alternatives honestly |
| Separate offboard BOM | BAT1/K1/K2 intentionally absent from CPL | Corrected 46-ref importer BOM, not uploaded |
| Website quoting is required | Geoff explicitly asked to complete uploads and full quotes | Immediate unfinished goal |
| Authentication succeeded; controller failed | PCBWay sign-in verified before global Calculate/navigation/observation timeouts | Do not diagnose login as current cause |
| GitHub/local-session handoff | User's new execution plan | Verify local access; cloud cause unproven |

Rev0's statements that PCB/firmware do not exist are superseded. Renders were generated from real fit-study CAD, but purchased parts are envelopes and omitted pins/wires/clearances were not validated. Old geometry does not match Q1 mounts/USB.
