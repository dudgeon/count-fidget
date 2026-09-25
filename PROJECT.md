# Count Fidget — project status

## Active Q5 checkpoint — 25 September 2026

The user asked for all findings from the Q4 simulation review to be resolved, plus a soft power key, a battery gauge with low warning and storage cut-off, charge status, a reachable hardware reset, new key logic (**both keys: increment wins; reset only after a deliberate 2 s hold and release**), a smaller enclosure and a BOM of standard JLC inventory parts only. **Q5 implements this as a coordinated revision of Q4:**
- same STM32L072CBT6 / ROM USB DFU, FM25V02A FRAM journal (Q4-compatible), HS96L01W4S03 SPI OLED module and 42 × 54 mm two-layer board (now 1.6 mm);
- adds a COUNT-key soft power latch on U7 (~8 µA off), a vendor-soldered LIR2032 holder (BT1) with an onboard NTC in place of the pack harness, SYS/2 battery sense and BQ25185 STAT inputs;
- 95 references: 81 fitted (80 vendor SMT + the DS1 display, home-soldered in variant A or JLC-fitted in variant B), 41 exact MPNs, all passing a read-only 10-board JLC stock screen;
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
- the estimate from published fees is A ≈ $246 and B ≈ $277 before shipping.
The macOS flashing tool is `tools/clicker-flash/` (skill `flash-clickers`). The first-article plan is `docs/q5-first-article-test-plan.md`.

## Previous Q4 checkpoint — 24 September 2026 (superseded by Q5 where inconsistent)

The user authorized choosing and implementing the best product architecture, prioritizing reliability, simple integration and easy home bootloading over small price differences. **Q4 is implemented with STM32L072CBT6, factory ROM USB DFU, a complete SPI OLED module and external SPI FRAM.** It has a 42 × 54 × 1 mm two-layer PCB, 70 fitted parts (67 factory SMT plus three home through-hole placements) and four PCB mounting holes. The USB-C port supports the intended home programming workflow through a data cable; physical enumeration remains untested.

Start at `docs/REVIEW-Q4-2026-09-24.md` and `docs/Q4-implementation.md`. Native Q4 schematic/board, target firmware, stock evidence and four-part enclosure are separate from all historical Q1/Q2/Q3 artifacts. Independent review corrected firmware sleep/recovery faults, supply margin, display/header geometry and enclosure retention/clearances. Final native, firmware, inventory, routing, CAD and export evidence is bound to the frozen sources. Fresh native checks are zero ERC/DRC/unconnected/parity; all 42 verifier corruptions were rejected. Full/UBSan firmware tests, 13 image/protocol negatives, two identical builds and four valid/manifold enclosure parts passed. Use the linked review entry point for the exact scope and physical limits.

**The quote pause remains in force:** no uploads, quote-draft changes, vendor messages, paid sourcing, purchases or manufacturing release. Read-only public stock research is allowed. Commit/push coherent engineering work to `codex/q2-engineering-audit` and the existing draft PR #1; do not merge.

Preserve the explicit physical gates in the Q4 review: regulator/transient and memory-rail behavior, real USB/MCU operation, battery/protection/temperature and insertion/recovery, qualified pack/NTC harness, display current/runtime, solder process and enclosure fit. Cold insertion still has a conditional counterexample. USB-first commissioning is a proposed testable workflow, not a demonstrated guarantee. Native checks, host firmware tests and ideal ngspice subcircuits are not whole-board simulation or physical qualification. The selected PCB MPNs have timestamped positive stock evidence; stock is unallocated, and the offboard pack/keycaps/process are not qualified.

## Historical checkpoints — superseded where inconsistent with Q5

## Active direction — 23 September 2026: home-programming options

The user requested concrete options after questioning the MCU choice and whole-board simulation coverage. The [completed options study](docs/mcu-options-2026-09-23.md) recommends **STM32L072CBT6 with factory USB programming** as the next engineering candidate. Fresh JLC stock is 2,211 orderable at $2.7916 each at ten; a candidate extra TPS7A0233 regulator has 8,852 orderable at $0.4751. These are unallocated component prices, not a revised device quote or both-vendor acceptance.

The study compares retained MSP430, STM32, ATtiny/UPDI and ESP32-C3; it includes separate programming and hardware reviews plus a runnable ngspice subcircuit study. The simulation reproduces conditional interface/inrush risks with ideal elements; **no complete board has been simulated or physically qualified**. Q3 remains unchanged. Developing the recommended STM32 circuit requires power/interface changes and a new EEPROM journal before layout, firmware, CAD and qualification can be considered complete.

**All quote submissions, uploads, draft changes, vendor requests, purchases and manufacture remain paused.** Continue engineering within the existing branch/draft PR, consolidate a future revision, and wait for explicit user instruction before any new vendor quote activity. The September22 review below remains the frozen Q3 baseline; historical retention of the MSP430 is superseded as a recommendation, not as the implemented design.

## Active direction — 22 September 2026: engineering review only

The user has **paused all new vendor quote submissions until a fresh explicit instruction**. Do not upload revisions, change quote drafts, advance automatic quotations, accept the old pending PCBWay Q3 notice, or send another technical review request. This supersedes every earlier portal-first/upload instruction below. Read-only stock research is allowed. No spending or manufacturing release is authorized.

Finish an independent adversarial functional review, use deterministic models where meaningful, and commit/push a coherent review candidate to the existing branch/draft PR so another agent can inspect it. The user now permits **home programming and limited through-hole soldering if materially cheaper**. The implemented MCU remains **MSP430FR4133IG48R**, not ESP32; home programming needs a compatible Spy-Bi-Wire adapter. This permission does not ask for an ESP32 redesign or home fine-pitch/FPC work, nor does it qualify the battery pack.

The dated review entry point is `docs/REVIEW-Q3-2026-09-22.md`. Historical Q1/Q2 and the September15 Q3 RFQ archive remain immutable evidence. Any new analysis must state what is actually verified and what still requires physical qualification. Do not call September15 catalog observations current stock or confuse the portal's preview with a final numbered-pad placement approval.

### Fresh review result — 22 September

The coordinated Q3 candidate is being committed for independent review. Fresh inventory covers40/43 exact PCB MPNs in JLC available stock; the remaining three exact identities have verified DigiKey stock, which is not accepted JLC/PCBWay sourcing or allocation. No substitutes were silently introduced. The new deterministic software harness passes more than2.5million bounded cases with no new confirmed production-code bug. The hardware review retains conditional I²C acknowledgement/rise-time and battery-insertion surge counterexamples, plus the existing OLED current, charging/protection, battery and physical qualification gaps. It does not claim a demonstrated working device. See `docs/REVIEW-Q3-2026-09-22.md` for the review entry point, evidence, stock sources and home-programming/USB tradeoffs.

### Last observed quote state, retained without resubmission

On **15 September at 13:58:26 UTC**, JLCPCB Q3 reached Quote & Order for five boards: **$255.86** = $22.04 PCB + $233.82 PCBA, including all43 component types. Depaneling was a separate **$3.28**. Programming/test/assembly remarks required review; battery/harness, keycaps and final delivered costs were incomplete. Earlier $27.63 freight was a PCB-stage estimate, not the final563.85g assembled/lithium shipment. All70 fitted refs were selected. There is **no observed ten-unit Q3 total**. No order/payment/manufacture occurred.

The minimal BOM corrected a portal column-mapping issue. DS1 and U5 received preview adjustments; the original CPL remains unchanged. Full model-offset, numbered-pad and final vendor DFM review remain open. PCBWay Q3 had only $131.62/5 and $177.00/10 calculators excluding components/services; its Q3 submission was not completed. The old Q3 agreement question is inactive while quoting is paused. See `procurement/q3/portal-quotes.json`.

## Historical instructions and checkpoint — superseded where inconsistent

## Active revision — Q3 replacement, 15 September 2026

The user explicitly requires replacing the unmatched DE188 with a display supported by both vendors. The historical retained-display recommendation below is superseded. Q3 engineering candidate: **X087-2832TSWIG02-H14 / C18723015**, with live JLC stock and assembly support verified; exact PCBWay sourcing/FPC assembly acceptance remains pending. See [selection evidence](docs/q3-display-selection.md).

The revised design, adversarial-agent reviews/fixes, final native/CAD/export checks and the actual updated rendering shown to the user are complete. **Q3 is ready for quotation; portal updates and complete 5/10 quotes are now underway.** The two-layer board uses bottom-only SMT, 70 fitted PCB refs and 43 exact stocked MPNs. Four layers were not a functional requirement; total savings still depend on complete quotes. Independent reviews corrected firmware input/recovery/power-guard defects, shortened OLED power loops, and resolved modeled enclosure collisions and the one-piece assembly trap with a four-part split cover. Q1/Q2 submitted files remain frozen.

Final evidence: native binding verifies **82 refs / 70 fitted / 218 connected pins / 50 NC**, with all 62 negative checks rejecting deliberately corrupted inputs. Connectivity, schematic parity and electrical DRC checks pass; the exact documented J1 shell/SW2 raised-courtyard projection remains visible. CAD checks cover four valid/manifold print solids, zero modeled collisions, 242 assembly poses and 4,837 sampled collision tests. These checks do not establish physical fit, measured power/runtime, safe cell/charger/protection operation or manufacturing release.

The [Q3 RFQ package](dist/q3/click-counter-Q3-RFQ.zip) contains **152 members / 4,031,548 bytes**, SHA-256 `4626d8ba64ef67d9bf5265399d6f6bf8e0d4ce9dda87d3656b5e5579aecef5ba`. The [Q3 Gerber archive](procurement/q3/click-counter-Q3-Gerbers.zip) is **106,301 bytes**, SHA-256 `ad3941a76d1c610792a9a38ed9eee54366379bdfb047c5e9a2a5d695628c6c85`.

## Historical Q2 engineering candidate, 15 September 2026

The independent audit has been implemented as a separate **Q2 engineering candidate** on `codex/q2-engineering-audit`, reviewed through [draft PR #1](https://github.com/dudgeon/count-fidget/pull/1). Q1's submitted board, firmware and RFQ remain frozen and on engineering hold.

Q2 retains the exact DE188 3 V reflective display. The original display choice, eight digits and dimensions were design assumptions; researched passive alternatives do not establish a JLCPCB stock advantage. Changing the display alone would not resolve JLCPCB's battery and test-service exclusions.

### Implemented design changes

- Add three 100 nF LCD bias reservoirs; use the separately verified 32 Hz firmware candidate; correct nominal LCD lead-row centers to 13.0 mm while retaining the existing 1.7 mm drills for sample review.
- Select the orderable TPS7A0230PDBVR regulator intentionally, including its active output discharge. Replace the thermal comparator with TLV7032DGKR, separate its outputs, and use two series charge-enable switches with local ground pulldowns.
- Reduce NTC excitation, retain the conservative nominal temperature window and document tolerance/fault limits. Increase V3 bulk capacitance to 10 µF and improve local decoupling placement.
- Create a six-sheet native schematic, independently compare physical pins/nets and add repeatable native ERC/DRC/parity checks with file hashes.
- Build a separate enclosure candidate around actual PCB mounts, USB, LCD, key centers, solder tails and the prepared battery/harness envelope.

See [power design](docs/q2-power-design.md), [display decision](docs/q2-display-selection.md), [open issues](docs/open-issues.md) and the native verification outputs for exact completion evidence. File consistency is not physical qualification. In particular, cell/protection compatibility, low-current charging, thermal fault response, effective capacitance, LCD response, FRAM brownout, enclosure retention and mass/runtime remain unmeasured.

**The source/binary allegation was refuted.** TI's `LCD4MUX` macro includes `LCDSON`, and the original source reproduces the frozen Q1 HEX byte-for-byte. Explicit LCDSON in the Q2 source is clarity; the real firmware change is 32 Hz timing. The suspected BQ25185 pin/resistor error was also refuted.

## Product and authorized scope

A lightweight two-key counter fidget with a display, rechargeable coin cell, USB-C charging and retained count. Geoff prints/fits the enclosure and attaches loose keycaps and the keyed battery plug. Vendors do all soldering, pack preparation and initial programming/testing. Quote **5 and 10 complete units separately**, including every component, assembly, fixtures, first-article work, recurring tests, shipping and landed charges.

Engineering, reversible fixes, quote preparation and established vendor correspondence are authorized. **On 15 September Geoff explicitly approved sharing the finished Q2 package and technical follow-up with both vendors.** **The latest work is to upload the completed Q3 revision through both portals and progress automatic quotes as far as possible; the earlier Q2 sharing approval remains historical evidence.** Use email only for matters the portals cannot accomplish; do not duplicate requests across channels. **No spending, paid part preorder or manufacturing release before Geoff approves a concrete order.** No final vendor, order quantity, budget cap, maximum size, minimum runtime or display response threshold has been fixed.

## Current Q3 portal work

| Vendor | Confirmed Q3 state | What remains |
|---|---|---|
| PCBWay | Calculator estimates **$131.62 / 5** ($43.62 PCB + $88 assembly) and **$177.00 / 10** ($43.62 + $133.38). Components and additional services are excluded. The new Q3-specific Agree notice awaits the user's response to the question already asked. | Complete the supported upload/submission steps after that notice is resolved; obtain all components, offboard battery/keycaps, programming/tests and landed costs. No Q3 upload success is established yet. |
| JLCPCB | Q3 Gerbers accepted as **2 layers / finished 42×40 mm**; five-unit Standard/both-sides draft has **70 refs / 43 exact MPNs matched and selected with positive quantities**. Component Placements reached. Five OLEDs total **$8.7715**. Earlier PCB-only **$22.04** plus estimated shipping **$27.63** exclude assembly/components. | Review placements and obtain complete separate 5/10 pricing without paid services or DNP. Full RFQ is attached in Function Test; requested battery/programming/test scope still needs explicit acceptance and pricing. |

Neither vendor has a full Q3 quote. JLCPCB uses 70×70 mm support rails around the finished board, 1 mm thickness, ENIG 1 microinch, tented vias and depaneled delivery; production and placement automatic approval are disabled. The separate `BOM-JLCPCB-Q3-minimal.csv` was accepted after the extended BOM's Notes column was misread as Footprint. Scope notes preserve all vendor soldering, programming, testing and battery work; imports do not establish acceptance of that full service scope. See the [vendor ledger](procurement/vendor-status.md) and [quote tracker](procurement/quote-tracker.json) for later live results.

Ignored Q3 DSN/SES remain local, checksum-bound router-exchange evidence, including the original DSN path. They are excluded from the frozen RFQ and public staging; the package and engineering sources are unchanged by the portal adapter.

## Historical Q2 vendor state

| Vendor | Confirmed state | What remains |
|---|---|---|
| PCBWay | Q2 four-file submission verified **11:51:09 UTC**, five units: **W914112AS1N6 / T-1N7W914112A**, both **Subject to audit**. Specific quote notice approved and accepted. Automatic estimates **$143.93 / 5** and **$184.31 / 10**, excluding components and advanced services. | Obtain complete components, programming/test/harness and landed costs. Ten is calculator-only; submitted case requests separate 5/10 prices. Preferred 0.5 oz inner copper and U5 mask/process acceptance remain open. |
| JLCPCB | Q2 Re-Upload processed **50 refs** and RFQ attachments in both test/assembly fields. Five- and ten-unit draft observations saved; current ten-unit labels **39 confirmed / 10 shortage / 1 not selected**. **DS1 unmatched**; Select parts retained all required parts and Quote & Order cannot advance. PCB estimates **$32.41 / 5** and **$39.81 / 10**, plus **$27.63 DHL DDP** shown each; assembly/component totals absent. | JLCPCB manual matching requires $10 and starts 1–2 working days after payment under its [service terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-parts-selection-service); it was not activated. Resolve LCD/shortages without DNP or payment; review forced 70×70 support panel and **Plugged** versus RFQ tenting. Battery assembly remains excluded and complete test scope/pricing is absent. |

**Q2 emails sent to both vendors, verified in Gmail Sent on 2026-09-15:** PCBWay Remi at **11:12:50 UTC**, in the existing W914112AS1N4 engineering-question thread; JLCPCB Frank at **11:17:46 UTC**, in the existing Budget RFQ email case. Each has the finished RFQ ZIP, Gerber ZIP and its vendor-specific BOM/placement files, with all four filenames and byte sizes checked. PCBWay was asked for exact U5 mask/process acceptance, file association/replacement instructions and complete 5/10 prices including test hours/scope. Both cases retain the full RFQ and engineering gates.

Neither vendor has supplied a complete quote or technical acknowledgment of Q2. JLCPCB accepted Q2 file imports into a saved draft, but the complete Quote & Order workflow is blocked; PCBWay Q2 files are submitted for review under the references above. Historical $84.93 PCBWay and $134.83/$157.82 JLCPCB figures remain incomplete Q1 subtotals. See [vendor ledger](procurement/vendor-status.md) and [quote tracker](procurement/quote-tracker.json).

## Local access and historical Q2 approvals/correspondence

**Native Chrome access is restored**, and vendor replies/pages were freshly inspected; the PCBWay order counters above were verified at **2026-09-15 10:36 UTC**. The initial locked-Mac/no-surface failure and unlock request are historical, resolved access events. Earlier sign-in and agreement acceptances remain completed.

**The specific Q2 sharing approval is now received for both vendors.** The earlier automatic approval review rejected a prepared PCBWay email until that specific approval was obtained; the blocked attempt was not sent. This is historical, resolved approval context. Both Q2 dispatches are now verified in Gmail Sent: PCBWay **11:12:50 UTC**, JLCPCB **11:17:46 UTC**. Vendor technical acknowledgment and complete quotes remain unconfirmed. JLCPCB Q2 draft file imports are now verified; PCBWay Q2 files are now submitted for review; the specific notice was approved and accepted.

At **2026-09-15 11:06:51 UTC**, the latest four vendor emails were reread; none was newer than Remi's **2026-09-15 03:23:59 UTC** email-only request or Frank's **2026-09-14 21:23:46 UTC** rough quote/import reply. That informed the earlier email sends. **The user has since clarified that portal actions come first:** proactively upload Q2 to both sites and advance their automatic quote workflows. Do not await email file-replacement instructions for actions the portal already supports. Use the existing email cases only for remaining matters the portals cannot accomplish; avoid duplicate messages. This replaces the earlier email-only workflow guidance.

**PCBWay quotation notice resolved:** the user explicitly approved Agree; it was accepted before the Q2 cart entry was created at **11:48:56 UTC**. All four files were then uploaded and submitted, with final cart verification at **11:51:09 UTC**. No further Q2 agreement or sharing question remains; the separate current Q3 notice is recorded above.

## Continue from here

1. Use the completed Q3 package and vendor-specific files under `procurement/q3/`; the design/review/render sequence is already complete. Keep Q1/Q2 uploads and archives as historical records, and revalidate Q3 only if inputs change.
2. Continue current PCBWay and JLCPCB portal workflows. PCBWay's Q3-specific Agree question is pending; do not ask again for already granted sharing/upload authority. No Q3 file acceptance is established at this checkpoint. Record accepted filenames, quantities, references and timestamps after actual site confirmation.
3. Obtain complete separate 5/10-unit prices. Use existing email cases only for sourcing, FPC/DFM, battery, programming/test or landed-cost matters the portals cannot resolve. Keep all required parts; no paid matching/preorder or DNP. Record explicit exclusions and a priced completion path.
4. Present a concrete itemized order and first-article conditions for approval before money or manufacture. Retain all physical release gates.

Historical Q2 package readiness remains unchanged: commit `c1240b9`, 124 files / 1,930,577 bytes, archive SHA-256 `29512016b9f83003bf416642617bfb0f8bbc76ea2ca64ba1c31d07e6df0b9438`; its native/package and 21 negative checks passed. Those files and prior vendor records are not the active Q3 upload package.
