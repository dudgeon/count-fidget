# Q4 power, interface and recovery design

**Circuit candidate, not hardware qualification or manufacturing release.** This document and the separate Q4 model replace no frozen Q1/Q2/Q3 file. Native layout, measured current, supply transients, pack safety and assembly tests remain required. The selected architecture is a common low-voltage rail, complete SPI OLED module, STM32 hardware USB recovery and external SPI FRAM. No firmware-controlled battery precharge bypass is fitted.

The model has **86 references / 70 fitted components**, a **42 × 54 × 1 mm, two-layer** board and root-owned placement overrides. U3 is **TLV76701DRVR**, with precision feedback set to **3.20481 V nominal**. This replaces the marginal first rail draft. DS1 and both large keys are designated for home through-hole completion; the other fitted parts are factory SMT. Fit the rear key plate before soldering the keys and complete the display-header joints while its cover is removed; the mechanical assembly instructions control the sequence.

## Connections that are stable

```text
USB VBUS ─ BQ25185 ─ SYS ─ U7 controlled-slew switch ─ SYS_LOAD ─ U3 ─ VLOGIC
protected cell ──────┘                                          ├─ MCU / USB domain
                                                               ├─ U6 slew/off switch ─ OLED module
                                                               └─ 68Ω ─ VFRAM / 10µF ─ SPI memory
```

Every circuit return remains on protected GND. Raw cell negative belongs only to the battery-protection circuit. SYS C2 and BAT C3 remain upstream of U7, as the charger requires. The original TLV7012 **push-pull** temperature window, separate series NMOS gates, 100k gate pulldowns and approximately30mA protection intent remain. The family’s TLV7022 is the open-drain part; no missing-pullup defect in Q3 was established. [TI exact TLV7012](https://www.ti.com/product/TLV7012).

### MCU and home recovery

STM32L072CBT6 supply pins1/24/48, VDDA9 and VDD_USB36 share VLOGIC; grounds8/23/35/47 join GND. USB requires3.0–3.6V, so nominal3.0V was rejected. The shared supply avoids independent USB-domain sequencing. USB PA11/PA12 connect both Type-C orientations through added data ESD; the original CC protection remains. No USB crystal is assumed necessary for the reviewed ROM boot mode. [ST DS10689](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf).

| Function | MCU pin / physical pad |
| --- | --- |
| Count, active low | PA0 /10 |
| Count reset and hardware BOOT0, active high | PA1 /11 plus BOOT0 /44 |
| Pinhole MCU reset | NRST /7; SW3 shorts to GND |
| Display reset / power enable | PB0 /18; PB1 /19 |
| Display CS / SCK / DC / MOSI | PB12 /25; PB13 /26; PB14 /27; PB15 /28 |
| Memory SCK / MISO / MOSI / open-drain CS | PB3 /39; PB4 /40; PB5 /41; PB8 /45 |
| USB DM / DP | PA11 /32; PA12 /33 |
| SWDIO / SWCLK | PA13 /34; PA14 /37 |

Unused PA8 is explicitly NC; no VBUS-present divider is fitted. USB recovery does not require application USB detection.

SW2 drives BOOT0 high only while held; it does not directly reset the MCU. BOOT0 must be high when reset is released, with the reviewed nBOOT1 option. With a battery attached, press and hold SW3 first, then SW2, then release SW3: pressing SW2 while the application runs is a count reset, and applying USB power does not reset a battery-powered MCU. Holding SW2 while applying USB power works only for an unpowered board (USB-first commissioning). See `q4-firmware.md` step 2 and [#3](https://github.com/dudgeon/count-fidget/issues/3). Firmware must load persistence before interpreting the held count-reset key. Keep SWD pads. ROM UART pins PA2/PA3/PA9/PA10 must not control display power or memory chip select. The exact option-byte/ROM proof belongs to the Q4 programming report.

## Display module and power switch

HS96L01W4S03/C5139758 is the seven-pin SPI module: GND,VCC,SCK,MOSI,RESET,DC,CS. Its actual drawing identifies **SSD1315**, a **27.30 × 27.80 mm** PCB and1.2mm board plus1.4mm top/1.0mm bottom geometry. This controls over contradictory26×26 prose. External input is specified3–5V and logic1.65–3.3V; internal panel tables do not establish an undocumented external-regulator dropout requirement. The resistor-strap page is not a full internal schematic. [HS manufacturer specification](https://datasheet.lcsc.com/datasheet/pdf/c5dd235441558974950f13e140069537.pdf?productCode=C5139758).

The module removes bare FPC bonding, flying capacitors, TPS63900 and its inductor. Its supplied header/stack, retention and exact low-voltage current still require inspection. Firmware uses sparse numeric rendering, low contrast, complete reset/initialization after power loss and guarded shutdown. Full-screen current is not an allowed normal-load assumption.

U6/U7 TPS22917DBVR pins are1VIN,2GND,3ON,4CT,5QOD,6OUT. **22nF CT connects to VIN**, not GND. U6 switches the complete module and connects QOD to its output; U7 is always enabled and leaves QOD unconnected. These are slew switches, not protection current limiters. Their programmed slew has typical values, not a guaranteed inrush maximum. [TI TPS22917](https://www.ti.com/lit/gpn/TPS22917).

R24 holds enable low. R25 holds reset low; PB0 must drive push-pull while powered, then become high impedance before power removal. The five display signals must never actively drive an unpowered module. R29 CS pullup connects to the switched output. The draft firmware reset setting was corrected to this push-pull/high-impedance contract.

## Selected common rail

**TLV76701DRVR / C2863998** uses R30 **150k RT0603BRD07150KL / C326734** and R31 **49.9k RT0603BRD0749K9L / C705780**, both 0.1%, 25ppm/°C. The DRV top-view pin contract is **1 OUT, 2 FB, 3 GND, 4 EN, 5 GND, 6 IN, exposed pad GND**. The local footprint represents the exposed pad as7. IN and EN join SYS_LOAD. Both ground pins and the exposed pad join GND. This is the adjustable WSON version; the family's SOT-23 version is fixed. [TI TLV767, Tables5-1 and6.5](https://www.ti.com/lit/ds/symlink/tlv767.pdf).

The 64-corner calculation includes ±1% reference, independent resistor tolerance and temperature drift over −40..85°C, a conservatively signed 50nA feedback current, an extra ±0.036% line allowance and ±0.01% load allowance for a 1–30mA operating envelope. The result is **3.151365–3.258661V before dynamic effects**. The line allowance applies the published maximum slope over an assumed1.8V excursion; its actual table test starts at VOUT+1.5V. Consequently this calculation is **conditional on regulation**, not a guaranteed low-headroom or dropout characteristic. The broad accuracy row also starts at1mA; sleep-load accuracy needs measurement. The earlier154k/100k TPS7A24 draft had insufficient ADC margin and is not the implemented circuit.

A −2% ADC underread at the calculated low corner still reports **3.088337V**, above the selected3.080V enable threshold by8.337mV. The divider consumes16.03µA; regulator quiescent current is50µA typical,80µA maximum at no output load. Regulator plus divider alone would consume an ideal45mAh cell in roughly28.4days typical or19.5days at maximum IQ, before every other load and usable-capacity loss. This is a battery-life cost of the selected straightforward architecture, not a whole-device runtime estimate.

C5 provides local input capacitance; C6 provides10µF local output bulk. Review total attached capacitance, including memory and the module, against the regulator's nominal1–220µF output range, effective minimum0.5µF and2–500mΩ ESR limits. Divider current exceeds5µA, so a feed-forward capacitor is not mandatory. The500µs soft start is typical. **No guaranteed numerical startup or dropout-recovery overshoot bound was found**; TI explicitly describes possible overshoot when leaving dropout. The output must stay within the module's logic limit in measured startup, USB removal/reconnection and load-step tests. At1A the DRV dropout maximum is1.4V; extrapolating that number proportionally to our much smaller load would not create a guaranteed dropout limit.

U3 has no guaranteed reverse-current limit. Its output must not exceed input by more than0.3V under absolute ratings. U7's reverse blocking and unconnected QOD reduce one discharge path but do not prove U3 safe during every power collapse. Record IN/OUT waveforms with the actual capacitance and loads; if reverse current occurs, implement reviewed protection rather than treating the internal body diode as protection. [TI TLV767 §§8.4.3 and9.1.4](https://www.ti.com/lit/ds/symlink/tlv767.pdf).

### Calibrated ADC policy

The proposed factory-VREFINT estimate budget totals1.8622% and rounds to2%: calibration supply uncertainty, reference calibration accuracy, maximum temperature drift over65°C, the stated1000-hour aging term, voltage dependence, and calibrated ADC total error plus quantization. The selected enable/disable thresholds are **3.080V/3.070V**. At a2% overread,3.07V means **3.0098V actual before switch loss and sampling delay**. Using a conservative175mΩ switch envelope at15mA leaves approximately3.0072V at the module; the actual current and switch loss must be measured. This is a steady-state guard, not a proof against arbitrary fast collapse. Periodic checks and full display reinitialization address recoverable brownout behavior; count persistence continues with display off. See the bounded calculation and ST Tables29/66. Long-term aging beyond the stated condition remains unbounded.

## Memory power and off-state behavior

**FM25V02A-GTR/C66029 remains selected.** Its2.0V minimum provides useful margin below STM32 BOR4’s2.68V minimum falling threshold. FM25CL64B’s2.7V minimum did not. V02 supports150µA maximum standby or8µA sleep; firmware therefore sends sleep only after the journal settles, wakes with a guarded delay, and queues incoming keys. Its limits include50µs/V rise,100µs/V fall and250µs power-up access delay. [Infineon FM25V02A](https://www.infineon.com/assets/row/public/documents/10/49/infineon-fm25v02a-256-kbit-32k-8-serial-spi-f-ram-datasheet-en.pdf).

R32=68Ω isolates C30=10µF. Requiring at least6.8µF effective capacitance, VLOGIC≤3.3V and total memory-rail sink≤3mA gives a conditional **137.8µs/V rise and129.9µs/V fall** bound, including resistor tolerance/temperature. The3mA envelope below2V is an explicit measurement requirement, not a datasheet guarantee. A short directly across VFRAM defeats this circuit.

At normal SPI≤1MHz, the0.22mA device limit plus pullup/leakage budget gives≤18.7mV DC drop. V02’s light-load output-high limit is VFRAM−0.2V; the model retains ample MCU threshold margin. The weaker VFRAM−0.8V figure belongs to CL64B, not V02. CS uses a100k pullup to VFRAM and open-drain MCU drive. With≤100pF net capacitance, firmware’s100µs release interval gives margin above VIH. Before power settles, SCK/MOSI/MISO/CS stay high impedance. Explicitly disable MCU internal pulls on these pins; their FT input limits permit the slowly decaying memory supply while MCU power falls. Physical ramp, injection, SPI edge quality and interruption tests remain required. STM32 itself also specifies a minimum supply-fall time with BOR enabled; the memory RC does not impose that waveform on the MCU rail.

## Battery attachment and recovery: not closed by a slew switch

Mandatory upstream C2=10µF and C3=2.2µF can present up to15.433µF in the deliberately conservative tolerance/temperature model. Maximizing an ideal series-R capacitor step over unknown resistance gives:

`max duration above SCC = C × Vcell × Rsense / (e × Vsc)`

At4.2V,3.333Ω and0.4V this is **198.692µs**, exceeding125µs minimum protection delay. This is a counterexample envelope, not a measured cell ESR or prediction that every unit trips. U7 only controls downstream capacitance. The charger's SYS-capacitor requirement is retained. [TI BQ25185](https://www.ti.com/lit/gpn/BQ25185).

### Intended USB-first commissioning

The intended sequence is: supply valid USB power, enter hardware ROM DFU with the display disabled, allow SYS and downstream rails/capacitors to settle, then attach the approved cell harness while USB remains connected. BQ25185 powers SYS from a valid input independently of charge-enable state; battery supplement operation is also independent of CE. The absent sensor can inhibit charging without preventing USB-powered commissioning. [TI BQ25185 §§6.1 and6.1.1](https://www.ti.com/lit/gpn/BQ25185).

Under these explicit preconditions, C2 and downstream capacitors are already charged. The remaining cold battery capacitor is C3:2.2µF ×1.10 ×1.15 = **2.783µF**. Its worst ideal single-step SCC exposure is **35.830µs**, below125µs. C4 charges through330Ω; conservatively treating its maximum12.856mA initial current as a constant additional discharge gives a combined **40.128µs** envelope, also below125µs. This bound depends on stable USB maintaining SYS, an initially uncharged C3, correct harness contacts and no connector bounce or extra unlisted battery-side capacitance. It is not an actual-cell-ESR measurement or a semiconductor state-machine simulation.

After a protection trip, reconnect USB. BQ2970 describes discharge-overcurrent/SCC recovery when charger connection satisfies its V− condition; BQ25185 also clears its own latched BATFET overcurrent condition with valid input. Verify that this exact combined circuit reaches those conditions, rather than assuming either individual description proves system recovery. [TI BQ2970 §8.4.4](https://www.ti.com/lit/ds/symlink/bq2970.pdf), [TI BQ25185 §6.3.7.3](https://www.ti.com/lit/gpn/BQ25185).

USB hot unplug is a separate transition: the cell must exceed the charger's battery-UVLO/recovery threshold, and MCU, module, regulator and memory currents plus transients must fit the existing protection window. Begin qualification with the display off and current measured, then repeat sparse-display operation and low-cell shutdown. Neither contrast10h nor the regulator's1A rating establishes a safe battery load.

Do not label normal cold insertion or recovery validated. Before release, test repeated cold attach, USB-first attach, USB rearm, low-cell cutoff/recovery, hot unplug and reset with the actual pack and temperature sensor. A persistent failure requires a revised power/protection architecture; instructions alone cannot close it. No relaxed current threshold, unsupported90mA cell rating or ADC-controlled bypass was adopted. The EEMB source lists standard/fast charging test conditions; use its exact approved pack specification. [EEMB cell specification](https://eemb.oss-accelerate.aliyuncs.com//uploads/20230323/ba65f4e593715c5dedf377f550c58f6b.pdf).

## Reproducible bounded checks

Run `python3 simulation/q4-power/check.py`. The [analytical result](../simulation/q4-power/result.json) binds model, circuit contract and analysis hashes; it checks all48 MCU pins, exact critical pin/net contracts,64 rail corners and three negative counterexamples. A1µF memory capacitor fails the ramp requirement, an excessively high divider violates3.3V, and300k/100k loses the required ADC enable margin. The unrestricted cold-insertion bound deliberately remains FAIL.

An additional runnable ngspice study is [run_spice.py](../simulation/q4-power/run_spice.py), using [ideal-envelope.cir](../simulation/q4-power/ideal-envelope.cir). Run it with `--library /absolute/path/to/libngspice.dylib`. The [SPICE result](../simulation/q4-power/spice-result.json) records the engine hash and input hashes. The real ngspice45.2 execution agrees with the ideal equations: USB-first C3 exposure35.829713µs, cold-upstream198.692048µs, memory rise137.809273µs/V and fall129.910925µs/V. The separate analytical check includes the extra conservative C4 branch.

These studies use ideal passive elements and declared current envelopes. **No manufacturer semiconductor model, complete-board simulation, physical qualification or manufacturing release is claimed.** They exclude charger/protector state machines, module current, regulator transients, real cell impedance and extracted layout parasitics. Native ERC/DRC, software tests and supplier stock do not replace those electrical measurements. The power-block author performed these calculations; an independent adversarial review is still required.
