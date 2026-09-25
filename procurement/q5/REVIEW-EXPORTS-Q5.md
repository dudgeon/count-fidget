# Q5 fabrication and assembly exports

Engineering outputs for JLCPCB quotation. The hardware has not been physically
qualified. A quote is not an order: no purchase or manufacturing release is authorized.

Board: 42 x 54 mm, 2 layers, 1.6 mm FR-4, 1 oz, ENIG, green mask / white silk.
All factory SMT is on the BOTTOM side (single-sided assembly).

Two quotation variants:

| Variant | BOM | CPL | Who solders what |
|---|---|---|---|
| A | `BOM-JLCPCB-Q5.csv` (80 rows) | `CPL-JLCPCB-Q5.csv` | JLC: all 80 SMT parts. User: DS1 display on its 7-pin header (14 joints) |
| B | `BOM-JLCPCB-Q5-FULL-ASSEMBLY.csv` (82 rows) | `CPL-JLCPCB-Q5-FULL-ASSEMBLY.csv` | JLC: all SMT plus through-hole DS1 (C5139758) stacked on header DS1H (C492406), module PCB 2.5 mm above the host, pins trimmed <= 1 mm |

Both variants: the two clicky switches (K1/K2, C49234235) clip into the printed key
plate and press into the vendor-placed hot-swap sockets SW1/SW2 (no soldering); four
M2 x 6 self-tapping screws (C357360) close the printed enclosure; the user inserts a
rechargeable LIR2032 (never a primary CR2032). See `LOOSE-PARTS-Q5.csv`,
`HOME-COMPLETION-Q5.csv`, `SEPARATE-HARDWARE-Q5.csv` and `OFFBOARD-items-Q5.csv`.

Placement review items for the JLC DFM preview (bottom side, KiCad rotations, no
manufacturer correction applied): polarity/pin 1 of U1-U8, Q1-Q5, D1-D4, J1, the
BT1 holder (+ contact on pad 1 / CELL_P, marked + on the silkscreen) and the two
hot-swap sockets (pads beside the 3.0 mm switch-pin holes).

`BOM-PCBA-Q5.csv` / `placements-KiCad-Q5.csv` describe all 81 fitted parts. Stock
counts are timestamped, unreserved public catalogue observations in `stock.json`.
See `export-manifest-Q5.json` for exact source/output hashes and checks.
