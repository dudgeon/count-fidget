# Q3 independent mechanical review

15 September 2026. **The revised split-lid candidate passes the reviewed static and sampled assembly-path checks. Physical fit remains unqualified.** The reviewer did not author the enclosure generator. This review caused corrections to two interferences, the original lid assembly sequence, and an inadequate nominal screw clearance. The final-source addendum binds the completed board/CAD files; this does not qualify an actual printed part, the custom battery, or the OLED solder process.

## Scope and reproducible snapshot

Reviewed [build_q3_enclosure.py](../scripts/build_q3_enclosure.py), native board/pad geometry, selected manufacturer drawings and the root-generated private CAD snapshot. Numerical fit/interference coordinates below use the generator’s internal frame: X=PCB_X−21, Y=PCB_Y−20, Z upward. The final exporter subsequently mirrors every STEP/STL/render shape across XZ, producing the right-handed output frame X=PCB_X−21, Y=20−PCB_Y, Z upward. Distances and overlaps are unchanged; Y signs and front/rear approach directions reverse in exported coordinates. The snapshot uses CadQuery2.8/Python3.12.14 and preserves Q1/Q2. The final `mechanical/q3/` regeneration is recorded in the addendum below; this earlier table remains historical trial evidence.

| Snapshot item | SHA-256 |
| --- | --- |
| Reviewed pre-mirror enclosure generator | `c91f24853d7af47259e8fb8e280ae0a1b0f0b2ebbe06fd51b7bcc75c7c13c99e` |
| Native board input | `d6f4d87a7cfe9a72624d2ab8dc896b697abee932dc967e521b6774fffac75938` |
| Model input | `874bf67556de2b7b6a84dbd28613dd90029c83cc8ec94670f5807680379f1232` |
| Reviewed pre-mirror assembly STEP | `d6dfa764b44e99adb3a74d3e013a6dd44ecbf22627a78f5354f03e54d02d2be3` |

The private snapshot's report and STEP hashes matched its manifest. Four printable parts—base, keeper, lid-front and lid-rear—were each valid single solids. Their four binary STLs had zero nonmanifold edges in the generator's quantized-edge check. All reported static shell/component/reservation intersections were zero. These are computational checks of stated envelopes.

## Findings and implemented corrections

### M01 — two definite initial interferences; corrected

The first trial had **3.84mm³ base/lid overlap** at the two stepped-roof side ends, and **0.275038mm³ lid/PCB overlap** at the front hooks. Its final assertion failed even though earlier export stages had written files.

The side intersections occupied CAD X±[23.4,25],Y[−8,−7.2],Z[13.5,15]. The hook interference occupied X approximately±[20.6,20.9365],Y[−19.2,−18.5],Z[10.5,11.5]. Root cleared the bridge seating region and narrowed/repositioned front retention features with inner edges at|X|=21.4, outside the42mm board. The reviewed corrected snapshot has zero volume in these pairs. [Shell/retention construction](../scripts/build_q3_enclosure.py#L192).

### M02 — a complete soldered PCBA could not accept the one-piece lid; corrected by split lid

The original14.05mm closed holes cannot pass over the soldered key's larger upper housing/flange. Requiring the lid before switch soldering would conflict with customer enclosure printing and vendor-completed electronics.

Root split the lid at the two key centers, with three tongue/notch joints in the intervening webs. The front and rear halves now approach horizontally around the lower switch housings, underneath their flanges, before the covered board is fitted into the base. Keycaps are installed afterward. This supports the intended **no customer soldering** workflow without requiring the vendor to solder switches in a printed enclosure. [Split construction](../scripts/build_q3_enclosure.py#L228).

Independent STEP checks sampled both30mm approaches at0.25mm increments: **242 poses,4,549 bounding-box-filtered exact solid intersections, zero positive-volume collisions**. The rear approach included the fitted front lid; fixed objects included PCB, glass/FPC/terminals, both switch envelopes, USB body/top joints, MCU/JST and all bottom component envelopes. This checks sampled nominal clearance; it is not continuous-motion proof or a test of spring clips, print roughness or assembly force.

### M03 — keeper screw heads had only0.1mm nominal clearance; increased to0.7mm

The initial left keeper head lay beneath C10/R16; the right beneath R26/R27. Both screw heads ended atZ9.3 and the generic0603 envelopes began atZ9.4. This was not an intersecting nominal solid, but0.1mm was not a useful assembly tolerance margin.

Root raised PCB bottom from10.5 to11.1mm and moved its related lid, port, glass and keycap elevations by the same0.6mm, leaving battery/keeper fixed. The reviewed minimum is now **0.7mm** without changing PCB coordinates or selecting a different screw. Body footprint remains50×45mm; upper body height is17.1mm and provisional keycap envelope height30.4mm. Component and screw heights remain envelope assumptions.

## Drawing and geometry checks

| Check | Reviewed result |
| --- | --- |
| Coordinate alignment | Internal fit calculations use board coordinates minus(21,20); final exports reflect Y as defined above. DS1 center is PCB(15.75,5.5); J1 is bottom-side(38.9,15.3),270°. Rear mounts are read from H1(2,38.2)/H2(40,38.2). Key centers are(11.475,28)/(30.525,28), rather than footprint pin1 origins. Native drill positions create PCB holes. |
| Key plate | Plate top is5mm above PCB top; thickness1.5mm. This agrees with the manufacturer's plate diagram, whose5mm dimension is to the plate top. The14.05mm opening is at the high end of the specified14.00±0.05mm cutout; lower housing width13.95±0.05mm leaves only0.025mm per side at the largest body before print error. Print a fit coupon and verify clip seating. [HanElectricity drawing, PDFpp6/8](https://atta.szlcsc.com/upload/public/pdf/source/20250618/D1C12809F8EDF275373534C56A4C291D.pdf). |
| OLED opening/support | The model uses29×8.8×1.22mm glass, checked at29.15×8.95×1.27mm, and proposed0.2mm supports. The24.2×7.4mm opening is aligned to the asymmetric active area. Maximum glass has0.53mm to the roof underside. This is clearance, not a clamping/support qualification. [Wisevision drawing, PDFp5](https://atta.szlcsc.com/upload/public/pdf/source/20231103/222F0746A2795BBD5263EDDBD3E1B824.pdf). |
| FPC transition | Proposed slope drops0.7mm over8.5mm, using0.13mm maximum tail thickness. Its solder-face elevation, protected bond region, permitted bend and strain relief require supplier section/process approval. The drawing does not establish this proposed assembled fold as a confirmed production configuration. |
| USB/switch proximity | The four rotated pad-sized shell-joint envelopes extend0.5mm above PCB top. Their closest distance to the nominal SW2 lower body is0.905mm: PCB jointYmax20.12 versus bodyYmin21.025. This replaces the earlier unrotated conservative0.355mm estimate. All four joints have zero modeled switch intersection. Preserve the required≤0.5mm controlled top-fillets and actual stake/board-thickness inspection; neither a courtyard exception nor this nominal geometry is solder-process approval. [GCT USB4105 identity/drawing source](https://gct.co/connector/usb4105). |
| Battery and fasteners | Reviewed minimums: pack→bottom components3.4mm; pack→switch tails2.7mm; keeper→bottom components2.234mm; keeper-head→components0.7mm; pack→fasteners1.768mm; pressed-keycap→rear screw1.2mm. Pack/keeper gap remains0.3mm. M2 screw envelopes do not model thread engagement, print strength or loosening. |
| Key travel/rendering | Provisional hollow keycap geometry translated through4mm travel showed no nominal switch/lid collision. The rendered12345678 bitmap is obtained from actual `oled_pixel_byte()` output; this does not verify physical panel orientation, contrast, glass optical properties or exact purchased keycap geometry. |

## Assembly and remaining acceptance

The customer receives fully soldered electronics, loose keycaps and a separately insulated/disconnected vendor-prepared pack. Fit the two printed lid halves around the already-mounted switches with the board outside the base; join their laps. Install the approved pack/keeper, route and mate its keyed harness with electronics unpowered, then seat the covered board and fasten the case; install keycaps last. Actual clip/lap/front-hook engagement and the insertion path into the base still require a print/first-article trial.

The generator reserves wire corridors but does not model the complete mating JST housing, individual wires, strain relief or the finished40±5mm harness bend. It also reserves a USB plug volume without selecting a cable/overmold. Neither is a confirmed assembly fit. The21×4.2mm pack envelope does not approve the custom cell, tab insulation or attached NTC. OLED solder heat, compliant-support material, glass/bond stress, switch solder process, keycap stem fit, battery retention, fasteners and drop behavior remain explicit acceptance gates.

**Package discipline:** use the final hash-bound four-part candidate below and the actual split-cover rendering. Do not export or quote the superseded one-piece-lid trial as a completed design.


## Final-source addendum — 15 September 2026

The completed `mechanical/q3/` build returned exit0. The reviewer independently verified every input/output hash in its [build manifest](../mechanical/q3/build-manifest.json), read the [final fit report](../mechanical/q3/fit-report.json), and repeated the sampled assembly approaches using the final exported STEP.

| Final item | SHA-256 |
| --- | --- |
| Enclosure generator | `896d9ecaa392db3d6c942dbdec4499bb3f28c7f0e1b6d627d04789e4545ec7b3` |
| Native board | `b33b1e1d0c9e4d58c5642fc3f63faaa4e190092601f26103376537a5b12621fd` |
| Coordinated model | `6f3dbc9d34e34576b680ad77fb27a0f70313f038b3d74dab6b434705e55d1c79` |
| Final assembly STEP | `8216bd83e34c5f4dd797ca1bbf89bee6118f414fa21024622a63cdc2ddc41be8` |
| Final fit report | `6e08155f61778c9fa9c3597968e91514302efe1b65c21c816b1b58c6987bb01b` |

All four print parts remain valid single solids with zero nonmanifold STL edges. Reported static shell/component/reservation intersections are zero. Final clearances remain0.7mm keeper-head→bottom components,3.4mm pack→bottom components,2.7mm pack→switch tails and2.23397mm keeper→bottom components. The final OLED capacitor moves are included in these native-footprint envelopes.

The final independent STEP approach check tested **242 poses,4,837 bounding-box-filtered exact solid intersections, zero positive-volume collisions**, including all85 fixed component/support envelopes and the fitted front lid during the rear approach. In the final right-handed output frame, the front approaches fromY+30mm to0 and the rear fromY−30mm to0, each sampled every0.25mm. This supersedes the earlier path-test hash for the final candidate. It remains a sampled nominal-geometry check, not continuous motion or physical clip/print/assembly qualification.

The final exports apply the documented global Y reflection. The four printable parts, raised board and split-cover assembly fixes are present. All supplier-section, solder, harness, battery, retention and physical-fit conditions above remain open.
