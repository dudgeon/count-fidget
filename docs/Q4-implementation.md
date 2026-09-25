# Q4 implementation — 24 September 2026

## Design decision

**Select STM32L072CBT6.** The user prioritizes product quality and simple design/integration/bootloading over small component-price differences. The selected device combines low-power operation, factory ROM USB DFU for first flashing and recovery, and sufficient pins and memory. A separate SPI FRAM provides durable count storage without flash wear or application-update erase. Fresh exact-part stock evidence is recorded with the complete Q4 BOM. ESP32 adds unnecessary radio/power constraints; the retained MSP430 needs an external programmer; ATtiny saves little while complicating durable storage and programming.

The [options study](mcu-options-2026-09-23.md) records the alternatives and primary references. This decision authorizes Q4 engineering, not purchases or manufacturing. Q1/Q2/Q3 remain frozen.

## Product and implementation priorities

- USB-C charging and first-time home programming through a data cable, with physical recovery access and retained SWD pads.
- Reliable single-count behavior, held-key suppression, reset priority and durable count recovery. The implemented FRAM journal is tested for interrupted operations; EEPROM is an alternate test backend, not the fitted product storage.
- A two-layer board with exact, verified JLC-orderable PCB parts. The complete SPI display module removes the bare FPC assembly operation and separate panel supply circuit.
- Reduce avoidable power domains and component types where guaranteed voltage/current/interface limits permit it. Reliability takes precedence over cents or reducing a schematic's part count artificially.
- Keep charging/protection independent of firmware and preserve explicit physical qualification gates.

## Completed engineering checkpoint

| Area | Current state | Completion evidence required |
|---|---|---|
| MCU choice | Selected STM32L072CBT6 | Rationale and exact stock record |
| Display, supply and startup circuit | Implemented; conditional power calculations and ideal ngspice subcircuits executed | Physical transients, current and battery recovery remain unmeasured |
| Native schematic and PCB | Final two-layer routing and native source binding passed | Zero ERC/DRC/connectivity/parity findings; 42 verifier mutations rejected; physical process remains open |
| STM32 target firmware | Built reproducibly; adversarial host and image-corruption tests passed | Physical USB/MCU execution and interruption tests |
| Complete JLC PCB inventory | Exact stocked identities and final model binding checked | Quantity and attrition screening; no allocation or order |
| Enclosure and rendering | Four print parts and actual CAD renderings complete; zero modeled collisions | 162 sampled assembly poses, manifold bed-aligned meshes; physical fit remains open |
| Physical qualification | No built hardware | First-article USB, power, charging/protection, count, display and fit tests |

## Authority and records

No vendor quote uploads, draft changes, messages, paid sourcing, purchases or manufacturing release are authorized. The user will explicitly reopen quotation activity. Public catalog research is allowed. Work is committed to the existing `codex/q2-engineering-audit` branch and draft PR #1; this document is updated as implementation and reviews complete.

A complete validated whole-board simulation does not exist. The September23 ngspice deck covers idealized subcircuits only. New models must declare their component coverage, assumptions, corner limits and missing real-device behavior. Tests cannot fabricate absent physical evidence.

## Implemented findings and decisions

- The complete **HS96L01W4S03 SPI OLED module** is selected with a separate **PZ254V-11-07P** seven-pin header. Fresh JLC inventory is recorded in `procurement/q4/stock.json`. Its mechanical drawing identifies **SSD1315**, a **27.30 × 27.80 mm** module PCB, and a header row **1.50 mm from the top**. The document's 26 × 26 mm summary and SSD1306 prose conflict with the drawing. Native CAD follows the drawing; header horizontal centering remains an explicit nominal inference with lateral enclosure clearance and a physical fit check. Active pixels are centered 2.10 mm above module center.
- The host PCB is **42 × 54 × 1 mm, two copper layers**. This accommodates the complete module, key spacing, USB access and assembly clearance without a four-layer stack. Final fresh native checks pass with zero ERC/DRC violations, zero unconnected items and zero schematic parity findings. The exact local footprint geometry, model pins and placements match the native files.
- **FM25V02A-GTR SPI F-RAM** stores counts separately from the MCU's program memory. This avoids program-update erase and EEPROM wear/bank-stall concerns. Its isolated supply, chip-select behavior and supply-ramp requirements have explicit conditional analysis and firmware tests; actual power waveforms remain a physical gate. The EEPROM implementation remains useful alternate-backend test evidence.
- **SW3, TS-1088-AR02016**, provides a physical reset button reached through a bottom service pinhole. Holding the reset-count key while resetting selects factory USB DFU; no external programmer is needed for ordinary home programming. SWD test lands remain for deeper repair.
- The shared supply uses **TLV76701DRVR with 150k/49.9k precision feedback**, nominal **3.20481 V**. The 64-corner regulated-supply calculation is **3.151365–3.258661 V**, supporting the conservative display guard. This is conditional on regulation; startup, dropout recovery, light-load accuracy and reverse-current behavior remain physical checks. Regulator quiescent current and divider current are an explicit battery-life tradeoff; see [power design](q4-power-design.md).
- The BQ29700 cold-battery-insertion timing bound still fails for the mandatory upstream charger capacitors. A downstream slew switch alone does not resolve it. USB-first commissioning/rearming has supporting device documentation but the combined circuit has not been physically demonstrated. This remains a release gate, not a successful complete-board simulation.

## Mechanical assembly decision

The Q4 enclosure uses four printed parts: **base, removable front display cover, rear key plate, and battery keeper**. Four M2 screws retain the board and covers; two new front mounting holes prevent an unsupported front PCB and let the display cover lift straight off. Fit the two switches into the key plate before soldering their four leads to the board. Solder the display and its separate header while the front cover is removed, trim protruding pins to at most 1 mm, then fit the board/plate into the base and install the display cover. The home work comprises four key joints and fourteen display/header joints. A separate header is specified rather than assuming the module includes one. Physical print fit, switch-plate engagement, screw strength, solder access and assembly remain first-article checks.

## Review entry point

See [the completed Q4 engineering review](REVIEW-Q4-2026-09-24.md) for final native, firmware, inventory, routing, CAD and export evidence; independent findings and fixes; the rendering; and the physical gates before an order. The quote pause remains unchanged.
