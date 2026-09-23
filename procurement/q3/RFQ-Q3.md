# Count Fidget Q3 — prototype quotation

**Quote 5 complete units and separately 10 complete units. Do not spend money, procure chargeable parts, charge a card or release manufacture. A concrete order requires the project owner's separate approval.** Q3 replaces the unsupported DE188 display and supersedes Q1/Q2 for future engineering quotation. Keep historical submissions on hold; do not combine files from different revisions.

This is an unassembled engineering candidate. Quote review, physical qualification, approval of an itemized order and release of manufacture are separate events. Use the authenticated account for delivery/contact details. Quote USD, number/expiry, lead time, exact stock/MOQs and exclusions.

## Revised scope

Q3 uses Wisevision/Newvisio **X087-2832TSWIG02-H14 / C18723015**, a128×32 white OLED, with the SSD1312 internal9V pump, a separate4.0V TPS63900 supply and controlled pump-input isolation. The 48-pin MSP430FR4133 remains. TLV7012DGKR supplies the independent temperature window. Switches are **HanElectricity CPG151101D13 / C49234235**, click-tactile with MX stems, with220k pull-ups meeting the10µA minimum contact rating. There are70 fitted PCB references and43 distinct exact MPNs, all with positive JLC live-stock evidence when recorded. Stock is not reserved.

The routed layout uses **two copper layers, with all SMT on the bottom for one reflow pass**. The OLED and switches remain separately soldered on top by the vendor. Native validation and the export manifest must accompany any final quotation package. A clean report cannot qualify analog behavior, assembly processes or physical fit.

## Itemized commercial scope

Include PCB fabrication/net test; every fitted part; procurement, attrition and unavoidable excess; bottom SMT; localized OLED FPC soldering; switch and USB shell soldering; panel/stencil/tooling; firmware programming; fixture and test-software setup; first-article engineering; recurring functional tests; custom battery/NTC harness; two loose keycaps; packaging; lithium freight; duty/brokerage/tax; and grand total delivered. Separate one-time charges from per-unit work. Mark pending prices and unsupported items explicitly; do not use zero for an unpriced required part.

The customer prints/fits the enclosure and mates the finished keyed battery plug. All soldering and battery lead preparation are vendor work. Keycaps ship loose. The cover is split into front/rear halves that slide around the already-soldered switches before the enclosure base is fitted; the customer then installs the loose caps. Supply the completed pack disconnected and insulated for transport. Enclosure printing is excluded.

PCBWay: quote the full scope, including battery/harness and programming/test. Exact OLED sourcing, proposed FPC lands and solder process require your explicit acceptance.

JLCPCB: your earlier response excludes battery assembly and defers functional-test review/pricing until payment. Quote supported work and show these missing lines explicitly. This RFQ does not authorize payment to unlock review, paid part matching or preorder. A supported-PCBA subtotal is not a complete delivered-unit quote.

## PCB and assembly

| Item | Requested construction |
|---|---|
| Outline |42×40mm,2mm corner radius, one design|
| Layers |Two: F.Cu/B.Cu; no controlled impedance|
| Thickness |1.0mm finished; state achievable tolerance|
| Material |Standard suitable FR4; identify grade/Tg and any special material charge|
| Copper |1oz outer on both sides; vendor construction approval required|
| Finish |ENIG1µin nominal, green mask, white legend; quote a cheaper finish only as a separately identified DFM-reviewed option|
| Minimum routing |0.127mm trace/spacing,0.30mm through drill,0.60mm via land; actual local land/mask details control|
| Holes |Separate plated/nonplated files; USB shell plated slots; switch finished holes per exact drawing|
| Vias |Tented both sides; any exposed-pad thermal-via/paste treatment must follow supplied layout and be reviewed for wicking|
| SMT |Bottom side only, one reflow-pass pricing target|
| Separate soldering |Top OLED FPC and two switches; hybrid USB shell joints; no customer soldering|
| Panel |Vendor rails/tooling as needed, depanel to finished outline; disclose any support-panel charge|
| Process |Lead-free;100% bare-board electrical test, AOI plus manual FPC/THT inspection|

BOM-Q3.csv includes70 fitted PCB references plus offboard BAT1/K1/K2. TP1–TP10 and H1/H2 are PCB features. No unapproved substitution, DNP or omitted required line. The placement origin is Xright/Yup; top-view engineering coordinates use Ydown. Bottom assembly drawings are mirrored. Confirm machine rotations and actual part pin1 against the native footprints.

### OLED assembly and rails

DS1's native footprint origin is the glass center, not its solder-row center. Glass is29×8.8×1.22mm nominal; its tail extends to the right. Front view, pin14 is the upper contact and pin1 the lower. The14 proposed top lands are2.8×0.4mm at0.62mm pitch, with0.05mm mask expansion and **no F.Paste**. Pin6 is NC. Do not apply DE188 lead-spacing, standoff or heat limits to this OLED.

Install the OLED after oven/wave work using an approved localized FPC process. JLC's “Wave Soldering/High difficulty” catalog label is not approval to expose the glass to a solder wave. Confirm exact lot/drawing, pad overlap, mask web, solder/flux, heat/dwell/pressure, cleaning, inspection, fixture and strain relief. Quote tooling and manual work explicitly. PCBWay must confirm exact sourcing and full vendor assembly of this part.

The mechanical candidate proposes0.2mm compliant rear support and a gently lowered FPC onto the PCB, leaving the bond/driver region unloaded. The supplier drawing's contact-height datum is ambiguous. **An approved section/fixture/support drawing and first-article fit are required**; no180°fold, hard clamp or unsupported4mm glass standoff is authorized.

VDD stays at3.0V. TPS63900 produces4.0V nominal; Q5 disconnects OLED_VBAT. SSD1312 command8D72 selects9V internal drive, with external750kIREF. Measure OLED_VBAT between3.8–4.2V in all intended states, including startup/USB handover/low cell and transitions. The10mA converter input setting is an average control, not a guaranteed peak or total-cell-current clamp. Startup capacitor charging, always-on VDD and MCU paths bypass that limit. Retain the existing cell/protection limits and verify complete system currents.

### Mechanical interfaces and process details

Switch stem centers remain(11.475,28) and(30.525,28)mm. Footprint origins are contactpin1. Exact HanElectricity lands use1.50±0.05mm finished terminal holes and3.95mm nominal centerNPTH within the drawing's3.90–4.00range; there are no extra locator legs. The printed plate uses14.05mm openings,1.5mm thickness and a top surface5mm above the PCB seating face. Clip engagement, force, tolerances and full keycap travel require a real fit sample.

The printed enclosure has four parts: base, front cover, rear cover and battery keeper. The 50×45mm body reaches17.1mm at the switch plate; the provisional keycaps reach30.4mm. PCB bottom is11.1mm above the base floor. The two cover halves approach horizontally around the lower switch bodies; a one-piece cover cannot pass over the soldered upper housings. Qualify print fit, lapped joint strength and clip engagement before release.

J1 is bottom mounted at(38.9,15.3)mm and opens through the right edge; use current native drawing coordinates. USB4105-GF-A's default shell stakes are0.95mm. Solder all four shell joints. Native DRC has one narrowly scoped J1 shell-pad/SW2 courtyard projection exception. The rotated rear shell pad ends at boardY20.12; the switch lower body beginsY21.025, giving0.905mm nominal separation. Its flange underside is5mm above the PCB, while the modeled top fillet is at most0.5mm. Confirm the actual joint/part tolerances and fillet height. This exception never waives electrical spacing or a short. See the bound native/3D review. Confirm all local mask webs for the0.65mm-pitch comparator and OLED. No whole-row mask opening is silently approved.

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

Design charging is nominal 18.2 mA with a 16.5 kΩ ISET resistor; 10% termination is nominal 1.82 mA. Two separate TLV7012 push-pull comparator outputs drive series Q3/Q4 switches; both must be HIGH to enable charge. Each gate has a local 100 kΩ ground pulldown. The revised ladder/excitation models charge enable near 7.49–35.92°C nominal at the attached NTC. The widened conditional tolerance model is 4.83–10.20°C cold / 31.85–40.50°C hot; these are not guaranteed physical cell-temperature bounds. See the included Q3 power-design review for assumptions and fault limitations. Obtain the current cell manufacturer's approved charging envelope. Electrical tolerance, actual resistance/temperature data, installed self-heating and thermal-contact behavior require first-article verification before claiming the retained 0–45°C target is protected. The BQ25185 TS input has a fixed resistor because the independent comparator/NTC circuit performs the narrower hardware temperature inhibit. It is not permission to omit the real battery-contact sensor.

The PCB contains a BQ29700 protector and opposing FETs. Do not bridge raw CELL_N_RAW to system GND; doing so bypasses protection. Ship with battery disconnected and terminal/connector protection appropriate for the cell's transport requirements. Include all related freight charges in the quote.

Specific open engineering issue: the BQ29700 nominal 2.8 V undervoltage threshold has a retrieved ±50 mV tolerance at 25°C, reaching the EEMB 2.75 V discharge endpoint at that condition. Complete temperature limits, recovery and depleted-cell behavior remain unqualified; do not infer a blanket ±0.1 V rating or full-temperature compatibility. The cell maker must approve the actual protection limits or the protection design must change before release. Pricing this prototype does not resolve that issue. Do not present an engineering test as approval from the cell manufacturer.

## Programming and tests to price

Use a TI MSP-FET or supported Spy-Bi-Wire programmer and bottom pogo fixture. USB charges only. Keep debugging unlocked. The assembly drawing and current model give TP1–TP10 locations; their signals remain GND,V3,SBWTDIO,SBWTCK,VBUS,SYS,CELL_P,CELL_N_RAW,COUNT_N,RESET_N respectively. Do not use Q1/Q2 fixture coordinates. Sense DUTV3; do not back-drive an unpowered/discharging regulator. Use open-drain button simulation toGND, never driven-high inputs.

For each unit:

1. Inspect component identity/polarity, FPC alignment, all solder joints, key seating and USB shell joints. Check unpowered shorts. Verify raw CELL_N_RAW is not bridged to systemGND.
2. Use a current-limited cell simulator and separateUSB supply before a real cell. At3.7V simulated cell and10kΩ sensor, verify3V logic, OLED4V input and correct display operation. Test USB insertion/removal and both cable orientations. Record currents/voltages.
3. Initially program and verify **firmware/q3-oled/build/factory-blank-info-Q3.hex**, then **click-counter-Q3-oled.hex**. The factory initializer writes exactly0x1800–0x1821 and intentionally clears the count/journal plus error marker. Use it only for initial factory setup. Ordinary firmware updates must preserve the entire information-FRAM0x1800–0x19FF and load only the application.
4. Confirm startup0,20 count pulses(50ms closed/50ms open)→20,2s heldCOUNT addsone,RESET→0, and150 pulses(33ms closed/34ms open)→150. Simultaneous qualified reset/count gives0. Test the actual keys and reset priority, no repeat and no release-generated count. Verify readability/orientation and full display area using an approved first-article diagnostic procedure.
5. At count123, wait35s: display sleeps. First COUNT press wakes with124. Power-cycle and recover the last committed count. Ship at0. Record active/sleep currents; target sleep≤10µA is a qualification target, not a measured result. Establish active current/runtime acceptance on the first article with the new OLED.
6. With a suitable source/sink simulator, measure nominal18.2mA charging(target17–20mA),4.20V regulation within charger tolerance and termination below the cell's2.25mA limit. Confirm low-current-loop stability and USB handover; use no real cell for forced fault voltages.
7. 30kΩ and4.7kΩ sensor replacements, open and short must inhibit charge;10kΩ restores it. On the first article sweep thresholds/hysteresis, supply loss/recovery and temperature corners, then qualify attached NTC-to-cell response. Measure both gates/CE_N and disable latency. A nominal schematic threshold does not establish actual cell-temperature protection.
8. First-article scope also includes cell-protection UV/OV/overcurrent/recovery, load/inrush pulses, OLED9V pump/start-stop timing,4V transients, I²C faults, effective rail capacitance, brownout during every journal/marker phase, and fit/USB strain/key travel/pack retention. No safety/protection bypass is permitted to conceal a fault. Verify the firmware's captured-input-overflow ERR behavior and reset-only recovery using a controlled test; a loss of input history must be visible.

Return numeric results/pass-fail records by unit serial. Quote engineering fixture/test-software work and time separately from recurring testing. Stop after a failed first article and return the evidence; do not proceed with remaining units around a known defect. The reviewed firmware captures inputs in its timer interrupt, keeps journal writes foreground and starts display power guards after acknowledged command completion. Independent rebuilding and adversarial ISR tests passed; they do not establish physical hardware behavior.

## Quote response and release conditions

For5 and10 separately provide: PCB; each component/MOQ/attrition line; bottomSMT; OLED/key/USB soldering; fixture/stencil/panel; battery materials/preparation; loose keycaps; programming setup/unit cost; test-software setup; first-article engineering; recurring tests; packing; lithium freight; duty/brokerage/tax; delivered grand total and cost per functional delivered unit. State extra boards/spares, stock lead time and each unsupported or unpriced line. A cheaper2-layer or finish option must retain the same complete assembly scope.

Retain all documented engineering gaps: exact display process/lot/optics/current; cell source and protector endpoint margins; sensor temperature/fault behavior; effective capacitance; charger low-current stability; inrush; FRAM power loss; physical fit/retention; runtime/mass; and unquoted vendor services. Source/firmware consistency, ERC, DRC and CAD checks are evidence only within their stated scope. No physical board is qualified and no manufacturing release is given.

Primary references and calculations are included in docs/q3-power-design.md, q3-display-mechanics.md, q3-display-selection.md and the independent review reports. The completed manifest binds current native files, BOM/CPL, firmware and renderings. Historical Q1/Q2 quote acceptance is not acceptance of Q3.
