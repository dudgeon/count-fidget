# Q3 independent electrical review

15 September 2026. **No new reproducible pin/net wiring defect was found in the reviewed circuit. The initial review covers schematic/source correctness; the final native-layout follow-up below covers the routed candidate. Neither is hardware qualification or release.** The reviewer did not author the Q3 power circuit, but did implement its separate firmware; the latter has its own [independent adversarial review](review-firmware-Q3.md). The original electrical snapshot and subsequent layout corrections are identified separately below.

## Reviewed identity

The review evaluated `make_model()` in memory, without regenerating electrical files. The selected model explicitly overrides the initial power schedule's historical part identities. Relevant sources are [model selection and placement](../scripts/build_q3_model.py#L15), [OLED pin schedule](../procurement/q3/power-candidates.json#L111), [converter/power pin schedule](../procurement/q3/power-candidates.json#L141), and [power rationale](q3-power-design.md). Source SHA-256 at the electrical review snapshot:

| File | SHA-256 |
| --- | --- |
| scripts/build_q3_model.py | `65e1afadd6a73ec59e4342ef5c6ef8453eca2627086e0aec91c0eb098c8430c3` |
| procurement/q3/power-candidates.json | `c0ab4a84ff6665a5180b0f2ce07eef3c4dc3e308606973ba9be6a80c226153cf` |

Placement-only changes after this snapshot require the final layout review. Any pin/value/identity change requires another electrical comparison. Q1/Q2 sources and submitted artifacts were not changed.

## Confirmed checks

| Circuit | Result and primary evidence |
| --- | --- |
| U6 regulation/configuration | Pins 1–10 and exposed ground pad agree with TI; L1 joins LX1/LX2. CFG1=5.11k, CFG2=20.5k, CFG3=24.9k select 4.0V in either SEL state and the 10mA input setting. SEL connects to SYS. [TPS63900, §5 and Tables7-2/7-3](https://www.ti.com/lit/ds/symlink/tps63900.pdf). |
| Q5/Q6 disconnect | Both use 1G/2S/3D. PMOS source is OLED_4V, drain OLED_VBAT; its body diode blocks forward feed while off but permits reverse flow. Q6 pulls its gate down; R23 restores gate to source. R24 defaults ENABLE low. The devices' low-voltage gate-drive ratings support the intended 3V/4V operation. This is not bidirectional isolation. [DMP2035U, pp1–3](https://www.diodes.com/datasheet/download/DMP2035U.pdf), [DMN2056U, pp1–3](https://www.diodes.com/datasheet/download/DMN2056U.pdf). |
| DS1 connections | Exact X087 pins1/2 and3/4 have separate flying capacitors, pin5 receives switched VBAT, pin7 GND, pin8 V3, pin9 reset, pins10/11 SCL/SDA, pin12 IREF resistor, pins13/14 reservoir capacitors; pin6 is NC. The module's generic VCC description conflicts with its internal-pump application; the chosen circuit follows that application and the controller's pump pin definition. [X087 VerA, pp6,9–10](https://atta.szlcsc.com/upload/public/pdf/source/20231103/222F0746A2795BBD5263EDDBD3E1B824.pdf). |
| Protected return | No added OLED/regulator ground connects to CELL_N_RAW. Its complete model membership remains J2.2, U4.4, Q1.2, C4.2 and TP8. Q1/Q2 still oppose their body diodes; R9 remains between SENSE_FET and protected GND. No new conductive bypass was found. [Retained protection reasoning](review-protection-Q2.md), [BQ2970 typical application/pin functions](https://www.ti.com/lit/gpn/BQ2970). |
| U5 and charge enable | TLV7012 pin mapping is OUTA/INA−/INA+/GND/INB+/INB−/OUTB/VBUS. Cold output drives only Q3; hot output drives only Q4. Both must be high to pull CE_N low through correctly oriented series FETs. Each gate keeps its 100k ground pulldown. TLV7012 is push-pull with POR-low behavior and fault-tolerant inputs; it is not the open-drain TLV7022. [TLV7012, §5, §7.4](https://www.ti.com/lit/ds/symlink/tlv7012.pdf), [2N7002 pin drawing](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf). |
| Selected resistors | UNI-ROYAL replacements preserve 0603,1%,100mW. R9's 3.3Ω type has ±200ppm/°C, matching the former low-ohmic class; R3/R11/R16/R23 and 220k button pullups have ±100ppm/°C. At30mA, R9 dissipates about3mW. R11 retains the thermal divider value and tolerance class. [ROYALOHM thick-film data, printed pp10–14](https://www.royalohm.com/assets/pdf/products/smd/1.pdf). |
| Selected capacitors | C17–19 are active Samsung CL21A226MAYNNNE,22µF25V,X5R,±20%,0805. The primary typical bias curve gives about11.90µF each at4V; this supports margin but not a guaranteed minimum. C1/C3/C5 retain2.2µF X7R with25V rating; C13 retains4.7nF C0G5% compensation. [Samsung selected data](https://product.samsungsem.com/mlcc/CL21A226MAYNNN.do), [exact passive evidence and limitations](../procurement/q3/passive-alternatives.md). |

The selected 220k switch pullups address the newly selected key's10µA minimum contact rating: at2.97V and+1% resistance, held current is13.37µA. The exact switch drawing/process and physical fit remain separate checks. [HanElectricity specification](https://atta.szlcsc.com/upload/public/pdf/source/20250618/D1C12809F8EDF275373534C56A4C291D.pdf).

## Findings and dispositions

### H01 — documentation differed from the selected circuit; corrected

The power document still named the original R23 and C17–19 and described enabling VBAT after clearing RAM. It now names the selected parts and explicitly distinguishes the frozen initial schedule from final model overrides. It also records U5, C13 and C1/C3/C5 replacements and the43-MPN dated inventory record. Stock is not reservation or both-vendor process acceptance.

The corrected startup contract matches reviewed firmware: VDD is already supplied, ENABLE raises VBAT while reset is held, then reset/init/clear/pump commands follow. This order is allowed by SSD1312 §6.9.2. No firmware change was needed. The105 nominal-ms shutdown guard begins after observed completion, as tested in the firmware review.

### H02 — converter limits require their actual conditions; clarified, physical gap open

The ±1.5% DC specification is tested at1mA output,10µF effective output capacitance and2.2µH effective inductance. It does not prove4V regulation at the current limit. The10mA setting has no specified min/max; short-circuit input current is12mA typical. C17 charges directly from SYS outside that control. The power document now states the DC-test conditions. [TPS63900 §6.5, §7.3.4 and Table7-4](https://www.ti.com/lit/ds/symlink/tps63900.pdf).

Measure cell current and OLED_VBAT together during startup, maximum displayed content, USB transitions and shorts. Preserve the existing roughly30mA protector interaction and unapproved cell-envelope gates; the converter setting cannot close them. The4V candidate must keep the controller's9V pump input in range, and the module's generated panel voltage must be measured because the controller's9V-mode table lacks a maximum. [SSD1312 Table8-1](https://admin.osptek.com/uploads/SSD_1312_1_2_6a7ea26d1f.pdf).

### H03 — I²C acknowledgement sink margin is not established by the cited table

At3V, a4.7k pullup demands about0.64mA near zero volts. The module/controller output-low specifications are tested at100µA; those tables alone do not guarantee the acknowledgement voltage at the chosen load. SSD1312 additionally warns about the panel's ITO resistance forming a divider with the pullup. This is a specific unverified interface margin, **not evidence of an actual failed ACK**. Measure SDA-low at the MCU and rising edges on the assembled FPC across supply/temperature; adjust resistance/speed if necessary. [X087 DC table, p8](https://atta.szlcsc.com/upload/public/pdf/source/20231103/222F0746A2795BBD5263EDDBD3E1B824.pdf), [SSD1312 §6.1.5 and Table8-1](https://admin.osptek.com/uploads/SSD_1312_1_2_6a7ea26d1f.pdf).

**Pullup alternative evaluated:** retain4.7k for this candidate. A33k,1% pullup would limit the near-zero ACK sink demand to about94.6µA at3.09V, but both the module and controller require a maximum300ns rise time without a slower-clock exception. Using the usual30–70% RC rise approximation, `tr = 0.8473 R C`,33k at+1% permits only10.6pF total bus capacitance, not35pF. The exact panel/FPC capacitance is not specified in the reviewed data; the MCU digital-only pin capacitance is3pF. Thus33k does not establish both DC and edge-timing compliance. A slower clock alone does not waive the specified edge limit. Obtain the panel sink/capacitance limits or qualify the existing resistor on hardware; no BOM/firmware change was made. X087 p9 and SSD1312 Table9-6 are linked above; [MSP430FR4133 §8.12.4.1](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf).

### H04 — retained qualification gaps, with concrete failure mechanisms

- **Power collapse:** normal sleep leaves VDD on and floats the pump feed. Abrupt protection opening or battery removal may collapse V3 before stored OLED rail charge disappears. U3's active-discharge variant makes this a real sequencing case to test, not one covered by the normal software guard. Q5 is not reverse isolation. [TPS7A02 §7.3.4](https://www.ti.com/lit/ds/symlink/tps7a02.pdf), [SSD1312 §6.9.2](https://admin.osptek.com/uploads/SSD_1312_1_2_6a7ea26d1f.pdf).
- **Thermal bounds:** nominal trips remain7.49/35.92°C. TLV7012's±8mV offset and15mV maximum hysteresis fit within the existing±21.5mV conditional allowance, but its table tests use half-supply common mode; output-level guarantees use5V. Neither the existing modeled temperature envelope nor POR prose guarantees every USB-ramp/ground-fault response. NTC self-heating, attached R/T behavior, low-current charging and uncovered faults such as R12-open remain open. [TLV7012 §6.10](https://www.ti.com/lit/ds/symlink/tlv7012.pdf), [retained conditional/fault analysis](q2-power-design.md).
- **Capacitance:** typical Samsung bias data does not close simultaneous tolerance, temperature, aging and lot variation. Verify effective input/output and MCU/OLED logic bulk values, as well as the flying/reservoir caps. Nominal values and DRC are insufficient.
- **Measurement bypass:** TP8 is raw cell negative, whereas USB, the OLED and MCU reference protected GND. Connecting common instrument grounds to both would bypass the low-side protection path. Use a reviewed differential/isolated measurement arrangement for those nodes. This is a fixture constraint inferred from the verified nets, not a new PCB short.

## Layout review scope

The final follow-up inspected native routing and its DRC/parity evidence, including: U6 VIN/C17 and VOUT/C18–19 loops, exposed-pad grounding, compact LX1/LX2, CFG parasitic capacitance below10pF, and OLED flying caps near their actual FPC pads. Check gate pulldown placement, shared-return coupling into the NTC/CE circuit, 25V MLCC height, and the glass/FPC soldering envelope. The result below closes the identified layout corrections, while final package validation and all physical release gates remain separate.

## Native layout review — correction and final checkpoint

The independent review inspected native board SHA-256 `85c55de68c84dabe321dc8bb5d613365ebe560e32bb54e4728f791580cc9a3bd`, its actual pad positions, locked route seeds, and separate native front/bottom copper plots. At this checkpoint the layout report disclosed zero unconnected items/parity/copper violations plus the one specifically reviewed J1-shell/SW2 flange projection.

**L01, avoidable pump-loop detours:** the measured flying-capacitor legs were C2P3.64mm, C2N7.21mm, C1P6.41mm and C1N11.00mm, one through via each. C27's100nF pump-input bypass was roughly10mm from the panel input;34.64mm was the aggregate branched VBAT-net length, not a single source-to-load measurement. The reviewer requested a compact bottom-side C25/C26/C27 cluster with locked direct escapes and local ground returns before freezing this revision. Merely moving C27 near the right edge was rejected when local routing still needed a9mm detour.

This correction addresses avoidable series parasitics and loop area. No SSD1312 maximum PCB-route-length specification or observed instability is asserted. Its pump table is conditional on the module's ITO resistance, which PCB shortening does not qualify. Analog Devices' charge-pump layout guidance supports close flying/input capacitors as a general design principle, but its MAX1576-specific performance statements are not transferred to SSD1312. [SSD1312 Table8-1](https://admin.osptek.com/uploads/SSD_1312_1_2_6a7ea26d1f.pdf), [Analog Devices charge-pump layout guidance](https://www.analog.com/en/resources/design-notes/circuit-board-layout-guidelines-for-white-led-charge-pumps.html).

The TPS63900 review found no additional avoidable placement blocker: its locked LX1/LX2 connections measured2.374/2.623mm without vias, with local input/output branches and external exposed-pad ground vias. The two copper-pour views were inspected for these local return connections. This visual/native review is not an extracted impedance simulation or converter-stability measurement. [TI TPS63900 §10](https://www.ti.com/lit/ds/symlink/tps63900.pdf).

### L01 resolution — independently checked final routes

The corrected native board is SHA-256 `b33b1e1d0c9e4d58c5642fc3f63faaa4e190092601f26103376537a5b12621fd`. The reviewer independently read its native pads/tracks, compared all82 footprint values, identities and pin/net memberships with the original checkpoint (no electrical changes), and recalculated the following centerline lengths. Mid-segment joins were included when calculating branched-net paths.

| Connection | Final planar length | Through vias |
| --- | ---: | ---: |
| OLED C2P / C2N flying legs | 3.380 / 5.281mm | 1 each |
| OLED C1P / C1N flying legs | 3.942 / 3.489mm | 1 each |
| DS1.5 to C27 positive | 3.183mm | 1 |
| DS1.7 to C27 negative, explicit local return | 6.178mm | 2 |
| DS1.8 to C20 logic bypass positive | 6.329mm | 1 |
| C20 ground pad to its local via/pour | 1.100mm | 1 |
| TPS63900 LX1 / LX2 | 2.374 / 2.623mm | 0 |

Lengths exclude via-barrel depth and are not impedance measurements. C25/C26 flying routes remain locked. The C27 relocation includes the local ground stitch at(35.15,7)mm. A remaining roughly16mm C20 bypass detour was also corrected: its new via at(34.775,4.825)mm joins the local display supply escape. C20 retains its separate nearby ground via. The finish script preserves these branches with the matching incremental route; clearing seed routes before importing that SES would invalidate this result.

The saved [native checkpoint](../electronics/q3/routing-checkpoint-Q3.json) binds the same board and [DRC report](../electronics/q3/routing-checkpoint-native-drc.json), SHA-256 `25584b90307cbbe970c84b7e62d4723f328942287584071372b86a106398864c`. The report has zero unconnected items, zero schematic-parity findings and zero copper/clearance/edge findings. Its sole remaining item is the explicitly reviewed J1 shell/SW2 raised-flange courtyard projection; its physical solder/fit conditions remain required.

**Disposition:** L01 and the additional logic-bypass detour are closed for this routed engineering candidate. No further avoidable layout blocker was found within the reviewed scope. Final hash-bound package checks and the coordinated mechanical regeneration still govern exported-file validity. H02–H04, supplier FPC/process acceptance and physical electrical/fit measurements remain open; this is not manufacturing release.

