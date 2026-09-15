# Project status and next work

Migrated from the September 14, 2026 cloud conversation. Some carried artifact clocks differ; preserve their timestamps without treating them as proof of later activity. Geoff's latest instruction is to put the full project in GitHub and resume locally after repeated cloud browser failures. That cause is a hypothesis; local browser access still needs verification.

## Goal

A lightweight two-key counter fidget with a display, rechargeable coin cell, USB-C and retained count. Geoff prints/fits the enclosure and attaches keycaps/battery connector. Vendors do all electrical soldering and initial programming/testing. Obtain complete quotes from JLCPCB and PCBWay before selecting and approving an order.

## Local continuation — verified by 2026-09-15 00:59:30 UTC

The existing local checkout matches `origin/main`. Package integrity and all portable host tests passed once. Local Chrome native control works, with intermittent stale accessibility state; the dedicated browser connection fails initialization. Both vendor accounts are locally accessible after Geoff completed PCBWay sign-in. This is no longer a cloud-only session.

- **PCBWay:** Empty local cart inspected; Q1 5-unit form completed with a separate 10-unit request, full scope and prototype restrictions. Calculate succeeded. Save to Cart opened a required **Special Notes / Agree** notice. User confirmation is pending; no PCBWay files uploaded and no submission number yet.
- **JLCPCB:** Existing orders/quotes inspected; no prior files found. Gerber-only ZIP accepted and detected as four layers, 42 × 40 mm. Full RFQ ZIP accepted in assembly-remark and functional-test attachment fields. Standard both-side assembly selected; the site adds a 70 × 70 mm handling panel, with depaneling requested. Production-file and placement auto-confirmation disabled. The assembly-service terms are unchecked pending user confirmation before Next. **PCB-only BOM/CPL import and final submission remain unfinished.**
- **Historical email images now read:** JLCPCB rough supported-scope totals are $134.83 for 5 and $157.82 for 10, both incomplete. SW2 was incorrectly matched to an E-Switch reset part; current stock/MOQ and exact matching still require review. See the comparison and vendor ledger.
- Engineering gaps remain open. A metadata discrepancy was documented under E13; no design, HEX or manufacturing package was altered. No money spent or manufacturing released.

| Deliverable | Actual state |
|---|---|
| Specification and history | Consolidated in `docs/`, separating direct user requirements from assumptions |
| Native PCB | KiCad 10, 42 × 40 × 1.0 mm, 4 layers, routed/filled, 46 fitted PCB components |
| Manufacturing files | Gerbers/drills, BOMs, placements, assembly drawings; corrected importer BOM |
| Connectivity | Explicit netlist, generator and pin schedule; no native schematic/ERC |
| PCB validation | Retained routed DRC reports 0 violations/0 unconnected; not hardware validation |
| Firmware | MSP430FR4133 C, application/factory HEX, ELF/map and checksums; compiled and host tested |
| Enclosure | Rev0 CadQuery source/STEP/STLs/renders; Q1 integration still needed |
| Vendor communications | Full original Q1 RFQ emailed to both; JLCPCB acknowledged and reviewed it |
| Website uploads | **JLCPCB Gerbers and RFQ supplements accepted; BOM/CPL and final submission pending. PCBWay remains before upload. No formal submission IDs.** |
| Complete quotes and spend | **No complete quote, chargeable procurement, order or manufacturing release** |

## Immediate next sequence

1. Resume the existing local vendor tabs after the pending site-agreement confirmations; inspect current state rather than assuming tab handles persist.
2. Complete PCBWay's website RFQ using Q1 Gerbers, PCB-only BOM, placements and full RFQ. Request complete 5/10-unit quotes and record a real submission number. Do not create a duplicate if the draft was submitted manually.
3. Complete JLCPCB PCB-only BOM/CPL import and exact manual matching, including both Cherry switches. Preserve attached scope, depaneling and no-auto-confirm settings; resolve current stock/MOQs and battery/test exclusions without paying to unlock quoting.
4. Continue to check the existing cloud follow-up before duplicate outreach; its current schedule status remains unverified. Mail and embedded images were checked locally; no newer reply was found.
5. Obtain vendor-reviewed itemized totals using `procurement/quote-comparison.md`. Unsupported work requires an explicit completion plan and price, not a zero line.
6. Close engineering issues, obtain a controlled first article, update enclosure CAD, and present a concrete order for Geoff's approval before purchase.

Engineering/quotation work may overlap, but a quote or geometric DRC does not clear hardware gates. No final vendor, quantity, budget ceiling, maximum size, minimum runtime or display response threshold has been set. Continue with the documented baseline unless a concrete tradeoff requires Geoff's choice.
