# Q4 engineering review exports

These files are for engineering review only. Hardware has not been physically
qualified. No upload, quotation, purchase or manufacturing release is authorized.

- `BOM-JLCPCB-Q4.csv` has four unambiguous import columns and exactly 67 SMT
  references. `CPL-JLCPCB-Q4.csv` contains those same 67 references, on the bottom.
- `BOM-PCBA-Q4.csv` and `placements-KiCad-Q4.csv` describe all 70 fitted board
  parts. The native placements include DS1/SW1/SW2 for engineering review.
- `HOME-COMPLETION-Q4.csv` lists DS1 and the two key switches, separately sourced
  as loose retail parts. Retail screening quantities are shown once per exact
  MPN group, so SW1/SW2 share one rounded switch order. These are not purchases.
  Fit the rear key plate BEFORE soldering switch leads.
  Complete the seven-pin display header with the front cover removed: 14 joints
  across module and host, plus four key-switch joints. Physical fit remains open.
- `SEPARATE-HARDWARE-Q4.csv` accounts for one PZ254V-11-07P interposer header.
  It shares DS1's holes and has no additional CPL row. Header inclusion with the
  module is unknown; count it once, and avoid a duplicate if supplied together.
- `OFFBOARD-items-Q4.csv` retains one prepared rechargeable pack including NTC
  harness and two keycaps as explicitly unqualified sourcing/fit requirements.
  `BOM-Q4.csv` combines the 70 board rows, one header row and two offboard rows.
  The board's 16 test/mounting features are neither purchased parts nor DNP parts.
- The native two-layer Gerbers/drills, their exact ZIP, and top/bottom assembly
  SVGs are review outputs. No top stencil paste is present; SMT is on the bottom.

CPL X/Y, rotations and sides come from KiCad's native placement export. KiCad
uses a negative Y coordinate here. These values are checked against the source
model; actual importer coordinate/orientation handling needs later authorized
assembly review. No manufacturer-specific rotation correction is assumed.

Stock counts are timestamped, unreserved catalog observations in `stock.json`;
loose home-part supply is separately checked through LCSC retail. Quantities for
ten boards include research spares rounded to retail packs, not confirmed
assembler attrition or a purchase. Neither inventory nor file agreement proves
battery safety, power/USB operation, display function, solder process or fit.
See `export-manifest-Q4.json` for exact source/output hashes and checks.
