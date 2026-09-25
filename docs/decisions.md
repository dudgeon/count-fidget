# Decisions and major findings

## Current decisions — 23 September 2026

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
