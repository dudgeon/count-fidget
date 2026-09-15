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

Engineering, reversible fixes, quote preparation and established vendor correspondence are authorized. **No spending, paid part preorder or manufacturing release before Geoff approves a concrete order.** No final vendor, order quantity, budget cap, maximum size, minimum runtime or display response threshold has been fixed.

## Actual vendor state

| Vendor | Confirmed state | What remains |
|---|---|---|
| PCBWay | Q1 four-file website submission, 5 units, PCB **W914112AS1N4** / assembly **T-1N5W914112A**, submitted 01:46:47 UTC. Fresh cart check at **10:48:59 UTC**: PCB **Awaiting reply**, assembly **Being reviewed**; Under Review **2**, Awaiting Payment **0**, Production **0**. Remi's **02:25:22 UTC** website reply says to follow supplied Gerbers/BOM/online parameters and put notes in the files; programming/testing is additional and needs step-by-step instructions. Testing starts at **$75**, then **$10/hour**, charged after the process. | No hours, complete scope or fixed 5/10 total. Obtain acceptance of the precise Q2 mask proposal/file replacement and full itemized prices. Follow up by email only as requested at 03:23 UTC. No combined-opening approval. |
| JLCPCB | Freshly verified saved Q1 draft: **46 refs, 38 confirmed, 7 shortage, 2 unselected**; no formal order. Mitchell's approximately **02:18 UTC** chat says programming/testing is quoted only after order, with **$15.70 engineering** and **$7.86/hour labor** additional. | These are rates, with no hours, accepted full scope or total. Vendor refuses quotes including non-stock parts; battery assembly is excluded. Q2 corrects U3 identity, but LCD/U5 sourcing and other shortages need a priced path. Prepayment test review remains declined. |

Neither vendor has supplied a complete quote. Historical $84.93 PCBWay and $134.83/$157.82 JLCPCB figures are incomplete subtotals. Q2 website submission has **not** occurred. See [vendor ledger](procurement/vendor-status.md) and [quote tracker](procurement/quote-tracker.json).

## Current access and approval constraints

**Native Chrome access is restored**, and vendor replies/pages were freshly inspected; the PCBWay order counters above were verified at **2026-09-15 10:36 UTC**. The initial locked-Mac/no-surface failure and unlock request are historical, resolved access events. Earlier sign-in and agreement acceptances remain completed.

A concrete email to PCBWay about Q2's TI U5 land pattern and replacing files under the existing references was prepared. **Automatic approval review rejected sending revised design details without specific user approval.** The email was not sent; a specific approval request to share the finished Q2 package/technical follow-up with both existing vendor cases is pending. Existing Q1 engineering-hold/correction messages remain the last confirmed outbound state. No money or manufacture.

## Continue from here

1. Q2 files are complete and checked: native ERC/DRC/connectivity/parity all zero, 21 deliberate corruption checks rejected, 50-ref BOM/CPL agree, enclosure solids/manifolds pass with no modeled collisions, and Q1 integrity passes. The [Q2 RFQ archive](dist/q2/click-counter-Q2-RFQ.zip) contains 124 files; its [manifest](dist/q2/manifest-Q2.json) binds every member. Physical qualification remains open.
2. After the pending specific Q2 email approval, use the existing vendor cases and the separately identified Q2 package. Browser access is available. Do not create duplicate orders or accept DNP to manufacture a partial product.
3. Obtain complete, vendor-reviewed 5/10-unit prices or explicit unpriced exclusions and a priced completion plan.
4. Present the concrete order and first-article conditions for approval; retain every physical release gate.
