# Click-counter fidget — engineering draft, Rev 0

Prepared 14 September 2026 for Geoff Dudgeon.

**This project is in progress, not ready to order.** Two preliminary vendor RFQs have been sent, but no quotation or order has been received/placed in this session. The PCB is not routed, the target firmware is not compiled, and the enclosure is a fit-study model.

## Product baseline

- Two familiar MX-compatible clicky keyboard keys. Left increments, right resets on one press.
- Retained eight-digit count, from 0 to 99,999,999; at the maximum, stop incrementing and request a visible overflow indication rather than silently wrap.
- Automatic display blanking and wakeable sleep after 30 seconds. The first count-key press after sleep also increments. Holding a key never auto-repeats.
- FRAM journal persists each accepted change; ordinary sleep and a flat battery do not erase committed counts. An update interrupted before its commit may lose that latest click.
- USB-C charging-only, rechargeable lithium-ion coin cell, no always-on LED. Hardware charging and protection are independent of counter firmware.
- Home-printed, screw-secured enclosure with removable keycaps. All electrical soldering and initial programming are requested from the assembly vendor.

## Current work

| Deliverable | Status |
|---|---|
|Electrical architecture and initial pin allocation|Written in electronics/design.md|
|Exact DE188 display matrix|Obtained and encoded; physical qualification pending|
|Counter and persistence C core|Host-tested, including power cuts between journal writes|
|MCU target firmware and programming binary|Not complete|
|Enclosure STEP/STL and renders|Generated fit-study CAD; not a final fit release|
|Native PCB/schematic, Gerbers, BOM/CPL|Not complete; no fabrication files supplied|
|JLCPCB and PCBWay quotes|Budget RFQs and display follow-ups sent, responses pending|
|Paid order|Not placed|

## Important design finding

The candidate reflective LCD fits well and has a direct pin interface, but its Rev4 table specifies a combined on/off response of 440 ms. Rapidly changing digits may blur. Current part-specific data, a faster reflective alternative, or a compact OLED must resolve this before the display and PCB are locked. The supplier inquiries explicitly flag this issue. Do not mistake the model's sharp illustrative digits for demonstrated display performance.

## Size and weight

CAD body is 46 × 44 mm, 16 mm tall except an 18 mm display bezel; maximum keycap envelope is about 29 mm. CAD assumes standard-height MX switches to retain the familiar click and wide keycap choice. This is a practical light design, not proof of the lowest achievable mass; low-profile switches or one small reset button could reduce size but change the feel/form factor.

The screen is on the front edge, below the two keys in a top view. An earlier layout put it behind the keys, where their height obscured the display at shallow angles. The current layout avoids that obstruction. A final weight optimization pass should compare clicky low-profile switches before committing to standard-height MX parts.

The two modeled PLA shell solids total approximately 10 g at 1.24 g/cm³. A 42 × 40 × 1 mm bare FR-4 board is roughly 3.1 g before copper and drilling. With two switches/keycaps, the display, 2.6 g cell, electronics and fasteners, an initial **25–30 g assembled target** is reasonable but unmeasured. Validate bought-part masses and slicer output before claiming final weight.

For an LCD implementation, a provisional 10 µA sleep budget and 50–250 µA active budget at 10 minutes/day imply approximately 0.247–0.28 mAh/day, before self-discharge. Derating a 45 mAh cell to 70% usable gives roughly 113–128 days before further allowances. Treat **2–4 months between charges as a planning target**, not verified runtime. A selected OLED would require a new estimate and substantially more active power.

## Printing the fit study

Files in mechanical/ are millimetres. Base prints flat. The lid STL places the raised display bezel on the bed and needs support under the rest of its outer face. Use this only to inspect hand feel, general size and component clearances. The target part/switch/USB fit, full-travel clearance, LCD supports, battery harness/NTC and screw choice need a final pass. Walls are 1.2 mm, compatible in principle with two 0.6 mm extrusion lines, but slicer settings govern actual widths. PLA is suitable for a room-temperature fit prototype; transparent PETG can be considered for a final shell after dimensional and charging-temperature checks.

Do not operate/charge a battery in an unqualified fit-study assembly. In the final design, the coin cell is retained behind screws and connected with a keyed harness. The permitted cell is explicitly labeled; primary CR2032 cells are not substitutes.

## Resume work

1. Review vendor responses in the two Gmail threads recorded in procurement/quote-tracker.json. Firm quote comparison must include all THT/hand soldering, firmware/fixture/test costs, battery preparation and delivery.
2. Resolve display response and battery assembly; then freeze the purchased mechanical drawings. A different display may require a smaller/different MCU, revised PCB and revised enclosure window.
3. Complete the native schematic, full BOM, PCB routing and ERC/DRC, with protection/charging review. Replace component envelopes with actual vendor CAD.
4. Complete target firmware, compile and program a prototype; measure count accuracy, power, display response and charging/protection behavior.
5. Confirm physical fit and revise print files. Present firm vendor quotes and the concrete selected order before purchase.

All sources are linked in electronics/design.md. Downloaded reference PDFs are working inputs, not evidence of physical testing.
