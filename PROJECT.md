# Project status and next work

## Current priority — engineering review, 15 September 2026

Q1 is on engineering hold. Independent review confirms missing LCD bias reservoir capacitors and inadequate frame-rate margin. The alleged firmware source/binary mismatch is **refuted**: TI's LCD4MUX macro includes LCDSON, and the unmodified source reproduces the archived application bytes with the original compiler/support version. The suspected BQ25185 pin/resistor error is also refuted. See `docs/adversarial-review-Q2.md` and linked technical audits.

Both vendors were notified of the engineering hold and the correction to the initial firmware claim. Their existing Q1 references remain useful for sourcing/budgetary work; final quotes require a reviewed revision. Display alternatives are being evaluated, with no replacement selected. Keep the submitted Q1 package intact. No money, paid procurement or manufacturing release is authorized.

The separate **Q2 LCD verification candidate** now runs at 32 Hz nominal and makes LCDSON explicit for clarity. It changes one loaded byte from Q1, has source/toolchain/output provenance, and passes reproducibility, package and host checks. No board revision or hardware validation has occurred. JLCPCB says no alternative to the requested LCD is stocked and suggests paid Global Sourcing preorder for DE188; that path is not authorized. It also identified stocked U3 candidate TPS7A0230PDBVR / C3747031, whose active output discharge still needs engineering review.

Migrated from the September 14, 2026 cloud conversation. Some carried artifact clocks differ; preserve their timestamps without treating them as proof of later activity. The cloud failure cause remains a hypothesis; local native Chrome access has now been verified and both agreements advanced.

## Goal

A lightweight two-key counter fidget with a display, rechargeable coin cell, USB-C and retained count. Geoff prints/fits the enclosure and attaches keycaps/battery connector. Vendors do all electrical soldering and initial programming/testing. Obtain complete quotes from JLCPCB and PCBWay before selecting and approving an order.

## Local continuation — PCBWay updated 2026-09-15 01:47:22 UTC

The vendor-submission checkpoint `a8128ec` is on `main`; current engineering work is on `codex/q2-engineering-audit`. Package integrity and all portable host tests passed. Local Chrome native control works, with intermittent stale accessibility state; the dedicated browser connection fails initialization. Both vendor accounts are locally accessible after Geoff completed PCBWay sign-in. This is no longer a cloud-only session.

- **PCBWay:** Website submission succeeded **2026-09-15 01:46:47 UTC** after Geoff manually accepted Special Notes. Linked five-unit entries **PCB W914112AS1N4** and **assembly T-1N5W914112A** are both **Subject to audit**. All four Gerber/BOM/placement/full-RFQ files showed 100% Success, were submitted, and appear as cart links. A linked site message to Remi requesting complete itemized 5/10 pricing was sent and verified **01:47:22 UTC**. Vendor review and complete quotes remain pending; the $84.93 calculator subtotal has $0 components and is incomplete. A refresh around **02:00 UTC** still showed both entries Subject to audit, zero unread messages and zero awaiting payment. No checkout, paid procurement or manufacturing release.
- **JLCPCB:** Final `BOM-JLCPCB-Q1.csv` adapter and unchanged CPL accepted with **46 detected references**, after correcting the importer's handling of MPNs. Exact Q3 Nexperia and J1 GCT matches selected. The site shows **38 confirmed, 7 shortage, 2 unselected**; R9 is partially stocked, so the counts overlap. Shortages are Murata capacitors (24 pieces), R9 (1 of 20) and Cherry switches (10); required DS1 LCD and exact U3 regulator remain unmatched. **Select parts** preserved their inclusion; no DNP approval, placement advancement or formal JLCPCB reference. At approximately **02:02 UTC**, Mitchell Chen stated JLCPCB cannot quote the order with non-stock parts included. Required parts remain included; no DNP approval. A support case ID was requested but not returned. The full Q1 quote is blocked by that vendor refusal, not an outstanding agreement or import problem.
- **Historical email images now read:** JLCPCB rough supported-scope totals are $134.83 for 5 and $157.82 for 10, both incomplete. SW2 was incorrectly matched to an E-Switch reset part; current stock/MOQ and exact matching still require review. See the comparison and vendor ledger.
- Engineering gaps remain open. A metadata discrepancy was documented under E13; no design, HEX or manufacturing package was altered. No money spent or manufacturing released.

| Deliverable | Actual state |
|---|---|
| Specification and history | Consolidated in `docs/`, separating direct user requirements from assumptions |
| Native PCB | KiCad 10, 42 × 40 × 1.0 mm, 4 layers, routed/filled, 46 fitted PCB components |
| Manufacturing files | Gerbers/drills, BOMs, placements, assembly drawings; corrected importer BOM |
| Connectivity | Explicit netlist, generator and pin schedule; no native schematic/ERC |
| PCB validation | Retained routed DRC reports 0 violations/0 unconnected; not hardware validation |
| Firmware | Frozen Q1 application/factory HEX and ELF/map; separate reproducible 32 Hz Q2 LCD verification candidate, compiled and host tested; no target flashed |
| Enclosure | Rev0 CadQuery source/STEP/STLs/renders; Q1 integration still needed |
| Vendor communications | Full original Q1 RFQ emailed to both; JLCPCB acknowledged and reviewed it |
| Website uploads | **PCBWay four-file submission complete: W914112AS1N4 / T-1N5W914112A, five units, Subject to audit. JLCPCB Gerbers/RFQ supplements/final adapter/CPL accepted; manual sourcing resolution, placement and final submission pending.** |
| Complete quotes and spend | **No complete quote, chargeable procurement, order or manufacturing release** |

## Immediate next sequence

First follow the controlled engineering sequence in `docs/adversarial-review-Q2.md`. The vendor steps below continue sourcing/budgetary work; final prices require the reviewed revision. No replacement display is selected, and eight digits/current dimensions are not hard user constraints.

1. Resume the existing local vendor tabs; Geoff manually advanced both site-agreement gates. Inspect current state rather than assuming tab handles persist.
2. Follow PCBWay's existing linked submission W914112AS1N4 / T-1N5W914112A and Remi's confirmed site-message thread for review and complete separate 5/10-unit quotes; do not duplicate the submission. The earlier stated review time was 1–2 days after file receipt, not guaranteed. Geoff authorizes clearing verified previous-project cart entries while preserving Count Fidget; the pre-submission recheck was empty and no deletion occurred.
3. Preserve the JLCPCB draft/full Q1 scope and record its refusal to quote non-stock parts; pursue the requested support case ID and stocked-display suggestions. Geoff has asked whether a more readily sourced display would be preferable, so evaluate stocked low-power alternatives and redesign consequences. JLCPCB was asked for stocked eight-digit, 3 V passive LCDs around 35 × 13 mm for a possible revision. This is evaluation only: no replacement display is selected, and submitted Q1 remains unchanged. Do not repeat imports, accept DNP or pay to unlock pricing.
4. Continue to check the existing cloud follow-up before duplicate outreach; its current schedule status remains unverified. Mail and embedded images were checked locally; no newer reply was found.
5. Obtain vendor-reviewed itemized totals using `procurement/quote-comparison.md`. Unsupported work requires an explicit completion plan and price, not a zero line.
6. Close engineering issues, obtain a controlled first article, update enclosure CAD, and present a concrete order for Geoff's approval before purchase.

Engineering/quotation work may overlap, but a quote or geometric DRC does not clear hardware gates. No final vendor, quantity, budget ceiling, maximum size, minimum runtime or display response threshold has been set. Continue with the documented baseline unless a concrete tradeoff requires Geoff's choice.
