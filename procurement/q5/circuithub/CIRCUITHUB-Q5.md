# Q5 at CircuitHub — feasibility, upload package and cost estimate (26 October 2026)

**Request (owner, 26 Oct 2026):** "see if you can get this pcb made and manufactured at circuithub.com".

**Status:** feasibility checked and upload package prepared. **No CircuitHub account was created or used; nothing was uploaded, quoted, ordered or paid.** CircuitHub quotes only inside a signed-in account (app.circuithub.com). This cloud session cannot sign in, and the agent never asks for or uses the owner's credentials. Placing an order or paying still needs the owner's explicit go-ahead at that moment.

## Bottom line

**Yes, CircuitHub can build Q5 with no change to the board, but not cheaply, and not all parts are available today.**

1. **Design fit:** pass. CircuitHub imports the KiCad 10 project natively, and the board meets its published rules for the low-cost ProtoBoard tier (table below).
2. **Parts:** 36 of the 42 part lines are in stock at Digi-Key, the US distributor CircuitHub buys from most:
   - 14 are the same part numbers as on the JLC first article;
   - 22 are same-footprint equivalents for LCSC house brands or Digi-Key stock-outs.

   The other six lines need handling:
   - **U3** (TLV76701 3.2 V regulator) and **U5** (TLV7012 comparator) are out of stock at Digi-Key. Restock is expected 19–23 Nov 2026.
   - **BT1**, **SW1/SW2** and **SW3** are LCSC-only. CircuitHub would buy them from LCSC as a "not preferred" custom source, or the owner consigns them.
   - **DS1** (display) is left for home soldering, 14 joints, as in JLC variant A.
3. **Cost (estimate):** about **$1,070–1,250 for 5 boards before shipping** ($214–249 a board), against $298.08 all-in for 5 at JLC. CircuitHub's 75 %-off Value Proto would be about $480 for 5, but Q5 does not qualify: J1 has plated shell stakes, and Value Proto excludes through-hole and hybrid parts.
4. **Binding quote:** this needs the owner's CircuitHub account. It cannot be done from this cloud session; see "How to get the binding quote" below.

**Recommendation:** unless US assembly is itself the goal, run the JLC first-article tests before paying for a second build. If a CircuitHub build is wanted, upload this package for the binding quote, and order only after U3/U5 stock and the LCSC lines are resolved.

## What CircuitHub needs, and what is in this folder

CircuitHub assembles everything at its factory in South Deerfield, Massachusetts. It imports **native KiCad projects, not Gerbers**: KiCad 10 is fully supported. It needs one `.kicad_pro`, every `.kicad_sch` (one root plus the sub-sheets it references) and one `.kicad_pcb` with zones filled.

It buys parts itself from approved distributors:
- **approved:** Digi-Key, Mouser, Arrow, TI direct, TTI, Future, OnlineComponents and a few others;
- **"not preferred":** LCSC, which CircuitHub asks to be checked with it first;
- anything else must be consigned (shipped in by the customer).

| File | What it is |
|---|---|
| `click-counter-Q5-circuithub.zip` | The 21 KiCad 10 files to upload: project, root schematic, 18 sub-sheets and the routed, zone-filled board. These are byte-identical copies of `electronics/q5/`. |
| `BOM-CIRCUITHUB-Q5.csv` | CSV BOM in CircuitHub's column format. It covers the same 82 fitted references and the same footprints. LCSC house-brand part numbers are replaced with stocked US-distributor equivalents; DS1 and the 14 test lands/mounting holes are marked DNP. |
| `crossref-q5.json` | One decision per canonical part line (keep, cross, consign or DNP), with the reason and the stock evidence. |
| `manifest-circuithub-Q5.json` | SHA-256 of every input and output, so a stale package is detectable. |
| `circuithub-price-examples-2026-10-26.json` | CircuitHub's own published price examples, read from its pricing page and used for the estimate below. |

Regenerate the package after any BOM or board change with `python3 scripts/export_q5_circuithub.py`.

## Board against CircuitHub's published rules

| Rule (CircuitHub) | Q5 board | Result |
|---|---|---|
| ProtoBoard / Value Proto fab spec: 1–4 layers, 1.6 mm, 1 oz, FR-4, ENIG, ≤ 380 mm | 2 layers, 1.6 mm, 1 oz, FR-4, ENIG, 42 × 54 mm | Pass |
| Min trace / gap 0.127 mm | Min track 0.127 mm (97 segments; the rest 0.15–0.2 mm); design-rule clearance 0.127 mm | Pass, exactly at the limit |
| Min drill 0.15 mm | 0.30 mm vias (130), 1.02 mm DS1 pins | Pass |
| Hole-to-hole ≥ 0.25 mm | Board rule 0.25 mm | Pass, at the limit |
| Plated slots ≥ 0.4 mm, annular ring ≥ 0.1 mm (0.15 recommended) | J1 shell slots 0.6 mm wide, ring 0.25 mm | Pass |
| Mask sliver ≥ 0.1 mm; mask expansion ≥ 0.05 mm recommended | Board mask expansion is 0, so the fab's CAM applies its own, as JLC did. Narrowest gaps between different pads of one part: U5 0.15 mm; U1, U2 and U3 0.20 mm; U4 0.22 mm | Fine. At 0.05 mm expansion, U1–U3 keep a 0.10 mm dam. U5 (SOT-23-8, 0.65 mm pitch) would drop to 0.05 mm, so expect CircuitHub to open those pads as one window. That is normal at this pitch; check it in the DFM report |
| Vias ≤ 0.3 mm can be mask-covered | 0.3 mm drill vias, tented both sides | Pass |
| Single board, CircuitHub panelizes | The KiCad board is the bare 42 × 54 mm outline; JLC's rails were added by JLC | Pass |
| Polarity: auto-detected; silkscreen marks recommended | Every polarised part has a pin-1 mark (`docs/vendor-clarity-rules.md`) | Pass |
| ProtoBoard colours: black mask / white silk | Colour is a quote setting (the JLC first article was green) | Choose black to stay ProtoBoard-eligible |

## Parts

All 82 fitted references keep their footprints. Every line, with its Digi-Key evidence, is in [`SOURCING-CIRCUITHUB-Q5.md`](SOURCING-CIRCUITHUB-Q5.md); the summary:

| Handling | Lines | References |
|---|---|---|
| Same part as the JLC first article, in stock at Digi-Key | 14 | BAT54C, USBLC6-2SC6, AO3400A, USB4105-GF-A-120, STM32L072CBT6, BQ25185, BQ29700, TPS22917, FM25V02A, NCP18XH103 NTC, the 0.1 % RT0603 resistors and two capacitor values |
| Same part, **out of stock at Digi-Key** | 2 | **U3** TLV76701DRVR: 0; the identical TLV76701DRVT has 250 expected 23 Nov 2026. **U5** TLV7012DDFR: 0; 2,000 expected 19 Nov 2026 |
| Same-footprint equivalent (LCSC house brand or Digi-Key stock-out) | 22 | Samsung/Cal-Chip capacitors instead of Fenghua and the stocked-out Samsung/Murata parts; Yageo/Stackpole 1 % resistors instead of UNI-ROYAL; Diodes 1N4148WS-7-F and onsemi 2N7002LT1G instead of CJ |
| LCSC-only: custom LCSC purchase source or consign | 3 | BT1 holder, SW1/SW2 hot-swap sockets, SW3 reset switch (US-stocked drop-in search still running) |
| Left unplaced, fitted at home | 1 | DS1 display + separate 7-pin header (14 joints) |
| Not parts (copper lands / holes), DNP | — | TP1–TP13 (10), H1–H4 |

Notes:
- **U5 alternative:** TLV7032DDFR is in stock with the same package, pinout and push-pull output. It is a different comparator (315 nA instead of 4.7 µA per channel, 3 µs response, different hysteresis), so it needs owner and engineering sign-off. Waiting for TLV7012 stock keeps the build identical to the JLC first article.
- **U3 alternative:** TLV76701DGNR is in stock, but it is an 8-pin HVSSOP package and would need a PCB change.
- **Value Proto:** buying the LCSC-only parts through a custom source keeps a build eligible, but consigning them does not. J1 rules Value Proto out regardless.

## Cost estimate (not a CircuitHub quote)

`scripts/estimate_q5_circuithub_cost.py` writes `circuithub-cost-estimate.json`. It combines:
- **Fabrication + assembly:** CircuitHub's own published example "2 layers, simple microcontroller", read from circuithub.com/pricing on 26 Oct 2026. That board is similar to Q5 in size and layer count. Q5 has more parts (81 placements, 41 unique), so the real assembly price is more likely above this than below.
- **Parts:** every CircuitHub-bought line at the Digi-Key price for the quantity bought, including CircuitHub's published attrition extras (0603/0805 passives: at least 10 extra and 25 minimum; small ICs: 5 extra; large ICs: 1 extra).

Shipping and the LCSC-only or consigned parts (BT1, SW1/SW2, SW3: well under $1 a board at LCSC) are not included.

| USD, before shipping | 2 boards | 5 boards | 10 boards |
|---|---|---|---|
| Parts bought by CircuitHub (Digi-Key + attrition) | 166 | 222 | 338 |
| Cheapest lead time (5 / 12 / 12 days): fab + assembly | 636 | 846 | 902 |
| **Cheapest total** | **802 (401/board)** | **1,068 (214/board)** | **1,240 (124/board)** |
| Fastest (3 days): fab + assembly | 716 | 1,023 | 1,533 |
| **Fastest total** | **882 (441/board)** | **1,245 (249/board)** | **1,870 (187/board)** |
| Value Proto (75 % off Priority fab + assembly), **if the design qualified** | 345 (172/board) | 478 (96/board) | 721 (72/board) |

**For comparison**, JLC built the 5 first-article boards for **$298.08 in total**, including 10 bare PCBs, DHL and duties: about $60 a board. At 5 boards, CircuitHub's standard service is roughly 3.5–4× JLC; Value Proto would be about 1.6×.

The largest part costs at 5 boards:
- FM25V02A F-RAM: $9.80 each at Digi-Key;
- STM32L072: $5.45;
- the 10 µF capacitor cross (Cal-Chip): $1.17 each, bought 25 at a time.

## How to get the binding quote (owner signed in)

1. Sign in or sign up at https://app.circuithub.com and create a project.
2. Upload the files from `click-counter-Q5-circuithub.zip`: all 21, unzipped if the uploader wants single files. Then upload `BOM-CIRCUITHUB-Q5.csv` as the CSV BOM.
3. In the BOM import, choose **prefer CSV part numbers**, so the LCSC brands in the schematic `MPN` fields are ignored. Tick **"Placements not in the CSV BOM should not be fitted"**.
4. Board tab:
   - 2 layers, 1.6 mm, 1 oz, ENIG, **black mask / white silk** (keeps the ProtoBoard fab spec);
   - panelization "Any";
   - **no custom requirements**: any text there triggers a manual quote, and so does "US FABRICATION".
5. Parts tab:
   - check that every line shows an approved part with stock;
   - set the consigned lines (listed above) to **Consign** under Edit sourcing;
   - confirm DS1 and the test lands are DNP.
6. Wait for the Advanced PCB Analysis (DFM) to finish (up to about 20 minutes). Then read the Priority, Standard and Flexible prices for 2, 5 and 10 boards, and download the DFM report.
7. **Stop before "Proceed to order"**: ordering and payment need the owner's explicit go-ahead.

If an order is placed, add any assembly instruction (e.g. "pin 1 marks: see POLARITY-REFERENCE-Q5.pdf") through the **order's issue system**, not the Board tab. CircuitHub's assembly team does not read the Board tab.

## Risks and open items

- **Test the JLC boards first.** The five JLC first-article boards arrived on 14 Oct 2026, and no first-article results are recorded yet (`docs/q5-first-article-test-plan.md`). A second build at CircuitHub before those gates pass could be wasted money if a revision is needed.
- **Same design, different factory.** CircuitHub's CAM applies its own solder-mask expansion; the board sets 0. The narrowest feature (0.127 mm track and gap) is exactly at the ProtoBoard limit. Read CircuitHub's DFM report before ordering.
- **J1 stake length is inherited.** USB4105-GF-A-120 has 1.20 mm shell stakes on the 1.6 mm board, the same as the JLC first article. First-article check A1 (stakes wetted) applies to both builds.
- **Crossed parts are not identical parts.** The 20 crossed lines match the original part's specification and package exactly, but they come from a different maker than the JLC first article. Low-risk examples: Samsung instead of Fenghua capacitors, Yageo instead of UNI-ROYAL resistors, onsemi/Diodes instead of CJ discretes.
- **LCSC-only parts** (BT1, SW1/SW2, SW3, DS1) need a custom purchase source or consignment:
  - CircuitHub lists LCSC as "not preferred" and asks to be checked with first;
  - consigned surface-mount parts must arrive on continuous tape, labelled with the full MPN, with CircuitHub's attrition extras;
  - parts of Chinese origin can attract US tariffs that CircuitHub bills afterwards, so CircuitHub prefers they ship to the customer first.
- **US fabrication is not guaranteed.** Assembly is always in Massachusetts. Bare boards are "generally" made in the US for short lead times and in China for longer ones. Guaranteed US fabrication needs the custom requirement "US FABRICATION", which triggers a manual quote and loses ProtoBoard/Value Proto eligibility.
- **Firmware.** CircuitHub pre-programs only orders above 200 units. Flash the boards over USB-C at home with `tools/clicker-flash/` (skill `flash-clickers`), as for the JLC boards.
- **Value Proto needs a design change.** The 75 % discount excludes through-hole/hybrid parts. J1 would have to become an all-SMT 16-pin USB-C receptacle (for example the Same Sky UJ20-C-H-G-SMT-P16-TR family; fit and stock not verified). That means a new footprint, a re-route and an enclosure-opening check, plus fresh ERC/DRC/parity and verifier runs. It needs the owner's go-ahead, like any design change.
