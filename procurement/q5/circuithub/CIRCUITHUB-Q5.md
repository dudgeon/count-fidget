# Q5 at CircuitHub — feasibility, upload package and cost estimate (26 October 2026)

**Request (owner, 26 Oct 2026):** "see if you can get this pcb made and manufactured at circuithub.com".

**Status:** feasibility checked and upload package prepared. Stock for U3 and U5 re-read on 25 Nov 2026. **No CircuitHub account was created or used; nothing was uploaded, quoted, ordered or paid.**
- CircuitHub quotes only inside a signed-in account (app.circuithub.com). This cloud session cannot sign in, and the agent never asks for or uses the owner's credentials.
- The BOM substitutions below are proposals: the owner approves them by uploading and ordering.
- Placing an order or paying needs the owner's explicit go-ahead at that moment.

## Bottom line

**Yes, CircuitHub can build Q5 with no change to the board. It costs about 3.5–4× JLC, and one TI chip (U3) is still out of stock: the earliest Digi-Key delivery is 66 parts due 7 December.**

1. **Design fit:** pass. CircuitHub imports the KiCad 10 project natively, and the board meets its published rules for the low-cost ProtoBoard tier (table below).
2. **Parts:** CircuitHub buys every part itself; nothing has to be consigned. Of the 41 part lines CircuitHub places, 40 are in stock at Digi-Key (U5 restocked by 25 Nov), the US distributor it buys from most:
   - 15 lines are the same part numbers as on the JLC first article;
   - 25 lines are same-footprint equivalents for LCSC-only parts or Digi-Key stock-outs. 22 are like-for-like passives and discretes. Three are mechanical parts to check on the first CircuitHub boards: the Keystone 1060 battery holder, the Kailh hot-swap sockets and the C&K reset switch.

   Two lines remain:
   - **U3** (TLV76701 3.2 V regulator) is still out of stock at Digi-Key (re-read 25 Nov 2026). The identical TLV76701DRVT has 66 due 7 Dec 2026 and 184 on 27 Jan 2027. TLV76701DRVR has 3,000 due 1 Apr 2027.
   - **DS1** (display) is left unplaced and soldered at home, 14 joints, as in JLC variant A.
3. **Cost (estimate):** about **$1,090–1,270 for 5 boards before shipping** ($218–253 a board), against **$298.08 all-in** for 5 at JLC (about $60 a board). CircuitHub's 75 %-off Value Proto would be about $500 for 5, but Q5 does not qualify: J1 has plated shell stakes, and Value Proto excludes through-hole and hybrid parts.
4. **Binding quote:** this needs the owner's CircuitHub account. It cannot be done from this cloud session; see "How to get the binding quote" below.

**Recommendation:** unless US assembly is itself worth the premium, run the JLC first-article tests (boards delivered 14 Oct) before paying for a second build. If a CircuitHub build is wanted, upload this package now for the binding quote, and order once U3 is in stock (the first 66 are due 7 Dec 2026).

## What CircuitHub needs, and what is in this folder

CircuitHub assembles everything at its factory in South Deerfield, Massachusetts. It imports **native KiCad projects, not Gerbers**: KiCad 10 is fully supported. It needs one `.kicad_pro`, every `.kicad_sch` (one root plus the sub-sheets it references) and one `.kicad_pcb` with zones filled.

It buys parts itself from approved distributors:
- **approved:** Digi-Key, Mouser, Arrow, TI direct, TTI, Future, OnlineComponents and a few others;
- **"not preferred":** LCSC, which CircuitHub asks to be checked with it first;
- anything else must be consigned (shipped in by the customer).

| File | What it is |
|---|---|
| `click-counter-Q5-circuithub.zip` | The 21 KiCad 10 files to upload: project, root schematic, 18 sub-sheets and the routed, zone-filled board. These are byte-identical copies of `electronics/q5/`. |
| `BOM-CIRCUITHUB-Q5.csv` | CSV BOM in CircuitHub's column format. It covers the same 82 fitted references and footprints, with the US-stocked part numbers below. DS1 and the 14 test lands and mounting holes are DNP. |
| `SOURCING-CIRCUITHUB-Q5.md` | One row per part line: CircuitHub part, original part, handling, Digi-Key stock and notes. |
| `crossref-q5.json` | The decision and evidence behind each line: reason, Digi-Key part number, stock, price breaks, URL, date. |
| `circuithub-cost-estimate.json` | The cost estimate below. |
| `circuithub-price-examples-2026-10-26.json` | CircuitHub's own published price examples, read from its pricing page. |
| `manifest-circuithub-Q5.json` | SHA-256 of every input and output, so a stale package is detectable. |

Regenerate after any BOM or board change:
- `python3 scripts/export_q5_circuithub.py` rebuilds the package;
- `python3 scripts/test_export_q5_circuithub.py` checks that 7/7 deliberate corruptions are rejected;
- `python3 scripts/estimate_q5_circuithub_cost.py` re-runs the estimate.

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
| Polarity: auto-detected; silkscreen marks recommended | Every polarised part has a pin-1 mark (`docs/vendor-clarity-rules.md`); BT1 has + and − marks | Pass |
| ProtoBoard colours: black mask / white silk | Colour is a quote setting (the JLC first article was green) | Choose black to stay ProtoBoard-eligible |

## Parts

All 82 fitted references keep their footprints. Every line with its evidence is in [`SOURCING-CIRCUITHUB-Q5.md`](SOURCING-CIRCUITHUB-Q5.md). Stock is from Digi-Key product pages read on 26 Oct 2026; Mouser, Arrow, TTI and Future refused automated reads, and TI direct shows inventory only when signed in.

| Handling | Lines | Parts |
|---|---|---|
| Same part as the JLC first article, in stock | 15 | TLV7012DDFR (U5, back in stock on 25 Nov), STM32L072CBT6, BQ25185, BQ29700, TPS22917, FM25V02A, USB4105-GF-A-120, USBLC6-2SC6, BAT54C, AO3400A, NCP18XH103 NTC, the 0.1 % RT0603 resistors and two capacitor values |
| Same part, **out of stock at Digi-Key** | 1 | **U3** TLV76701DRVR: 0 on 25 Nov 2026, 3,000 due 1 Apr 2027. The identical TLV76701DRVT: 66 due 7 Dec 2026 and 184 on 27 Jan 2027 (the 250 due 23 Nov did not arrive as planned) |
| Like-for-like equivalent, same footprint | 22 | Samsung, Cal-Chip and Yageo capacitors instead of Fenghua and stocked-out Samsung/Murata parts. Yageo and Stackpole 1 % resistors instead of UNI-ROYAL. Diodes 1N4148WS-7-F and onsemi 2N7002LT1G instead of CJ |
| Mechanical equivalent, fits the same pads (check on the first boards) | 3 | **BT1:** Keystone 1060 instead of the Q&J copy of it. **SW1/SW2:** Kailh MX hot-swap socket, sold as Adafruit 4958 (pack of 20), instead of the HanElectricity copy. **SW3:** C&K PTS820J20MSMTR LFS instead of XUNPU TS-1088 |
| Left unplaced, fitted at home | 1 | DS1 display + separate 7-pin header (14 joints) |
| Not parts (copper lands / holes), DNP | — | TP1–TP13 (10 lands), H1–H4 |

The three mechanical equivalents, from the makers' drawings:
- **BT1, Keystone 1060** (36-1060-ND, 10,689 in stock, $1.12 at 10, bulk):
  - same 22 × 16 × 5.5 mm body and 3.6 mm tabs as the Q&J part, so the enclosure is unchanged;
  - Keystone's lands (2.6 × 3.6 mm at ±14.65 mm) and the tabs fall wholly inside our 4.2 × 3.8 mm pads at ±14.39 mm, with 0.10 mm side margin on the tab;
  - the + contact must go on pad 1 (the + silkscreen side);
  - cut-tape alternative: MPD BU2032SM-G (31,025 in stock). It is 5.2 mm tall and drawn with + on the other side, so check its orientation in the placement view.
- **SW1/SW2, Adafruit 4958** (1528-4958-ND, 253 packs of 20 in stock, $4.95 a pack):
  - Adafruit's datasheet is the Kailh drawing, identical to the HanElectricity one dimension for dimension, including the 2.55 × 2.5 mm pads and 3.0 mm holes our footprint uses;
  - gold rather than tin contacts;
  - **one pack covers 10 boards:** make sure CircuitHub buys packs, not one pack per socket;
  - bulk bag, so hand placement.
- **SW3, C&K PTS820J20MSMTR LFS** (CKN10505CT-ND, $0.92 at 10):
  - same 3.9 × 2.9 mm size, 2.0 mm actuator height and 160 gf force, no pegs;
  - its J-lead terminals (tips ±2.2 mm, 1.0 mm wide) land inside our 1.05 × 2.0 mm pads at ±2.225 mm;
  - C&K's own layout puts pads 0.15 mm further in and marks four corner frame-leg areas where our board has solder-masked bottom-layer tracks, as under the original switch;
  - ask CircuitHub to reduce the SW3 paste openings to about 0.95 × 1.4 mm;
  - never use the pegged "P" version.

Other options:
- **U5:** back in stock (1,884 on 25 Nov 2026), so the TLV7032DDFR alternative is no longer needed.
- **U3:** TLV76701DGNR is in stock but is an 8-pin HVSSOP and would need a PCB change. Adding LCSC as a custom purchase source for TLV76701DRVR is the other route; check with CircuitHub first.
- **DS1 for home soldering:** either the LCSC HS96L01W4S03 + XFCN PZ254V-11-07P header used by JLC, or the Digi-Key-stocked Orient Display AOM12864A0-0.96WW-ANO ($9.38 at 10) with a Sullins PRPC007SAAN-RC header.
  - The Orient module matches our outline, holes, pin order and active area on its drawing, and runs from 2.7–3.3 V (our display rail is 3.15–3.26 V).
  - It is up to 5.0 mm thick and has larger glass, so sample one and re-check the enclosure before buying in quantity.

## Cost estimate (not a CircuitHub quote)

`scripts/estimate_q5_circuithub_cost.py` writes `circuithub-cost-estimate.json`. It combines:
- **Fabrication + assembly:** CircuitHub's own published example "2 layers, simple microcontroller", read from circuithub.com/pricing on 26 Oct 2026. That board is similar to Q5 in size and layer count. Q5 has more parts (81 placements, 41 unique), so the real assembly price is more likely above this than below.
- **Parts:** every line at the Digi-Key price for the quantity bought, including CircuitHub's published attrition extras (0603/0805 passives: at least 10 extra and 25 minimum; small parts: 5 extra; large ICs: 1 extra). The sockets are priced per 20-piece pack.

Shipping is not included.

| USD, before shipping | 2 boards | 5 boards | 10 boards |
|---|---|---|---|
| Parts bought by CircuitHub (Digi-Key + attrition) | 182 | 243 | 374 |
| Cheapest lead time (5 / 12 / 12 days): fab + assembly | 636 | 846 | 902 |
| **Cheapest total** | **818 (409/board)** | **1,090 (218/board)** | **1,276 (128/board)** |
| Fastest (3 days): fab + assembly | 716 | 1,023 | 1,533 |
| **Fastest total** | **898 (449/board)** | **1,266 (253/board)** | **1,906 (191/board)** |
| Value Proto (75 % off Priority fab + assembly), **if the design qualified** | 361 (180/board) | 499 (100/board) | 757 (76/board) |

**For comparison**, JLC built the 5 first-article boards for **$298.08 in total**, including 10 bare PCBs, DHL and duties: about $60 a board. At 5 boards, CircuitHub's standard service is roughly 3.5–4× JLC; Value Proto would be about 1.7×.

The largest part costs at 5 boards:
- FM25V02A F-RAM: $9.80 each;
- STM32L072: $5.45;
- the 10 µF capacitor (Cal-Chip): $1.17 each, bought 25 at a time.

## How to get the binding quote (owner signed in)

1. Sign in or sign up at https://app.circuithub.com and create a project.
2. Upload the 21 KiCad files from `click-counter-Q5-circuithub.zip` (unzip first if the uploader wants single files), plus `BOM-CIRCUITHUB-Q5.csv` as the CSV BOM.
3. In the BOM import, choose **prefer CSV part numbers**, so the LCSC brands in the schematic `MPN` fields are ignored. Tick **"Placements not in the CSV BOM should not be fitted"**.
4. Board tab:
   - 2 layers, 1.6 mm, 1 oz, ENIG, **black mask / white silk** (keeps the ProtoBoard fab spec);
   - panelization "Any";
   - **no custom requirements**: any text there triggers a manual quote, and so does "US FABRICATION".
5. Parts tab:
   - check every line shows the part number in the CSV with stock;
   - for U3, use "Supply Pricing" to enter the restock date (TLV76701DRVT, 7 Dec 2026) if CircuitHub shows no stock; the ship date then moves;
   - check that the hot-swap socket line buys **packs of 20**;
   - confirm DS1 and the test lands are DNP.
6. Wait for the Advanced PCB Analysis (DFM) to finish (up to about 20 minutes). Then read the Priority, Standard and Flexible prices for 2, 5 and 10 boards, and download the DFM report.
7. **Stop before "Proceed to order"**: ordering and payment need the owner's explicit go-ahead.

If an order is placed, give CircuitHub's assembly team these points through the **order's issue system**, not the Board tab (the assembly team does not read the Board tab):
- BT1 + contact on pad 1 (+ silkscreen);
- SW3 paste openings about 0.95 × 1.4 mm;
- the sockets come 20 to a pack;
- pin-1 reference: `POLARITY-REFERENCE-Q5.pdf`.

## Risks and open items

- **Test the JLC boards first.** The five JLC first-article boards arrived on 14 Oct 2026, and no first-article results are recorded yet (`docs/q5-first-article-test-plan.md`). A second build at CircuitHub before those gates pass could be wasted money if a revision is needed.
- **Substituted parts are not identical parts.**
  - The 22 like-for-like lines match the original's value, rating and package from a different maker: low risk.
  - BT1, SW1/SW2 and SW3 fit on paper; check them on the first CircuitHub boards:
    - **BT1:** cell retention and contact (already a first-article gate);
    - **SW1/SW2:** socket grip on the switch pins;
    - **SW3:** pinhole press feel and solder joints.
- **Same design, different factory.** CircuitHub's CAM applies its own solder-mask expansion; the board sets 0. The narrowest feature (0.127 mm track and gap) is exactly at the ProtoBoard limit. Read CircuitHub's DFM report before ordering.
- **J1 stake length is inherited.** USB4105-GF-A-120 has 1.20 mm shell stakes on the 1.6 mm board, the same as the JLC first article. First-article check A1 (stakes wetted) applies to both builds.
- **Stock moves.** Digi-Key restock dates slip: U3's moved from 23 Nov to 7 Dec 2026 (66 parts) and 1 Apr 2027 (3,000). The Kailh socket pack (253 in stock) and the Orient display (144) have shallow stock. CircuitHub's quote shows availability from one distributor at a time; it can look elsewhere on request.
- **Tariffs.** CircuitHub bills afterwards any US tariff on China-origin components it buys; most parts here are not affected.
- **US fabrication is not guaranteed.** Assembly is always in Massachusetts. Bare boards are "generally" made in the US for short lead times and in China for longer ones. Guaranteed US fabrication needs the custom requirement "US FABRICATION", which triggers a manual quote and loses ProtoBoard/Value Proto eligibility.
- **Firmware.** CircuitHub pre-programs only orders above 200 units. Flash the boards over USB-C at home with `tools/clicker-flash/` (skill `flash-clickers`), as for the JLC boards.
- **Value Proto needs a design change.** The 75 % discount excludes through-hole/hybrid parts. J1 would have to become an all-SMT 16-pin USB-C receptacle (for example the Same Sky UJ20-C-H-G-SMT-P16-TR family; fit and stock not verified). That means a new footprint, a re-route, an enclosure-opening check and fresh ERC/DRC/parity and verifier runs. It needs the owner's go-ahead, like any design change.
