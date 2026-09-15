# Click Counter Q2 — quotation package

**Request a written, itemized quotation for 5 complete units and separately 10 complete units. Quote only. Do not manufacture, procure chargeable parts, or charge a card until a purchase order is approved.** This separate Q2 engineering candidate adds a native schematic and corrected circuitry. It has not been assembled or qualified. The submitted Q1 files remain historical and on hold; do not mix Q1 and Q2 manufacturing files. Supplier DFM review and a first article are required before releasing the remaining units.

Customer: Project owner (contact through authenticated vendor account). Delivery: postal code 20815, Maryland, United States. Use the customer's account shipping address to finalize delivery and tax if available. Quote in USD. Identify quote number, expiry, lead time, stock/MOQ assumptions, exclusions, and payment terms.


## Q2 revision and hold

The controlled changes are three 100 nF LCD bias reservoirs (C14–C16); 32 Hz display drive; 13.0 mm nominal LCD lead rows with existing 1.7 mm holes retained pending sample review; U3 TPS7A0230PDBVR; U5 TLV7032DGKR with separate outputs and series Q3/Q4 inhibit devices; revised thermal ladder; 10 µF V3 bulk capacitor; corrected local decoupler/gate-resistor placement; native schematic; and a separate matching enclosure fit candidate. There are 50 fitted PCB components.

U5 uses TI DGK0008A lands: 1.40 × 0.45 mm, 0.65 mm pitch, 4.40 mm row centers, 0.05 mm mask expansion. Copper gap is 0.20 mm; nominal mask web is 0.10 mm. PCBWay process acceptance is pending. Do not substitute whole-row mask openings without a specific reviewed proposal. Project-local footprints preserve the original modified geometry; library consistency does not qualify every land pattern.

C6's nominal 10 µF must retain at least 4.7 µF effective at 3 V after bias, tolerance, temperature and aging to meet the MCU bulk-capacitance recommendation. Verify that bound and actual rail transients. The thermal change addresses the identified monitor-supply-loss mechanism; resistor breaks, stuck outputs, transistor shorts and other faults remain subject to analysis/testing.

No new files are approved for manufacture or chargeable procurement. Vendor review, a concrete itemized order approved by Geoff, and the documented first-article hold are separate requirements.

## Required commercial scope

Include bare PCB fabrication, electrical bare-board test, every fitted BOM line, component sourcing/handling and unavoidable excess quantities, both-side SMT soldering, THT installation of the LCD and two switches, USB shell-tab soldering, any panel tooling/stencil, custom battery/NTC harness fabrication, two keycaps per unit, firmware programming and verification, functional tests below, one-time fixture/tooling/programmer charges, first-article review, packaging, freight including lithium-battery handling, duty, brokerage and sales tax. If DDP/tax-inclusive delivery is unavailable, state each excluded landed-cost item. Do not show a component line as zero merely because its price is pending.

The enclosure is printed and installed by the customer; exclude enclosure printing from the price. Supply the two keycaps loose for installation after the printed switch plate is fitted. All electronic soldering and battery lead preparation are vendor work. No soldering is to be left to the customer. Supply the completed battery assembly disconnected, insulated and protected in transport, subject to the supplier's shipping requirements; the customer can mate its keyed plug during enclosure installation.

PCBWay: please include the complete scope, including CC-BAT-001 and all programming/test work. Your website chat representative confirmed these can be quoted and requested submission through the customer's existing account; the stated review time was 1–2 days after receiving files.

JLCPCB: your website representative confirmed that battery assembly is unsupported and functional-test review is only available after payment. Please quote every supported line, explicitly mark the battery/harness and unavailable test price as excluded/pending, and do not label that subtotal a complete delivered-unit quote. We have requested pre-payment test review; no paid-order authorization is given by this RFQ.

## PCB fabrication and assembly

| Item | Specification |
|---|---|
| Board | One design, 42 × 40 mm, 2 mm corner radius |
| Layers | Four: F.Cu / In1.Cu / In2.Cu / B.Cu |
| Thickness | 1.0 mm finished, quote the vendor's achievable tolerance |
| Material | FR-4 Tg150 or higher; quote actual material/stackup |
| Copper | 1 oz (35 µm) outer, 0.5 oz (17.5 µm) inner requested; identify and price any alternative. Native dielectric split is a proposed thickness allocation, pending vendor construction approval |
| Finish | ENIG, nominal 1 µin gold; green solder mask, white legends |
| Minimum feature | 0.127 mm (5 mil) trace and copper spacing; 0.30 mm through-via drill, 0.60 mm via land |
| Holes | Separate plated and nonplated Excellon files; USB shell plated slots |
| Vias | Through vias, tented both sides, no filled/capped via requirement |
| Impedance | No controlled-impedance requirement |
| Electrical test | 100% bare-board net test against manufacturing netlist |
| SMT | Both sides; U1/J1/J2 on top, other SMT parts on bottom |
| THT | DS1, SW1, SW2 on top; hand/controlled soldering, no LCD reflow |
| Lead-free | Lead-free process and solder |
| Panel | Vendor panelization/rails if necessary; depanel to final outline; include tooling cost |

BOM-Q2.csv contains 50 fitted PCB components plus the off-board battery assembly and two keycaps. Pogo lands TP1–TP10 and holes H1–H2 are PCB features, not purchased components. Report substitutions before purchase. Battery chemistry, charger/protection components, LCD and switch geometry are not automatically substitutable.

Placement CSVs use the same Cartesian origin as the Gerbers: X right, Y up (therefore board positions have negative Y). The human-readable coordinate tables in this document instead use top-view Y down. Do not mix these conventions. Bottom assembly drawings are mirrored to show the underside directly. Native KiCad rotations are supplied; confirm machine rotations against pad 1 and the drawings during assembly review.

DS1: Display Elektronik DE188-RU-30/7,5/V (3 V), 34.9 × 13 mm, 20 leads, two 10-pin rows, 2.54 mm pitch, 13.0 mm nominal row separation. Its front-side pin numbering is embedded in the board. Maintain **4.0 mm from PCB top to rear glass surface**, approximately 5 mm to bottom-side solder. Manufacturer maximum solder exposure is 260°C for 5 s, at least 4 mm from glass. Do not clamp glass or reflow it. Trim LCD lead tails to no more than 1.0 mm below PCB. The 1.70 mm finished holes allow the flat leads; confirm against an actual sample before first-article soldering. Quote a reusable standoff jig or temporary removable assembly spacer. Display support in the final enclosure is customer-printed/compliant.

SW1/SW2: Cherry MX1A-E1NW PCB-mount clicky blue. Actual stem centers are (11.475, 28.000) and (30.525, 28.000) mm, measured from the top-left board corner, top view. The KiCad footprint placement origin is contact pin 1, offset from the stem; use the supplied footprint and assembly drawing rather than assuming these origins are the key centers. Plastic posts must sit fully in the holes. Preserve switch clips for the printed plate. Quote mechanical/hand soldering and cleaning suitable for these parts.

USB J1 opens through the right board edge, centered at y=13.3 mm. Check its standard 0.95 mm stake variant against the approved GCT drawing. Fill/solder all four shell tabs. No USB data functionality is required. J1 shell tabs and SW2 ground contact pad 2 use solid connections to the internal ground planes to avoid incomplete thermal islands. Review the additional solder heat demand and use an appropriate controlled process; do not exceed the parts’ soldering limits. Through vias are tented on both sides. Confirm mask registration/tenting around nearby same-net SMD lands, including the 0.038 mm nominal copper gap at C11; propose any necessary local change for review before fabrication.

## CC-BAT-001 custom battery assembly

One genuine **EEMB LIR2032, 45 mAh**, per unit. 3.7 V nominal lithium-ion rechargeable, 4.20 V CC/CV specification, 20 mm diameter, 3.2 mm nominal height (3.4 mm maximum bare-cell envelope). The supplier must obtain the current cell specification and approve its welded-tab preparation, insulation, shipping and charge-current compatibility. **CR2032 primary cells are not acceptable.** No direct iron soldering to the cell.

The prepared pack includes factory-welded tabs, individually insulated tab joints, four flexible insulated leads, a battery-contact thermistor and a keyed JST SH plug. Use JST SHR-04V-S housing and four SSH-003T-P0.2 contacts to mate the PCB's SM04B-SRSS-TB(LF)(SN). Wire length 40 ±5 mm from cell edge to connector, 30 AWG stranded insulated conductors, with strain relief at the cell and connector. Supplier may quote an equivalent qualified wire gauge within the JST terminal range; identify it. Keep the connector pin numbering tied to the JST drawing, not an assumed wire color orientation.

| Connector pin | Signal | Wire color | Connection |
|---|---|---|---|
| 1 | CELL_P | Red | Welded positive cell tab |
| 2 | CELL_N_RAW | Black | Welded negative cell tab |
| 3 | TEMP_SENSE | White | One NTC termination |
| 4 | GND | Blue | Other NTC termination; electrically isolated from both cell tabs |

Thermistor: Murata NCP18XH103F03RB, 10 kΩ at 25°C ±1%, 0603. This is a quoted prototype part (manufacturer lifecycle review required before a repeat build). Attach an insulated pre-soldered/wired thermistor closely to the cell can using thin electrically insulating thermally coupled material, with strain relief and protective encapsulation. All soldering to the thermistor and wiring occurs before it is attached to the cell. No thermistor termination may touch either cell pole. Added thickness over the cell face ≤0.8 mm; completed insulated cell body diameter ≤21.0 mm excluding the flexible tab/wire exit. Supply a dimensioned proposed pack drawing, current cell specification, NTC specification, insulation method, minimum order, and assembly price for approval before fabrication. If this exact pack is unavailable, quote a clearly identified proposal separately; do not silently substitute a holder or pouch cell.

Design charging is nominal 18.2 mA with a 16.5 kΩ ISET resistor; 10% termination is nominal 1.82 mA. Two separate TLV7032 push-pull comparator outputs drive series Q3/Q4 switches; both must be HIGH to enable charge. Each gate has a local 100 kΩ ground pulldown. The revised ladder/excitation models charge enable near 7.49–35.92°C nominal at the attached NTC. The widened conditional tolerance model is 4.83–10.20°C cold / 31.85–40.50°C hot; these are not guaranteed physical cell-temperature bounds. See the included Q2 power-design review for assumptions and fault limitations. Obtain the current cell manufacturer's approved charging envelope. Electrical tolerance, actual resistance/temperature data, installed self-heating and thermal-contact behavior require first-article verification before claiming the retained 0–45°C target is protected. The BQ25185 TS input has a fixed resistor because the independent comparator/NTC circuit performs the narrower hardware temperature inhibit. It is not permission to omit the real battery-contact sensor.

The PCB contains a BQ29700 protector and opposing FETs. Do not bridge raw CELL_N_RAW to system GND; doing so bypasses protection. Ship with battery disconnected and terminal/connector protection appropriate for the cell's transport requirements. Include all related freight charges in the quote.

Specific open engineering issue: the BQ29700 nominal 2.8 V undervoltage threshold has a retrieved ±50 mV tolerance at 25°C, reaching the EEMB 2.75 V discharge endpoint at that condition. Complete temperature limits, recovery and depleted-cell behavior remain unqualified; do not infer a blanket ±0.1 V rating or full-temperature compatibility. The cell maker must approve the actual protection limits or the protection design must change before release. Pricing this prototype does not resolve that issue. Do not present an engineering test as approval from the cell manufacturer.

## Programming and functional test to price

Use a TI MSP-FET or equivalent supported programmer in **Spy-Bi-Wire** mode. Quote a bottom-side pogo fixture, programming adapter/software work, and both setup and per-unit test labor. USB is charge-only. Keep JTAG/SBW unlocked for prototype debugging; do not blow security fuses or change BSL security settings.

| Pogo pad | Signal | Top-view coordinates (mm) |
|---|---|---|
| TP1 | GND | 9, 37.5 |
| TP2 | V3 / target voltage sense | 12, 37.5 |
| TP3 | SBWTDIO / reset | 15, 37.5 |
| TP4 | SBWTCK / TEST | 18, 37.5 |
| TP5 | VBUS | 21, 37.5 |
| TP6 | SYS | 9, 31.7 |
| TP7 | CELL_P | 12, 31.7 |
| TP8 | CELL_N_RAW | 15, 31.7 |
| TP9 | COUNT_N | 18, 31.7 |
| TP10 | RESET_N | 21, 31.7 |

These are viewed through the board from the top; a bottom fixture must mirror X. Use a current-limited cell simulator and separate USB supply for electrical checks before installing a real battery. DUT V3 is sensed by the programmer; do not drive it simultaneously from another source. No external signal may exceed the MCU rail. Simulate button presses with open-drain contacts to GND, never by driving the inputs high.

1. Inspect assembly, polarity, USB tabs, LCD orientation/standoff and all solder joints. Check for shorts with power removed. Quote AOI plus the required manual THT inspection.
2. Power with 3.7 V at J2 pins 1/2 through a current-limited cell simulator; connect a 10 kΩ test resistor across J2 pins 3/4. Confirm V3=2.91–3.09 V. Apply USB 5.0 V, then remove it, confirming continuous operation. Verify both cable orientations using a USB-C source and cable.
3. Load and verify `firmware/q2-lcd-check/click-counter-Q2-lcd-check.hex` and `firmware/factory-display-info.hex`, with the latter used **only during initial factory test**. Its valid journal starts at 88,888,888 for an all-digit visual check. The application's information-FRAM journal is 0x1800–0x181F. Confirm all eight digits show 8 with all seven segments visible; icons stay off. Press RESET to obtain 0. Do not ship a unit with the diagnostic starting count.
4. Apply 20 distinct count pulses, 50 ms closed / 50 ms open: expect 20. Hold COUNT for 2 s: expect exactly one more. RESET once: expect 0. Apply 150 pulses, 33 ms closed / 34 ms open: expect 150 after the display settles. Simultaneous qualified RESET and COUNT must produce 0. Check both physical switches manually too.
5. Set count to 123. Wait 35 s; LCD must blank. Measure and record battery-only sleep current, target ≤10 µA at room temperature. First subsequent COUNT press must wake and display 124. Release, reset, and check no release-generated count. Disconnect all power, reconnect, and verify the last committed count is retained. Final shipped count is 0. Measure actual active current as well; acceptance limits are finalized on the first article. Use the selected TPS7A0230PDBVR active-output-discharge regulator and Q2 C6=10 µF/C7=100 nF rail. Interrupt power during every journal-write phase, including abrupt protection cutoff and slow collapses. Do not drive V3 from the programming fixture into an unpowered or discharging regulator.
6. With the cell simulator near 3.6 V, apply USB and record CC charge current, target 17–20 mA. Sweep simulated battery voltage and observe CV regulation at 4.20 V within the charger data-sheet tolerance and termination below the cell's specified 2.25 mA limit. Use a four-quadrant source/sink or appropriate battery simulator; do not connect a real cell for forced overvoltage tests.
7. Substitute 30 kΩ then 4.7 kΩ for the NTC: charge must inhibit in both cases; 10 kΩ must restore charge. NTC open and short must both inhibit charging. On the first article, sweep sensor resistance to record both threshold values and hysteresis across voltage and temperature corners; verify the attached sensor's actual cell-temperature behavior before release. Open U5 VCC while VBUS still powers the sensor/reference dividers and CE_N pullup: measure both gates, CE_N and battery current through startup, removal and recovery. Charging must be inhibited when either temperature condition is invalid or the monitor supply is absent. Establish the actual disable latency and leakage margin; nominal logic is insufficient.
8. On the first article with a simulator, verify protection trip/recovery behavior and that charge/discharge faults cannot bypass the FETs. Record UV/OV/overcurrent thresholds against the selected protector's tolerances and current cell limits. Measure LCD common/segment AC waveforms, 1/4 multiplex, approximately 32 Hz nominal frame rate (30.88–33.12 Hz calculated REFO tolerance range), and negligible DC offset. Confirm acceptable visible digit response during fast clicking, plus charge termination and low-current-loop stability. These engineering checks are not replaced by AOI or firmware verification.

Quote the first-article engineering work separately from recurring functional tests, and give the proposed time allowance. Return numeric readings and pass/fail records by board serial number. Stop for customer review if the first article fails; do not build the remaining units around a known fault. The candidate firmware has host-verified counter/journal logic and reproduces the documented build. The original source/binary-mismatch allegation was refuted: TI's LCD4MUX macro includes LCDSON. The Q2 timing change is real; it is not a repair for a proven missing segment-enable bit. No hardware qualification is claimed.

## Quote response format

Provide for each quantity: fabrication; all BOM components; both SMT/THT assembly; LCD jig; pack materials/preparation; keycaps; programming setup and per-unit cost; fixture and test-software setup; first-article engineering; per-unit functional test; panel/stencil/tooling; sourcing/MOQ leftovers; packing; lithium freight; duty/brokerage; sales tax; grand total delivered; total divided by delivered quantity. Include any additional purchased boards/spares and whether all five/ten ordered units are delivered functional. Where a line is unsupported, state that explicitly.

## Engineering status and sources

This package provides a separately identified Q2 schematic, native PCB, Gerbers/drills, BOMs, placements, firmware image/source, connector/assembly notes and test scope. Its manifest binds these files to the checked candidate. Existing Q1 submissions do not establish Q2 upload or acceptance. Fresh Q2 schematic ERC, PCB DRC and schematic/PCB parity reports, with source hashes, accompany the completed package; software build/provenance results identify the separate 32 Hz candidate. These checks are not measurements or vendor approval. It is suitable to review for **prototype quotation**, not an authorization or certification of a child-ready product. Display speed, cell/harness construction, temperature tolerance, protection thresholds, low-current charging, and enclosure fit remain first-article release checks. DE188's Rev4 combined optical response is 440 ms; count capture can be faster than visible digit settling. Pricing this candidate does not assert that it has passed that check.

Primary references: [DE188 Rev4](https://display-elektronik.de/filter/DE188-RU-30_75_3V.pdf); [MSP430FR4133](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf); [LCD_E user guide](https://www.ti.com/lit/ug/slau445i/slau445i.pdf); [BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf); [BQ25185 EVM](https://www.ti.com/lit/ug/sluucs1/sluucs1.pdf); [TPS7A02](https://www.ti.com/lit/ds/symlink/tps7a02.pdf); [BQ2970](https://www.ti.com/lit/ds/symlink/bq2970.pdf); [TLV7032](https://www.ti.com/lit/ds/symlink/tlv7032.pdf); [USBLC6-2](https://www.st.com/resource/en/datasheet/usblc6-2.pdf); [GCT USB4105](https://gct.co/connector/usb4105); [EEMB LIR2032](https://www.eemb.com/product-9); [Adafruit 4997 keycaps](https://www.adafruit.com/product/4997).
