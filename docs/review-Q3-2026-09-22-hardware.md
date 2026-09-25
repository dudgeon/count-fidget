# Q3 functional hardware review — 22 September 2026

**Disposition: retain Q3 as a review candidate; electrical qualification and manufacturing release remain open.** No new verified pin/net error was found in the circuits checked. Two conditional counterexamples explain why a correct netlist and passing software tests do not yet establish reliable power-up and display operation. Neither is a measurement of a failed board.

Quote submissions and vendor contact are paused. This review changes no frozen Q3 board, firmware, BOM, exports or RFQ. The reviewer previously authored the Q3 power additions and routing, so this is a fresh **self-review of those areas**, not an author-independent audit. The separate [September 15 review](review-hardware-Q3.md) records the independent electrical and layout review.

## Evidence and reproducibility

[The deterministic analysis](../scripts/analyze_q3_hardware_corners_20260922.py) reads selected values and topology from the frozen native model and writes [this dated report](../verification/q3-hardware-corners-2026-09-22.json). Run `python3 scripts/analyze_q3_hardware_corners_20260922.py`. The report binds its script, model, PCB and both firmware source files by SHA-256. It enumerates 512 conditional thermal corners, 135 idealized insertion cases and 12 energy-budget sensitivities. An independent 10 ns Euler calculation checks the insertion example against the analytical RC solution. This is a transparent calculation, not SPICE, an IC state-machine simulation or a physical PASS.

Validation: repeated execution produced byte-identical report bytes; all five bound input hashes and local review links matched. The analytical/Euler and deliberately specification-consistent I²C assertions passed. These checks validate the stated calculations, not omitted physical effects.

Reviewed native PCB SHA-256: `b33b1e1d0c9e4d58c5642fc3f63faaa4e190092601f26103376537a5b12621fd`. Model: `6f3dbc9d34e34576b680ad77fb27a0f70313f038b3d74dab6b434705e55d1c79`. Fresh manufacturer datasheets for TPS63900, BQ25185, BQ2970, TLV7012 and MSP430FR4133, plus the manufacturer-authored exact X087 specification, were read. The previously reviewed SSD1312 reference remains linked; its primary-host download timed out during this review, so no fresh retrieval is claimed.

## H22-1 — the published I²C rating does not guarantee the fitted interface

The actual R26/R27 are 4.7kΩ to V3. X087 specifies `VOL ≤ 0.2 VDD` at only 100µA. A hypothetical 6kΩ output sink satisfies that point at 3V, but against 4.7kΩ it produces an ACK voltage of **1.682V**. The MCU's specified negative-going threshold at 3V is 0.75–1.65V: that hypothetical sink would not produce a valid low. This deliberately constructed device model demonstrates insufficient specification, **not an actual 6kΩ measurement or a prediction that every panel fails**. [X087 electrical table, pp7–9](https://atta.szlcsc.com/upload/public/pdf/source/20231103/222F0746A2795BBD5263EDDBD3E1B824.pdf), [MSP430FR4133 §8.12.4.1](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf).

The competing rise-time constraint matters. The panel specifies 300ns maximum edges without a slower-clock exception. Using the 30–70% RC relation `tr = 0.8473 R C`, including +1% resistance:

| Pull-up | Sink demand at VOL=0.2VDD, VDD=3.09V, −1% R | Total capacitance permitted for 300ns rise |
| --- | ---: | ---: |
| 4.7kΩ, fitted | 531.3µA | 74.59pF |
| 25.5kΩ, candidate | 97.9µA | 13.75pF |
| 33kΩ, candidate | 75.7µA | 10.62pF |

The 25.5kΩ candidate uses the specified low-output operating point; it does **not** limit near-zero current to 100µA. Even the MCU pin contributes capacitance, and no guaranteed complete panel/FPC bus capacitance was established. Slowing the current nominal 65.536kHz clock may improve sampling margin but does not waive the panel edge limits. Counting ACKs alone does not measure margin.

**Smallest remedy and decision:** first characterize SDA ACK low voltage and both edge directions at the MCU and panel, including probe loading, supply and temperature. A resistor-only change to 25.5kΩ is a reasonable separately reviewed candidate only if the complete ≤13.75pF/rise and falling-edge conditions are demonstrated. Alternatively, a documented stronger panel sink-current guarantee could validate the existing resistors. No vendor request is authorized during the current pause.

If capacitance prevents the resistor-only solution, weak pull-ups with a gated **LTC4311** rise accelerator are a concrete next circuit to evaluate. It supports 1.6–5.5V, detects positive transitions and draws under 5µA disabled. It requires sufficient initial slew and improves rising edges; it does not establish the panel's unspecified falling-edge drive. Enable can track the awake display interval, with VDD retained. This adds a component and requires native layout, stock and waveform review. A generic I²C buffer is not automatically a fix: the panel-facing pull-up/current source must still respect the panel sink rating. [LTC4311 electrical characteristics and application equations](https://www.analog.com/media/en/technical-documentation/data-sheets/4311fa.pdf).

**Exit criterion:** a bounded panel sink/capacitance specification or assembled waveforms that establish input-low margin and both ≤300ns edges over the intended operating envelope. No resistor or buffer is declared a guaranteed drop-in fix from the present data.

## H22-2 — battery insertion can bypass the converter current setting

The model has direct SYS capacitors C2=10µF, C5=2.2µF and C17=22µF: **34.2µF nominal**. Charging C17 does not pass through the TPS63900's controlled conversion path; setting its EN low or selecting 10mA does not limit that initial charge. The BQ25185 battery-to-SYS path has low on-resistance, but no guaranteed battery-insertion slew bound was found. [TPS63900 input-limit function](https://www.ti.com/lit/ds/symlink/tps63900.pdf), [BQ25185 battery power path](https://www.ti.com/lit/ds/symlink/bq25185.pdf).

The exact BQ29700 short-current detection point is 0.5V nominal with ±0.1V accuracy at 25°C; its 250µs delay has ±50% tolerance. A legitimate evaluation therefore includes **0.4V and 125µs**, rather than nominal values alone. Its longer discharge-overcurrent response is a separate constraint. [BQ2970 device table and electrical characteristics](https://www.ti.com/lit/gpn/BQ2970).

For a hard-connected empty capacitor, with R9=3.3Ω, the analytic duration above a selected sense threshold is:

`t = (R9 + Rother) C ln[Vcell R9 / ((R9 + Rother) Vthreshold)]`

It is zero when the logarithm's argument is ≤1. At **4.2V, Rother=1Ω, C=20µF and Vthreshold=0.4V**, the duration is **179.455µs**, longer than the minimum 125µs delay. **The 1Ω is a hypothetical total additional series resistance, not a measured cell impedance, an approved pack specification or a guaranteed component bound.** The 20µF is likewise a sensitivity input, not an established effective-capacitance minimum/maximum.

The simple model omits actual gate/BATFET slew, nonlinear ceramic capacitance, inductance, cell dynamics, direct BAT capacitance, LDO/MCU startup load, protector state transitions and recovery. Those omissions prevent an actual failure-rate prediction. It nonetheless supplies a specific counterexample to “10mA setting makes startup safe.” A trip could appear as failure to boot or repeated power cycling; recovery behavior needs measurement.

**Smallest robust design direction if qualification fails:** separate the charger-local SYS decoupling from a controlled-slew **SYS_LOAD** branch feeding the added bulk, LDO and converter loads. Use hardware turn-on control that works before the MCU runs. Retain protection and the roughly30mA discharge setting. Verify local charger stability and all direct battery-side capacitance separately; switching C17 alone is not a proof for the remaining loads.

A concrete bench candidate is **TPS22918DBVR** with a CT capacitor near 10nF, QOD disabled unless shutdown sequencing supports it. TI's approximate equation gives a 10–90% rise of about22.1ms at4V; charging50µF through the central80% swing is about7.2mA average, before load current. This is typical slew behavior, **not a maximum-current guarantee or a selected BOM change**. It consumes8.3µA typical/15µA maximum at3.3V; 45mAh/15µA is125 days for this added load alone, before all existing loads/self-discharge. Whole-device sleep must therefore be remeasured. [TPS22918 §§6.5,8.3.3](https://www.ti.com/lit/ds/symlink/tps22918.pdf).

Do not silently reduce charger C2 to make the arithmetic pass. BQ25185's pin table requests ≥10µF nominal and ≥1µF after bias, while its application table lists1µF minimum/10µF nominal: resolve that interpretation and stability before a smaller local capacitor is adopted. Do not select TPS22946 from its30mA headline: it intentionally permits435mA typical inrush for8ms. A permanent series resistor only in the converter branch is incomplete and reduces available OLED power. [BQ25185 Table4-1/§7.2.2.3](https://www.ti.com/lit/ds/symlink/bq25185.pdf), [TPS22946 inrush behavior](https://www.ti.com/lit/ds/symlink/tps22946.pdf).

**Exit criterion:** simultaneous cell-current/sense-voltage/SYS/V3 captures across battery insertion, recovered protection, USB transitions and repeated brownout, using the approved pack and capacitor corners. If a revision adds slew control, bound its fastest ramp and startup load, then repeat these tests. Never common-ground raw cell negative and protected GND with test equipment; that would bypass the protection being tested.

## Remaining critical-function checks

| Area | Result and unresolved constraint |
| --- | --- |
| OLED and converter pins | Exact14-pin display schedule, U6 power/configuration pins and exposed-pad ground agree with the reviewed primary drawings. No added raw-negative bypass or reversed Q5/Q6 pin mapping was found. Model assertions protect the inputs used by this analysis. |
| OLED energy budget | At3V SYS and a nominal10mA input limit, even ideal conversion supplies only7.5mA at4V; at an assumed80% it is6mA. Panel all-on typical VBAT current is13mA. The sparse10h firmware may draw less, but pixels/contrast cannot be linearly scaled into a guarantee. A pump rail can droop while I²C still ACKs; there is no measured power-good feedback. Verify maximum allowed numeric content, rail minimum and brightness before raising contrast or input current. |
| Sudden power loss | Normal firmware shutdown does not cover protection opening or battery removal. V3 may collapse while OLED reservoir rails remain charged; U3 active discharge and Q5's reverse body diode require direct sequencing/reverse-current checks. This remains the earlier H04, not a newly proven failure. |
| Thermal polarity/faults | Separate TLV7012 outputs drive the two series enable FETs correctly; cold/hot invalid or absent drive inhibits CE under the reviewed assumptions. Nominal trips7.49/35.92°C reproduce. Conditional conservative corners are4.83–10.20°C cold and31.85–40.50°C hot. Half-supply offset-table corners give5.03–9.99/32.30–39.91°C, but do not bound actual common-mode, leakage, sensor attachment or beta extrapolation. R12-open remains a documented fail-enabled fault. Preserve installed-sensor and pack-envelope qualification. [TLV7012 electrical conditions](https://www.ti.com/lit/gpn/TLV7012) |
| Charger/protector | Pin assignments remain consistent. The18.18mA nominal charge current is below the range carrying the charger's general ±10% accuracy claim; qualify actual current/stability. BQ25185 battery UVLO is around3V, so normal load disconnection can precede BQ29700's2.8V undervoltage action. Do not use nominal thresholds as a tested boot/recovery envelope. [BQ25185 electrical table](https://www.ti.com/lit/ds/symlink/bq25185.pdf) |

Effective capacitor values, the SSD1312 pump maximum, attached NTC behavior and the exact pack's permissible charge/discharge envelope remain unresolved. No battery-life estimate is validated by this analysis. Native/ERC/DRC and firmware results remain separately scoped evidence, not replacements for these measurements.

## Lower-cost home completion

Two keys require four accessible electrical through-hole solder joints total; home key installation and SBW programming are plausible cost options. TP1=protected GND, TP2=V3 reference, TP3=SBWTDIO and TP4=SBWTCK. A proven fixture must power the target through its intended supply path and avoid back-driving the unpowered active-discharge regulator. [Home-completion plan](home-completion-Q3-2026-09-22.md).

Keep the14-contact OLED FPC attachment with a qualified assembly process. J2 is an SMT JST SH connector, and J1 combines fine-pitch SMT contacts with shell stakes; neither is a simple all-through-hole home kit. The incoming JLC statement that the OLED is normally a Standard assembly part clarifies the representative’s intended assembly category; a live catalog correction was not verified, and it does not approve this exact land geometry, support or thermal process. Battery tabs/NTC/insulation belong in the approved pack process, not improvised soldering to the coin cell. Savings cannot be quantified while quoting is paused; factory FPC setup and minimum charges may remain even when key soldering/programming move home.

## Next decision

Commit the frozen Q3 candidate with these dated findings and reproducible calculations for the next reviewer. Keep manufacture blocked. The immediate engineering work is a narrowly specified interface/startup fixture and its acceptance measurements, or a separately identified revision implementing qualified interface and slew-control changes. Neither a slower clock, one guessed resistor, an average input-limit setting nor another passing software simulation closes these two hardware margins.
