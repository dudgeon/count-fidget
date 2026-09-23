# Q3 OLED power circuit — implementation candidate

2026-09-15. This defines the new circuit for **X087-2832TSWIG02-H14 / C18723015**, with the existing protected battery path, charger, MCU and 3.0 V logic regulator retained. It does not change or qualify Q1/Q2. The initial pin/net schedule is [power-candidates.json](../procurement/q3/power-candidates.json). Final selected identities are controlled by the explicit overrides in [build_q3_model.py](../scripts/build_q3_model.py), including the stocked replacements below; the frozen initial schedule is not the final procurement BOM.

## Chosen rails and controls

Use **TPS63900DSKR / C1518762**, set to **4.0 V with the 10 mA average input-current setting**, from `SYS`. Its output feeds the panel's `VBAT` through a PMOS disconnect. Keep OLED logic `VDD` on the existing `V3` continuously. This uses one power-enable GPIO and one reset GPIO, with I²C pulled up to the same 3.0 V as the MCU.

The preliminary 3.7 V proposal is superseded. The panel calls for 3.5–4.2 V on its pump input, but the SSD1312's 9 V mode is characterized for **VBAT ≥3.8 V**. A 4.0 V target has more useful symmetric margin than 3.9 V. The converter's ±1.5% DC-accuracy specification, tested at 1 mA output with 10 µF effective output capacitance and 2.2 µH effective inductance, gives 3.94–4.06 V under that specification's conditions. This does not bound ripple, switch drop, operation at the current limit or transients. [TI DC-accuracy conditions, §6.5](https://www.ti.com/lit/ds/symlink/tps63900.pdf). Neither that arithmetic nor the 100 ms firmware delay proves the pump rail stays in range under current limiting. [Panel electrical table/application, pp7–10](https://atta.szlcsc.com/upload/public/pdf/source/20231103/222F0746A2795BBD5263EDDBD3E1B824.pdf), [SSD1312 Rev1.2, Table8-1](https://admin.osptek.com/uploads/SSD_1312_1_2_6a7ea26d1f.pdf).

| Node | Source / destination | Required behavior |
|---|---|---|
| SYS | Existing protected charger power path → U6 VIN | Planned 3.0–4.5 V range; direct converter-input capacitor charging is outside its current limit |
| V3 | Existing U3 → U1, OLED pin8, I²C pullups | 3.0 V logic; remains on in normal sleep |
| OLED_4V | U6 VOUT → Q5 source | 4.0 V; stored charge remains after EN low |
| OLED_VBAT | Q5 drain → OLED pin5 | Pump input; disconnect when sleeping; do not deliberately clamp to ground |
| OLED_VCC | OLED pin14 → reservoir capacitors | Internal approximately9 V pump output, not an external supply input in this design |
| OLED_ENABLE | U1 pin24/P1.2 → U6 EN and Q6 gate | Active high, R24=100k to ground defaults off |
| OLED_RESET_N | U1 pin23/P1.3 → OLED pin9 | Active low, R25=100k to ground defaults reset |
| OLED_SCL / SDA | U1 pins27/P5.3 and28/P5.2 → OLED pins10/11 | Hardware I²C, each4.7k to V3 |

All grounds in this added circuit are protected system `GND`, not raw `CELL_N`.

## Exact schematic schedule

U6 pins: **1 EN=OLED_ENABLE; 2 SEL=SYS; 3 CFG1=OLED_CFG1; 4 CFG2=OLED_CFG2; 5 CFG3=OLED_CFG3; 6 VOUT=OLED_4V; 7 LX2=OLED_LX2; 8 GND; 9 LX1=OLED_LX1; 10 VIN=SYS; exposed pad11=GND**. L1 joins LX1/LX2. R20=5.11k, R21=20.5k, R22=24.9k connect the respective CFG nodes to ground: both SEL selections therefore request4.0 V, with SEL hard-wired high. Configuration resistors are1%,≤100ppm/°C; total RMS error including temperature/aging must remain below3%. Use the TI DSK0010A land drawing: lead pitch0.5mm, pads0.6×0.25mm centered at x±1.15mm, exposed copper1.2×2.0mm. Do not copy a same-sized DRX footprint. [TI TPS63900 RevD, §§5,7.3.6 and DSK0010A drawing](https://www.ti.com/lit/ds/symlink/tps63900.pdf).

Q5 **DMP2035U-7**:1G=OLED_SWITCH_GATE,2S=OLED_4V,3D=OLED_VBAT. Q6 **DMN2056U-7**:1G=OLED_ENABLE,2S=GND,3D=OLED_SWITCH_GATE. R23=47k pulls Q5 gate to its source. Q6 is the same exact low-voltage-drive type as existing Q1/Q2. The PMOS body diode opposes forward supply when off; it is not bidirectional isolation. At4 V Q5 gate drive is within its±10 V rating; Q6's3 V drive is within±8 V. Use manufacturer pin drawings, not the panel application's ambiguous transistor pin numbers. [Diodes DMP2035U](https://www.diodes.com/datasheet/download/DMP2035U.pdf), [Diodes DMN2056U](https://www.diodes.com/datasheet/download/DMN2056U.pdf).

| New references | Exact MPN / value | Connection |
|---|---|---|
| U6 | TI TPS63900DSKR | Pin schedule above |
| L1 | Murata DFE201612E-2R2M=P2,2.2µH | LX1↔LX2; TI-listed family,2.4 A saturation |
| Q5 / Q6 | Diodes DMP2035U-7 / DMN2056U-7 | Switched pump input |
| R20 / R21 / R22 | Yageo RC0603FR-075K11L / -0720K5L / -0724K9L | 5.11k /20.5k /24.9k configuration |
| R23 | UNI-ROYAL 0603WAF4702T5E / C25819 | 47k, 1%, 100mW, 0603 PMOS gate pullup |
| R24 / R25 | Yageo RC0603FR-07100KL | 100k enable /reset pulldowns |
| R26 / R27 | Yageo RC0603FR-074K7L | 4.7k SCL/SDA pullups |
| R28 | Yageo RC0603FR-07750KL | 750k IREF→GND |
| C17 | Samsung CL21A226MAYNNNE / C602037,22µF25V X5R ±20%,0805 | SYS→GND, close to U6 |
| C18 / C19 | Same22µF part, two in parallel | OLED_4V→GND, close to U6 |
| C20 / C24 / C27 | Murata GRM188R71H104KA93D,100nF50V X7R0603 | V3 /OLED_VCC /OLED_VBAT →GND |
| C21 | Murata GRM21BR61E106KA73L,10µF25V X5R0805 | V3→GND at OLED logic supply |
| C22 | Murata GRM21BR71E225KE11L,2.2µF25V X7R0805 | OLED_VCOMH→GND |
| C23 | Murata GRM21BZ71H475KE15L,4.7µF50V X7R0805 | OLED_VCC→GND |
| C25 / C26 | Samsung CL10B105KA8NNNC,1µF25V X7R0603 | OLED pins1↔2 and3↔4 respectively |

The JSON has the complete14-pin OLED schedule; pin6 remains NC. There are24 added power/support components, plus the replacement display. Nominal capacitance alone is insufficient: require C17≥5µF effective, C18+C19≥10µF effective at4 V, and C21≥4.7µF effective at3 V after DC bias, temperature, tolerance and aging. Confirm pump-reservoir/flying capacitance on the selected parts. The two output capacitors add margin without claiming a measured minimum. [Samsung1µF part data](https://product.samsungsem.com/cn/mlcc/CL10B105KA8NNN.do), [Murata4.7µF reference sheet](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BZ71H475KE15-01A.pdf).

Use short local VIN/CIN/GND and VOUT/COUT/GND loops, keep both LX nodes compact and away from I²C/reset and analog sense, solder the exposed pad, and place flying capacitors directly beside their panel contacts. These requirements apply on a two-layer candidate as well as four layers. Check routing/return geometry independently after layout.

## Firmware contract and current budget

VDD remains on. The reviewed firmware first holds reset LOW and asserts ENABLE, supplying VBAT; SSD1312 §6.9.2 permits VBAT after VDD with zero minimum separation. It then waits 23 nominal ms, holds a further 2 ms reset interval, releases reset, and initializes with display off, 32-row mapping, external IREF mode `AD40`, low contrast and all controller RAM cleared. After at least the scheduled pump-feed settling interval, it selects **`8D72` for9 V**, sends display on, and observes a further guard. It does not copy the panel example's `8D12` (7.5 V). On sleep: `AE`, `8D10`, wait 105 nominal ms measured from observed acknowledged completion, then hold reset LOW and set ENABLE LOW. VDD stays present. Fresh completion/action timestamps and clock-tolerance margins are detailed in [the firmware README](../firmware/q3-oled/README.md). Input capture and foreground FRAM commits continue during waits and I²C faults. [SSD1312 §§6.9.2,6.10 and command table](https://admin.osptek.com/uploads/SSD_1312_1_2_6a7ea26d1f.pdf).

R28=750k intentionally replaces the panel example's560k. Using the controller's approximate IREF voltage VCC−2 V, it produces about8.58–10.10µA over VCC8.5–9.5 V and1% resistance tolerance. This falls within its recommended10±2µA and below the panel's12.5µA stated ceiling. It reduces a hardware current-reference risk; it does not guarantee whole-board current. Candidate contrast starts at10h with30h ceiling; show sparse eight-digit numerals and update only dirty pages. Do not use an all-pixels-on startup graphic. [Controller current-reference equation](https://admin.osptek.com/uploads/SSD_1312_1_2_6a7ea26d1f.pdf), [Yageo exact750k specification](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-07750KL).

At the converter's nominal10 mA setting, a3 V SYS offers30 mW input; assuming80% conversion efficiency gives24 mW at4 V, or6 mA pump-feed capability. That is an illustrative budget, not a guaranteed regulator output. OLED conversion loss, logic/MCU current, I²C pullup current and transient charging all consume additional budget. The panel's all-on current table is internally difficult to reconcile energetically and cannot establish battery current. Sparse operation must be measured.

**The TPS63900 limit is an average-input control, not a peak clamp or a battery protection replacement.** TI provides no guaranteed minimum/maximum for that setting; low-setting short-circuit current is also only typical. Output droop can occur instead of adequate brightness. Retain the existing BQ29700, opposing protection FETs and3.3Ω shunt. Measure current at the cell, including OLED startup and the capacitor surge that bypasses the converter limit. [TI clarification on limit tolerances](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1551457/tps63900-average-input-current-limit-minimums-maximums), [TI clarification on peak current](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1393207/tps63900-input-current-limit-simulation).

The I²C pullups remain4.7k pending interface qualification. At3V they demand about0.64mA near zero volts, whereas the cited display output-low table is tested at100µA. Increasing to33k would reduce current but require total bus capacitance below roughly10.6pF to meet the module/controller300ns rise specification; no slower-clock exception is stated. No guaranteed panel/FPC capacitance was found. Check ACK voltage and rise time on assembled hardware rather than calling either resistor value guaranteed from these data alone. [Exact calculation and primary tables](review-hardware-Q3.md#h03--i²c-acknowledgement-sink-margin-is-not-established-by-the-cited-table).

## Procurement and release gates

Root observed the exact TPS63900DSKR on native JLC at approximately12:14 UTC2026-09-15:21,624 in stock,21,370 available,MOQ1, Economic/Standard SMT, $1.1245 single/$0.9797 at10. This is an observation, not reserved supply. [JLC exact part](https://jlcpcb.com/partdetail/TexasInstruments-TPS63900DSKR/C1518762).

Final selected PCB identities now have root-verified native JLC inventory records for all **43 unique MPNs** in [live-stock-2026-09-15.json](../procurement/q3/live-stock-2026-09-15.json). This is dated stock evidence, not allocation, complete quote or both-vendor process acceptance. C17–C19 use the active Samsung **CL21A226MAYNNNE / C602037**; neither the original C86816 nor NRND MAQ family is selected. C1/C3/C5 use **Murata GRM21BR71E225KE11L / C77081**, C13 uses **GRM1885C1H472JA01D / C85980** (4.7nF,50V,C0G,5%), and U5 uses **TLV7012DGKR / C2859969**, preserving the separate push-pull outputs and two series charge-enable FETs. R23's exact stocked 47k identity is listed above. [Passive qualification/stock evidence](../procurement/q3/passive-alternatives.md), [comparator and key evidence](../procurement/q3/stock-alternatives.md).

Samsung's [selected active capacitor data](https://product.samsungsem.com/mlcc/CL21A226MAYNNN.do) gives a typical DC-bias curve, not a guaranteed combined bias/temperature/tolerance/aging minimum. The calculated typical 4V value is about11.90µF per capacitor; C18+C19 therefore have useful nominal margin, while their required effective minimum still needs qualification. Preserve the input and output capacitance bounds above. The replacement C0G compensation capacitor does not qualify 18.2mA charging stability.

Before manufacture: complete native parity/ERC/DRC and adversarial review; confirm exact component availability and FPC assembly process; establish MLCC effective values; measure all supply rails and cell current at battery extremes, temperature extremes, maximum digits/contrast, startup, sleep/wake, USB transitions, reset and protection opening; verify I²C edge timing; test FRAM retention during sudden rail collapse. The9 V mode has no controller maximum listed in its pump table, so measure panel VCC against the panel limits. Neither TFT-like continuous lighting nor nominal45mAh divided by a guessed load supports a battery-life claim. Physical OLED support/Z transition, enclosure fit, battery pack approval, charger/protector qualification and explicit order approval remain open.

## Cost review: retain external thermal window for this revision

The8–36°C nominal window is an engineering margin choice, not a new user requirement. Removing U5/Q3/Q4 and their resistor network could reduce cost, but directly connecting the existing10kΩ/B3380 pack NTC to BQ25185 TS does not preserve the documented0–45°C charging target. TI's typical38µA excitation and0.115/1.0075 V trip points correspond to3.026/26.513kΩ, or about60.1/1.4°C using that nominal beta model. Independent electrical-table corners plus±1% sensor resistance/beta produce approximately55.5–65.2°C hot and−1.0–3.8°C cold; these are modeled values, not guaranteed installed sensor temperatures. The sensor's0–45°C resistance ratio is only5.76 versus the charger's8.76 nominal threshold ratio. Ordinary positive series/shunt compensation further compresses the ratio. [TI BQ25185 RevB Table5.5 and §6.3.9](https://www.ti.com/lit/ds/symlink/bq25185.pdf).

An alternative NTC with a suitable complete R/T curve could support a future lower-part-count TS design, after cell-maker envelope approval and tolerance/fault validation. It is not an exact-part substitution for the existing unapproved pack. Direct TS open/short inhibits charging including trickle, but a persistent low also invokes the manual-reset/factory-mode behavior after10s and USB removal, adding a SYS/FRAM power-loss case. Keep Q2's external push-pull window in Q3, preserve its unqualified failure cases, and price its real assembly cost. Neither the present narrow window nor the native TS function replaces attached-sensor testing and pack approval.
