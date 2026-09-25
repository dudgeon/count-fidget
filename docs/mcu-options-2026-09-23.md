# Home-programmable MCU options — 23 September 2026

## Recommendation

**Develop the next candidate around STM32L072CBT6, using USB-C for both charging and home programming.** It combines factory USB programming, a low-power architecture and ample currently orderable stock. Its built-in EEPROM provides a plausible count-storage path without another memory chip, but requires a new, reviewed journal. The existing MSP430 implementation remains the frozen Q3 baseline and fallback.

This is an engineering recommendation, **not a completed replacement board**. No new design has been qualified or sent to a vendor. The user's pause on all quote uploads, draft changes and vendor requests remains absolute until explicitly lifted. No spending or manufacture is authorized.

The study used three parallel reviewers for inventory, programming/persistence and electrical feasibility, followed by cross-review. Supporting records: [fresh stock and prices](../procurement/mcu-options-2026-09-23-stock.md), [programming analysis](mcu-options-2026-09-23-programming.md), and [hardware/model coverage](mcu-options-2026-09-23-hardware.md).

## Four concrete options

Public JLCPCB inventory was read on **23 September at 11:07–11:09 UTC**. Prices are USD **per chip/module at ten pieces**, excluding attrition, supporting parts, assembly, programmer, shipping and tax. These are parts prices, not new quotes or reserved stock.

| Option | Orderable quantity | Each at ten | Home programming | Assessment |
|---|---:|---:|---|---|
| **STM32L072CBT6**, LQFP48 | **2,211** | **$2.7916** | USB data cable; factory ROM USB DFU supports first programming and recovery | **Recommended direction.** New power/interface circuit and EEPROM journal required. |
| Retain **MSP430FR4133IG48R**, TSSOP48 | 23 | $3.5334 | Shared, voltage-compatible Spy-Bi-Wire programmer and contact fixture | Least firmware disruption; keeps fast FRAM persistence. USB-C stays charge-only. |
| **ATTINY3226-SU**, SOIC20 | 44 | $2.4907 | Shared UPDI programmer and small programming connection | Potential simpler non-USB alternative; only 256 bytes of EEPROM makes write wear a substantial design constraint. |
| **ESP32-C3-MINI-1-H4X**, module | 1,840 | $2.5883 | USB data cable; factory USB Serial/JTAG download | Convenient programming, but a poor fit for the present small coin cell and protection budget. Wireless has no requested purpose. |

Catalog sources: [STM32](https://jlcpcb.com/partdetail/C465977), [MSP430](https://jlcpcb.com/partdetail/C2053877), [ATtiny](https://jlcpcb.com/partdetail/C3234898), [ESP32-C3](https://jlcpcb.com/partdetail/C41349510). LCSC separately showed 1,329 STM32L072CBT6 ready to ship. Those units are not added to JLC stock. The -H4X module is deliberately used because Espressif marks the older -N4 variant not recommended for new designs.

All four pass an illustrative 15-piece stock screen for ten boards plus allowance; this is not a vendor-specified attrition quantity. The smaller STM32L072KBU6 has only three orderable units. L072KZU6 and L432KBU6 have no verified immediate batch supply. The stocked 48-pin part is preferable to designing around a hoped-for smaller-package supply.

## Why STM32 is the best next candidate

The current MSP430 was attractive for its reflective-LCD controller and FRAM. The LCD controller became unused after the OLED change. Home programming is now an explicit design priority, so retaining that MCU deserves reassessment.

ST documents a **factory-installed USB bootloader** for this exact L072 family. That matters: a blank device can be loaded through USB, without first paying the assembler to install a custom bootloader. A physical boot-entry/reset path can recover a device whose application fails. USB clocking can use the internal oscillator. These capabilities are documented in [DS10689 §3.9](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf) and [AN2606](https://www.st.com/resource/en/application_note/an2606-introduction-to-system-memory-boot-mode-on-stm32-mcus-stmicroelectronics.pdf); they still need demonstration on the eventual board and the user's computer.

The intended home procedure is: connect a USB **data** cable, invoke hardware boot mode, load/verify the application with ST's programming software, then reset into the counter. Retain SWD test pads for development and exceptional recovery. Firmware updates must explicitly preserve count EEPROM; a factory reset must be a separate operation. Cable-only programming does not eliminate first-article electrical testing.

### Concrete power/interface approach to develop

- Retain the OLED's existing nominal **3.0 V** logic rail.
- Add a low-quiescent-current **3.3 V** regulator from protected SYS, supplying **all MCU power domains together**, including VDD_USB. This avoids the startup sequencing problem of powering the USB domain independently of a lower MCU rail.
- Candidate regulator **TPS7A0233PDBVR / C2887324** has 8,852 orderable units at **$0.4751 each at ten**, observed 11:12 UTC. This is a stocked candidate, not yet a selected circuit.
- Keep OLED I²C pulled to 3.0 V; make OLED reset open drain with a 3.0 V pull-up, replacing the existing R25 pulldown. Preserve the pump-enable pulldown so it stays off during ROM programming, and explicitly assert reset before pump startup. Validate mixed-rail startup, shutdown, leakage and input thresholds. Merely connecting 3.3 V outputs to the OLED is insufficient.
- Connect both orientations of the USB-C data contacts correctly, add suitable USB protection, and route a short controlled return path. Provide accessible boot/reset controls and retain debug pads.

The existing nominal 3.0 V rail cannot guarantee USB's 3.0 V minimum once tolerance is included. Simply raising the entire existing rail also leaves an unresolved OLED limit. The added regulator is a conservative starting point; a single precisely specified intermediate rail could reduce parts, but no such regulator/tolerance/transient design has been established. Battery operation in regulator dropout, brownout timing and cross-domain leakage remain review requirements.

### Count storage is the main firmware tradeoff

STM32L072CBT6 has 6 KiB of data EEPROM. It must use a distributed journal with validated records, commit ordering and recovery after interrupted writes. Do not copy the MSP430's two frequently rewritten FRAM records into EEPROM: their endurance assumptions differ. EEPROM write latency, code execution during writes, interrupt handling, ECC errors and updates that preserve storage all need target-specific treatment. The programming review develops those constraints; no new journal implementation or device-lifetime guarantee is claimed here.

A useful starting layout keeps code/vectors/constants in flash Bank 1 and the journal in the 3 KiB EEPROM region in Bank 2. A staged writer can then preserve input responsiveness while individual memory operations complete. Final linker placement and actual read-while-write behavior must be verified; issuing a complete multiword record as one blocking foreground operation would undermine the existing input-queue guarantees.

## Why the other choices rank lower

**Keep MSP430:** sensible if preserving the reviewed implementation matters more than cable convenience. It is not proven to be the cheapest home workflow. TI's full MSP-FET supports target-voltage sensing; the inexpensive LaunchPad's fixed-voltage debugger cannot simply be assumed compatible with the externally powered 3.0 V Q3 rail. A compatible adapter, fixture and host-software procedure remain to be qualified. An onboard USB-to-UART bridge adds parts and also inherits MSP430 bootloader entry/password/erase hazards, so it is not the leading approach. See [TI debugger guidance](https://www.ti.com/lit/ug/slau647o/slau647o.pdf) and [FRAM bootloader guide](https://www.ti.com/lit/pdf/slau550).

**ATtiny:** saves only about **$0.30 per MCU** versus the STM32 before memory or adapter costs. Its UPDI interface is useful; programming-only adapters are an option, with cost and target-voltage compatibility still to establish for this board. Small EEPROM capacity makes frequent per-click saves harder to distribute. Adding external FRAM, its decoupling and another feeder can erase the chip-price advantage. This remains the best secondary architecture to investigate if a small shared programmer is acceptable and USB convenience is unimportant.

**ESP32-C3:** its current datasheet gives about **17 mA typical at 80 MHz with radio off**, before the OLED, while radio activity can require much larger peaks. These are specified operating examples, not a measured counter budget. They leave much less margin under the existing roughly 30 mA protection target. A lower-duty-cycle implementation might improve average consumption, but changing the cell/protection system just for USB programming is unnecessary when the STM32 provides it. The module also occupies more area. [Espressif electrical data](https://documentation.espressif.com/esp32-c3_datasheet_en.html).

## Cost decisions that actually matter

1. **Two layers are already implemented.** None of these MCU options inherently requires returning to four. Routing and return-path checks still decide the final board.
2. **Native USB can remove a purchased home programmer and vendor programming work.** It adds protection, boot circuitry and power components; those are real costs. Test labor remains separate.
3. The STM32 alone saves **$7.418 per ten boards** against today's MSP430 tier. The proposed extra regulator uses **$4.751** of that, leaving only **$2.667 per ten** before capacitors, USB protection, boot circuitry, additional feeders or assembly. Therefore **do not sell this as a large PCB BOM saving**. The clear benefit is easier home programming.
4. **Fewer component types and simpler assembly are more promising than four home-soldered switch joints.** The historical five-board automatic result included $62.73 in feeder charges and $51.12 setup. The displayed hand/manual-solder lines total only $5.06 for that batch; even these may include work beyond the switches. No new savings quote is implied.
5. **The rechargeable coin cell was explicitly requested.** Its custom welded/insulated NTC pack and charging/protection qualification are material cost and risk drivers. A standard protected pouch pack would be a separate user-visible size/battery decision, not an arbitrary substitution to make this options table cheaper. The MCU change does not resolve the pack.

The last automatic vendor pricing remains the incomplete September15 five-board result. No complete ten-board or landed-price comparison exists. Current component inventory does not establish full revised-board support by both vendors.

## What simulation established today

A real **ngspice 45.2** run is now recorded alongside the analytical checks. It models three idealized electrical subcircuits, not just firmware behavior:

| Conditional scenario | Simulated result | Meaning |
|---|---:|---|
| Hypothetical 6 kΩ OLED acknowledgement sink against a 4.7 kΩ pull-up | 1.682 V low level | A specification-consistent weak sink can fail guaranteed low recognition. Actual display drive strength is unknown. |
| 4.7 kΩ pull-up with hypothetical 100 pF bus | 398.22 ns rise from 30% to 70% | Exceeds the reviewed 300 ns limit under those assumptions. Actual bus capacitance is unknown. |
| 4.2 V insertion into 20 µF through 3.3 Ω sense + 1 Ω other resistance | 179.45 µs above 0.4 V at the sense resistor | Can exceed the protector's minimum delay. Actual cell impedance and IC switching behavior are absent. |

All three agree with independent equations. This **reproduces unresolved risks**, not a functioning-board verdict. [Deck, runner and results](../simulation/mcu-review-2026-09-23/) are reproducible; [hardware review](mcu-options-2026-09-23-hardware.md) records vendor-model availability and limitations. A complete circuit simulation with validated charger, protector, converter, OLED and cell behavior has **not** been performed. Temperature, real insertion/startup, USB operation, display power, count retention and assembled fit still require appropriate hardware evidence.

## Next engineering work before another quote

Develop a separate STM32 candidate while keeping Q3 immutable. Resolve the shared electrical gaps in that candidate: OLED bus margins, insertion current, display startup/current budget and cell/protection behavior. Implement and adversarially test the EEPROM journal and USB recovery/update procedure. Then synchronize schematic, PCB, firmware, BOM and enclosure; run fresh native checks and render the actual revised CAD. Recheck the complete inventory and consolidate the remaining vendor questions. **Do not upload or request another quote until the user explicitly says to.**

This report supplies options and a ranked engineering recommendation. It does not label an unimplemented STM32 design ready for manufacture or silently close any Q3 issue.

### Review and reproducibility

The inventory reviewer cross-checked this report's exact stock, prices and cost arithmetic against the catalog records. The programming reviewer checked ROM entry, EEPROM capacity and bank/write constraints. The hardware reviewer checked rail/interface requirements and simulation scope; its power/layout work is an author review, not a claim of an unrelated external reviewer. Their corrections are reflected above, including the reset-pull resistor change, common MCU power domains and component-only cost limits. The coordinating agent independently reran the saved ngspice deck and reproduced its results. No reviewer found a reason to call the proposed board qualified; all stated design and physical gates remain open.
