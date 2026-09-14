# Project status and next work

Migrated from the September 14, 2026 cloud conversation. Some carried artifact clocks differ; preserve their timestamps without treating them as proof of later activity. Geoff's latest instruction is to put the full project in GitHub and resume locally after repeated cloud browser failures. That cause is a hypothesis; local browser access still needs verification.

## Goal

A lightweight two-key counter fidget with a display, rechargeable coin cell, USB-C and retained count. Geoff prints/fits the enclosure and attaches keycaps/battery connector. Vendors do all electrical soldering and initial programming/testing. Obtain complete quotes from JLCPCB and PCBWay before selecting and approving an order.

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
| Website uploads | **Neither vendor has a confirmed Q1 file upload/submission ID** |
| Complete quotes and spend | **No complete quote, chargeable procurement, order or manufacturing release** |

## Immediate next sequence

1. Read `HANDOFF.md`, verify local browser access and inspect existing vendor account state.
2. Check established email threads for replies, including JLCPCB's unread embedded price/stock images. Check the scheduled cloud follow-up task to avoid duplicate outreach.
3. Complete PCBWay's website RFQ using Q1 Gerbers, PCB-only BOM, placements and full RFQ. Request complete 5/10-unit quotes and record a real submission number. Leave unrelated cart items alone.
4. Complete JLCPCB website import/manual matching. Resolve exact stock/MOQ lines. Preserve battery/test exclusions; do not pay just to unlock quoting.
5. Obtain vendor-reviewed itemized totals using `procurement/quote-comparison.md`. Unsupported work requires an explicit completion plan and price, not a zero line.
6. Close engineering issues, obtain a controlled first article, update enclosure CAD, and present a concrete order for Geoff's approval before purchase.

Engineering/quotation work may overlap, but a quote or geometric DRC does not clear hardware gates. No final vendor, quantity, budget ceiling, maximum size, minimum runtime or display response threshold has been set. Continue with the documented baseline unless a concrete tradeoff requires Geoff's choice.
