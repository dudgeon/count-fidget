# Display options for a possible Q2 revision

Research snapshot: **2026-09-15 02:05 UTC**. This is an evaluation, not a selected replacement or released Q2 design.

Geoff asked whether to replace the display with one easier to work with on both assembly platforms, explaining that the original display choice was arbitrary. Evaluating alternatives is authorized. Eight digits, the present glass dimensions and the earlier 2–4-month charging-interval estimate were implementation assumptions, not independent user requirements. The core product remains a lightweight two-key visible counter with a rechargeable coin cell, USB-C charging, inactivity behavior and retained count.

## Recommendation

Reconsider the DE188 before manufacturing. **HS HS91L02W2C01 is the most concrete sourcing candidate found**, but its power supply, current and mounting need confirmation before selection. No verified drop-in alternative presently solves both platforms. Neither vendor has accepted any candidate below for this project, and catalog availability does not establish order-specific assembly acceptance.

| Candidate | Official-source evidence | Assessment |
|---|---|---|
| **HS HS91L02W2C01**, 0.91-inch 128 × 32 OLED, **C5248081** | [LCSC product page](https://www.lcsc.com/product-detail/C5248081.html) reported **3,107 in stock**, MOQ 1, about **$2.26 single / $1.87 each at ten**. [LCSC dimensional listing](https://item.szlcsc.com/5960632.html) gives **38 × 12 mm**, four-pin I²C. [JLCPCB listing](https://jlcpcb.com/partdetail/Hs-HS91L02W2C01/C5248081) identifies wave soldering and **high assembly difficulty**. | Best sourcing lead; compact numeric-display option with a serial interface. Requires a different footprint, firmware driver and power review. JLC's opened page did not expose current inventory. |
| **Sharp LS011B7DH03**, 1.08-inch memory LCD, **C9900140463** | [Sharp catalog, printed page 4](https://global.sharp/products/device/catalog/pdf/sharp_device202109_e.pdf) gives **32 × 14 × 0.745 mm**, 160 × 68 pixels, **25 µW typical** under catalog conditions, maximum mass **0.73 g**. [JLCPCB listing](https://jlcpcb.com/partdetail/Sharp-LS011B7DH03/C9900140463) shows **stock 0**, high assembly difficulty, a required fixture, and displayed minimum 445. | Attractive size and low-power direction, but no present easy-sourcing advantage. Needs serial-display wiring/firmware and FPC attachment review. |
| **Varitronix VIM-878-DP-RC-S-LV**, segmented LCD, **C17231725** | [JLCPCB listing](https://jlcpcb.com/partdetail/18360830-VIM_878_DP_RC_SLV/C17231725) shows **stock 0**, wave soldering and a required fixture. | A segmented-LCD alternative, but its catalog record provides no demonstrated procurement improvement. Compatibility, dimensions and drive configuration would require exact-part review before considering a design change. |

The observations above came from official pages through web retrieval, which may serve indexed/cached content. The HS LCSC result was marked crawled the previous day; JLC pages had differing crawl ages. These are **not live stock reservations or supplier commitments**. Prices are component-only catalog indications, excluding assembly, fixtures, freight, tax and other scope. Disregard search-snippet inventory when the opened page does not verify it.

## OLED power uncertainty

The [HS manufacturer datasheet hosted by LCSC](https://datasheet.lcsc.com/lcsc/2504101957_HS-HS91L02W2C01_C5248081.pdf) gives **23 mA typical / 29 mA maximum** internal-converter input current under **Note 8**. The electrical table was retrieved, but Note 8's display pattern was not. Do not describe these figures as measured application current or verified full-screen current.

For scale only, **if battery draw were a steady 23 mA**, ideal capacity arithmetic gives 45 mAh ÷ 23 mA ≈ **2 active hours**, before losses or the rest of the circuit. The datasheet figure is not a battery measurement. Sparse numerals and reduced brightness may draw less; converter behavior, idle leakage and actual usage also matter. No revised runtime is established.

The same retrieved table specifies **1.65–3.3 V for logic** and **3.5–4.2 V for the internal converter input**. These are glass-level rails, not a verified specification for the finished four-pin module's supply terminal. Guaranteed module operation from Q1's existing **3.0 V rail is unverified**. Obtain the exact module schematic/supply limits and review the required power circuit before selection.

## Required next evidence and change scope

1. Ask both vendors to confirm the exact candidate's available assembly quantity, sourcing/MOQ/lead time, mounting method and fixture/assembly charge. Obtain its guaranteed module supply specification. [PCBWay's turnkey service](https://www.pcbway.com/pcb-assembly.html) sources through external authorized distributors, so it need not use JLC's inventory.
2. Compare numeric readability/response, current, mass and mechanical support against the product's actual needs. Do not preserve eight digits or a speculative runtime at the expense of a better practical design without explaining the tradeoff.
3. If a replacement is selected, make a controlled revision of wiring/footprint, display firmware, sleep/current behavior, enclosure support, manufacturing files and relevant verification. Preserve retained-count behavior and validate the physical first article.

**Q1 remains unchanged.** Existing uploaded Gerbers, BOMs, firmware and quotations still describe the DE188-based Q1 prototype. No replacement has been chosen, no board rerouted and no manufacturing files superseded. The battery/harness, charging/thermal/protection, schematic/ERC, hardware, fit, runtime and other documented engineering gaps remain open. Evaluation and quotations authorize neither spending nor manufacturing release.
