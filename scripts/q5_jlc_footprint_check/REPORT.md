# Count Fidget Q5: JLC/LCSC footprint cross-check and predicted CPL corrections

Date 2026-09-26. The repo was only read, never modified. Scripts and outputs are in this directory:
- `kicad_dump.py`: pcbnew dump of board pads (`kicad.json`) and library pads (`kicad_lib.json`).
- `easyeda/*.json`: raw EasyEDA API responses.
- `analyze.py`: local alignment and JLC preview model (`results.json`/`.csv`).
- `detail.py`: per-pad overlap.
- `corrections.py`: `corrections.json`/`.csv`.
- `pins.py`: symbol pin-name cross-check.

## 1. Fetch

The endpoint `https://easyeda.com/api/products/<LCSC>/components?version=6.4.19.5` returned `success:true` with a package for **all 42 unique LCSC numbers** in the variant-A and variant-B BOMs, including DS1 C5139758 and DS1H C492406. **No part failed to fetch**, so the easyeda2kicad fallback was not needed.

Every EasyEDA part's manufacturer and MPN matches the BOM. The BOM LCSC numbers equal `netlist-Q5.json` for every reference; DS1H is not in the netlist.

## 2. Footprint agreement (library-local, EasyEDA vs KiCad)

For each part I fitted EasyEDA pads onto the KiCad library pads:
- rotation 0/90/180/270 with and without a mirror;
- pads matched by pad number (EasyEDA compound names such as `A1-B12` are split);
- offset by least squares.

**Results**
- **No part needs a mirror.**
- **No part has a pin-number mismatch** except two where the numbering alone differs:
  - J1 shield pads: KiCad `SH`, EasyEDA `1`-`4`. They coincide geometrically to 0.000 mm.
  - The SW1/SW2 socket (explained below).
- Symbol pin names from the LCSC symbol agree with our netlist:
  - BT1: 1 = `+`. The EasyEDA silkscreen draws `+` beside pad 1 at +x.
  - D3: 3 = K. D4: 1 = K.
  - Q*: 1 G / 2 S / 3 D.
  - U1-U8: all pins.
  - USB-C: A6 = Dp1 and so on.
  - DS1: 1 = GND.

| Part(s) | LCSC | EasyEDA rotation vs KiCad | Max pad-centre residual | Verdict |
|---|---|---|---|---|
| BT1 CR2032-BS-6-1 | C70377 | 0 | 0.005 | Identical; pad 1 = + in both |
| J1 USB4105 | C5184243 | 0 | 0.000 for pads, 0.65 mm stake holes and 4 shield slots | Identical copper; **origins differ by 1.302 mm** |
| SW1/SW2 hot-swap socket | C41430893 | 0 (geometric), 180 (by number) | 0.26-0.27 on SMD tabs; 3.0 mm holes 0.013 | See below; **origins differ by 3.86 mm** |
| SW3 TS-1088 | C720477 | 0 | 0.040 | OK |
| U1 LQFP-48 | C465977 | 270 | 0.087 | Pin 1 consistent |
| U2 WSON-10 DLH | C19725033 | 270 | 0.050 (EP 0.000) | OK |
| U3 WSON-6 DRV | C2863998 | 0 | 0.141 | Benign: LCSC lands 0.61 mm long vs KiCad-standard 0.40 mm; EP identical |
| U4 WSON-6 DSE | C183096 | 0 | 0.062 | OK |
| U5 SOT-23-8 | C2871502 | 270 | 0.122 | Benign toe/heel convention |
| U6/U7 SOT-23-6 | C2681320 ("BR") | 180 | 0.213 | Benign: LCSC lands shifted 0.21 mm outboard, overlap 91 % |
| D1/D2 SOT-23-6 | C7519 ("BL") | **270** | 0.012 | OK. The same package name as U6 has a different EasyEDA orientation, so a generic "SOT-23-6" correction table would get one of them wrong |
| U8 SOIC-8 | C66029 | 270 | 0.230 | Benign: LCSC toe 0.23 mm longer, overlap 88 % |
| D3 BAT54C SOT-23 | C37704 (W1.6/LS2.8 variant) | 180 | **0.397** on pad 3, origin 0.099 | Benign: LCSC uses a wider-body land. Our pads fully cover LCSC pads 1 and 2 and 82 % of pad 3 |
| Q1-Q5 SOT-23 | C5208862, C8545 | 180 | 0.083, origin 0.021 | OK |
| D4 SOD-323 | C2128 | 0 | 0.122 | Benign (KiCad-standard small lands); cathode = pad 1 in both |
| 0603/0805 R and C, TH1 | various | 0 | 0.050-0.075 | OK |
| DS1 HS96L01W4S03 (variant B) | C5139758 | 0 | 0.000 | Identical holes; **origin differs by 12.4 mm**; EasyEDA also draws the module's 4 × 2.5 mm mounting holes as host holes, which our PCB does not have |
| DS1H header (variant B) | C492406 | 0 | 0.000 | OK |

Every residual above 0.1 mm is a land-pattern convention difference (toe or heel length, or a wider-body SOT-23 land). None is a pitch or pin-order error. The only real placement issues are **origin offsets**: J1, SW1/SW2 and DS1.

**Hot-swap socket detail (C41430893).**
- The EasyEDA origin is the midpoint of the two 3.0 mm pin holes. KiCad's origin is the switch centre.
- EasyEDA pad 1 sits beside the other hole, so KiCad pad numbers are swapped relative to LCSC. This is harmless for a two-terminal switch.
- The pad/hole set is point-symmetric; the socket body is not. The EasyEDA body outline (layer 99) has its concave arc toward the MX centre post. Only the "0°, numbers swapped" alignment puts that arc at our 4.0 mm centre hole (error 0.007 mm). The by-number 180° alignment would put the body over the post hole.
- The KiCad F.Fab outline of our own footprint also overlaps the 4 mm post hole. That is cosmetic, but it will not match JLC's overlay.
- Copper tabs: LCSC tab centres sit 0.26 mm further outboard than ours, overlap 89 %. Acceptable, but the tab land was derived from the maker drawing, so check it at first article.

## 3. Predicted JLC preview and corrections

**JLC documentation**
- CPL `Rotation` is counter-clockwise-positive.
- `Mid X/Mid Y` is "the X/Y coordinate of the component centroid" ([JLC pick & place help](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly)).
- JLC does **not** publish a bottom-side rotation formula.

**Community-documented bottom convention used here (not an official JLC statement)**
- KiCad flips about the local Y axis, while JLC changing T→B flips about local X. The fix is `rot_bottom = 180 − θ` ([KiKit discussion #664](https://github.com/yaqwsx/KiKit/discussions/664); KiKit `MirrorBottom` in `kikit/fab/common.py`).
- The same formula is in [Bouni kicad-jlcpcb-tools](https://github.com/Bouni/kicad-jlcpcb-tools) `fabrication.py` (`rotation = (180 - rotation) % 360`).
- [KiBot position notes](https://kibot.readthedocs.io/en/latest/notes_position.html) say "KiCad mirrors components on the bottom side, but JLCPCB doesn't (november 2023)".
- An open issue ([Bouni #636](https://github.com/Bouni/kicad-jlcpcb-tools/issues/636)) questions how corrections combine on the back side.

My geometric model is bottom: pad = C + Mirror_x · R(β) · E_easyeda. It reproduces 180 − θ exactly. Nothing is taken from a correction table: every value below is fitted per part from its own EasyEDA pads.

**Our CPL** is raw `kicad-cli pos` output. It uses KiCad bottom rotations, top-view X with no negation, and the KiCad footprint origin. No JLC correction has been applied.

**Two predictions do not depend on the bottom convention**
- For β = 90/270 the old "KiCad-like" interpretation and the 180 − θ interpretation give the same result.
- Position offsets are model-independent.

The table separates model-independent from model-dependent items.

### 3a. Corrections needed. Polarity/pin 1 is wrong if left uncorrected.

| Ref | CPL rot | Predicted preview needs | Depends on bottom convention? | Consequence if not fixed |
|---|---|---|---|---|
| **BT1** | 0 | **180** | yes (a KiCad-like interpretation would need 0) | **+ contact on CELL_N_RAW pad: reversed cell** |
| **D4** | 0 | **180** | yes | Cathode reversed |
| **D1, D2** (USBLC6) | 90 | **0** | yes (KiCad-like: 180) | GND and VBUS swapped |
| **U3** TLV76701 | 0 | **180** | yes | IN and OUT swapped |
| **U4** BQ29700 | 0 | **180** | yes | Pin 1 wrong |
| **U1** LQFP-48 | 0 | **90** | no | Pin 1 wrong |
| **U2** BQ25185 | 0 | **90** | no | Pin 1 wrong |
| **U5** TLV7012 | 180 | **270** | no | Pin 1 wrong |
| **U7** TPS22917 | 90 | **270** | no | Pin 1 wrong |
| **U8** FM25V02A | 0 | **90** | no | Pin 1 wrong |
| **Q1, Q2, Q3** | 90 | **270** | no | G/S/D wrong |

The following already match under the 180 − θ convention: **D3 (0), Q4 (0), Q5 (0), U6 (0)**. Under a KiCad-like interpretation they would each need 180.

Two-pad non-polar parts may show 180° "rotated" in the preview, which does not matter electrically. These are all R, C, TH1 and SW3 at 0/180; R and C at ±90 already match.

### 3b. Position corrections (model-independent; offset > 0.2 mm between JLC's footprint origin and ours)

| Ref | CPL Mid X, Y | Rotation | Corrected Mid X, Y | Offset |
|---|---|---|---|---|
| **SW1** | 11.475, −40.800 | 90 (OK) | **7.665, −41.428** | 3.86 mm: EasyEDA origin = hole midpoint |
| **SW2** | 30.525, −40.800 | −90/270 (OK) | **34.335, −40.172** | 3.86 mm |
| **J1** | 38.900, −26.600 | −90/270 (OK) | **37.598, −26.600** | 1.302 mm |
| **DS1** (variant B only) | 21.000, −16.700 | 0 (OK) | **21.000, −4.300** | 12.4 mm: EasyEDA origin = pin-row centre, same as DS1H |

Small benign origin offsets: D3 0.099 mm, Q1-Q5 0.021 mm.

**CPL vs pad centroid.** CPL = KiCad origin. It differs from the copper-pad centroid by more than 0.2 mm for:
- Q1-Q5 and D3: 0.31 mm. This is normal: SOT-23 origin = body centre, and LCSC uses the same, so no action.
- SW1/SW2: 3.86 mm.
- J1: 3.15 mm to the all-copper centroid; 1.30 mm to JLC's origin.
- DS1: 12.4 mm.

It is 0.000 mm for BT1 and SW3 and ≤ 0.008 mm for every other part.

## 4. Uncertainty and how to confirm

1. The bottom-side convention comes from community tools (KiKit, Bouni, KiBot, 2023-2026), not from JLC documentation. **BT1, D4, D1/D2, U3 and U4 flip between conventions.** Before accepting, confirm in the JLC preview:
   - BT1: the EasyEDA `+` mark sits on our pad at board X ≈ 35.4 mm.
   - D4: the cathode bar sits on our pad 1.
   - D1/D2: pin-1 dot on our pin 1.
   - U3/U4: pin-1 dot on our pin 1.
   - Once one of these is confirmed, the rest follow the same rule.
2. JLC engineers often re-rotate parts themselves during DFM review. The table predicts the as-uploaded preview, not what JLC might silently fix.
3. Pad data is from the public EasyEDA API as of 2026-09-26. LCSC can revise library footprints.
4. None of this checks physical leads against datasheets. It compares two land patterns only. Remaining items for first article:
   - BT1 polarity against the physical holder;
   - socket tab land;
   - U3 short KiCad-standard land.
5. Variant B: EasyEDA DS1 shows four 2.5 mm host holes that do not exist on our PCB. Expect a DFM query, or explain in the order notes.
