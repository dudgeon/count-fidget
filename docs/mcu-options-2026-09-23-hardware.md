# MCU options: hardware and simulation review — 23 September 2026

**Recommended migration candidate: STM32L072CBT6, with a separate 3.3V MCU rail and the existing 3.0V OLED rail retained.** Retaining MSP430 remains the lowest engineering-risk option. ESP32-C3 does not fit the present battery/protection budget well. No processor is a pin-compatible replacement, and none removes the OLED, startup or pack qualification gaps. This document proposes a future revision; frozen Q3 is unchanged. Quotes, vendor contact, purchases and manufacture remain paused.

## Processor comparison

Figures below are chip-level data-sheet conditions, not measured whole-device battery current. They exclude OLED, pull-ups, regulator losses, memory writes and boot transients.

| Option | Electrical/power consequence | Hardware/system tradeoff |
| --- | --- | --- |
| **Existing MSP430FR4133IG48R** | 1.8–3.6V operation;126µA/MHz advertised active consumption, under1µA standby with RTC/LCD. Current3.0V rail remains appropriate. | Existing tested software and FRAM journal; SBW fixture needed. USB remains charge-only. No migration cost or extra memory chip. [TI product/data sheet](https://www.ti.com/product/MSP430FR4133) |
| **STM32L072CBT6 / CZT6, LQFP48** | VDD can operate below3V, but USB domain needs3.0–3.6V. Flash execution at4MHz is650µA typical/670µA characterized maximum under the table conditions;32MHz is6.65/7.2mA. Stop mode at≤25°C is0.43µA typical/1µA maximum, excluding added clocks/peripherals. | CB128KB versus CZ192KB Flash; larger CZ memory alone offers no present functional advantage. Native USB can avoid a routine external programmer; retain SWD recovery pads. Both expose separate VDD_USB. [ST DS10689, Tables2/26/30/37](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf) |
| **STM32L072KZ, 32-pin** | Same family; USB power is internally tied to VDD because the separate pin is absent. | Common3.3V MCU rail below works, but smaller pin budget and a distinct pin map. LQFP32 is still7×7mm body; do not infer a large area saving from pin count alone. Exact package suffix and routing matter. [ST package/power definitions](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf) |
| **ESP32-C3** | 3.0–3.6V supply. Radio-off80MHz running is17mA typical before OLED; Wi-Fi RX84mA and TX up to335mA listed peaks. Deep sleep5µA is not the active or boot current. | Radio-off MCU plus nominal10mA OLED-converter input already approaches/exceeds the lower corner of the existing roughly30mA protection threshold. Radio operation is incompatible without a substantially different energy source/power design. [Espressif v2.4 electrical/current tables](https://documentation.espressif.com/esp32-c3_datasheet_en.html) |
| **ATtiny3226 with UPDI** | 1.8–5.5V, limited to10MHz at3V;5MHz active1.6mA typical, power-down0.1µA typical/1.5µA maximum at25°C with peripherals off. | A credible inexpensive MCU/programming alternative, but no native USB and no retained FRAM journal. Requires a software port and EEPROM wear/power-loss design. It does not deliver the plug-in USB experience motivating STM32. [Operating limits](https://onlinedocs.microchip.com/oxy/GUID-ACE76F82-8072-410B-AFA7-16B2BF7B4CBA-en-US-8/GUID-7F86BCC6-B62F-49BA-B774-3C93C9197DDE.html), [current table](https://onlinedocs.microchip.com/oxy/GUID-ACE76F82-8072-410B-AFA7-16B2BF7B4CBA-en-US-8/GUID-6BF6C784-3E2F-4690-ABC2-73A384F3711F.html) |

ESP32-C3's vendor recommends a≥500mA source and a40MHz crystal for the bare chip. A module incorporates RF/clock/flash circuitry but adds area, keepout and expense; native Serial/JTAG is not a general-purpose user-configurable USB device controller. Underclocking and short awake bursts could improve average consumption, but do not supply a guaranteed boot/flash-current envelope under the present protector. A battery/radio redesign would exceed the scope of a cheaper programming interface. [Espressif hardware checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/schematic-checklist.html).

## Concrete STM32L072CBT6 power architecture

Keep every return on protected **GND**, not raw cell negative. Continue using charger **SYS**, not the4.2V cell directly, as regulator input. The proposed distribution is:

```text
protected charger SYS ── existing TPS7A0230P ── OLED_VDD3V / I²C pull-ups
                     └─ new TPS7A0233P      ── MCU_VDD3V3 / VDDA / VDD_USB
                     └─ existing TPS63900   ── switched OLED pump input
```

**Added regulator candidate:** TPS7A0233PDBVR, SOT23-5, a real ordering-table variant of the existing family. Candidate pin schedule:1IN=SYS,2GND,3EN=SYS,4NC as explicitly permitted by TI,5OUT=MCU_VDD3V3. It needs local input/output capacitance and the MCU decoupling below. Typical no-load ground current is25nA; it is not a fixed25nA at every load. The family has ±1.5% temperature accuracy under its specified conditions, additional line/load effects, and active output discharge. [TI electrical/pin/ordering data](https://www.ti.com/lit/gpn/TPS7A02). JLC's [C2887324 listing](https://jlcpcb.com/partdetail/TexasInstruments-TPS7A0233PDBVR/C2887324) establishes catalog identity only here; the separate procurement review controls current stock.

For the exact48-pin part, VDD pins1/24/48, VDDA9 and VDD_USB36 join the same MCU rail; grounds8/23/35/47 join GND. USB uses PA11/32 and PA12/33. These are a proposed connection schedule requiring native symbol/pad and alternate-function review, not a generated design. The32-pin version needs its own schedule. [ST package definitions](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf).

**Why not simply reuse3.0V?** Its negative tolerance and dropout fail USB's3.0V minimum. **Why retain OLED3.0V?** X087's DC table permits3.5V, but its AC table/application states1.65–3.3V and requests matching interface voltage. A shared3.3V nominal rail exceeds the stricter3.3V limit at positive tolerance. A precision shared≈3.15V supply could reduce parts, but requires an exact regulator/tolerance/transient design rather than silently changing the limit. [Exact X087 specification](https://atta.szlcsc.com/upload/public/pdf/source/20231103/222F0746A2795BBD5263EDDBD3E1B824.pdf).

**Battery versus USB:** when valid USB supplies the charger, SYS has useful headroom for3.3V regulation; programming must wait for that supply to settle. On battery, the new LDO may enter dropout as SYS falls. Lower MCU voltage is allowed with USB detached and a suitable clock/BOR policy; it is not proof of a particular low-battery runtime. Dropout recovery can overshoot, and added capacitance/load changes the unresolved insertion transient. Test cold battery, USB attach/detach and brownout. Do not promise3.3V regulation down to the charger's≈3V battery cutoff.

**Separate USB-only supply rejected as the default:** although the48-pin device allows an independent USB domain, ST constrains its relationship to VDD during below-minimum startup/shutdown. A bareVBUS-to3.3V LDO could violate that order. The common MCU rail avoids needing an extra sequencer for this purpose. It still needs USB presence detection so battery power does not advertise an attached device to an unpowered port. [ST power constraints, Table26 note2](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf).

### Interface and boot details that must accompany the rail split

- Use I²C pins as open drain with the pull-ups remaining on OLED3.0V. Review exact pin thresholds and off-state injection in both power orders. The lower OLED ACK rating remains a problem with4.7k; a different MCU does not strengthen the OLED sink.
- Drive OLED RESET_N open drain and provide a pull-up to OLED3.0V. **Existing Q3 R25 is a pulldown: changing only firmware would leave reset stuck low.** Replace/review that resistor connection/value in the future design. With a pull-up, reset's initial state changes; retain the ENABLE pulldown, assert reset before powering the pump, and execute the full VDD/reset sequence. ROM bootloader mode must keep the pump disabled.
- OLED_ENABLE can drive the existing converter/Q6 controls at3.3V subject to their pin/gate ratings. All unpowered-interface and discharge paths still need checking.
- Connect both USB-C orientation pairs correctly, retain the two CC resistors, route D+/D− as a differential pair, add a suitable low-capacitance ESD device and provide reviewed VBUS sensing. Reserve series-resistor footprints only where the exact USB PHY/reference design calls for them; do not blindly copy another STM32 family.
- Provide BOOT0 selection, NRST access and SWDIO/SWCLK/GND/Vref pads. USB bootloader availability is not a reason to remove recovery access. Use the separate firmware analysis for exact boot option bytes, DFU behavior and nonvolatile-storage design.

The mixed-rail interface is an engineering proposal, not blanket compliance with the panel's matching-voltage wording. Its open-drain levels must be checked against both devices and supplier clarification or physical characterization before release.

## BOM consequences to include in cost comparison

The migration replaces the MCU footprint and its power network; it does not save the charger, protector, thermal window, OLED converter or specialized FPC work. Allow for:

1. One added3.3V regulator and local input/output capacitors; all effective-capacitance and reverse-current requirements remain.
2. Three100nF VDD decouplers, a100nF USB-domain decoupler, VDDA decoupling and a package bulk capacitor; some existing Q3 capacitance can be reassigned only after layout review. ST's reference uses local decoupling plus bulk and analog capacitors. [AN4467 supply/decoupling guidance](https://www.st.com/resource/en/application_note/an4467-getting-started-with-stm32l0xx-hardware-development-stmicroelectronics.pdf).
3. USB ESD, VBUS-sense components and boot/reset access; SWD pads add no fitted connector if a pogo fixture is used. Crystal-less USB can avoid a USB crystal, subject to the exact ROM/application clock setup.
4. A validated persistence solution. Internal EEPROM may avoid an external chip, but per-click durability, torn writes, write time and data preservation across DFU differ from FRAM. External FRAM, if selected, adds its device, bypass and bus connections. Do not price that decision as already resolved.

Do not convert typical MCU current into45mAh runtime: OLED demand and awake duty cycle dominate uncertainty, and new boot/current/decoupling transients must remain below the actual protection envelope. A cheap USB-capable chip whose supply needs redesign can cost more than retaining the SBW fixture.

## Manufacturer model coverage

[The model inventory](../simulation/mcu-review-2026-09-23/vendor-models.json) records official URLs, downloaded ZIP hashes and scope. Vendor files remain temporary; no proprietary model was copied into the repository.

| Device | Verified model situation | What it cannot establish here |
| --- | --- | --- |
| BQ25185 | No public SPICE model found in the current [TI catalog](https://www.ti.com/product/BQ25185) or bounded search. Its EVM is physical hardware. | Actual SYS/BATFET slew, startup state machine, charging/thermal interactions require measurement or a later verified model. |
| BQ29700 | No current public model located; a [historical TI answer](https://e2e.ti.com/support/tools/simulation-hardware-system-design-tools-group/sim-hw-system-design/f/simulation-hardware-system-design-tools-forum/828079/webench-tools-bq2970-spice-and-tina-ti-model) explicitly reported none. This is not a claim that no private model exists. | Threshold/delay/state-machine behavior must be modeled from documented corners and labeled behavioral, then validated. |
| TPS7A02 | Official [SBVM950](https://www.ti.com/lit/zip/sbvm950) generic plain-text PSpice core downloaded and inspected. | Header excludes input/quiescent current, temperature and noise. ExactP-variant discharge/reverse behavior was not established; generic dropout is not the exact low-load curve. No vendor-model execution claimed. |
| TPS63900 | Official [SLVMDC0A](https://www.ti.com/lit/zip/slvmdc0a) encrypted PSpice transient model inspected. Models soft start/input limit/DVS via parameters. | Physical CFG resistor decoding and temperature are explicitly excluded. Encryption prevents direct use in available ngspice; no decryption attempted. Nominal simulation does not create absent min/max guarantees. |
| Candidate MCU I/O | ST lists [STM32L0 IBIS3.0](https://www.st.com/en/microcontrollers-microprocessors/stm32l072cb.html); this study did not validate its internal package/pin coverage. No executable I/O model obtained for the other candidates or exact OLED FPC. | IBIS concerns electrical buffers and interconnect, not CPU execution, USB protocol, boot current, EEPROM or OLED pump behavior. The missing OLED sink/capacitance data remains missing. |

### Executed bounded ngspice study

The official temporary KiCad installation includes **ngspice45.2** as a shared library. [Original deck](../simulation/mcu-review-2026-09-23/interface-and-inrush.cir), [runner](../simulation/mcu-review-2026-09-23/run.py) and [result](../simulation/mcu-review-2026-09-23/result.json) reproduce three separate idealized circuits:

| Hypothesis, not a fitted device model | ngspice result |
| --- | ---: |
|3V/4.7k pull-up against hypothetical6k OLED sink | ACK1.682243V |
|Ideal released4.7k/100pF bus |30–70% rise398.217ns |
|4.2V insertion,3.3Ω shunt+**hypothetical1Ω** extra resistance, empty20µF |179.454712µs above0.4V |

They independently reproduce the earlier [analytical concerns](review-Q3-2026-09-22-hardware.md). The RC example excludes the charger's turn-on slew and protector state machine; the1Ω is not an approved cell impedance. All semiconductor behavior is absent. The report binds deck/runner/engine hashes, reruns byte-identically and matches independent equations; deliberately changing each of sink resistance, bus capacitance and SYS capacitance makes its analytical check fail.

Run `python3 simulation/mcu-review-2026-09-23/run.py --library /absolute/path/to/libngspice.dylib`. The engine reported a missing optional `spinit`; the deck uses only built-in linear elements and explicitly sets its numeric tolerances. The report retains that warning. No whole-board simulation or hardware PASS is asserted.

**Next simulation work:** (1) bounded, explicitly behavioral charger/protector state machines with documented corner sweeps; (2) exact cell impedance/MLCC bias and measured gate-slew inputs; (3) compatible manufacturer regulator runs cross-checked against their examples; (4) MCU/OLED I/O electrical models plus extracted bus capacitance; and (5) hardware USB/rail/persistence tests. Every reported result must state which of those layers it actually includes. This comparison supports choosing a feasible candidate, not manufacturing it.
