# Q2 power correction proposal

Engineering candidate, 2026-09-15. This document specifies changes for a separate Q2 design. It does not alter the submitted Q1 package, approve a cell, establish measured performance, or release manufacture.

## Decisions

1. Select **TPS7A0230PDBVR** for U3. Its active output discharge is an intentional functional choice, not a spelling correction to the unmatched Q1 ordering code.
2. Replace U5 with **TLV7032DGKR**, split its two push-pull outputs, and require both outputs HIGH through two series MOSFETs before CE_N can be pulled LOW. Each gate has its own ground pulldown. This removes the external powered pullup that created the E18 monitor-supply-loss mechanism.
3. Retain the real, battery-contact NTC and the narrower external temperature monitor. Keep R5 = 10 kΩ on the charger's TS input and R6 = 100 kΩ from VBUS to CE_N. Reduce sensor excitation and recalculate the window using the parts below.
4. Retain the intended charger settings: **4.2 V**, **100 mA input-limit option**, and **18.18 mA nominal charging current**. The earlier pin/resistor allegation was refuted in [the charger audit](review-charger-Q2.md). Cell approval, protection, low-current charging, thermal contact and power-loss tests remain open.

The existing circuit and physical pin assignments are recorded in `electronics/build_pcb.py:77`–90 and 96–124. The implementation should live in the separate Q2 model/board/BOM; do not run the Q1 builder over its routed historical output.

## Exact candidate components and connections

All resistor changes below use 0603, 1%, 0.1 W parts with ±100 ppm/°C temperature coefficient. Manufacturer one-page specifications are linked individually.

| Ref | Q2 value / exact MPN | Terminal 1 | Terminal 2 |
|---|---|---|---|
| R10 | 57.6 kΩ / [RC0603FR-0757K6L](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0757K6L) | VBUS | TEMP_SENSE |
| R11 | 115 kΩ / [RC0603FR-07115KL](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-07115KL) | VBUS | TEMP_COLD |
| R12 | 24.3 kΩ / [RC0603FR-0724K3L](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-0724K3L) | TEMP_COLD | TEMP_HOT |
| R13 | 16.2 kΩ / [RC0603FR-0716K2L](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-0716K2L) | TEMP_HOT | GND |
| R14 | 100 kΩ / RC0603FR-07100KL, existing value repurposed | TEMP_COLD_OK | GND |
| R15 | 100 kΩ / RC0603FR-07100KL, replaces 1 MΩ | TEMP_HOT_OK | GND |
| R6 | 100 kΩ / RC0603FR-07100KL, retained | VBUS | CE_N |
| R5 | 10 kΩ / RC0603FR-0710KL, retained | TS_FIXED | GND |

Retain C9 = 100 nF directly between U5 supply and ground. Retain R3 = 24 kΩ, R4 = 16.5 kΩ, and the R19 = 2 kΩ / C13 = 4.7 nF compensation branch. Retain the four-wire harness: J2.1 CELL_P, J2.2 CELL_N_RAW, J2.3 TEMP_SENSE, J2.4 GND. The NTC spans J2.3–J2.4 and remains insulated from both cell terminals. Its physical contact with the cell is essential.

### U5 comparator polarity

Use **TLV7032DGKR**, DGK VSSOP-8. Physical pin functions follow [TI Table 4-2](https://www.ti.com/lit/gpn/TLV7042).

| Pin | Function | Q2 net |
|---|---|---|
| 1 | OUTA | TEMP_COLD_OK |
| 2 | INA− | TEMP_SENSE |
| 3 | INA+ | TEMP_COLD |
| 4 | VEE | GND |
| 5 | INB+ | TEMP_SENSE |
| 6 | INB− | TEMP_HOT |
| 7 | OUTB | TEMP_HOT_OK |
| 8 | VCC | VBUS |

Channel A is HIGH when the sensor voltage is below the cold threshold: the cell is warm enough. Channel B is HIGH when it is above the hot threshold: the cell is cool enough. Both must be HIGH. **Do not join pins 1 and 7.** Remove the old TEMP_OK net and its VBUS pullup relationship; repurposed R14 goes to ground.

With an intact passive divider, each input stays between GND and VBUS, including the open/short-sensor endpoints. This fits the powered common-mode range. A monitor-supply disconnection leaves inputs potentially above U5 VCC, so its explicitly fault-tolerant input behavior matters; do not assume the same behavior for a replacement comparator.

### Q3/Q4 series charge-enable path

Use **Nexperia 2N7002,215** for both devices, SOT-23. This is the Nexperia 2N7002 type with the identified ordering/packing suffix; do not substitute the importer's similarly named part from another manufacturer. The [Nexperia datasheet](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf) assigns pin 1 gate, pin 2 source, pin 3 drain.

| Device | Pin 1: gate | Pin 2: source | Pin 3: drain |
|---|---|---|---|
| Q3, upper FET | TEMP_COLD_OK | CE_MID | CE_N |
| Q4, lower FET, new | TEMP_HOT_OK | GND | CE_MID |

```text
VBUS -- R6 100k -- CE_N -- D Q3 S -- CE_MID -- D Q4 S -- GND
                           G                   G
                      TEMP_COLD_OK         TEMP_HOT_OK
                           |                   |
                       R14 100k            R15 100k
                           |                   |
                          GND                 GND
```

The body diodes point from source toward drain. With the orientation above, an OFF device blocks the positive CE_N voltage. Reversing either source/drain connection defeats the intended isolation. In normal operation both FETs conduct and their source voltages are near ground; either LOW output interrupts the sink path.

## Temperature setting and excitation calculations

The retained sensor is **Murata NCP18XH103F03RB**: 10 kΩ at 25°C, resistance tolerance ±1%, B25/50 = 3380 K ±1%. Murata's current list marks it NRND and specifies 0.1 mA maximum operating current at 25°C. NRND sourcing and the complete installed resistance/temperature curve remain open, as already documented under E12. [Murata component list, NCP18 table](https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/static-model/component-list-ntc-2508.ashx?cvid=20250930011345000000&la=en-sg).

For the proposed ladder, define:

```text
S = R11 + R12 + R13 = 155.5 kΩ
a_cold = (R12 + R13) / S = 0.260450161
a_hot  = R13 / S = 0.104180064
Vsense / VBUS = Rntc / (R10 + Rntc)
Rtrip = R10 × a / (1 − a)
T(°C) = 1 / [1/298.15 + ln(Rtrip/R25)/B] − 273.15
```

Calculated nominal cold/hot resistances are **20.2852 kΩ / 6.69864 kΩ**. The constant-beta model gives **7.49°C / 35.92°C**, preserving the earlier conservative nominal window. At 25°C and 5 V, excitation is 73.96 µA and NTC dissipation is 0.0547 mW; Q1's 10 kΩ excitation produced 250 µA and 0.625 mW. With intact R10, 5.5 V maximum and R10 at −2.01%, even a nonnegative arbitrarily small NTC resistance cannot draw more than **97.45 µA**. Installed self-heating and thermal lag still need measurement.

### Conditional corner envelope

The following is an engineering model, not a guaranteed cell-temperature limit. Independently vary all four divider resistors, R25 and beta; evaluate both signs of comparator threshold error and the VBUS endpoints. Use `a_effective = a + error/VBUS` in the resistance equation.

| Assumptions | Cold trip model | Hot trip model |
|---|---:|---:|
| Nominal components, zero comparator error | 7.49°C | 35.92°C |
| R10–R13 ±1%; R25 and B each ±1%; VBUS 2.95–5.5 V; threshold error ±21.5 mV | 5.52–9.48°C | 32.64–39.56°C |
| Same, with each divider resistor widened to ±2.01% | 4.83–10.20°C | 31.85–40.50°C |

The ±2.01% model conservatively covers 1% initial tolerance combined with 100 ppm/°C over a 100°C excursion. The error allocation is 8 mV offset + 12.5 mV half-hysteresis + 1 mV allowance for common-mode/supply effects. TI's dual-device electrical table specifies offset ±8 mV and hysteresis up to 25 mV at stated test conditions; the 1 mV addition is our allowance, not a new TI guarantee. [TI section 5.9 and hysteresis diagram 6-1](https://www.ti.com/lit/gpn/TLV7042).

The widened resistance limits are 18.3645–22.3497 kΩ cold and 5.8010–7.65625 kΩ hot. The constant-beta fit extrapolates B25/50 below 25°C; the manufacturer specifies different reference beta values across other intervals. A complete guaranteed R/T tolerance table and cell-contact measurements must replace this model before claiming an actual 0–45°C envelope. The apparent minimum margins of 4.83°C cold and 4.50°C hot are model margins only. Comparator bias/leakage, board contamination and the full voltage/temperature range also require qualification.

The 0–45°C target is retained from `procurement/RFQ-Q1.md:62`. Obtain the cell manufacturer's current approved charging envelope for the custom pack. The [currently linked EEMB specification](https://eemb.oss-accelerate.aliyuncs.com//uploads/20230323/ba65f4e593715c5dedf377f550c58f6b.pdf) documents its 25°C charging characterization; that alone does not approve this complete circuit across temperature.

### Why the existing NTC is not moved directly to TS

The BQ25185's typical 38 µA TS excitation and 0.115/1.0075 V hot/cold thresholds correspond to about 3.026/26.513 kΩ. A nominal 10 kΩ, B3435 sensor reaches those values near 59.5/1.7°C. Direct connection therefore permits charging substantially above the retained 45°C target. [TI BQ25185 electrical table and section 6.3.9](https://www.ti.com/lit/ds/symlink/bq25185.pdf).

The native resistance-threshold ratio is about 8.76; the retained B3380 model changes by only a factor of 5.76 between 0°C and 45°C. Ordinary positive series/shunt resistance compresses that sensor ratio further. This bounded revision therefore retains the external window instead of treating a simple TS rewiring as an adequate correction. R5 is deliberately fixed; it supplies no independent backup temperature protection.

## Supply loss, gate margin and fault reasoning

TI section 6.4 specifies TLV703x POR output LOW while supply is below its minimum on either rising or falling ramps; its operating range starts at 1.6 V. Section 6.4.1 permits inputs driven while VCC is zero without feeding VCC. However, it provides no zero-supply output-sink resistance or maximum power-down response time. Treat a fully unpowered output as potentially floating for passive-bias design. [TI functional modes](https://www.ti.com/lit/gpn/TLV7042).

R14/R15 discharge the gates without any externally powered gate pullup. Thus loss of U5's supply no longer leaves a resistor divider actively commanding charge. This corrects the identified E18 connectivity mechanism, subject to the transient and leakage tests below. It does not establish that every possible component failure disables charging.

- At 5 V, TI specifies output HIGH ≥4.65 V and LOW ≤0.35 V at 3 mA. Our 100 kΩ gate pulldown loads each output by about 50 µA. Nexperia specifies RDS(on) ≤5.3 Ω at VGS = 4.5 V, 25°C. The illustrative two-FET drop at 50 µA is about **0.53 mV**; CE_N is expected comfortably below the charger's 0.4 V LOW limit. Full gate-drive margins near a USB brownout require measurement because the cited output-voltage guarantee is at 5 V.
- The FET threshold range is not an ON-resistance guarantee or a guarantee of zero subthreshold current. In particular, its VGS = 0 leakage rating does not certify leakage at the comparator's maximum 0.35 V LOW bound. At a 2.95 V input and R6 = 102.01 kΩ, combined off-state leakage must stay below **16.17 µA** to keep CE_N above 1.3 V. Measure this with each gate commanded LOW, each monitor-power fault, temperature extremes and board leakage included.
- Nexperia's 25°C gate-leakage maximum of 100 nA corresponds to only 10.2 mV across a 102.01 kΩ pulldown. It does not include unspecified unpowered U5 output leakage. The 50 pF input-capacitance maximum suggests a roughly 5 µs RC scale; capacitance is nonlinear and parasitics add to it, so this is not a guaranteed disable time. [Nexperia electrical characteristics](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf).

| Applied condition | Inferred candidate response / limitation |
|---|---|
| Normal 10 kΩ sensor, monitor powered | A and B HIGH; both FETs ON; charge permitted. |
| Cold or NTC open | TEMP_SENSE rises above TEMP_COLD; A LOW; Q3 interrupts charge enable. |
| Hot or NTC short | TEMP_SENSE falls below TEMP_HOT; B LOW; Q4 interrupts charge enable. |
| U5 VCC connection open with VBUS and ground intact | POR/passive gate pulldowns request both FETs OFF; R6 requests charge disable. Verify the complete ramp/floating-supply response. |
| Comparator output/interconnect open upstream of an intact gate-to-ground pulldown | That gate's pulldown requests OFF. Place the pulldown close to the MOSFET gate. |
| R10 open or short | Sense goes toward GND or VBUS respectively; one channel requests disable. |
| R11 open or R13 open | Reference tends toward GND or VBUS respectively; one channel requests disable. |
| R12 open | Thresholds spread toward opposite rails; the temperature window can fail enabled. Not covered. |
| Comparator stuck HIGH, FET short, gate/pulldown connection open, monitor ground open, CE_N short, harness cross-wiring | Not established safe by this change; include in remaining fault analysis. An open between the gate and its pulldown can leave the gate floating. |

## U3 ordering decision and count retention

Select **TPS7A0230PDBVR**, 3.0 V, SOT-23-5. Keep pin 1 IN = SYS, pin 2 GND, pin 3 EN = SYS, pin 4 NC = GND, pin 5 OUT = V3. Grounding NC and tying EN to IN are permitted. Retain C5. Increase C6 from 2.2 µF to **10 µF, Murata GRM21BR61E106KA73L**, 25 V X5R ±10%, in the same 0805 footprint; move the separate C7 = 100 nF close to U1 DVCC/DVSS. TI MSP430FR4133 §8.3 specifies CDVCC 4.7 µF minimum / 10 µF nominal, with ±20% or better tolerance. Q1's 2.2 µF + 100 nF rail falls below that recommendation; the 10 µF SYS capacitor is upstream and does not satisfy it. Confirm **at least 4.7 µF effective V3 bulk capacitance** at 3 V after DC bias, temperature, aging and tolerance. The selected nominal part alone does not prove that worst-case bound. This also exceeds the LDO's lower 0.5 µF effective minimum once verified. [TI MCU recommended conditions and power layout](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf). [TI TPS7A02 Table 5-1, sections 7.3.2/7.3.4 and ordering section 9.1.1](https://www.ti.com/lit/gpn/TPS7A02).

The P variant actively discharges OUT during disable/UVLO. Its nominal discharge resistance is 60 Ω; falling input UVLO is typically 1.12 V, with a specified 1.0–1.41 V interval. TI also limits brief reverse current following input collapse to 5% of rated output current. These are component facts, not a hold-up guarantee. [TI electrical characteristics and active-discharge discussion](https://www.ti.com/lit/gpn/TPS7A02).

Keep U3 enable independent of the temperature interlock. A temperature fault inhibits charging while the battery can continue powering the counter. Do not use thermal shutdown to switch V3 off.

Illustratively, 60 Ω and the Q2 nominal 10.1 µF bulk/decoupling capacitance give a 606 µs RC constant and approximately 310 µs to fall from 3.0 to 1.8 V when that discharge path is active. The actual rail has other loads/capacitances, and the resistance is not guaranteed with input completely absent. No firmware commit time can be budgeted from this example. Its UVLO point is below the MCU's supported operating supply, so the LDO is not a substitute for MCU brownout behavior or journal verification.

The firmware commits journal updates before refreshing the visible count (`firmware/main_msp430.c`, journal/write/commit paths). Preserve the information-FRAM journal and its write-protection policy. Test interruption during every journal-write phase using the actual P regulator, including abrupt battery protection cutoff, USB removal, both sources removed and slow collapses. An SBW fixture must not drive V3 into an unpowered/discharging regulator; power the target through its intended supply and use V3 as the voltage reference unless a separately reviewed fixture provides isolation. Existing host interruption tests do not qualify electrical brownout behavior.

### Sourcing observations

The exact U3 [LCSC C3747031 listing](https://www.lcsc.com/product-detail/C3747031.html) showed 42,373 available when checked on 2026-09-15; [JLCPCB's exact catalog entry](https://jlcpcb.com/partdetail/TexasInstruments-TPS7A0230PDBVR/C3747031) exists. This supports the selected orderable identity, not allocation to this job.

The U5 [TI part page](https://www.ti.com/product/TLV7032/part-details/TLV7032DGKR) identifies DGKR as active. [LCSC C2863894](https://www.lcsc.com/product-detail/C2863894.html) was out of stock. The exact [DigiKey TLV7032DGKR page](https://www.digikey.com/en/products/detail/texas-instruments/TLV7032DGKR/10715597), opened on 2026-09-15, showed 2,004 available and cut tape from one piece, supporting an external sourcing path. Stock is not allocated and must be confirmed in the vendor's concrete quotation. DGKT was not found in TI's current ordering addendum and is not selected. Do not silently choose an open-drain device or a different package. Stock is separate from circuit qualification and purchase remains subject to a concrete approved order.

## Required verification before release

1. Independently compare native Q2 schematic pin functions/netlist/footprints, including Q3/Q4 orientation and the absence of the old TEMP_OK pullup. Run ERC/DRC on the completed Q2 design; Q1's retained reports do not apply.
2. Begin with a current-limited supply and battery simulator. Sweep VBUS through startup, 2.95–5.5 V, rapid removal and slow ramps. Open U5 VCC while the divider and R6 remain powered. Record U5 VCC, both gates, CE_MID, CE_N and actual battery current. Charging must remain inhibited after the fault and during recovery until both temperature conditions are valid. Establish a measured maximum disable latency.
3. Sweep sensor resistance in both directions and record both hysteresis thresholds. Verify 10 kΩ permits charge and open/short/30 kΩ/4.7 kΩ inhibit it. Repeat voltage and temperature corners, measure leakage margins, and compare with the model rather than declaring nominal thresholds sufficient.
4. Obtain the current cell/NTC pack specifications and guaranteed R/T tolerance information. On the actual insulated, attached sensor, measure cell temperature and sensor lag at both threshold directions. Establish that charging is disabled before leaving the cell maker's approved envelope, including heating while USB remains connected.
5. Verify 18.18 mA charging accuracy, precharge, termination, low-current compensation/stability, power-path transients and cell-protector recovery. Retain the existing E01/E03/E04/E05/E07/E11/E12 gates. The proposed E18 correction and valid U3 ordering code do not close those tests.
