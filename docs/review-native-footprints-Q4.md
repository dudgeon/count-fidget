# Q4 independent native-footprint review

Reviewed 25 September 2026 UTC. Scope: the project-local DS1, SW3 and J1 footprint geometry and selected header against primary manufacturer drawings. The review reads engineering files; it makes no PCB edits, vendor contact, quote submission or manufacture approval. Routing, native DRC/parity and the final enclosure are separate checks.

## Outcome

Two display drawing interpretation errors were identified and corrected by the board owner before this snapshot: the header row is **1.50 mm below the module top**, and the active area center is **2.10 mm above the module center**. The previously recorded 1.32 mm is a horizontal LCD inset. The corrected native footprint has y=-12.40 mm terminals and active-area y=-7.53..+3.33 mm. No additional dimensional or pin-map defect was found in the reviewed SW3 or J1 footprint. The model subsequently selected **USB4105-GF-A-120**, retaining the same planar footprint and avoiding the shorter -060 stake condition. This is a drawing comparison, not first-article fit or solder-process qualification.

## Geometric checks

| Item | Primary drawing and native result | Remaining limitation |
|---|---|---|
| DS1 module body | Page 6 drawing gives 27.30 ×27.80 mm; native F.Fab spans x=±13.65, y=±13.90. Module holes are Ø2.50 on 23.30 ×23.80 centers, represented on Dwgs.User only. | The source prose instead says 26 ×26 ×2.62 mm and SSD1306; the drawing says SSD1315. The exact delivered variant/dimensions remain a source-resolution and first-article gate. |
| DS1 terminal row | Seven 2.54 mm terminals, span15.24 mm, y=-12.40 mm; pin1 GND,2 VCC,3 SCL/SCK,4 SDA/MOSI,5 RES,6 D/C,7 CS. | Horizontal first-pin offset is not dimensioned. Native x=-7.62..+7.62 centers the row as an explicit inference. A photograph supports the broad layout but cannot prove that offset. |
| DS1 visible area | 21.74 ×10.86 mm; lower edge is10.57 mm above PCB bottom, giving center y=-2.10. Corrected native display rectangle agrees. | The enclosure window must use this corrected center; physical glass placement tolerances still apply. |
| Header | XFCN PZ254V-11-07P has seven0.64 mm square pins,2.54 mm pitch and recommended finished Ø1.02 holes. Native host holes are now1.02 mm, pads1.80 mm. Nominal radial annulus is0.39 mm. | Module hole diameter is not explicitly established by the module drawing. The photo shows bare holes, not an attached header. Separate header inclusion, insertion, assembled height and fillets must be verified. |
| SW3 reset switch | TS-1088-AR02016 drawing:3.90 ×3.00 body;2.00 mm actuator height; two-terminal normally-open switch. Native pads1.05 ×2.00 mm at x=±2.225,y=0 match the recommended land pattern; pin1 left and2 right in component top view. | Pinhole alignment and actuation over print/component tolerances require a physical fit check. |
| J1 USB-C | GCT USB4105 recommended component-side pattern:0.50 mm signal spacing;0.30 ×1.15 mm signal lands;0.60 ×1.15 mm shared power/GND lands; locator holesØ0.65 on5.78 mm pitch; shield slots0.60 ×1.70 and0.60 ×1.40 with1.00 ×2.10 and1.00 ×1.80 lands. Native local geometry matches. | Selected -120 stake is 1.20 ±0.15 mm. The generic footprint/model name also covers other stake lengths; final STEP and enclosure checks must use the selected vertical geometry. |

The USB electrical mapping agrees with GCT's table: A5 CC1, B5 CC2, A6/B6 D+, A7/B7 D−, A8 SBU1, B8 SBU2; shared outer A1/B12 and A12/B1 are GND, A4/B9 and A9/B4 are VBUS. Coincident pad numbers represent the connector's combined physical termination; they are not additional distinct copper lands.

## Assembly findings and limits

- **Header accounting:** one physical seven-pin interposer per board, with seven joints at the module and seven at the host: **14 through-solder joints**. It belongs in `procurement/q4/hardware-bom.json`, not a second independently placed footprint. Pin lengths are6.1 ±0.2 mm and3.0 ±0.2 mm around a2.5 mm insulator. Assembled spacing, trimming/fillet access and the actual module hole fit remain open. No loose-header supply is assumed established.
- **USB stake selection corrected:** the initially proposed -060 stake (0.60 ±0.15 mm) does not protrude through a nominal 1.0 mm board. The owner changed the selected part to the stocked -120 option (1.20 ±0.15 mm), giving nominal 0.20 mm and a 0.05–0.35 mm protrusion interval when board thickness is held exactly at 1.0 mm. Actual PCB thickness tolerance, paste/reflow/barrel wetting, fillets and retention under cable insertion still require verification. This closes the avoidable nominal short-stake choice; it is not physical solder qualification or assembler acceptance.
- **Footprint versus board:** component-side local coordinates were checked. A bottom-side placement must preserve the native mirror and pin net mapping in PCB, CPL and previews; this review does not substitute for final native parity and placement verification.
- The drawing's default tolerances and module part-number/prose contradiction remain visible. The corrected nominal geometry must not be called physical qualification.

## Reviewed footprint hashes

Directory: `electronics/q4/CountFidgetQ4.pretty/`.

| Ref | File | SHA-256 |
|---|---|---|
| DS1 | `HS96L01W4S03_Module_7Pin.kicad_mod` | `fa4f5330e96535492b3181720ccfd4127dfa726f1bcb95c01ea0b9350db22a99` |
| SW3 | `XUNPU_TS-1088-AR02016_SMD.kicad_mod` | `3362a6a9015fb0c38f81c291f6d44018349129a9686e16079572383c9a9f0efb` |
| J1 | `Connector_USB_USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.kicad_mod` | `a2617d52a4e9b6ab2729406cc8d3c5520c8b3355eb4d1846ca9240b144a2829a` |

## Primary sources

- [HS module manufacturer document, page6 drawing revisionA1,6July2019](https://datasheet.lcsc.com/datasheet/pdf/c5dd235441558974950f13e140069537.pdf?productCode=C5139758), SHA-256 `12a7bef24eec502ce2c0b54859d270d3f017dbbd3efe246b2f6ed9b831ffe7a9`. This review used the upright drawing, not the inconsistent prose dimensions.
- [XUNPU TS-1088-AR02016 drawing](https://datasheet.lcsc.com/datasheet/pdf/0475ac02febf455ca9ddcfb380b0df0d.pdf?productCode=C720477), SHA-256 `368d4cc2c26b08cb63e1b67193f671d0860b6d3fb2e6b9f2696ffade401afc30`.
- [XFCN PZ254V-11-XX header drawing](https://datasheet.lcsc.com/datasheet/pdf/3b85a1cdf6ed945f2e278f00c1e42442.pdf?productCode=C492406), SHA-256 `d4cb67e0fd15267bd26f8e782f79b44bc2c8e05fd2ac63c5a88712860c9aacd0`.
- [GCT USB4105 official drawing, sheet1, revisionB4,18December2023](https://gct.co/files/drawings/usb4105.pdf), SHA-256 `fb331fbabee8392ed2937ed757c1610cb0f174b84625147c0b580a18eea8c0e5`. Ordering grid distinguishes blank0.95,0600.60 and1201.20 mm stakes.
