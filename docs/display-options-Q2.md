# Display options for a possible Q2 revision

Catalog snapshot: **2026-09-15 02:05 UTC**, with later vendor/audit findings below. This is an evaluation, not a selected replacement or released Q2 design.

Geoff asked whether to replace the display with one easier to work with on both assembly platforms, explaining that the original display choice was arbitrary. Evaluating alternatives is authorized. Eight digits, the present glass dimensions and the earlier 2–4-month charging-interval estimate were implementation assumptions, not independent user requirements. The core product remains a lightweight two-key visible counter with a rechargeable coin cell, USB-C charging, inactivity behavior and retained count.

## Recommendation

Reconsider the DE188 before manufacturing, while preserving a low-power reflective LCD as the preferred direction for the coin-cell design. **No qualified replacement currently solves both platforms.** HS HS91L02W2C01 has the clearest positive catalog-stock evidence in this initial search, but it is not the recommended electrical replacement: its supply/current are unverified for this circuit and its listed current approaches the existing protection cutoff. Catalog availability does not establish order-specific assembly acceptance.

Around **02:15 UTC**, JLCPCB's Mitchell Chen said there was no stocked alternative to the requested LCD; he had suggested paid Global Sourcing preorder for DE188 around **02:07 UTC**. The original request specified eight digits/about 35 × 13 mm, so this is not proof that every other numeric LCD is unavailable. Paid preorder is not authorized. Both vendors have been asked about sourcing, but neither has approved a replacement for this project.

| Candidate | Official-source evidence | Assessment |
|---|---|---|
| **HS HS91L02W2C01**, 0.91-inch 128 × 32 OLED, **C5248081** | [LCSC product page](https://www.lcsc.com/product-detail/C5248081.html) reported **3,107 in stock**, MOQ 1, about **$2.26 single / $1.87 each at ten**. [LCSC dimensional listing](https://item.szlcsc.com/5960632.html) gives **38 × 12 mm**, four-pin I²C. [JLCPCB listing](https://jlcpcb.com/partdetail/Hs-HS91L02W2C01/C5248081) identifies wave soldering and **high assembly difficulty**. | Positive stock lead, with significant power/assembly uncertainty. Requires a different footprint, firmware driver and power review. JLC's opened page did not expose current inventory. |
| **Sharp LS011B7DH03**, 1.08-inch memory LCD, **C9900140463** | [Sharp catalog, printed page 4](https://global.sharp/products/device/catalog/pdf/sharp_device202109_e.pdf) gives **32 × 14 × 0.745 mm**, 160 × 68 pixels, **25 µW typical** under catalog conditions, maximum mass **0.73 g**. [JLCPCB listing](https://jlcpcb.com/partdetail/Sharp-LS011B7DH03/C9900140463) shows **stock 0**, high assembly difficulty, a required fixture, and displayed minimum 445. | Attractive size and low-power direction, but no present easy-sourcing advantage. Needs serial-display wiring/firmware and FPC attachment review. |
| **Varitronix VIM-878-DP-RC-S-LV**, segmented LCD, **C17231725** | [JLCPCB listing](https://jlcpcb.com/partdetail/18360830-VIM_878_DP_RC_SLV/C17231725) shows **stock 0**, wave soldering and a required fixture. | A segmented-LCD alternative, but its catalog record provides no demonstrated procurement improvement. Compatibility, dimensions and drive configuration would require exact-part review before considering a design change. |

The observations above came from official pages through web retrieval, which may serve indexed/cached content. The HS LCSC result was marked crawled the previous day; JLC pages had differing crawl ages. These are **not live stock reservations or supplier commitments**. Prices are component-only catalog indications, excluding assembly, fixtures, freight, tax and other scope. Disregard search-snippet inventory when the opened page does not verify it.

## Broader passive-display search

Relaxing the assumed digit count produces a credible smaller lead: **Lumex LCD-S401M16KR / C17355221**, four reflective digits, 20.32 × 10.16 × 2.8 mm. Its [manufacturer drawing](https://www.lumex.com/datasheet/files/LCD-S401M16KR.pdf) specifies 3 V AC, 1/4 duty, 1/3 bias, with 12 pins. This could use the same MCU LCD-controller approach after changing wiring, footprint and segment mapping. Optical response remains unverified; four digits would require a count-presentation decision.

[DigiKey's opened listing](https://www.digikey.com/en/products/detail/lumex-opto-components-inc/LCD-S401M16KR/7364561) reports 6,108 units, quantity 1 available, $2.07 single/$1.484 at ten, component-only, indexed the prior day. [JLCPCB's listing](https://jlcpcb.com/partdetail/Lumex-LCDS401M16KR/C17355221) confirms wave soldering but exposes no inventory figure; [LCSC](https://www.lcsc.com/product-image/C17355221.html) reports zero. It is a plausible external-distributor sourcing lead for PCBWay, subject to acceptance, **not a verified stocked solution on both platforms**.

[NXP AN12579, §4](https://www.nxp.com/docs/en/application-note/AN12579.pdf) demonstrates this LCD active in a development-board configuration drawing 7 µA. That supports the low-power direction; it is not a Q1 current/runtime prediction. Five-digit VIM-516-DP-RC-S-LV / C17460562 and six-digit VI-602-DP-FC-S / C17366023 also showed no positive JLC inventory evidence in this broader search: [five-digit listing](https://jlcpcb.com/partdetail/18589755-VIM_516_DP_RC_SLV/C17460562), [six-digit listing](https://jlcpcb.com/partdetail/18495193-VI_602_DP_FCS/C17366023).

Current recommendation: obtain the existing DE188 sourcing price/lead-time and compare it with a qualified low-power alternative before changing the design solely for catalog availability. Do not pay a preorder to discover whether the complete build can be quoted. No smaller candidate resolves the battery/test exclusions by itself.

## OLED power uncertainty

The [HS manufacturer datasheet hosted by LCSC](https://datasheet.lcsc.com/lcsc/2504101957_HS-HS91L02W2C01_C5248081.pdf) gives **23 mA typical / 29 mA maximum** internal-converter input current under **Note 8**. The electrical table was retrieved, but Note 8's display pattern was not. Do not describe these figures as measured application current or verified full-screen current.

For scale only, **if battery draw were a steady 23 mA**, ideal capacity arithmetic gives 45 mAh ÷ 23 mA ≈ **2 active hours**, before losses or the rest of the circuit. The datasheet figure is not a battery measurement. Sparse numerals and reduced brightness may draw less; converter behavior, idle leakage and actual usage also matter. No revised runtime is established.

The independent [protection review](review-protection-Q2.md) calculates a nominal discharge trip near **30 mA** from Q1's 3.3 Ω sense resistor and FETs. This OLED example plus the rest of the system could approach or trigger it. A replacement requires a full battery-current and protection review, not simply an added connector or driver.

The same retrieved table specifies **1.65–3.3 V for logic** and **3.5–4.2 V for the internal converter input**. These are glass-level rails, not a verified specification for the finished four-pin module's supply terminal. Guaranteed module operation from Q1's existing **3.0 V rail is unverified**. Obtain the exact module schematic/supply limits and review the required power circuit before selection.

## Required next evidence and change scope

1. Ask both vendors to confirm the exact candidate's available assembly quantity, sourcing/MOQ/lead time, mounting method and fixture/assembly charge. Obtain its guaranteed module supply specification. [PCBWay's turnkey service](https://www.pcbway.com/pcb-assembly.html) sources through external authorized distributors, so it need not use JLC's inventory.
2. Compare numeric readability/response, current, mass and mechanical support against the product's actual needs. Do not preserve eight digits or a speculative runtime at the expense of a better practical design without explaining the tradeoff.
3. If a replacement is selected, make a controlled revision of wiring/footprint, display firmware, sleep/current behavior, enclosure support, manufacturing files and relevant verification. Preserve retained-count behavior and validate the physical first article.

**Submitted Q1 remains unchanged and on engineering hold.** Existing uploaded Gerbers, BOMs and firmware still describe the DE188-based Q1 prototype. A separate 32 Hz LCD firmware candidate now exists; no replacement has been chosen, no board rerouted and no manufacturing files superseded. The battery/harness, charging/thermal/protection, schematic/ERC, hardware, fit, runtime and other documented engineering gaps remain open. Evaluation and quotations authorize neither spending nor manufacturing release.
