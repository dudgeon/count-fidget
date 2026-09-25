# Q3 cost and design-intent review

The user asks to expose avoidable cost, starting with the unexplained four-layer PCB. This is a small low-speed counter, not a high-speed data board. Four layers were a compact-layout choice, not a functional requirement. The OLED replaces twenty LCD signal connections with I²C and control signals, making two layers practical. The Q3 native board is now routed on **two copper layers**, with all SMT on the bottom. Fresh checks and independent power-layout review control the final package; routing success does not qualify analog behavior.

| Choice | Why it exists | Q3 action / cost decision |
|---|---|---|
| Four layers | Q1 compact routing and internal ground planes | Two-layer routing implemented. Quote this construction. Do not compare different assembly scopes as a layer saving. |
| Mixed-side SMT | Q1 fit beneath the raised glass and keys | MCU and connectors moved to the bottom, so all SMT can use one reflow pass. OLED/key manual soldering remains vendor scope. Portal assembly-side labels may not map directly to reflow passes; obtain actual pricing. |
| Custom passive LCD sourcing | Arbitrary original display selection, low-power aim | Replace with exact stocked JLC OLED. Compare the complete display circuit and FPC assembly cost, not just the cheaper display price. Runtime must be re-budgeted. |
| External temperature window | Limits charging to the cell's temperature range | Retain. Directly connecting the existing 10k/B3380 sensor to the charger gives about 1.4–60.1°C nominal and may permit charging to about 65°C with tolerances. That does not meet the intended cell range. See the Q3 power review. |
| 48-pin LCD-capable MCU | FRAM persistence plus direct passive-LCD drive | OLED no longer uses the LCD peripheral. A smaller FRAM MCU could reduce area/part cost but needs exact stock, pin mapping and firmware review. Do not silently substitute based on package price alone. |
| ENIG finish and high-Tg FR4 | Fine-pitch assembly assumptions | Ask whether standard material/lead-free HASL are accepted for the actual fine-pitch parts; show any cheaper quote as an explicit process alternative. Do not assume an unqualified finish is interchangeable. |
| Clicky MX switches | Familiar clicky behavior and standard removable caps | Select HanElectricity CPG151101D13 at live JLC $0.107 each (1+), with 14,501 in stock. The old Cherry part is unavailable. Exact lands/plate retention and 220k pull-ups are revised with it. This is a manufacturer change; physical feel and fit remain first-article checks. |
| 1 mm PCB | Low mass | Retain a mechanically supported board; thicker standard stock might cost less but adds mass and changes clip fit. Price only if material to the quote. |
| Custom cell/NTC harness | Rechargeable coin cell, insulation and temperature sensing with no customer soldering | Pack preparation, genuine cell, sensor attachment and keyed plug remain full assembly scope. Compare an existing approved pack only with chemistry, fit and thermal evidence. |
| First-article test/fixture charges | Verify power, charging, protection, retention and assembly | Separate one-time engineering/fixture costs from recurring unit tests. At five/ten units these can dominate the bare-board price. Preserve essential safety/functional tests. |

## Cost consequence of the display replacement

The supported-stock OLED simplifies signal routing, but it **adds power-circuit parts**. Q2 had50fitted PCB references; Q3 has70. The OLED needs its own regulated4V input, power isolation and pump capacitors. Its low module price therefore does not prove a cheaper complete device. Compare the actual component and assembly totals against the layer/reflow savings. A future smaller MCU or display with integrated power support is a separate cost reduction, requiring confirmed supply, electrical review and firmware changes; neither is claimed here.

## Pricing evidence already available

Historical **Q2** portal estimates were incomplete: PCBWay PCB-only $55.93/5 and $81.36/10, plus assembly $88/$102.95 before components and advanced services. JLCPCB PCB-only $32.41/5 and $39.81/10, assembly/components unquoted; its ten-board subtotal included $17.60 ENIG. These are not Q3 prices or a reliable layer-saving comparison.

The concrete Q3 quote must itemize PCB, components, FPC and key soldering, one/two SMT passes, tooling, firmware, test setup versus per-unit work, battery/harness, packaging and delivered costs. Cost options are design decisions to examine, not new user requirements or permission to weaken qualification.

## Implemented stock-driven choices

All 43 distinct fitted PCB MPNs have positive native JLC stock evidence in [the live record](../procurement/q3/live-stock-2026-09-15.json). Several resistors now use equivalent stocked UNI-ROYAL parts; the 2.2 µF capacitors share one stocked Murata identity. The 22 µF OLED power capacitors use Samsung's current CL21A226MAYNNNE, avoiding its NRND predecessor and the original 43-piece minimum. Selected parts still require final PCBA matching and attrition checks. These observations are not stock reservations or complete quotes.

C13 changes from KEMET X7R to Murata GRM1885C1H472JA01D / C85980, retaining 4.7 nF, 50 V, ±5%, 0603 and improving temperature/bias stability with C0G. Live stock was 7,690, available3,183, MOQ1. The [Murata manufacturer list](https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/static-model/component-list-s-mlcc-2506.ashx?cvid=20250805040438000000&la=ja-jp) confirms the family specification. The nominal charger compensation is unchanged; low-current charge-loop stability still needs measurement.
