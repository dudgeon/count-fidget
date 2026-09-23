# Q3 display replacement

15 September 2026. The user explicitly requires a replacement supported by both assemblers. **Retaining the unmatched DE188 is no longer the plan.** The earlier Q2 recommendation failed that requirement. Q1/Q2 submitted artifacts remain historical evidence and on engineering hold.

## Selected engineering candidate

**Wisevision / Newvisio X087-2832TSWIG02-H14, JLCPCB/LCSC C18723015**, white 0.87-inch 128 × 32 OLED, SSD1312, I²C. Engineering selection is distinct from confirmation that both vendors will source and assemble it.

| Requirement | Evidence / current state |
|---|---|
| Exact JLC match and stock | [Exact JLCPCB part](https://jlcpcb.com/partdetail/Newvisio-X087_2832TSWIG02H14/C18723015), live native Chrome at approximately **12:10 UTC**: **1,075 in stock, 1,060 available**, minimum 1, full reel 54. Displayed $1.7543 at 1+, $1.4842 at 10+, before assembly/other charges. No reservation. |
| JLC assembly | Same live page supports Economic and Standard PCBA, classifies **Wave Soldering**, difficulty **High**. Actual FPC process, land pattern and heat limits need clarification; this is not approval of our footprint. |
| PCBWay source | [Exact LCSC source](https://www.lcsc.com/product-detail/C18723015.html). PCBWay accepts recommended distributor sourcing in its [published process](https://www.pcbway.com/pcb_prototype/Electronic_Components.html), but **exact sourcing/FPC assembly acceptance remains pending**. Do not claim full support by both vendors yet. |
| PCBWay fallback email | Exact source, process, pad pattern, heat limits, attrition, lead time and 5/10 charges requested in existing Remi case; Gmail Sent verified **12:11:01 UTC**. Q2 portal IDs W914112AS1N6 / T-1N7W914112A identified; Q1/Q2 engineering holds reiterated. |
| JLC fallback email | Exact FPC process and Wave Soldering classification queried in existing Frank case; Sent verified **12:11:44 UTC**. No duplicate chat. Revised files will use portals. |

## Coordinated changes and gates

The [manufacturer specification](https://atta.szlcsc.com/upload/public/pdf/source/20231103/222F0746A2795BBD5263EDDBD3E1B824.pdf), revision A dated 2022-09-26, defines a 29 × 8.8 × 1.22 mm panel and fourteen soldered FPC contacts: **0.62 mm pitch, 0.32 mm width, 2 mm length**. This is not a generic 0.5 mm connector. Use the controlled drawing for land-pattern and mechanical work; do not substitute it onto DE188 pads.

The OLED needs a separate regulated pump supply, support parts and sequenced firmware. The existing 3 V rail and raw USB-powered SYS cannot directly replace that supply. Converter candidate **TPS63900DSKR / C1518762**: live JLC at approximately12:14UTC showed21,624stock/21,370available, SMT assembly Economic/Standard. Rail voltage/tolerance, current limiting and controller requirements need independent cross-checks. Do not relax battery protection to accommodate display current.

Q3 firmware, power and mechanical work are separate from frozen Q2. Preserve count/reset/FRAM behavior, use bounded I²C transfers and fault recovery, and account for glass/FPC/MCU clearance. Q3 native CAD, reviews, rendering and quote package are not complete at this checkpoint.

The user explicitly requires: **confirm stock → revise design → adversarial agents review → updated rendering image → revised online portal quotes**. During revision, expose cost-driving assumptions. Attempt two layers; four layers are an implementation choice requiring routing/electrical justification, not a functional requirement.

## Selection rationale

Relaxing digit count and dimensions did not establish a stocked passive JLC LCD. That calls for a different display architecture, not retention of DE188. The stocked HS91L02W2C01/C5248081 module was also checked, but its unidentified 662K regulator and conflicting supply descriptions add uncertainty. The selected bare OLED exposes supplies and reset for review; controller/module sequencing and vendor process acceptance still need reconciliation.

Eight digits, previous dimensions and months-long runtime were assumptions. The OLED can show eight digits but needs a revised measured current/runtime budget. Keep existing charger, cell/protection, thermal, FRAM, physical fit and first-article gates. No physical qualification, purchase, paid sourcing or manufacture is claimed or authorized.

## Full PCB inventory checkpoint

Native JLC stock checking on 15 September 2026 at approximately12:40–12:45UTC verified positive inventory for all43 distinct selected PCB MPNs (70 fitted parts per board). See [live records](../procurement/q3/live-stock-2026-09-15.json). Stock is not reserved, and the sample BOM tool quantities are not final Q3 assembly allocations. Exact final BOM/CPL matching follows the checked layout. PCBWay sourcing/FPC acceptance, offboard pack preparation, and complete vendor service prices remain separate unresolved items.
