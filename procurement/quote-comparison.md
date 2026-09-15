# Quote comparison — awaiting vendor review

No complete values available at handoff. Fill this from actual vendor-reviewed evidence, with currency, quote number/date/expiry, quantity and explicit inclusions. A dash below means unquoted, not free. Use one column per vendor and quantity; add separately priced supported-scope alternatives if needed.

| USD cost / scope | JLCPCB 5 | JLCPCB 10 | PCBWay 5 | PCBWay 10 |
|---|---|---|---|---|
| Quote/RFQ number, date, expiry | — | — | — | — |
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
