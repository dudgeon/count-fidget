# Count Fidget — project status

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
