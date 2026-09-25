# MCU options: programming and retained counts — 23 September 2026

## Recommendation

**Use STM32L072CBT6 as the leading candidate for a future USB-programmable revision. Keep the existing MSP430 design as the lowest-change alternative.** This is a candidate selection study, not approval of a replacement board or firmware. STM32L072CZT6 adds program space but does not improve the counter's EEPROM capacity. ESP32-C3 provides convenient USB programming, but its power demand and flash-write behavior add work that this non-radio counter does not otherwise need.

No Q3 production source, board, previous evidence or frozen RFQ was changed. No device was programmed, purchased or quoted. Current public availability and component prices belong in the separate dated stock report; this document addresses technical feasibility.

| Option | First programming | Ordinary update / recovery | Main engineering cost |
|---|---|---|---|
| Keep MSP430FR4133IG48R | Existing SBW contacts and compatible external probe | Same fixture; preserve information FRAM | Qualify an affordable, voltage-compatible Mac workflow; no MCU port |
| STM32L072CBT6, LQFP48 | Factory ROM USB DFU; no preloaded application required | Hardware BOOT0 plus reset can recover a broken application; retain SWD contacts | New board pinout, MCU supply, USB routing, EEPROM journal and hardware abstraction layer |
| STM32L072CZT6, LQFP48 | Same programming architecture | Same recovery architecture | More flash; no additional count-storage benefit |
| ESP32-C3-MINI-1-H4X candidate | ROM download through native USB Serial/JTAG | Automatic download when available; GPIO9 plus reset for manual recovery | Larger software/power change, flash-latency handling and module layout |

## Exact STM32 choice and boot path

The exact **CBT6** has 128 KiB flash, 20 KiB RAM and **6,144 bytes EEPROM**; CZT6 has 192 KiB flash. The 3 KiB EEPROM entry in the family table belongs to the 64 KiB variant, not CBT6. ST's exact-part listing and RM0376's 128 KiB category-5 map independently resolve the merged datasheet table. With bank swapping disabled, EEPROM banks occupy `0x08080000–0x08080BFF` and `0x08080C00–0x080817FF`. [ST exact CBT6 listing](https://www.stmcu.jp/stm32/stm32l0/stm32l0x2/12614/), [RM0376, Tables 8–9](https://www.st.com/resource/en/reference_manual/dm00108281.pdf).

Relevant **LQFP48** pins: NRST **7**, USB DM/PA11 **32**, USB DP/PA12 **33**, SWDIO/PA13 **34**, VDD_USB **36**, SWCLK/PA14 **37**, BOOT0 **44**. The 32-pin LQFP K variant lacks the independent USB supply; package suffixes are not interchangeable. [DS10689, Figure 8 and Table 2](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf).

At reset, **BOOT0=1 and nBOOT1=1** select system memory. The factory option-byte value has nBOOT1 set. BOOT0=0 selects the normal application. Keep read protection at level 0, ordinary bank-1 boot, and accessible BOOT0/NRST controls. A software command to enter the bootloader can supplement these controls but cannot recover an application that never runs. [RM0376, boot configuration and FLASH_OPTR](https://www.st.com/resource/en/reference_manual/DM00108281.pdf).

AN2606 explicitly assigns the **V4.x USB DFU bootloader to STM32L072/073 and L082/083**. Its internal oscillator supplies the bootloader clocks; an external USB crystal is unnecessary. PA11/PA12 carry USB, with the internal pull-up. The similarly named L071 and L052 are not substitutes for this ROM-USB requirement. Avoid noisy or loaded bootloader UART pins, and account for the documented PA4–PA7 pull-down behavior during ROM execution. [AN2606, STM32L07xxx/08xxx V4.x section](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf).

### Supply architecture

USB requires **3.0–3.6 V** at VDD_USB. A nominal 3.0 V regulator cannot guarantee that minimum after tolerance and loading. Although LQFP48 exposes a separate USB domain, ST requires VDD_USB below VDD while VDD is below its minimum during power-up/down. [DS10689, Table 26 and its supply-sequencing footnote](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf).

The hardware review's simpler proposal is preferable: add a **3.3 V MCU rail**, connecting VDD, VDDA and VDD_USB together, while retaining the OLED's 3.0 V regulator. Keep I²C pull-ups at OLED 3.0 V and use open-drain display reset. This requires changing the existing R25 reset pull-down into an appropriate 3.0 V pull-up; changing the GPIO mode alone would leave the display in reset. Preserve a hardware pull-down on OLED_ENABLE, assert reset before enabling pump power, and preserve the OLED startup/off guards.

Battery-only regulator dropout is potentially acceptable for the MCU while USB is absent, but requires a complete check of clock/voltage limits, BOR thresholds, I/O thresholds, supply ramp and disconnect transients. Choose BOR to stop writes before the supply leaves the specified range. USB flashing must operate from the USB-powered rail with its minimum voltage demonstrated. This analysis does not certify the proposed regulator circuit or its battery runtime.

### Count storage: viable, with a new journal

EEPROM is not a drop-in replacement for the MSP430's FRAM. ST specifies **100,000 EEPROM erase/write cycles** over −40 to +105 °C, versus 10,000 for program flash. Each erase or program operation can take **3.94 ms**; a replacement needing both can take 7.88 ms. The memory operating range is 1.65–3.6 V. [DS10689, Tables 53–54](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf).

The recommended prototype is a rotating journal in **EEPROM bank 2**, with all code, vectors and constants kept in **flash bank 1** (64 KiB on CBT6). This follows ST's method for allowing code to execute while the other bank is programmed. Writes in the execution bank stall instruction fetch and can postpone interrupts; placing only the ISR in RAM is insufficient if foreground execution stalls first. If the application later needs both banks, redo the placement strategy or move the entire critical execution path and vectors into RAM. [AN4808, §§2–4](https://www.st.com/resource/en/application_note/dm00260799-writing-to-nonvolatile-memory-without-disrupting-code-execution-on-microcontrollers-of-the-stm32l0-and-stm32l1-series-stmicroelectronics.pdf).

Engineering requirements for that prototype:

- Store sequence, count, confidence/fault state, format version, integrity check and a separately written commit indication. Retain the previous valid record until the successor is verified and committed.
- Rotate the commit indication as well as the count. A fixed head pointer or confidence word could otherwise become the endurance bottleneck.
- Use aligned writes, explicit busy/error checks and readback. Treat a torn write as unsuccessful; do not assume a 32-bit CPU store is a power-fail-atomic EEPROM transaction.
- Advance persistence in bounded steps while draining captured inputs. Eight dirty-word replacements alone can exceed the present queue's approximately 63 ms capacity; copying the current blocking FRAM routine is unsafe.
- Define the retained value as the last successful commit. Delaying writes to reduce wear enlarges the window in which a counted press can be lost on battery removal.
- Model interrupted invalidation, payload and commit writes; sequence wrap; all-invalid records; marker recovery; and repeated brownouts. Actual ECC/error handling and supply-failure behavior still need hardware tests.

Illustrative capacity arithmetic, not a device-life promise: a 3 KiB bank holds 96 records of 32 bytes. Budgeting two rated cycles at the most-used word per slot reuse gives `96 × 100,000 / 2 = 4.8 million` commits. The final format must measure its actual per-word wear, retries and reset traffic; temperature, retention and the product's click-rate target remain separate constraints. External FRAM is an alternative if that budget proves insufficient, at additional BOM and bus cost.

### First flash, updates and recovery are different operations

For a blank candidate board, enter ROM DFU with hardware BOOT0/reset, flash the application, verify it, return BOOT0 low and reset. Factory initialization may create an initial zero journal. For an existing counter, first back up EEPROM, program only the application region, verify it and compare the saved count region before resuming. Do not make mass erase, protection changes or factory initialization part of the ordinary update path. Interrupted application updates should remain recoverable through hardware ROM entry; preserving the count requires a tested updater and memory-range policy.

ST provides STM32CubeProgrammer with USB DFU and Mac support. Current UM2237 lists macOS 15/26 and x86_64/ARM-aarch64; this is documented platform support, not a completed test on the user's Mac. ST's current product FAQ distinguishes development use from production programming and directs production users to programming partners, so the manufacturing workflow requires its own tool selection. [STM32CubeProgrammer interfaces and FAQ](https://www.st.com/content/st_com/en/stm32cubeprogrammer.html), [UM2237](https://www.st.com/resource/en/user_manual/um2237-stm32cubeprogrammer-software-description-stmicroelectronics.pdf).

## What retaining MSP430 preserves

FR4133 has 15 KiB program FRAM, 512 bytes information FRAM, 2 KiB RAM and specified 10^15 read/write endurance. Those characteristics suit frequent count commits. It has SBW and UART BSL, not native USB. [TI FR4133 datasheet, §§8.12.9, 9.4 and 9.6](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf).

Q3's existing fixture contacts are TP1 ground, TP2 target-voltage sense, TP3 SBWTDIO/reset and TP4 SBWTCK. A shared external programmer avoids redesign. It must match the real 3.0 V target; do not backfeed the regulator output. A fixed 3.3 V LaunchPad probe is not automatically compatible. An inexpensive probe's Mac support and voltage behavior need an actual trial before purchase recommendation.

Current updates must preserve `0x1800–0x19FF`, including count journal and gap marker. The factory initializer deliberately clears their first 34 bytes. Adding a USB-UART bridge also conflicts with Q3's buttons on the FR4133 BSL pins, and a wrong BSL password can erase information FRAM. See the completed [22 September firmware review](review-Q3-2026-09-22-firmware.md) for the primary references and preservation procedure.

## ESP32-C3: easy USB, less attractive counter fit

The C3's native USB Serial/JTAG controller is fixed-function hardware, not a general USB DFU peripheral. GPIO19 is D+, GPIO18 is D−. It supports flashing without a bridge and automatic download entry; if firmware disables the controller or changes its pins, recover with GPIO9 low and reset. Deep sleep disconnects USB. [Espressif USB Serial/JTAG guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-guides/usb-serial-jtag-console.html).

Provide a manual recovery path: **GPIO9 low, GPIO8 high, then pulse EN/CHIP_PU low and release**. Respect the remaining strap requirements; do not burn download-disabling security fuses during this study. [Espressif boot selection](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/advanced-topics/boot-mode-selection.html).

The current MINI-1 datasheet covers a 3.0–3.6 V supply and specifies a source capable of at least 0.5 A. Its radio-clock-gated CPU-running example is 17 mA at 80 MHz; deep sleep is 5 µA typical. Those are component conditions, not measured counter runtime. Module flash specifications include 100,000 program/erase cycles minimum, 5 ms maximum page programming and **500 ms maximum 4 KiB-sector erase**. The module includes its oscillator. [Espressif MINI-1 datasheet v2.2, §§1, 6.2 and 6.4–6.5](https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf).

This is a larger supply redesign than simply changing the MCU. A radio-disabled application still needs measured startup, flash-write and wake currents on the small cell. Deep sleep also turns first-button wake into a boot-path problem that must preserve the first press and held-key semantics.

NVS provides append-based wear leveling and recovery, but its documentation identifies unstable-power erase failures that can exhaust available pages. Use one encoded counter-state record and explicit commit; never respond to an NVS initialization error by automatically erasing the user's counter partition. Preserve that partition during application updates and test power cuts during garbage collection. [Espressif NVS, robustness, unstable-power and log sections](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/storage/nvs_flash.html).

Espressif documents both Python installation and native macOS x86_64/arm64 esptool binaries. Initial flashing installs the second-stage bootloader, partition table and application; subsequent application updates should leave NVS untouched. [esptool installation](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/installation.html).

## Port scope and qualification gates

The existing portable debounce, queue and OLED state machines are useful starting points. A STM32 port replaces startup/linker configuration, interrupt capture, timebase, sleep/wake, GPIO/I²C, watchdog, nonvolatile storage and build/flash scripts. It must requalify clock tolerance and display guards; a faster CPU does not preserve timing automatically. ESP-IDF adds its task/flash/sleep integration to the same work. Neither target has a completed production port in this study.

Relevant L072 errata include clock-enable delays, wake-up behavior by silicon revision, dual-bank-boot interrupt masking, and USB's minimum 10 MHz APB clock. Record the actual revision, use ordinary bank-1 boot, and audit the selected peripheral modes against ES0292 before bring-up. ROM availability does not prove that every cable, power transition or host will enumerate successfully. [ES0292 Rev 8](https://www.st.com/resource/en/errata_sheet/es0292-stm32l07xxxl08xxx-device-errata-stmicroelectronics.pdf).

The existing Q3 deterministic tests validate only their stated production-code model. A new EEPROM journal model can attack write ordering and scheduling; it cannot simulate the complete board, prove EEPROM/ECC behavior, USB analog compliance, cell capacity, regulator transients, OLED compatibility or charging safety. Required physical tests include blank-part Mac flashing, recovery after an interrupted update, EEPROM preservation, rapid presses during commits, first/held wake, real power cuts, battery extremes and display current/timing.

**Decision boundary:** favor L072CBT6 if cable-only home flashing is worth a new revision and port. Keep MSP430 plus a qualified shared fixture if minimizing new engineering is more important. ATtiny3226-SU remains a separate low-cost UPDI option in the stock/hardware comparison; it does not itself provide native USB flashing.
