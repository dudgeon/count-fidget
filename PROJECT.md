# Count Fidget — project status

## Current work — Q2 engineering candidate, 15 September 2026

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

Engineering, reversible fixes, quote preparation and established vendor correspondence are authorized. **On 15 September Geoff explicitly approved sharing the finished Q2 package and technical follow-up with both vendors.** **The latest user correction is to upload revised Q2 files through both portals and progress automatic quotes as far as possible.** Use email only for matters the portals cannot accomplish; do not duplicate requests across channels. **No spending, paid part preorder or manufacturing release before Geoff approves a concrete order.** No final vendor, order quantity, budget cap, maximum size, minimum runtime or display response threshold has been fixed.

## Actual vendor state

| Vendor | Confirmed state | What remains |
|---|---|---|
| PCBWay | Q2 four-file submission verified **11:51:09 UTC**, five units: **W914112AS1N6 / T-1N7W914112A**, both **Subject to audit**. Specific quote notice approved and accepted. Automatic estimates **$143.93 / 5** and **$184.31 / 10**, excluding components and advanced services. | Obtain complete components, programming/test/harness and landed costs. Ten is calculator-only; submitted case requests separate 5/10 prices. Preferred 0.5 oz inner copper and U5 mask/process acceptance remain open. |
| JLCPCB | Q2 Re-Upload processed **50 refs** and RFQ attachments in both test/assembly fields. Five- and ten-unit draft observations saved; current ten-unit labels **39 confirmed / 10 shortage / 1 not selected**. **DS1 unmatched**; Select parts retained all required parts and Quote & Order cannot advance. PCB estimates **$32.41 / 5** and **$39.81 / 10**, plus **$27.63 DHL DDP** shown each; assembly/component totals absent. | JLCPCB manual matching requires $10 and starts 1–2 working days after payment under its [service terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-parts-selection-service); it was not activated. Resolve LCD/shortages without DNP or payment; review forced 70×70 support panel and **Plugged** versus RFQ tenting. Battery assembly remains excluded and complete test scope/pricing is absent. |

**Q2 emails sent to both vendors, verified in Gmail Sent on 2026-09-15:** PCBWay Remi at **11:12:50 UTC**, in the existing W914112AS1N4 engineering-question thread; JLCPCB Frank at **11:17:46 UTC**, in the existing Budget RFQ email case. Each has the finished RFQ ZIP, Gerber ZIP and its vendor-specific BOM/placement files, with all four filenames and byte sizes checked. PCBWay was asked for exact U5 mask/process acceptance, file association/replacement instructions and complete 5/10 prices including test hours/scope. Both cases retain the full RFQ and engineering gates.

Neither vendor has supplied a complete quote or technical acknowledgment of Q2. JLCPCB accepted Q2 file imports into a saved draft, but the complete Quote & Order workflow is blocked; PCBWay Q2 files are submitted for review under the references above. Historical $84.93 PCBWay and $134.83/$157.82 JLCPCB figures remain incomplete Q1 subtotals. See [vendor ledger](procurement/vendor-status.md) and [quote tracker](procurement/quote-tracker.json).

## Current access, sharing approval and correspondence

**Native Chrome access is restored**, and vendor replies/pages were freshly inspected; the PCBWay order counters above were verified at **2026-09-15 10:36 UTC**. The initial locked-Mac/no-surface failure and unlock request are historical, resolved access events. Earlier sign-in and agreement acceptances remain completed.

**The specific Q2 sharing approval is now received for both vendors.** The earlier automatic approval review rejected a prepared PCBWay email until that specific approval was obtained; the blocked attempt was not sent. This is historical, resolved approval context. Both Q2 dispatches are now verified in Gmail Sent: PCBWay **11:12:50 UTC**, JLCPCB **11:17:46 UTC**. Vendor technical acknowledgment and complete quotes remain unconfirmed. JLCPCB Q2 draft file imports are now verified; PCBWay Q2 files are now submitted for review; the specific notice was approved and accepted.

At **2026-09-15 11:06:51 UTC**, the latest four vendor emails were reread; none was newer than Remi's **2026-09-15 03:23:59 UTC** email-only request or Frank's **2026-09-14 21:23:46 UTC** rough quote/import reply. That informed the earlier email sends. **The user has since clarified that portal actions come first:** proactively upload Q2 to both sites and advance their automatic quote workflows. Do not await email file-replacement instructions for actions the portal already supports. Use the existing email cases only for remaining matters the portals cannot accomplish; avoid duplicate messages. This replaces the earlier email-only workflow guidance.

**PCBWay quotation notice resolved:** the user explicitly approved Agree; it was accepted before the Q2 cart entry was created at **11:48:56 UTC**. All four files were then uploaded and submitted, with final cart verification at **11:51:09 UTC**. No further agreement or sharing question remains.

## Continue from here

1. Q2 files are complete and checked: native ERC/DRC/connectivity/parity all zero, 21 deliberate corruption checks rejected, 50-ref BOM/CPL agree, enclosure solids/manifolds pass with no modeled collisions, and Q1 integrity passes. The [Q2 RFQ archive](dist/q2/click-counter-Q2-RFQ.zip), ready at commit `c1240b9`, contains **124 files / 1,930,577 bytes**; its [manifest](dist/q2/manifest-Q2.json) binds every member and archive SHA-256 `29512016b9f83003bf416642617bfb0f8bbc76ea2ca64ba1c31d07e6df0b9438`. Physical qualification remains open.
2. Continue from the verified PCBWay Q2 submission and JLCPCB saved draft. Both quantity estimates were captured. Use the existing email cases for unresolved components, DFM, battery and test scope. Do not pay to unlock matching or quotes, omit required parts, or repeat completed uploads.
3. Obtain complete 5/10-unit prices through available portal workflows. For sourcing, DFM, battery, programming/test or landed-cost items the portal cannot resolve, use the existing email cases as the fallback and record explicit exclusions plus a priced completion plan. Do not repeat the same request across channels.
4. Present the concrete order and first-article conditions for approval; retain every physical release gate.
