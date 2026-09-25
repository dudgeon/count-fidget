# Q3 passive sourcing alternatives — 15 September 2026

These are exact nominal-equivalent candidates, not substitutions already applied. The current model uses **GRM21BR71E225KA73L** at C1/C3/C5; it does not use the guessed 16 V part. Firmware and engineering files were not changed by this research.

## Live follow-up and selection

The parent subsequently checked the native JLC bulk BOM on15September: **C25819 2,444,046; C23352 1,132,835; C22783 109,076; C22979 371,398; C2828649 4,538; C77081 115,774; C602037 352,428**. Each one-per-board line for10units recommended20pieces. The parent selected **C25819/C23352/C22783, R9 C22979, C1/C3/C5 C77081 and C17–19 C602037** and owns the engineering substitutions. The actual combined BOM quantities/attrition must still be confirmed. No purchase or reservation occurred. The selected active Samsung successor avoids the NRND alternative below; its effective-capacitance and1.45mm maximum-height gates remain.

## Initial recommendation and indexed evidence

Use the three UNI-ROYAL values below if the live JLC BOM confirms availability. R9 also has a matching UNI-ROYAL option and a tighter Viking option. Consolidate C1/C3/C5 onto the existing C22 Murata part if its live allocation and effective capacitance qualify. For C17–19, compare the existing 43-piece Murata lot with Samsung's Basic alternative: the latter avoids the large minimum but is NRND. Its active successor is a candidate only after stock and fit checks.

| References | Exact candidate / JLC code | Required properties preserved | Evidence available here |
|---|---|---|---|
| R16/R23 | 0603WAF4702T5E / **C25819** | 47 kΩ, 0603, 1%, 100 mW, 100 ppm/°C | [JLC Basic SMT identity](https://jlcpcb.com/partdetail/C25819); [LCSC](https://www.lcsc.com/product-detail/_UNI-ROYAL-Uniroyal-Elec-_C25819.html) indexed 897,500, MOQ100, crawl5days |
| R3 | 0603WAF2402T5E / **C23352** | 24 kΩ, same package/tolerance/power/TCR; preserves VSET ratio | [JLC Basic SMT identity](https://jlcpcb.com/partdetail/0603WAF2402T5E/C23352); [LCSC](https://www.lcsc.com/product-detail/Chip-Resistor-Surface-Mount_Uniroyal-Elec-0603WAF2402T5E_C23352.html) indexed282,600, MOQ100, crawl lastmonth |
| R11 | 0603WAF1153T5E / **C22783** | 115 kΩ, 0603, 1%, 100 mW, 100 ppm/°C; preserves thermal calculation envelope | [LCSC](https://www.lcsc.com/zh-TW/product-detail/Chip-Resistor-Surface-Mount_Uniroyal-Elec-0603WAF1153T5E_C22783.html) indexed99,600, MOQ100, crawl lastmonth; live JLC class/allocation pending |
| R9 | 0603WAF330KT5E / **C22979** | 3.3 Ω, 0603, 1%, 100 mW, **200 ppm/°C**, matching baseline low-ohm Yageo | [LCSC](https://www.lcsc.com/es/product-detail/C22979.html) indexed52,700, MOQ100, crawl lastmonth; live JLC pending |
| R9, tighter alternative | Viking ARG03BTC3R30 / **C2828649** | 3.3 Ω, 0603, 100 mW, **0.1%, 25 ppm/°C** | [JLC Extended SMT](https://jlcpcb.com/partdetail/VikingTech-ARG03BTC3R30/C2828649) indexed12,424 stock/12,284 orderable, MOQ1, crawl3months |
| C1/C3/C5 | Murata GRM21BR71E225KE11L / **C77081**, already C22 | 2.2 µF, 25 V, X7R, 10%, 0805 | [JLC Extended SMT identity](https://jlcpcb.com/partdetail/MurataElectronics-GRM21BR71E225KE11L/C77081); [LCSC](https://www.lcsc.com/product-detail/Multilayer-Ceramic-Capacitors-MLCC-SMD-SMT_Murata-Electronics-GRM21BR71E225KE11L_C77081.html) indexed150,000, MOQ20, crawl lastmonth |
| C17–19 | Samsung CL21A226MAQNNNE / **C45783** | 22 µF, 25 V, X5R, 20%, 0805 | [JLC Basic](https://jlcpcb.com/partdetail/C45783) indexed4,982,390 stock/4,323,754 orderable, MOQ1, crawl4days; **NRND** |
| C17–19, active successor | Samsung CL21A226MAYNNNE / **C602037** | Same nominal electrical specification; maximum height1.45 mm | [JLC Extended SMT identity](https://jlcpcb.com/partdetail/631473-CL21A226MAYNNNE/C602037); stock not exposed by extractor |

**Stock caveat:** all index observations were retrieved15September; their crawl ages are shown. They are leads for the live BOM checker, not current reservations. LCSC inventory/MOQ is separate from JLC allocation/assembly attrition. Parts-only prices and availability do not establish either vendor's full quote. The accompanying JSON preserves the parent-reported live shortages and source hashes.

## Electrical qualification

The [ROYALOHM primary thick-film specification](https://www.royalohm.com/assets/pdf/products/smd/1.pdf), printed pp10–12, confirms 0603 dimensions, 100 mW rating, reflow/wave compatibility and **100 ppm above10Ω /200 ppm from1–10Ω**. Keep R11 within the existing ±2.01% resistor envelope. The [Viking ARG primary datasheet](https://www.viking.com.tw/Templates/att/ARG_Series.pdf?lng=en), printed pp1–3, confirms the tighter R9 encoding and range. At30mA a3.3Ω resistor dissipates about3mW; this does not prove protector timing, overload response or OLED transient margins.

Murata's [primary model list](https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/dynamic-model/component-list-d-mlcc-2506.ashx?cvid=20250805040419000000&la=ja-jp) confirms both2.2µF variants' nominal electrical/package data. An exact guaranteed DC-bias minimum was not obtained here: **C1 must retain ≥1µF effective at5V**, and other rails retain their documented minima. Nominal voltage rating alone is insufficient.

Samsung's [CL21A226MAQNNN primary page](https://product.samsungsem.com/mlcc/CL21A226MAQNNN.do) identifies NRND status and provides typical curves. At4V,25°C,120Hz,0.5Vrms, it gives−41.05%, approximately12.97µF each. Multiplying illustratively by0.8 tolerance and0.85 temperature gives8.82µF each/17.64µF pair. The [active successor](https://product.samsungsem.com/mlcc/CL21A226MAYNNN.do) gives−45.92%, approximately11.90µF each, or8.09µF each/16.18µF pair with the same illustrative factors. At5.5V those illustrative per-part values are6.66/5.97µF respectively. These support candidate margin against converter input≥5µF and output pair≥10µF, **not guaranteed minima**: combined bias/temperature, aging, lot spread and physical transients remain unqualified. Do not reduce the two output capacitors.

No purchases, parts reservations, vendor messages or manufacturing release occurred in this subtask.
