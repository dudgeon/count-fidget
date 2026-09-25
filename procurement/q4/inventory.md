# Q4 inventory research — 24 September 2026

**All 70 fitted positions / 38 exact types in the bound Q4 model pass the ten-board inventory screen.** The machine-readable [stock record](stock.json) contains 64 JLC exact-code observations from fresh, read-only Chrome views of JLCPCB's public catalog, between 24 September 23:36 and 25 September 00:17 UTC, plus a separate fresh LCSC retail check at 00:20 UTC. These are displayed orderable quantities, not reserved stock or vendor acceptance of a board, footprint or assembly process.

The user has paused all vendor contact and quotation activity. No quote form, cart, private parts library, paid sourcing, order or vendor message was changed during this research. No money or manufacture is authorized. Previous Q1–Q3 records remain historical.

## Main candidates and retained critical parts

Parts-only USD prices exclude board fabrication, assembly, feeder charges, attrition, shipping, tax, testing and programming. “At 10” reports the applicable displayed price tier; it does not override the available quantity. Each timestamp and source is in the JSON.

| Exact MPN / catalog source | Available / minimum | USD each at 1 / 10 | Engineering and sourcing status |
|---|---:|---:|---|
| [STM32L072CBT6 / C465977](https://jlcpcb.com/partdetail/C465977) | 2,160 / 1 | 3.3218 / 2.7874 | Selected MCU; LQFP-48, factory USB bootloader facts are separately reviewed. |
| [HS96L01W4S03 / C5139758](https://jlcpcb.com/partdetail/C5139758) | 524 / 1 | 2.2968 / 1.8274 | Selected seven-pin SPI OLED module, currently home-fitted. Catalog says Wave Soldering and High Assembly Difficulty. |
| [TLV76701DRVR / C2863998](https://jlcpcb.com/partdetail/C2863998) | 12,740 / 1 | 0.2676 / 0.2676 | Selected precision adjustable LDO with 150k/49.9k divider; board transient qualification remains open. |
| [TPS7A2401DBVR / C2693328](https://jlcpcb.com/partdetail/C2693328) | 4,915 / 1 | 0.2687 / 0.2687 | Earlier 3.15 V candidate, superseded by TLV76701DRVR after the rail corner review. |
| [TPS7A0331PDBVR / C3748940](https://jlcpcb.com/partdetail/C3748940) | 159 / 1 | 0.4614 / 0.3688 | Exact TI part is 3.1 V despite JLC's incorrect 3.3 V attribute. Fixed-rail USB margin and module capacitance make this a reviewed alternative, not an automatic selection. |
| [TPS22917DBVR / C2681320](https://jlcpcb.com/partdetail/C2681320) | 15,133 / 1 | 0.3538 / 0.3538 | Selected controlled-slew load switch. Its reverse blocking specification is not an ideal-diode guarantee. |
| [FM25CL64B-GTR / C9830](https://jlcpcb.com/partdetail/C9830) | 2,888 / 1 | 3.6174 / 3.2308 | Unselected 8 KiB SPI FRAM alternative. Power rise/fall conditions still require an engineering solution. |
| [FM25V02A-GTR / C66029](https://jlcpcb.com/partdetail/C66029) | 19,137 / 1 | 3.8773 / 3.4907 | Selected 32 KiB SPI FRAM with controlled power ramps and sleep mode; physical ramp limits remain open. |
| [USB4105-GF-A-120 / C5184243](https://jlcpcb.com/partdetail/C5184243) | 4,360 / 1 | 0.9129 / 0.7180 | Selected 1.20 mm stake option. Planar drawing comparison passed; actual board thickness, protrusion, fillets and retention remain first-article checks. High Assembly Difficulty. |
| [DMN2056U-13 / C5208862](https://jlcpcb.com/partdetail/C5208862) | 189 / 1 | 0.1487 / 0.1487 | Selected alternate reel ordering of the same Diodes transistor family; circuit qualification remains governed by the hardware review. |
| [0603WAF1622T5E / C22885](https://jlcpcb.com/partdetail/C22885) | 89,774 / 1 | 0.0014 / 0.0014 | 16.2 kΩ, 1%, 0603, 100 mW, ±100 ppm/°C selected for R13. Preserve thermal error budget. |
| [TLV7012DGKR / C2859969](https://jlcpcb.com/partdetail/C2859969) | 21 / 1 | 1.1712 / 0.9730 | Retained comparator has the narrowest stock cushion. Ten plus two screening spares fits; allocation is unreserved. |
| [BQ25185DLHR / C19725033](https://jlcpcb.com/partdetail/C19725033) | 4,043 / 1 | 1.7283 / 1.4652 | Retained charger. |
| [BQ29700DSER / C183096](https://jlcpcb.com/partdetail/C183096) | 2,499 / 1 | 0.6595 / 0.5166 | Retained protector. |
| [CPG151101D13 / C49234235](https://jlcpcb.com/partdetail/C49234235) | 13,808 / 1 | 0.1068 / 0.1068 | Retained exact key switch; two per board. |

Every fitted identity, reference group and assembly role is bound by the canonical `fitted_identity_sha256` in the JSON. The removed R34/R35/C37 are excluded; H3/H4 are non-purchased PCB features. The full-model binding was refreshed after final placement/routing freeze; its current SHA is recorded in `screening_plan.final_model_sha256`. Refresh it after any model change. These are the same saved catalog observations, not a new live stock check. Researched alternatives remain separately marked and are not silently included in the selected BOM. The separate display header is screened as stacked hardware, not a second native component footprint.

## Source details and qualification boundaries

- **OLED:** The [manufacturer document linked by LCSC](https://datasheet.lcsc.com/datasheet/pdf/c5dd235441558974950f13e140069537.pdf?productCode=C5139758) is internally inconsistent: prose says 26 × 26 × 2.62 mm and SSD1306, but its page-6 HS96L01xxx03 mechanical drawing (revision A1, 6 July 2019) says **27.30 × 27.80 mm PCB and SSD1315**. Use the drawing for the engineering envelope and retain the source conflict as a qualification gate. It gives 23.30 × 23.80 mm mounting-hole spacing, Ø2.50 mm holes, PCB thickness 1.20 mm, approximately 1.40 mm above and 1.00 mm below (approximately 3.60 mm total), and a 7 × 2.54 mm terminal row 1.50 mm from the top edge (the 1.32 mm dimension is a horizontal LCD inset). Horizontal centering of this row is a nominal inference, not an explicitly dimensioned first-pin offset. The 128 × 64 active area is 21.74 × 10.86 mm, with its lower edge 10.57 mm above the module PCB bottom: its center is 2.10 mm above the module center. These dimensions were corrected after reviewing the drawing upright. Its seven terminals are GND, VCC, SCL, SDA, RES, DC, CS. The freshly viewed JLC rear photograph is explicitly labelled HS96L01W4S03 and shows seven bare plated holes and four corner mounts, consistent with the broad drawing layout. The photograph cannot establish exact dimensions or whether a loose header is included; no fitted header is shown. SCL/SDA are the module's SPI clock/data naming here. Page 8 provides connection/strap information rather than a complete internal schematic. The document's module supply, panel supply and logic tables must be reconciled by the circuit review; do not infer that a catalog “3–5 V” entry proves low-end supply operation or that the maximum all-on current predicts sparse-counter consumption.
- **LDO and switch:** Primary TI datasheets are [TPS7A24](https://www.ti.com/lit/ds/symlink/tps7a24.pdf), [TPS7A03](https://www.ti.com/lit/ds/symlink/tps7a03.pdf), and [TPS22917](https://www.ti.com/lit/ds/symlink/tps22917.pdf). The [exact TPS7A0331 ordering page](https://www.ti.com/product/TPS7A03/part-details/TPS7A0331PDBVR) controls the output identity, not the catalog's inconsistent parameter. No exact stocked TPS7A0332 or TPS7A03315 variant was established.
- **FRAM:** [FM25CL64B primary datasheet](https://www.infineon.com/assets/row/public/documents/10/49/infineon-fm25cl64b-64-kbit-8-k-8-serial-spi-f-ram-datasheet-en.pdf) requires at least 30 µs/V rise and fall time at any point. [FM25V02A primary datasheet](https://www.infineon.com/assets/row/public/documents/10/49/infineon-fm25v02a-256-kbit-32k-8-serial-spi-f-ram-datasheet-en.pdf) requires 50 µs/V rise and 100 µs/V fall. These conditions, brownout write inhibition, startup access guards and board-level faults matter more than headline endurance. Catalog inventory alone does not qualify either memory.
- **USB:** [GCT's USB4105 drawing](https://gct.co/files/drawings/usb4105.pdf) and [family page](https://gct.co/connector/usb4105) control pin/stake geometry. The stocked [USB4105-GF-A-060 / C3025063](https://jlcpcb.com/partdetail/C3025063) alternative has 716 orderable, but its shorter stake is not an automatically equivalent assembly choice.
- **FET:** [Diodes' DMN2056U datasheet](https://www.diodes.com/assets/Datasheets/DMN2056U.pdf) controls SOT-23 pin 1 gate / 2 source / 3 drain, low-gate-voltage on-resistance and reel ordering. Preserve the opposing protection body diodes and battery/protection gates when implementing an exact ordering suffix change.

## Negative and insufficient candidates

- NCP170BXV310T2G / C894979: zero stock; preorder minimum 67. Not a current-stock solution.
- FM25CL64B-GTR / C2061806: zero stock / consignment option. This is a separate catalog entry from stocked **C9830**; neither entry's state should be generalized to the other.
- CY15B064Q-SXET / C22442778: one orderable. Its advertised ten-piece price does not make ten available.

## Final screening method

The bound screen groups fitted positions by exact MPN and compares ten boards' requirement plus **max(2, ceiling(10% of fitted quantity))** extra against the catalog's available quantity and minimum order. This is a conservative research allowance, not a vendor-confirmed attrition quantity or a purchase request. All 38 exact fitted types pass this allowance. Refresh shortages, changed identities or quantities and the model hash; all assembly, electrical, battery, USB and mechanical qualification gates remain open as documented by the engineering review.


## Separate header and recovery switch

The exact **XFCN PZ254V-11-07P / C492406** header has 51,053 orderable, minimum one, USD 0.0455 at one or ten. The [manufacturer drawing](https://datasheet.lcsc.com/datasheet/pdf/3b85a1cdf6ed945f2e278f00c1e42442.pdf?productCode=C492406) specifies seven 0.64 mm square pins, 2.54 ±0.05 mm pitch, 15.24 mm terminal span, 17.78 ×2.50 ×2.50 mm insulator, 6.1 ±0.2 mm long ends and 3.0 ±0.2 mm solder ends. It recommends Ø1.02 mm PCB holes. Its function is the physical interposer for DS1's terminal row; account for its height, clipping/fillet process and offboard assembly exactly once. A loose header supplied with the OLED has not been established. Catalog assembly is Wave Soldering; the specific stacked assembly remains unaccepted by either vendor while contact is paused.

The selected **XUNPU TS-1088-AR02016 / C720477** recovery switch has 902,842 orderable, minimum one, USD 0.0537 at one or ten. The [manufacturer drawing](https://datasheet.lcsc.com/datasheet/pdf/0475ac02febf455ca9ddcfb380b0df0d.pdf?productCode=C720477) gives a 3.90 ×3.00 mm body, 5.00 mm lead span, Ø1.80 mm actuator, 2.00 mm height for the 020 suffix, and 0.20 ±0.10 mm travel. It is a two-terminal normally-open SPST: pin 1 left, pin 2 right in top view. Recommended lands are 1.05 ×2.00 mm centered at x=±2.225 mm, y=0. The pinhole and switch actuation fit still need a first-article check.

## Additional regulator screen, 25 September UTC

The bound model now selects [TLV76701DRVR / C2863998](https://jlcpcb.com/partdetail/C2863998), which has **12,740 available**, minimum one, USD 0.2676 at one or ten (fresh 00:12:08 UTC). The [TI datasheet](https://www.ti.com/lit/ds/symlink/tlv767.pdf) controls its adjustable output, accuracy, output capacitance and startup requirements. The selected 150k/49.9k divider and calculated voltage corners are controlled by the power review. Physical transients and sleep consumption remain to be measured. Refresh the fitted-BOM binding after any further selection changes.

[LP5907MFX-3.2/NOPB / C2832238](https://jlcpcb.com/partdetail/C2832238) has 58 available, minimum one, USD 0.5020/one and 0.3996/ten. Its [TI specification](https://www.ti.com/lit/ds/symlink/lp5907.pdf) gives ±2% DC tolerance at the stated input/load conditions; this is not an automatic startup-overshoot guarantee below the OLED logic maximum. [XC6220B321MR-G / C7393027](https://jlcpcb.com/partdetail/C7393027) has 50 available, minimum one, USD 0.9227/one and 0.9015/ten, but the [Torex table](https://product.torexsemi.com/system/files/series/xc6220.pdf) gives its accuracy at 25°C, wider power-save accuracy and only a typical temperature coefficient. Neither was accepted as a fully bounded replacement. Exact TPS7A2032PDBVR / C2877862 has only one available, despite quantity price breaks; it fails the ten-board stock screen.

The selected precision divider also has sufficient fresh stock: [RT0603BRD07150KL / C326734](https://jlcpcb.com/partdetail/C326734) has 14,908 available, minimum one, USD 0.0433 at one or ten; [RT0603BRD0749K9L / C705780](https://jlcpcb.com/partdetail/C705780) has 102,599 available, minimum one, USD 0.0381 at one or ten. Exact [150k Yageo specification](https://yageogroup.com/component-documentation/download/specsheet/RT0603BRD07150KL) and [49.9k Yageo specification](https://yageogroup.com/component-documentation/download/specsheet/RT0603BRD0749K9L) confirm 0603, 0.1%, ±25ppm/°C and 0.1W at 70°C. Their circuit selection is controlled by the Q4 model and power review, not stock alone.

## Current bound assembly split

The updated model contains **86 references: 70 fitted positions and 16 PCB features**, using 38 exact fitted MPNs. Every fitted MPN passes the ten-board plus screening-spares comparison. The model classifies 67 positions for JLC assembly and DS1/SW1/SW2 as three home-fitted through-hole parts. The separate seven-pin interposer is additional hardware. **JLC parts-library inventory is reserved for PCBA and cannot be shipped as loose components**; the separate LCSC retail check below establishes an available loose-parts sourcing path. Availability remains unreserved and shipping/tax totals are unquoted. No paid sourcing, vendor contact, quote update or order has occurred.

The final selected changes in this binding are TLV76701DRVR / C2863998, 150k RT0603BRD07150KL / C326734, 49.9k RT0603BRD0749K9L / C705780, and USB4105-GF-A-120 / C5184243. The USB-120's earlier fresh detail observation gives 4,360 orderable. The -060 alternative remains historical research, rather than the selected assembly. See `docs/review-native-footprints-Q4.md` for its distinct stake-height implication.

## Loose home-assembly parts — fresh LCSC retail check

Read-only public retail pages checked 25 September 2026, 00:20:25–00:20:59 UTC. All three exact identities display **“In stock, ships now”**. No cart, quotation, account, vendor-contact or purchase action was taken. This is separate evidence from JLC's PCBA-only library.

| Exact part | Retail stock | Minimum / multiple | Displayed promotional unit price at 10 | Ten-board screening quantity including spares, rounded to pack |
|---|---:|---:|---:|---:|
| [HS96L01W4S03 / C5139758](https://www.lcsc.com/product-detail/C5139758.html), one display each |526|1 /1|USD 1.6962|12|
| [CPG151101D13 / C49234235](https://www.lcsc.com/product-detail/C49234235.html), two key switches each |13,620|5 /5|USD 0.1021|25 (20 fitted plus five spares after rounding)|
| [PZ254V-11-07P / C492406](https://www.lcsc.com/product-detail/C492406.html), one interposer each |50,550|10 /10|USD 0.0438|20 (10 fitted plus ten after pack rounding)|

The display one-piece promotional price is USD 2.1320. Switches cannot be ordered singly at this listing (minimum five); headers require a ten-pack. The displayed original, pre-discount ten-piece prices are respectively USD 1.8437, 0.1074 and 0.0461. Promotions may change; these are parts-only observations, not fixed totals. The site also displays a 25 September–7 October holiday service-adjustment notice, so “ships now” stock is not a verified dispatch or arrival date.

This resolves the previously unverified **retail availability** of these three home-assembly identities. It does not resolve module source inconsistencies, header/plate fit, solder sequence, user workmanship, battery/harness sourcing or complete delivered-order cost. If a later authorized assembler instead fits DS1 and its header, the same hardware must be counted once and that process must be explicitly agreed; no such change or outreach occurred here.
