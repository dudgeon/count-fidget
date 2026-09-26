# Q5 JLCPCB quotation record — 25 September 2026

Authorized scope: JLCPCB quotes for two variants of the locked Q5 design. **A** has JLC doing all SMT, and the user solders DS1. **B** has JLC assemble everything. Not authorized: ordering, payment, part allocation or preorder, manufacturing release, and contact with other vendors. No account was created or used. No cart item was saved. No vendor was contacted.

## What was actually quoted (public quote page, no sign-in)

Page: https://cart.jlcpcb.com/quote.

Uploaded file: `click-counter-Q5-Gerbers.zip`, sha256 `f9b9afe4ead8ebe9c9f7066926ef95a16f03e42750d92ad6f939462d12864230`. This is the design-lock export. The run was repeated after the final Basic-part substitution, with the same result.

JLC detected 2 layers and 42 × 54 mm. Selected options: 10 pcs, FR-4, 1.6 mm, 1 oz, green/white and ENIG.

| Line | USD |
|---|---|
| 10 bare PCBs ("Special Offer") | 5.00 |
| ENIG surface finish | 17.10 |
| Build time: 3 days, or "24 hours PCBA only" | 0.00 |
| **PCB calculated price** | **22.10** |
| Shipping estimate: DHL Express (DDP), 0.20 kg, 2–4 business days | 29.45 |

The PCBA section accepted Economic/Standard, bottom side and PCBA qty 10. After that, **NEXT (BOM/CPL upload and the parts-matched assembly price) does not proceed without a JLCPCB sign-in.** That login is the user's; the agent did not ask for credentials, and none were used. The binding PCBA figure therefore still has to be read by the user in the signed-in flow. The steps are below.

JLC displayed a factory holiday notice at the time: closed 25 and 27 Sep and 1–4 Oct 2026.

## Pre-quote estimate of the full JLC order (not a JLC quote)

The estimate is computed by `scripts/estimate_q5_jlc_cost.py` and saved in `jlc-cost-estimate.json`. Its inputs are:
- JLC's published PCBA fee schedule, https://jlcpcb.com/help/article/pcb-assembly-price, read 25 Sep 2026;
- live LCSC/JLC catalogue prices and minimum order quantities from `stock.json`;
- the joint counts of the routed board;
- the PCB and shipping figures above.

Part counts:
- 276 SMT joints per board;
- 40 SMT part types, of which 15 are Basic (no feeder fee) and 25 are Extended.

All figures are for 10 boards.

| USD, 10 boards | A Economic | A Standard | B Economic | B Standard |
|---|---|---|---|---|
| PCB (observed) | 22.10 | 22.10 | 22.10 | 22.10 |
| Setup + stencil | 9.71 | 33.77 | 9.71 | 33.77 |
| SMT joints | 4.42 | 4.42 | 4.42 | 4.42 |
| Feeder loading | 76.75 | 61.20 | 76.75 | 61.20 |
| SMT components | 132.96 | 132.96 | 132.96 | 132.96 |
| DS1 display + header, THT feeders, 140 hand joints, labor | — | — | 30.74 | 27.66 |
| **Subtotal** | **245.94** | **254.45** | **276.68** | **282.11** |
| + DHL DDP estimate | 275.39 | 283.90 | 306.13 | 311.56 |
| **Per board, shipped** | **27.54** | **28.39** | **30.61** | **31.16** |

Variant A also needs parts that the user buys from LCSC:
- DS1 displays, 12 at $22.12 (includes 2 spares);
- headers, 20 at $0.92.

Both variants need:
- K1/K2 clicky switches C49234235, 25 at $2.69;
- M2 × 6 screws C357360, 100 pcs (price not published at screen time);
- LIR2032 cells (retail);
- a 3D-printed enclosure (home print, `mechanical/q5/`);
- LCSC shipping.

Variant B is therefore about $30 more at JLC and saves the user about $23 of LCSC display/header parts plus 140 home solder joints.

Caveats:
- The estimate excludes coupons (JLC advertises setup-fee coupons), attrition extras JLC adds per part, and any extended-part price change after 20:21 UTC.
- Whether Economic PCBA accepts the through-hole DS1 stacked on header DS1H, or requires Standard, is a quote question for variant B.

## 5-board variant (observed 25 Sep 2026, same page and options)

On the public quote page, PCB Qty 5 gave:
- Special Offer $4.00 + ENIG $16.90 = **$20.90**;
- DHL DDP shipping $29.45 (0.16 kg).

PCBA qty 5 is offered (the minimum is 2). The estimate is in `jlc-cost-estimate-5.json`, from `estimate_q5_jlc_cost.py --qty 5`:

| USD, 5 boards | A Economic | B Economic |
|---|---|---|
| PCB (observed) | 20.90 | 20.90 |
| Setup + stencil + joints | 11.92 | 11.92 |
| Feeder loading (25 Extended types) | 76.75 | 76.75 |
| SMT components | 66.48 | 66.48 |
| DS1 + header, THT feeders, hand joints, labor | — | 20.23 |
| **Subtotal** | **176.05** | **196.28** |
| **With DHL** | **205.50** | **225.73** |
| **Per board, shipped** | **41.10** | **45.15** |

The feeder fee is per part type, not per board. That is why 5 boards cost about 75 % of the price of 10. Component prices use the 10-piece price break, so 5-piece breaks may add a few dollars. Standard PCBA adds about $8.50 (A) or $5.40 (B).

## Cost per board at 2, 5 and 10 (estimate, Economic PCBA, DHL included)

The 2-board case is 5 bare PCBs with 2 assembled; JLC's PCBA minimum is 2, and `--qty 2` prices parts at the 1-piece break.

| Assembled boards | A (user solders DS1) | B (JLC fits everything) | B − A per board | A also needs from LCSC per board |
|---|---|---|---|---|
| 2 | $167.74 → **$83.87** | $182.60 → **$91.30** | $7.43 | ~$2.3 display + header, plus LCSC shipping |
| 5 | $205.50 → **$41.10** | $225.73 → **$45.15** | $4.05 | ~$1.9 |
| 10 | $275.39 → **$27.54** | $306.13 → **$30.61** | $3.07 | ~$1.9 |

At every quantity, soldering the display yourself saves less than $10 per board: about $1–5 net after buying the display yourself. **Owner decision (26 Sep 2026): variant B**, because self-soldering is only wanted when it saves more than $10 per board.

## Steps for the binding quote (user, signed in; stop at the cart)

1. Open https://cart.jlcpcb.com/quote and sign in.
2. Upload `click-counter-Q5-Gerbers.zip`. Choose 10 pcs, 1.6 mm, ENIG, and leave everything else at its default.
3. Turn on **PCB Assembly** and set:
   - Economic;
   - **Bottom Side**;
   - PCBA qty 10;
   - "Added by JLCPCB" tooling holes;
   - Confirm Parts Placement: yes.
4. Tick the terms box and click NEXT.
5. Upload the BOM and CPL for the variant:
   - **Variant A:** `BOM-JLCPCB-Q5.csv` + `CPL-JLCPCB-Q5.csv`.
   - **Variant B:** `BOM-JLCPCB-Q5-FULL-ASSEMBLY.csv` + `CPL-JLCPCB-Q5-FULL-ASSEMBLY.csv`. If Economic refuses the through-hole lines, repeat with **Standard**.
6. On the parts page:
   - every line should match the LCSC number in the BOM, with no "shortfall" or "not selected";
   - for variant B, DS1 (C5139758) and DS1H (C492406) should show as through-hole/manual.
7. On the placement preview, check pin 1 / polarity against `assembly-bottom-Q5.svg`:
   - U1–U8, Q1–Q5, D1–D4 and J1;
   - BT1 (+ contact on pad 1);
   - the two hot-swap sockets SW1/SW2, whose pads sit beside the 3.0 mm pin holes.
   JLC's preview may need rotation corrections. Record any correction in this file; do not edit the CPL silently.
8. Record the product total, the shipping total and each rotation correction below. **Stop before "Save to cart"/checkout**: ordering is not authorized.

| Signed-in result | Variant A | Variant B |
|---|---|---|
| PCBA total (10) | pending | pending |
| Parts shortfall / substitutions | pending | pending |
| Rotation corrections | pending | pending |
| Date/time | pending | pending |

## Enclosure

The finished-product plan prints the five enclosure parts at home (PETG, per `mechanical/q5/README.md`). A JLC3DP print quote was not requested: it needs the same account sign-in, and it was not part of the authorized A/B scope.
