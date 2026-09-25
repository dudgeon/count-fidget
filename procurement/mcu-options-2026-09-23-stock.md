# MCU options — fresh stock and component costs, 23 September 2026

## Result

**STM32L072CBT6 is a credible stocked candidate for the low-power USB-programming study.** Its public JLC page explicitly shows **2,211 orderable units**, minimum 1, at **$2.7916 each for ten**. LCSC independently shows 1,329 ready to ship. This resolves the earlier small-package stock concern without assuming that STM32L072KBU6 or KZU6 can supply the batch.

There are four useful paths to compare: keep the current MSP430; investigate STM32L072CBT6 for USB programming; consider the stocked ESP32-C3 module if its broader power/design changes are acceptable; or investigate ATtiny3226-SU with an external UPDI programmer. **No MCU is selected or changed by this stock report.** Final circuitry, application/update behavior and retention suitability require the separate MCU engineering review. Existing Q3 engineering gaps and the procurement pause remain in force.

The independent firmware review confirms **STM32L072CBT6 has factory ROM USB DFU**: [ST DS10689 §3.9](https://www.st.com/resource/en/datasheet/stm32l072cb.pdf) and [AN2606, STM32L07/L08 bootloader](https://www.st.com/resource/en/application_note/an2606-introduction-to-system-memory-boot-mode-on-stm32-mcus-stmicroelectronics.pdf). LQFP48 provides PA11/USB_DM on pin 32, PA12/USB_DP on pin 33 and separate VDD_USB on pin 36. USB requires a compliant 3.0–3.6 V supply; the current nominal 3.0 V rail cannot guarantee the lower bound. Supply topology and sequencing need design review; the additional regulator could power all MCU domains together while retaining the OLED's 3.0 V rail, rather than requiring an independently powered USB domain. Factory USB capability is therefore established; a functioning replacement board and safe update/retention procedure are not.

## Fresh public catalog observations

Native Chrome pages were read at **11:07–11:09 UTC on 23 September 2026**. Counts below are explicit **Available Order Qty**, not search snippets or total-stock numbers. Each main option had enough for ten boards plus an illustrative five-piece allowance; actual assembly attrition must be established later. All prices are **USD, parts only**.

| Path / exact MPN | Catalog and package | Total stock / available | Minimum | Unit price at 1 | Unit price at 10 | Ten MCUs, no attrition |
|---|---|---:|---:|---:|---:|---:|
| Current design — MSP430FR4133IG48R | [C2053877](https://jlcpcb.com/partdetail/C2053877), TSSOP48 | 23 / **23** | 1 | $4.1663 | $3.5334 | $35.334 |
| Leading USB study — STM32L072CBT6 | [C465977](https://jlcpcb.com/partdetail/C465977), LQFP48 7×7 mm | 3,113 / **2,211** | 1 | $3.3268 | $2.7916 | $27.916 |
| USB/radio module study — ESP32-C3-MINI-1-H4X | [C41349510](https://jlcpcb.com/partdetail/C41349510), 16.6×13.2 mm module | 1,979 / **1,840** | 1 | $2.9153 | $2.5883 | $25.883 |
| External-programmer study — ATTINY3226-SU | [C3234898](https://jlcpcb.com/partdetail/C3234898), SOIC20 300 mil | 52 / **44** | 1 | $2.9299 | $2.4907 | $24.907 |

For the leading STM32 candidate, [LCSC C465977](https://www.lcsc.com/product-detail/C465977.html) separately showed **1,329 in stock, ships now**, minimum/multiple 1, $3.3514 at one and $2.8122 at ten (11:08:23 UTC). This is independent distributor inventory; it must not be added to JLC's count or treated as reserved stock.

The STM32's **MCU-only difference is $7.418 less per ten boards** than the MSP430. The module and ATtiny differences are $9.451 and $10.427 less, respectively. These small differences exclude programmer/fixture costs, USB support circuitry, persistent-memory changes, power changes, assembly charges, firmware work and qualification. They do not establish that a redesigned complete device is cheaper. Native USB convenience may be more material than the component saving.

## Candidate support components

Fresh JLC observation at **11:12:34 UTC on 23 September**:

| Proposed part | Package | Total stock / Available Order Qty | Minimum | Unit at 1 | Unit at 10 |
|---|---|---:|---:|---:|---:|
| [TPS7A0233PDBVR / C2887324](https://jlcpcb.com/partdetail/C2887324), 3.3 V regulator | SOT-23-5 | 8,897 / **8,852** | 1 | $0.5613 | $0.4751 |

This is a **candidate additional supply component**, not a frozen circuit selection or Q3 BOM change. Ten regulators add **$4.751** in parts before attrition. Combining only the STM32 CBT6 and this regulator gives **$32.667 per ten sets**, versus $35.334 for ten current MSP430s: just **$2.667 lower** before required capacitors, supply sequencing/isolation, extra feeder/assembly costs or redesign work. This arithmetic is not a complete revised BOM or a claimed saving. Final supply topology, dropout, start/stop sequencing and rail behavior remain engineering work.

## Ordering identities and alternatives

- **ATtiny suffix:** Microchip's [official ordering table](https://onlinedocs.microchip.com/oxy/GUID-ACE76F82-8072-410B-AFA7-16B2BF7B4CBA-en-US-8/GUID-E3986A10-C6AA-428F-8A32-963AA16EAFDD.html) lists **ATTINY3226-SU** and **-SF** for SOIC20; it does not list the suggested **-SN**. This report prices the explicitly different, valid **-SU** ordering code. Its 32 KiB flash, 3 KiB RAM and 256-byte EEPROM are documented by [Microchip](https://onlinedocs.microchip.com/oxy/GUID-ACE76F82-8072-410B-AFA7-16B2BF7B4CBA-en-US-8/GUID-EAE59C90-03CE-49C3-870E-6EFF5910201D.html). EEPROM is not a direct substitute for the existing FRAM retention implementation.
- **ESP module suffix:** the current [Espressif module datasheet v2.2](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.html) marks **ESP32-C3-MINI-1-N4** not recommended for new designs and identifies **-H4X** as recommended. The priced exact part is **-H4X**; this report makes no inventory claim for unqueried **-N4** or **-F4**. Its module dimensions and antenna provisions differ substantially from the current MCU footprint.
- **Larger-flash STM32 fallback:** [STM32L072CZT6 / C1337587](https://jlcpcb.com/partdetail/C1337587), LQFP48 7×7 mm, showed stock/available **45/45**, minimum 1, $5.8679 at one and **$5.0415 at ten**. It is an available fallback within the L072 study, but offers no component-price advantage over the 128 KiB CBT6.

## Poor-stock or unverified candidates

| Exact MPN | Fresh JLC result | Decision for this study |
|---|---|---|
| [STM32L072KBU6 / C2927347](https://jlcpcb.com/partdetail/C2927347) | Stock 4, **available 3**, minimum 1; $3.8930 at one / $3.7937 at ten | Insufficient even before attrition. A displayed ten-piece price does not mean ten are orderable. |
| [STM32L072KZU6 / C1340191](https://jlcpcb.com/partdetail/C1340191) | Stock 0, minimum 1, **Pre-order**, no Available Order Qty | No immediate batch-stock evidence. $10.0016 is only an estimated preorder unit price. |
| [STM32L432KBU6 / C94784](https://jlcpcb.com/partdetail/C94784) | Stock 3, minimum 2, **Pre-order**, no Available Order Qty | No immediate batch-stock evidence. $5.6157 is only an estimated preorder unit price. |
| STM32L072KZT6 | [ST lists the active LQFP32 ordering code](https://www.st.com/en/microcontrollers-microprocessors/stm32l072kz.html), but exact JLC/LCSC stock was not verified | Do not infer nonexistence or availability. The stocked CBT6 makes further variant hunting unnecessary for this bounded comparison. |

No L082 search was needed after identifying two adequately stocked L072 choices. Cached search counts were used only to locate exact catalog identities, then replaced by the fresh native readings above. Prices are volatile and quantities are unallocated.

## Scope and evidence

The companion [machine-readable record](mcu-options-2026-09-23-stock.json) contains eight MCU JLC observations, one candidate regulator observation, the LCSC cross-check, timestamps, quantity/minimum distinctions, ordering-source links and calculated component-only differences.

No quote forms, carts, private parts libraries or existing drafts were touched. No vendor messages, reservations, paid sourcing, purchases, manufacturing release or Q3 design/artifact edits occurred. Catalog availability alone does not approve a new circuit, USB boot workflow, power budget, persistence scheme or either assembler's acceptance of a revised board.
