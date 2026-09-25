# Q3 stock recheck — 22 September 2026

**Engineering only. Vendor contact and quote submissions are paused.** This check used a new, read-only public catalog browser tab; it did not change either quote, contact suppliers, reserve parts, place preorders or spend money. The Q3 BOM, native design, firmware and frozen RFQ archive remain unchanged.

## Result and recommendation

Fresh public pages checked **23:48–23:58 UTC on 22 September** show explicit JLCPCB **Available Order Qty for 40 of the 43 exact MPNs** in the 70-placement Q3 BOM. Those 40 quantities cover ten boards before assembly attrition. Three pages offer **Pre-order**, with no Available Order Qty. Their total-stock numbers do not establish immediately purchasable assembly inventory.

**Retain the three exact original identities for engineering review.** All three have ample, freshly verified DigiKey stock, so availability does not currently justify a footprint or electrical substitution. This is a credible external sourcing path, **not JLCPCB inventory, allocation, accepted turnkey sourcing or an approved order**. Supplier acceptance and attrition quantities must be resolved after the user resumes procurement. If the requirement becomes exclusively JLC in-house stock, these three remain unresolved; do not silently treat distributor stock as meeting that narrower condition.

The complete 43-part record, per-part timestamps, fitted references, ten-board counts, BOM hash and six external checks are in [stock-recheck-2026-09-22.json](stock-recheck-2026-09-22.json). The historical [15 September snapshot](live-stock-2026-09-15.json) is preserved.

## Three JLC exceptions, with exact-stock alternatives

| References / exact MPN | JLC settled page | LCSC settled page | Exact same part at DigiKey |
|---|---|---|---|
| J1 — USB4105-GF-A | [C3020560](https://jlcpcb.com/partdetail/C3020560): stock 860, minimum 7, **Pre-order; no available-order quantity** | [C3020560](https://www.lcsc.com/product-detail/C3020560.html): **Out of Stock**, minimum/multiple 1 | [USB4105-GF-A](https://www.digikey.com/en/products/detail/gct/USB4105-GF-A/11198441): **129,457**, cut-tape tiers start at 1; checked 23:57:28 UTC |
| Q1/Q2/Q6 — DMN2056U-7 | [C332302](https://jlcpcb.com/partdetail/C332302): stock 5, minimum 160, **Pre-order; no available-order quantity**. Ten boards need 30 before attrition. | [C332302](https://www.lcsc.com/product-detail/C332302.html): **Out of Stock**, minimum/multiple 10 | [DMN2056U-7](https://www.digikey.com/en/products/detail/diodes-incorporated/DMN2056U-7/7352909): **57,542**, cut-tape tiers start at 1; checked 23:58:08 UTC |
| R13 — RC0603FR-0716K2L | [C137790](https://jlcpcb.com/partdetail/C137790): stock 62, minimum 3,112, **Pre-order; no available-order quantity** | [C137790](https://www.lcsc.com/product-detail/C137790.html): **Out of Stock**, minimum/multiple 100 | [RC0603FR-0716K2L](https://www.digikey.com/en/products/detail/yageo/RC0603FR-0716K2L/726967): **262,066**, cut-tape tiers start at 1; checked 23:58:26 UTC |

J1's settled JLC page labels **7 pcs as Recent Order**. That is not evidence of a seven-piece resale offer. Search results for LCSC contained older positive stock numbers, contradicted by the freshly loaded pages; those cached numbers were rejected. No current lead time was promised by either assembler.

Exact identities preserve the existing package/pinout and electrical review: [GCT USB4105 drawing](https://gct.co/files/drawings/usb4105.pdf), [Diodes DMN2056U datasheet](https://www.diodes.com/assets/Datasheets/DMN2056U.pdf), and [Yageo exact R13 specification](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-0716K2L). The Yageo sheet confirms 16.2 kΩ, 1%, 0603, 0.1 W at 70°C and ±100 ppm/°C. No alternate manufacturer's similarly named transistor or changed resistor value was qualified or selected.

## Priority parts still explicitly orderable at JLC

All rows below showed minimum 1. Available Order Qty is the useful planning field; total stock may be larger.

| Exact part | References | Total stock | Available Order Qty | Needed for 10, before attrition |
|---|---|---:|---:|---:|
| [X087-2832TSWIG02-H14 / C18723015](https://jlcpcb.com/partdetail/C18723015) | DS1 | 1,065 | 1,052 | 10 |
| [MSP430FR4133IG48R / C2053877](https://jlcpcb.com/partdetail/C2053877) | U1 | 23 | 23 | 10 |
| [TLV7012DGKR / C2859969](https://jlcpcb.com/partdetail/C2859969) | U5 | 22 | 21 | 10 |
| [TPS63900DSKR / C1518762](https://jlcpcb.com/partdetail/C1518762) | U6 | 19,391 | 19,145 | 10 |
| [CPG151101D13 / C49234235](https://jlcpcb.com/partdetail/C49234235) | SW1/SW2 | 14,141 | 13,928 | 20 |
| [BQ25185DLHR / C19725033](https://jlcpcb.com/partdetail/C19725033) | U2 | 4,248 | 4,161 | 10 |
| [TPS7A0230PDBVR / C3747031](https://jlcpcb.com/partdetail/C3747031) | U3 | 37,689 | 37,631 | 10 |
| [BQ29700DSER / C183096](https://jlcpcb.com/partdetail/C183096) | U4 | 2,607 | 2,552 | 10 |
| [CL21A226MAYNNNE / C602037](https://jlcpcb.com/partdetail/C602037) | C17–C19 | 131,284 | 71,631 | 30 |
| [GRM21BR71E225KE11L / C77081](https://jlcpcb.com/partdetail/C77081) | C1/C3/C5/C22 | 155,395 | 152,310 | 40 |
| [GRM1885C1H472JA01D / C85980](https://jlcpcb.com/partdetail/C85980) | C13 | 3,811 | 2,814 | 10 |

U1 and U5 have the smallest buffers: **23 and 21 available**, respectively. No quantities were allocated. Inventory says nothing about the outstanding OLED/FPC process, effective capacitance, cell/protection, thermal, soldering, mechanical or physical-test acceptance gates.

## MSP430 versus an ESP32

**Keep the MSP430 for this counter.** The present OLED firmware uses 546 bytes of static RAM out of 2 KiB and 5,033 addressed load-image bytes. It runs at nominal 1.048576 MHz, samples the keys with a timer and preserves accepted counts in information FRAM. The original integrated LCD controller is unused with the new OLED; it is no longer a reason to retain this MCU. Low-power operation, FRAM and the already reviewed implementation are the practical reasons. TI specifies 126 µA/MHz typical active current under its stated conditions; that is not measured whole-device runtime. [TI product documentation](https://www.ti.com/product/MSP430FR4133); [current firmware review](../../docs/review-firmware-Q3.md).

“ESP32” is a family. As a concrete comparison, **ESP32-C3** adds Wi-Fi/BLE, up to 160 MHz, 400 KiB SRAM and USB Serial/JTAG. Its recommended supply is 3.0–3.6 V; the existing nominal 3.0 V rail cannot guarantee its 3.0 V minimum after tolerance/droop. The datasheet gives 5 µA typical deep sleep, 17 mA typical 80 MHz modem-sleep with peripheral clocks off, and 335 mA peak for the specified +21 dBm Wi-Fi transmission. These conditions differ from the MSP430 figures and do not predict application battery life. The radio peak also exceeds this design's approximately 30 mA protection target. [Espressif ESP32-C3 v2.4, tables 5-2 and 5-7–5-9](https://documentation.espressif.com/esp32-c3_datasheet_en.html).

An ESP32 change would therefore require new power/protection analysis, PCB/pinout work, a firmware port and a nonvolatile count-retention strategy rather than reusing the present FRAM journal directly. RTC SRAM does not preserve count through loss of battery power. Wireless or USB-data requirements could justify that separate revision; neither is required for the current two-button counter. Today's narrow MSP430 stock buffer deserves monitoring when procurement resumes, but is not evidence that an ESP32 redesign is necessary.
