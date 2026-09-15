# Quote comparison — awaiting vendor review

No complete values available at handoff. Fill this from actual vendor-reviewed evidence, with currency, quote number/date/expiry, quantity and explicit inclusions. A dash below means unquoted, not free. Use one column per vendor and quantity; add separately priced supported-scope alternatives if needed.

| USD cost / scope | JLCPCB 5 | JLCPCB 10 | PCBWay 5 | PCBWay 10 |
|---|---|---|---|---|
| Quote/RFQ number, date, expiry | Saved draft and manual support review only; no formal order/quote reference or expiry | Separate 10-unit pricing requested through the same manual review; no formal reference | PCB W914112AS1N4 / assembly T-1N5W914112A; submitted 2026-09-15 01:46:47 UTC; Subject to audit; expiry unquoted | Alternative requested under the same linked RFQ; no separate 10-unit submission ID |
| PCB fabrication and bare-board test | — | — | — | — |
| All fitted BOM parts, stock and excess/MOQ | — | — | — | — |
| Both-side SMT and THT/manual assembly | — | — | — | — |
| LCD standoff jig / controlled soldering | — | — | — | — |
| Battery/NTC harness materials and preparation | Unsupported per chat | Unsupported per chat | — | — |
| Two loose caps per delivered unit | — | — | — | — |
| Programming setup/fixture/software | — | — | — | — |
| Programming/verification per unit | — | — | — | — |
| First-article engineering | Test review after payment per chat | Test review after payment per chat | — | — |
| Recurring functional tests and records | Pending/excluded | Pending/excluded | — | — |
| Panel/stencil/tooling and other NRE | — | — | — | — |
| Packaging / lithium freight | — | — | — | — |
| Duties / brokerage / sales tax | — | — | — | — |
| Complete delivered total | **Unavailable** | **Unavailable** | **Unavailable** | **Unavailable** |
| Total / delivered functioning units | — | — | — | — |
| Lead time / stock / quote conditions | — | — | — | — |
| Actual stackup and thickness tolerance | — | — | — | — |
| Remaining exclusions / other supplier work | — | — | — | — |

Distinguish one-time charges, recurring charges, purchased spare boards/parts and delivered working-unit quantity. Taxes/freight must refer to the actual destination and lithium handling; do not reuse a default calculator estimate. Do not choose a supplier by incomplete subtotal. No budget ceiling or spending approval exists.

## PCBWay website submission — full quote pending

At **2026-09-15 01:46:47 UTC**, PCBWay accepted and submitted the Q1 Gerber ZIP, corrected 46-reference PCB-only BOM, generic placements and full RFQ ZIP (278,870 bytes). Linked five-unit entries **PCB W914112AS1N4** and **assembly T-1N5W914112A** both show **Subject to audit**. All four files showed 100% Success before Submit File Now, and their links appeared in the cart afterward. Geoff manually accepted Special Notes; no checkout, chargeable procurement or manufacturing release occurred.

The unreviewed five-unit calculator subtotal is **$84.93**: PCB $55.93 + assembly $29.00, with **components $0.00**, displayed shipping $27.27 and discount −$27.27. The zero component line reflects missing pricing, not free parts. Full battery/harness, programming, fixture, first-article/test, lithium freight and tax/duty scope remains unquoted. The shipping discount does not establish landed lithium delivery. **This subtotal is incomplete and is not entered as a complete quote above.**

A linked site message to Remi requesting full itemized separate **5/10-unit** prices was sent and verified **2026-09-15 01:47:22 UTC**. It includes full RFQ scope, explicit exclusions/completion paths, no-charge/no-manufacture restrictions, and preferred **0.5 oz inner** versus standard-form **1 oz inner** stack pricing. The earlier stated audit/quote review time is **1–2 days after file receipt**, not guaranteed. Complete totals, current sourcing, quote validity and delivery terms remain pending.

## JLCPCB current import — full quote blocked by vendor refusal

The final **BOM-JLCPCB-Q1.csv** adapter and unchanged CPL were accepted, with exact MPNs in `Comment` and source wording retained in `Source Label`. All **46 references** were detected. Site labels are **38 confirmed, 7 shortage, 2 unselected**; partially stocked R9 overlaps categories. The original BOM and intermediate original-comment import mismatches have been superseded by this final adapter, not by a change to the PCB design.

| Current unresolved sourcing | Refs | Required exact MPN / catalog code | Live state |
|---|---|---|---|
| Murata 2.2 µF capacitors | C1, C3, C5, C6 | GRM21BR71E225KA73L / C469542 | 24 pieces short |
| Yageo 3.3 Ω resistor | R9 | RC0603FR-073R3L / C137725 | Requires 20; 19 available; 1 short |
| Cherry switches | SW1, SW2 | MX1A-E1NW / C5120587 | 10 pieces short |
| Display Elektronik LCD | DS1 | DE188-RU-30/7,5/V(3V) | Required, unmatched |
| Texas Instruments regulator | U3 | TPS7A0230DBVR | Required exact MPN, unmatched |

Q3's wrong CJ C8545 match was corrected to intended **Nexperia 2N7002,215 / C65189**, after manufacturer packing verification; **J1 GCT USB4105-GF-A / C3020560** was selected. Neither correction authorizes a different electrical part. U3's functional variant distinction remains unresolved; see `JLCPCB-IMPORT-ADAPTER-Q1.md`.

The site offered **Do not place** or **Select parts**. **Select parts** was chosen, preserving all required components. No DNP approval, placement advancement or formal JLCPCB submission/order reference exists. At approximately **2026-09-15 01:56 UTC**, a manual engineering/sales request was visibly sent through live chat to Chian with the private saved-draft link, all shortages and required unmatched parts, full itemized 5/10-unit RFQ scope, explicit exclusions/priced completion path and no-charge/no-manufacture limits. It was transferred to **Mitchell Chen**, who acknowledged receipt around **01:56:30 UTC**. Around **02:02 UTC**, Mitchell said JLCPCB cannot quote the order with non-stock parts included. Required parts remain in scope; a requested case ID has not been returned. Thus the complete Q1 quote is blocked by vendor refusal. The private draft link is not stored in this public document.

Geoff has asked to evaluate an easier-to-source display. JLCPCB was asked for stocked eight-digit, 3 V passive LCD suggestions around 35 × 13 mm for a possible revision. No substitute or redesign is approved; this evaluation does not alter submitted Q1 or remove any remaining shortfall, unmatched U3 or engineering gate.

## Historical JLCPCB partial estimates — incomplete scope

Source: embedded images in Frank's reply received **2026-09-14 at 21:23:46 UTC**, read through native Gmail in the local session. The email text describes a rough five-piece estimate; the second price image explicitly identifies **10 units**, so both image quantities are recorded below. The images display source clocks of September 15 at 05:20 and 05:22. These are retained as displayed, without assigning a timezone or treating them as proof of later quotation activity. No formal current quote number, expiry or complete delivered scope is established by this evidence.

| Historical image line, USD | 5-unit image | 10-unit image |
|---|---:|---:|
| PCB subtotal | 7.00 | 13.00 |
| PCBA setup | 51.12 | 51.12 |
| Stencil | 16.42 | 16.42 |
| Components included in estimate | 25.93 | 42.23 |
| Feeders | 32.13 | 32.13 |
| SMT assembly | 1.74 | 2.43 |
| Packaging | 0.49 | 0.49 |
| Panel charge shown | 0.00 | 0.00 |
| Large-size charge shown | 0.00 | 0.00 |
| **Standard PCBA subtotal** | **127.83** | **144.82** |
| **Historical PCB + PCBA partial estimate** | **134.83** | **157.82** |
| PCB lead time shown | 3 days | 3–4 days |
| Standard assembly lead time shown | 3–4 days | 3–4 days |
| Optional rush assembly shown | 2–3 days; +49.26 | 2–3 days; +49.26 |

The five-unit component line is labeled **21 items**. The setup, stencil, components, feeders, SMT and packaging lines sum to each displayed Standard PCBA subtotal; adding PCB produces the displayed partial totals. Rush charges are optional and are not included in those totals. The zero panel/large-size lines are only the values explicitly shown in the historical images; they do not establish that other unquoted work is free. Lead times are historical estimates, not current commitments.

**Excluded or unresolved scope:** these estimates exclude missing, shortfall and unmatched parts. They do not establish prices or inclusion for the battery/NTC harness, loose caps, complete THT/manual work, LCD jig, programming/fixtures, first-article engineering, recurring functional tests, lithium delivery, duty/brokerage or tax. The small packaging line does not establish lithium shipping. Both complete delivered totals remain **unavailable**, and no order or procurement is approved.

### Historical matching and stock exceptions

- The stock image shows SW2 matched to **E-Switch TL1220S1BBSG-RESET, C5798268**, with a shortfall of **5**. The exact MPN is confirmed by the [official JLCPCB part listing](https://jlcpcb.com/partdetail/ESwitch-TL1220S1BBSGRESET/C5798268). This conflicts with Q1's required **Cherry MX1A-E1NW** for both SW1 and SW2, listed by [LCSC as C5120587](https://lcsc.com/products/Pushbutton-Switches_425.html?brand=12820). It is an importer matching error, not an approved design change or substitute. Correct live matching and stock review remain open.
- The historical U1 match **C2053877 / Texas Instruments MSP430FR4133IG48R** identifies the required 48-pin MCU. A correct part identity does not establish current availability or resolve other missing lines.
- The unmatched references shown are **D1, DS1, J1, J2, Q1, Q2, Q3, SW1, U2, U3, U4 and U5**. Their omission prevents treating the component/assembly subtotal as complete.
- This evidence is historical. Current stock, exact MPN matches, quantities, MOQs, lead times and prices still require live sourcing review with the corrected 46-reference `BOM-PCBA-Q1.csv`. Offboard BAT1/K1/K2 remain separately required commercial scope.

The historical email review does not prove a new website upload or formal submission. Keep these partial estimates separate from the full-scope comparison above until vendor-reviewed completion evidence is available.
