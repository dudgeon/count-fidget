# JLCPCB Q1 import adapter

Prepared 2026-09-15 01:50:59 UTC. Quotation only; no design or manufacturing release.

## Observed import failure

During the local JLCPCB BOM import, the matching screen used descriptive Comment values such as COUNT and RESET and generic capacitor descriptions instead of the supplied Manufacturer Part Number column. This produced incorrect component matches. The earlier vendor screenshot also matched SW2 to E-Switch TL1220S1BBSG-RESET (C5798268), whereas the specified switch is Cherry MX1A-E1NW. Do not accept these automatic substitutions.

A first adapter import recognized the explicit catalog codes but still displayed the old descriptive values, including an incorrect LED match for R7 from the description 330. The importer appears to choose the last header containing Comment. The preserved-description header is therefore Source Label, with no Comment, Description or Value substring. This is an observed parser diagnosis, not a claim of successful matching.

The subsequent Source Label reimport displayed the exact MPN Comment values. This confirms the field-interpretation fix, while exact component matching and stock review remain unfinished. In particular, Q3 was still automatically mapped to a different manufacturer's part; U3 and DS1 remained unmatched. No complete quote resulted from this import.

## Adapter transformation

Use `BOM-JLCPCB-Q1.csv` with the unchanged `CPL-JLCPCB-Q1.csv` for this importer. It preserves every source row, row order and column. The only modified source field is Comment, set to the exact Manufacturer Part Number. The prior descriptive Comment is preserved in the appended Source Label column. The appended LCSC Part # column contains the verified exact catalog codes below for 11 references; all other code cells are blank.

`BOM-PCBA-Q1.csv` remains the controlling PCB BOM. The source BOM, full commercial BOM, CPL, Gerbers, firmware, electrical design and RFQ ZIP are unchanged. This adapter is a separately uploaded supplement and is not yet included in the RFQ archive.

## Verified catalog identities

| References | Exact MPN | Code | Official identity source |
|---|---|---|---|
| SW1, SW2 | MX1A-E1NW | C5120587 | [LCSC catalog](https://lcsc.com/products/Pushbutton-Switches_425.html?brand=12820) |
| J1 | USB4105-GF-A | C3020560 | [JLCPCB](https://jlcpcb.com/partdetail/3542626-USB4105_GFA/C3020560) |
| J2 | SM04B-SRSS-TB(LF)(SN) | C160404 | [LCSC](https://www.lcsc.com/product-detail/C160404.html) |
| U1 | MSP430FR4133IG48R | C2053877 | [LCSC](https://www.lcsc.com/product-image/C2053877.html) |
| U2 | BQ25185DLHR | C19725033 | [LCSC](https://www.lcsc.com/product-detail/C19725033.html?s_z=n_MS2548) |
| U4 | BQ29700DSER | C183096 | [JLCPCB](https://jlcpcb.com/partdetail/BQ29700DSER/C183096) |
| U5 | TLV7042DGKR | C2760466 | [LCSC](https://www.lcsc.com/product-image/C2760466.html) |
| Q1, Q2 | DMN2056U-7 | C332302 | [JLCPCB](https://jlcpcb.com/partdetail/DMN2056U-7/C332302) |
| D1 | USBLC6-2SC6 | C7519 | [LCSC](https://www.lcsc.com/product-image/C7519.html) |

No exact code was established for DS1. U3 and Q3 code cells remain blank in this adapter. No alternatives have been approved.

## Technical ordering notes

**U3: unresolved functional variant.** TI's TPS7A02 Rev. C datasheet, sections 7.3.2 and 9.1.1, identifies P as the active-output-discharge feature. The P version pulls the output toward ground when disabled through EN or undervoltage lockout. The current ordering addendum, dated August 21, 2026, lists TPS7A0230PDBVR; the exact BOM code TPS7A0230DBVR was not found. The extra P is a functional distinction, not a packing suffix. Preserve the exact BOM discrepancy as an engineering/sourcing gap and review the discharge behavior before selecting a variant. [TI datasheet and ordering addendum](https://www.ti.com/lit/gpn/TPS7A02)

**Q3: verified type, packing suffix clarified.** Nexperia maps orderable part 2N7002,215 (12NC 934003470215) to type 2N7002 in SOT23. Its FAQ states that the numeric suffix specifies packing and does not change function or material composition. SOT23_215 is a 7-inch reel with 8 mm tape and standard packing quantity 3,000; the reel quantity does not establish a purchasing MOQ. Catalog C65189 is therefore a documented orderable packing of the intended Nexperia type and may be considered for quotation once the vendor confirms that packing. This note makes no selection or procurement commitment; the CSV and controlling BOM remain unchanged. [Nexperia identity table](https://www.nexperia.com/chemical-content/2N7002.html), [suffix FAQ](https://www.nexperia.com/support/customer-support/faq), [packing sheet](https://assets.nexperia.com/documents/packing-information/SOT23_215.pdf), [LCSC C65189](https://www.lcsc.com/product-detail/MOSFET_Nexperia_2N7002-215_Nexperia-2N7002-215_C65189.html)

Catalog identity does not establish current stock, MOQ, price, placement suitability or assembly support. Inspect each imported row and the rendered placements. BAT1/K1/K2 remain in the separate offboard commercial scope and have no fabricated CPL positions. All existing engineering qualification gaps remain open.

## Integrity

- Source BOM SHA-256: `5698723d578d83831dbed50f4657e02a423e7774705b8e703fb4eb955fb73349`
- Adapter SHA-256: `f9ee94d67b7c9b908563e4461acd866a7702c9557c117fae1b217782b816e8e7`
- Adapter size: 5823 bytes.
- Verified 46 distinct PCB references, unchanged row order, exact CPL-reference equality and equality of every other original field.
- Verified all 46 Comment fields equal their exact MPN and all original Comment values are retained.
- Verified 11 populated catalog-code cells and 35 blank code cells.
- `python3 scripts/verify_project.py` passed after creation, including unchanged firmware hashes, source BOM/CPL/offboard relationships, Gerber archive and RFQ archive/manifest. No rebuild or fresh PCB DRC was performed.
