# Instructions for agents

## Active Q5 checkpoint — 25 September 2026

The user asked for all findings from the Q4 simulation review to be resolved, plus a soft power key, a battery gauge with low warning and storage cut-off, charge status, a reachable hardware reset, new key logic (**both keys: increment wins; reset only after a deliberate 2 s hold and release**), a smaller enclosure and a BOM of standard JLC inventory parts only. **Q5 implements this as a coordinated revision of Q4:**
- same STM32L072CBT6 / ROM USB DFU, FM25V02A FRAM journal (Q4-compatible), HS96L01W4S03 SPI OLED module and 42 × 54 mm two-layer board (now 1.6 mm);
- adds a COUNT-key soft power latch on U7 (~8 µA off), a vendor-soldered LIR2032 holder (BT1) with an onboard NTC in place of the pack harness, SYS/2 battery sense and BQ25185 STAT inputs;
- 96 references: 82 fitted (81 vendor SMT + the DS1 display, home-soldered in variant A or JLC-fitted in variant B), 42 exact MPNs (16 JLC Extended types after the 26 Sep Basic-part review), all passing a read-only 10-board JLC stock screen;
- five-part printed enclosure (base, front cover, rear key plate, two keycaps), 47.2 × 59.2 × 16.8 mm.

Start at `docs/REVIEW-Q5-2026-09-25.md`, then `docs/q5-power-design.md` and `docs/q5-firmware.md`. Q5 lives in `electronics/q5/`, `firmware/q5-stm32/`, `mechanical/q5/`, `procurement/q5/`, `simulation/q5-*` and `scripts/*q5*`. Q1–Q4 artifacts are frozen; never run a Q4 builder against Q5.

Evidence:
- fresh KiCad 10.0.6 ERC/DRC/unconnected/parity all zero;
- 42/42 verifier corruptions rejected;
- full and UBSan firmware suites plus 13 image negatives passed;
- 37 instruction-level emulator scenario records on the final ELF with zero failures;
- five valid/manifold enclosure parts with zero modelled collisions.

**None of it is a measurement.** Preserve the Q5 physical gates:
- latch timing with a real contact and clean release;
- ADC/gauge accuracy and STAT behaviour;
- holder contact/retention and USB-first cell insertion (the cold-insertion counterexample remains);
- the display module power tree and repeated hard resets;
- USB cable fit, printed keycaps, pinhole access;
- solder process.

**Quote authorization (user, 25 September 2026):** once the Q5 hardware design is locked, obtain **JLCPCB quotes** for two variants:
- (A) JLC performs SMT and the user solders the through-hole parts;
- (B) JLC assembles everything, including the through-hole parts.

This lifts the quote pause for JLCPCB quoting only. Uploading the locked design files to JLCPCB's quote tools is allowed. Placing an order, paying, allocating or preordering stock, releasing manufacturing, or contacting other vendors remains unauthorized. Record quote results in `procurement/q5/` and the quote tracker, without account IDs, personal data or private screenshots. Read-only public stock research is allowed. Commit/push Q5 work to `claude/loving-noether-4qogm0` and its draft PR #10; do not merge.

**Design locked (25 September evening).** SW1/SW2 are vendor-SMT MX hot-swap sockets on a 1.6 mm PCB; the clicky switches K1/K2 press in without soldering. Ten passives/FETs moved to JLC Basic parts. Quote status is in `procurement/q5/JLC-QUOTE-Q5.md`:
- the public quote page gave PCB $22.10 and DHL $29.45 for 10 boards;
- the parts-matched PCBA step needs the user's JLCPCB sign-in;
- the estimate from published fees, shipped, for variant B (chosen): ≈ $156 for 2 boards, $200 for 5, $281 for 10.
The macOS flashing tool is `tools/clicker-flash/` (skill `flash-clickers`). The first-article plan is `docs/q5-first-article-test-plan.md`.

**First-order de-risking (26 September).** The owner decided on variant B (JLC assembles everything) and a small first batch. Three independent checks found no pinout, footprint or dead-on-arrival defect: a datasheet pinout audit, a fit against JLC's EasyEDA footprints and a DOA review. The resulting changes are the R39/C9 filter on U5's supply, C40 raised to 10 nF, the JLC-corrected CPLs with a preview checklist, and a flasher rule to press the pinhole before unplugging a unit in DFU; see the REVIEW-Q5 section. The owner may bring this session to their Mac and sign in to JLCPCB themselves; the agent may then drive the signed-in quote flow up to the order summary. **Payment or order placement needs the owner's explicit go-ahead at that moment.**

## Previous Q4 checkpoint — 24 September 2026 (superseded by Q5 where inconsistent)

The user authorized choosing and implementing the best product architecture, prioritizing reliability, simple integration and easy home bootloading over small price differences. **Q4 is implemented with STM32L072CBT6, factory ROM USB DFU, a complete SPI OLED module and external SPI FRAM.** It has a 42 × 54 × 1 mm two-layer PCB, 70 fitted parts (67 factory SMT plus three home through-hole placements) and four PCB mounting holes. The USB-C port supports the intended home programming workflow through a data cable; physical enumeration remains untested.

Start at `docs/REVIEW-Q4-2026-09-24.md` and `docs/Q4-implementation.md`. Native Q4 schematic/board, target firmware, stock evidence and four-part enclosure are separate from all historical Q1/Q2/Q3 artifacts. Independent review corrected firmware sleep/recovery faults, supply margin, display/header geometry and enclosure retention/clearances. Final native, firmware, inventory, routing, CAD and export evidence is bound to the frozen sources. Fresh native checks are zero ERC/DRC/unconnected/parity; all 42 verifier corruptions were rejected. Full/UBSan firmware tests, 13 image/protocol negatives, two identical builds and four valid/manifold enclosure parts passed. Use the linked review entry point for the exact scope and physical limits.

**The quote pause remains in force:** no uploads, quote-draft changes, vendor messages, paid sourcing, purchases or manufacturing release. Read-only public stock research is allowed. Commit/push coherent engineering work to `codex/q2-engineering-audit` and the existing draft PR #1; do not merge.

Preserve the explicit physical gates in the Q4 review: regulator/transient and memory-rail behavior, real USB/MCU operation, battery/protection/temperature and insertion/recovery, qualified pack/NTC harness, display current/runtime, solder process and enclosure fit. Cold insertion still has a conditional counterexample. USB-first commissioning is a proposed testable workflow, not a demonstrated guarantee. Native checks, host firmware tests and ideal ngspice subcircuits are not whole-board simulation or physical qualification. The selected PCB MPNs have timestamped positive stock evidence; stock is unallocated, and the offboard pack/keycaps/process are not qualified.

## Historical checkpoints — superseded where inconsistent with Q5

## Current task and authorization — 23 September 2026

Continue the Q3 engineering review on `codex/q2-engineering-audit` and the existing draft PR #1. Read `PROJECT.md`, `HANDOFF.md`, `docs/REVIEW-Q3-2026-09-22.md`, `docs/product-spec.md`, `docs/user-research.md`, `docs/decisions.md`, `docs/open-issues.md`, and `procurement/vendor-status.md`. The user's current instructions override historical checkpoints.

The latest task is to bring concrete MCU/home-programming options and continue engineering. Read `docs/mcu-options-2026-09-23.md` and its programming, hardware and stock evidence. STM32L072CBT6 is the recommended next architecture, not an implemented replacement or user-approved order. Fresh stock supports that candidate; all-MCU-domain 3.3 V regulation, OLED 3.0 V interfaces, ROM USB recovery and EEPROM journaling still require a coordinated design. Preserve Q3 as the baseline. The new ngspice study contains idealized subcircuits only; never describe it as a whole-board simulation or hardware pass.

**All new vendor quotations are paused until the user explicitly authorizes another.** Do not upload revisions, change quote drafts, advance automatic quotations, accept the old pending PCBWay Q3 notice, or send another technical review request. Read-only catalog/stock research and reading incoming replies are allowed. No spending, paid sourcing/preorder, order placement or manufacturing release is authorized.

The user requests adversarial functional review, meaningful deterministic simulation where useful, and a coherent committed review candidate for another agent. The user permits home programming and limited through-hole soldering when materially cheaper. This does not mandate an ESP32 redesign: the current MCU is **MSP430FR4133IG48R**, programmed with Spy-Bi-Wire. USB is charge-only. See the home-completion cost note for the supported scope and limits.

## Engineering truthfulness

- Q3 is a two-layer OLED candidate, not physically qualified. Source consistency, host tests, corner models and CAD checks are separate from measured electrical function, reliable assembly and manufacturing approval.
- Do not call September15 inventory observations current. Read the September22 stock report and distinguish in-house stock, MOQ/preorder, third-party stock, allocation and both-vendor acceptance.
- OLED X087-2832TSWIG02-H14/C18723015 is recognized by JLCPCB as an assembly component. Its corrected category is not an approved FPC heat/land/support process. Exact PCBWay sourcing/process acceptance remains open.
- Preserve the OLED I²C sink/rise margin, converter/cell current, capacitor inrush, charging/protection/thermal, battery-pack, FRAM brownout, effective-capacitance, fit and runtime gaps. Simulated assumptions must not become specifications.
- Preserve Q1/Q2 and the September15 Q3 RFQ archive as historical evidence. New analysis belongs in dated files. Do not overwrite frozen packages to make their old claims appear current.
- The original Q1 source/binary mismatch allegation was refuted: TI's LCD4MUX includes LCDSON, and an exact rebuild reproduced the HEX. Missing LCD reservoir capacitors were real; the Q3 OLED removes that LCD circuit.

## Active design and verification

Q3 native sources live in `electronics/q3/`, target firmware in `firmware/q3-oled/`, mechanics in `mechanical/q3/`, and procurement evidence in `procurement/q3/`. The top-level firmware and older directories are historical separate revisions. Never run a Q1/Q2 builder against Q3.

Run `scripts/verify_q3.py` for model/schematic/PCB/BOM/CPL consistency and source-bound native evidence; `scripts/test_verify_q3.py --full --bound` checks deliberate corruption rejection. A saved DRC report revalidated against unchanged inputs is not a new native DRC run. One exact documented J1/SW2 courtyard projection is disclosed; no electrical-clearance or connectivity exception is allowed.

Any actual design change requires corresponding native synchronization, fresh ERC/DRC/parity, exports, firmware and mechanics checks as affected. `build_q3_board.py` can discard routes; do not regenerate the routed board casually. Read `docs/build-and-verify.md` first. Retain four enclosure parts (base, front lid, rear lid, battery keeper), not the obsolete one-piece lid.

Firmware factory initialization clears exactly0x1800–0x1821. Ordinary updates must preserve all information FRAM0x1800–0x19FF. Verify sources, exact compiler flags, ELF/HEX/map/listing hashes and the factory/application separation. A successful flash does not qualify the hardware.

Run `scripts/verify_project.py` to preserve prior-revision provenance. Never infer physical qualification from a package existing or from old reports passing.

## Procurement and handoff

The September15 JLCPCB five-board automatic result was $255.86 plus separately displayed $3.28 depaneling; final freight, battery/harness, keycaps, programming/testing and delivered costs were incomplete. There is no observed ten-unit Q3 total. PCBWay Q3 calculators excluded components/services and its representative cautioned they were not final prices. The old pending Q3 agreement is inactive during the quote pause. No payment/manufacture occurred.

Preserve quote history in `procurement/q3/portal-quotes.json`, `procurement/quote-tracker.json` and the vendor ledger. Historical portal-first and correspondence instructions do not authorize activity during the current pause. When quoting is reauthorized, use one consolidated revision and one communication channel per unresolved matter.

## Repository maintenance and privacy

Commit/push coherent engineering progress to the existing branch/draft PR; do not merge or invent reviewer approval. Update the review entry point and current status after material findings. Distinguish planned, checked, submitted, acknowledged, quoted, paid and released.

This repository is public. Do not commit credentials, mail/account IDs, personal delivery/contact details, private screenshots or signed attachment links. The ignored Q3 DSN/SES are local router-exchange provenance; the DSN contains a local path and is checksum-bound. Do not stage or silently sanitize those files. They are excluded from the frozen RFQ. Keep private working material ignored.
