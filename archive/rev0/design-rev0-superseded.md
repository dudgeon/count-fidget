# Electrical design draft — Rev 0, not a manufacturing release

## Architecture and what is actually complete

The selected architecture is a reflective segmented LCD driven directly by a TI MSP430FR4133, with FRAM for the count, a rechargeable lithium-ion coin cell, standalone USB charging and independent cell protection. Functional topology, charger settings and proposed MCU pin allocation are defined below. The display segment matrix has been checked against the manufacturer's Rev4 PDF.

**No routed PCB, ERC/DRC-cleared native schematic, Gerbers or production firmware binary exists yet.** The mechanical PCB in the STEP file is an envelope. This draft must not be uploaded as fabrication data. Pending items include display speed qualification, final battery assembly, charge/protection tolerance analysis, all final orderable component suffixes/footprints, and target firmware/hardware validation.

## Display choice is conditional

Candidate: Display Elektronik DE 188-RU-30/7,5/V (3 VOLT), 8 digits. Manufacturer's catalog lists 34.9 × 13 mm glass, 5 mm digit height, 1/4 multiplex. Rev4 drawing has two 1.1 mm glass sheets (nominal 2.2 mm stack) and a 2.85 mm maximum at the pin wrap. The two pin rows are 13.5 ±0.3 mm apart; ten pins per row at 2.54 mm pitch. The generic application-note row-spacing formula is NOT used where it conflicts with the specific drawing.

Critical issue: Rev4's general table specifies **440 ms combined on/off response** and omits a product-specific bias value. That is too slow to promise a visibly crisp update for every rapid click. Counter logic can still count correctly, but the least-significant digits may blur. Obtain a current part-specific spec and qualify a sample or change the display. A small OLED is the fallback if rapid visible feedback is the priority; it requires a different interface and a revised energy budget. Do not release a PCB for this LCD solely on outline/pin compatibility.

LCD soldering limits from Rev4: 260°C maximum, 5 seconds maximum, minimum 4 mm separation from glass substrate to solder location. Planned glass rear surface is 4 mm above the PCB top, giving approximately 5 mm to bottom-side solder. Trim tails to ≤1 mm below PCB after controlled hand soldering. Add compliant support after exact clip geometry is approved; never clamp the glass hard.

## USB and charger

- J1: USB-C receptacle, candidate GCT USB4105-GF-A; verify drawing and current availability before footprint creation. Ground both GND contacts and shell. Join both VBUS contacts. Leave D+/D− and SBU unconnected.
- Separate 5.1 kΩ, 1% resistors from CC1 and CC2 to system GND. Do not join CC1 to CC2. No USB-PD negotiation is needed for 5 V, low-current charging.
- Add appropriate connector ESD protection; specific devices and footprints remain to be selected.
- U2: BQ25185DLH family, 10-pin WSON, 2.2 × 2.0 mm. Exact orderable tape/reel suffix to be confirmed.
- IN pin 10 → USB VBUS. CIN: 2.2 µF, 25 V X7R, with ≥1 µF effective at 5 V.
- SYS pin 1 → SYS rail. CSYS: 10 µF, 25 V X7R, with ≥1 µF effective at 4.5 V.
- BAT pin 2 → PACK+. CBAT: 2.2 µF, 10 V X7R to system GND.
- GND pin 5 and exposed pad → system GND/thermal copper; pin 4 /CE → GND for standalone operation.
- ILIM/VSET pin 7 → 24.0 kΩ, 1% to GND. This selects 4.2 V regulation and nominal 100 mA input limit in TI Rev B Table 6-1. The input-current limit is distinct from battery charge current.
- ISET pin 8 → 15.0 kΩ, 1% to GND: 300 AΩ / 15,000 Ω = **20 mA** nominal charge current. Expected termination is nominally 2 mA (10%). Include TI's recommended low-current 50 pF compensation network; its exact RC placement must be checked against the latest application guidance before schematic release.
- TS/MR pin 6 → a 10 kΩ-at-25°C, beta 3435 K NTC thermally coupled to the battery; its other lead goes to system GND. Use insulated attachment. Do not replace the NTC with a fixed resistor in the delivered design. Temperature thresholds/tolerances must fit the exact cell's approved charging range.
- STAT1 pin 9 and STAT2 pin 3 may be unconnected. No always-on power LED.

Power path allows the counter to run from USB while charging without confusing cell termination. SYS can be about 4.5 V, so it MUST NOT directly power a 3.6 V maximum MCU.

## Regulator and MCU

- U3: TPS7A02, fixed 3.0 V variant. VIN and EN → SYS; VOUT → V3; GND → system GND. Use the final package's verified pin numbering. CIN/COUT: 1 µF effective or higher, as required by TI. Expected quiescent current is 25 nA typical, not total-device sleep current.
- U1: MSP430FR4133IPM, 64-pin LQFP. DVCC pin 9 → V3; DVSS pin 8 → GND. Place 100 nF and 4.7 µF nearby. No external crystal is required for this counter baseline.
- /RST pin 10 → 47 kΩ pullup to V3; keep reset capacitance compatible with Spy-Bi-Wire (initial 1 nF). TEST pin 11 and /RST go to accessible programming pads alongside GND and target-voltage sense. The programming fixture must not back-feed USB or the battery.
- LCDCAP1 pin 4 / LCDCAP0 pin 5: reserve 100 nF pump capacitor and the required layout; verify against LCD_E configuration. Pins 1–3 (R13/R23/R33) must be configured consistently with internal-bias operation.
- Count button → P1.0 pin 24; reset button → P1.1 pin 23. Each switch shorts its signal to GND. Each signal gets 470 kΩ to V3 and 1 nF to GND. Firmware provides stable-state debounce; no auto-repeat. Inputs have defined states while sleeping. Verify leakage, edge rate and contact behavior on the prototype.
- Reserve P1.2 pin 22 for a switched battery-voltage divider to measure PACK+ without exceeding V3. Divider/control transistors are not yet finalized; avoid a permanent low-value divider that drains the cell during sleep.

### LCD line allocation

| Glass pin | Function | MCU LCD line | MCU physical pin |
|---|---|---|---|
|20|COM1|L0|64|
|1|COM2|L1|63|
|11|COM3|L2|62|
|10|COM4|L3|61|
|2|SEG0|L4|60|
|3|SEG1|L5|59|
|4|SEG2|L6|58|
|5|SEG3|L7|57|
|6|SEG4|L8|56|
|7|SEG5|L9|55|
|8|SEG6|L10|54|
|9|SEG7|L11|53|
|12|SEG8|L12|52|
|13|SEG9|L13|51|
|14|SEG10|L14|50|
|15|SEG11|L15|49|
|16|SEG12|L16|48|
|17|SEG13|L17|47|
|18|SEG14|L18|46|
|19|SEG15|L19|45|

The display is driven with alternating waveforms, never static GPIO levels. At sleep the display must be blanked without imposing a DC differential. FRAM retains the count with no battery power. The MCU remains in a wakeable low-power mode during ordinary inactivity; this is functional auto-off, not galvanic power disconnection.

## Cell and independent protection

Baseline battery: **EEMB LIR2032, 45 mAh**, 3.7 V rechargeable lithium-ion, 20 mm diameter, 3.2 +0.2 mm high, 2.6 g. Its manufacturer's specification gives 4.20 V CC/CV charging, discharge endpoint 2.75 V, and charge termination below 0.05C (2.25 mA). Proposed charger nominal 20 mA / 2 mA termination is inside the 1C fast-charge example, but the full tolerances and temperature range must be approved for the supplied cell. This does not permit any other LIR2032 brand as an automatic substitute. A normal CR2032 is not rechargeable and must never be installed.

A supplier-prepared insulated, keyed lead assembly avoids a bulky holder and eliminates soldering by the user. The exact termination and NTC arrangement is an RFQ dependency. Battery installation is inside a screw-secured enclosure.

Protection candidate: BQ29700, whose nominal limits are OVP 4.275 V, UVP 2.8 V and ±100 mV charge/discharge overcurrent detection, with external opposing N-channel MOSFETs. Configure the low-side path as CELL− → discharge FET source → joined FET drains → charge FET source → series sense resistor → system GND. DOUT drives the discharge gate; COUT drives the charge gate. BAT senses CELL+ through 330 Ω with 100 nF to raw CELL−; VSS → raw CELL−; V− senses system GND through 2.2 kΩ. Do not tie raw CELL− directly to system GND anywhere else.

Initial sense-resistance target is 3.3 Ω plus FET resistance, for roughly 30 mA cutoff. Final MOSFET part, thresholds/delays at temperature, actual current limits and charging recovery are **not yet qualified**. BQ25185's own high-current and low-voltage protections alone are not sufficient justification for this small coin cell. Battery wire protection and insulation must also be assessed. A VARTA replacement needs its own review; do not assume this EEMB circuit qualifies it.

## PCB layout requirements

42 × 40 mm envelope, rounded corners, preliminary four layers and 1.0 mm thickness. The printed plate and screw bosses carry click loads; PCB thickness must match the approved switch mounting method. All IC footprints must be copied from their selected package drawings, with pad numbering verified against the schematic. Maintain a continuous system ground plane while keeping raw cell ground isolated through the protector. Keep the charger capacitors/current-setting/NTC routes short, MCU decoupling adjacent, high-impedance button nodes short, and USB shell tabs mechanically supported. Provide test pads for VBUS, SYS, V3, PACK+, raw CELL−, system GND, SBW and both switches.

Place LCD/switches on top, low-profile logic beneath LCD, battery on the enclosure floor below the key area. Keep all bottom-side solder tails and component bodies away from the battery and its wires. Use a paper or printed fit gauge plus actual parts before final board routing. The CAD envelopes omit the LCD legs and therefore do not establish lead clearance.

## Production gates

1. Select a display whose measured visual response is acceptable, and approve current drawings.
2. Select battery lead/NTC assembly and finish charger/protection worst-case review.
3. Complete native schematic/PCB, ERC, DRC, source-to-BOM/placement checks and assembly drawing.
4. Complete and compile target firmware; bench-test at least one unit before any repeat order.
5. Verify count/reset at 1–15 clicks/second; first wake click; no repeat while held; memory brownouts; LCD waveforms and visibility; battery charging, termination and thermal inhibit; fault protection; USB-C both orientations; enclosure/drop/connector fit.
6. Obtain firm comparable vendor quotes including all hand assembly, programming, fixture/test charges and delivery, then present the selected payable order for review.

## Sources

- [Display Elektronik DE188 Rev4](https://display-elektronik.de/filter/DE188-RU-30_75_3V.pdf)
- [Display Elektronik product catalog](https://display-elektronik.de/wp-content/uploads/2021/05/company-profile.pdf)
- [TI MSP430FR4133 datasheet](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf)
- [TI BQ25185 datasheet](https://www.ti.com/lit/ds/symlink/bq25185.pdf)
- [TI TPS7A02 datasheet](https://www.ti.com/lit/ds/symlink/tps7a02.pdf)
- [TI BQ2970 family datasheet](https://www.ti.com/lit/ds/symlink/bq2970.pdf)
- [EEMB LIR2032 product and official datasheet](https://www.eemb.com/product-9)
