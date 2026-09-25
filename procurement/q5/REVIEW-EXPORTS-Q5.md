# Q5 engineering review exports

These files are for engineering review only. Hardware has not been physically
qualified. No upload, quotation, purchase or manufacturing release is authorized.

- `BOM-JLCPCB-Q5.csv` has four unambiguous import columns and exactly 76 SMT
  references, all standard JLC inventory parts; `CPL-JLCPCB-Q5.csv` contains the
  same 76 references. All factory SMT is on the bottom side (single-sided assembly),
  including the BT1 LIR2032 holder and the onboard NTC TH1.
- `BOM-PCBA-Q5.csv` and `placements-KiCad-Q5.csv` describe all 79 fitted parts.
- `HOME-COMPLETION-Q5.csv` lists DS1 and the two key switches (loose LCSC retail
  parts). Fit the rear key plate BEFORE soldering the four switch leads; solder the
  seven-pin display header with the front cover removed (14 joints). 18 joints total.
- `SEPARATE-HARDWARE-Q5.csv` accounts for one PZ254V-11-07P interposer header.
- `OFFBOARD-items-Q5.csv` lists only the user-supplied LIR2032 cell. Keycaps are
  printed enclosure parts (`mechanical/q5`). The 14 test/mounting features are
  neither purchased parts nor DNP parts.
- The native two-layer Gerbers/drills, their exact ZIP and assembly SVGs are review
  outputs. No top stencil paste is present.

CPL X/Y, rotations and sides come from KiCad's native placement export (negative
Y). No manufacturer-specific rotation correction is assumed; the importer's
orientation handling needs authorized assembly review. Stock counts are
timestamped, unreserved public catalog observations in `stock.json`.
See `export-manifest-Q5.json` for exact source/output hashes and checks.
