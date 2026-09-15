# Independent review of the Q2 candidate

**2026-09-15 — engineering review, not manufacturing release.** Reviewed the Q2 model, native board, local footprint library, schematic XML and firmware source. This report records confirmed findings, the preliminary route and subsequent routing corrections. **Final native PCB checks passed after the last via correction: 0 physical violations, 0 unconnected items and 0 schematic-parity issues.** The separate complete hash-bound validation record is being finalized. No hardware qualification or manufacturing release is implied. Q1 remains preserved.

## Confirmed new findings and corrections

### E19: insufficient nominal MCU bulk capacitance inherited from Q1

The initial Q2 model retained C6=2.2 µF on V3. C7 adds 0.1 µF; C2's 10 µF is on upstream SYS and does not supply equivalent local DVCC bypassing through the regulator. TI specifies CDVCC **4.7 µF minimum, 10 µF nominal** in §8.3, with capacitor tolerance addressed in note 5. Its layout guidance also places the bypass/decoupling parts near DVCC/DVSS. This was a confirmed departure from the recommendation, not a measured failure. [TI MSP430FR413x datasheet, §8.3 and §10.1.1](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf).

`scripts/build_q2_model.py` now assigns C6 the already specified **GRM21BR61E106KA73L**, 10 µF, 25 V, X5R, ±10%, on the same 0805 land. This corrects the nominal shortfall. **At least 4.7 µF effective at 3 V after DC bias, temperature and tolerance remains a qualification condition.** Nominal 10 µF alone does not establish that bound. Keep supply ramp, output collapse, reverse-current and interrupted-FRAM-write tests open for the chosen TPS7A0230PDBVR variant. See [the power design](q2-power-design.md).

### Local parts initially had long electrical connections

The first model placed R14/R15 roughly 19 mm from the Q3/Q4 gates, contrary to the local-pulldown intent. The revised model places R14 at (17.5,25.45), R15 at (17.5,29.6), both 180°. Their pad-center distances to the respective gate are about **1.74 mm**. C7 was moved from (25,4.3) to (22.6,12.5); C8 moved to (20,10.1). C14–C16 are the new LCD bias reservoirs.

**Placement distance did not predict actual routed length.** The subsequent autoroute still took several capacitor paths around unnecessary detours and through extra layers. Those paths were reported and shortened in the subsequent routing correction below. The original measured snapshot is retained for comparison. DRC cannot by itself certify supply-loop quality, LCD charge-pump stability or immunity to transients.

### Connector anchor semantics and native parity

The original J2 footprint assigns both independent mechanical solder anchors the pad number `MP`. With one explicit NC net, native DRC requests a copper connection between them. Copying `passive+no_connect` pin metadata did not eliminate that requirement. The agreed correction is **distinct MP1/MP2 anchors with separate NC markers**, preserving J2's four electrical pins. Do not add an electrical strap merely to satisfy that duplicate-number representation.

The schematic owner generated `unconnected-(J2-ANCHOR1-PadMP1)` and `unconnected-(J2-ANCHOR2-PadMP2)`. The layout owner must retain matching native/library pad numbers. There are then 195 connected schematic pins and 28 unique explicit NC pins; current validation must confirm the final files.

`scripts/sync_q2_board.py` now copies Description/MPN/Datasheet and pin metadata, and converts XML `/` characters in NC pin-function names to native `{slash}` spelling. This removed the preliminary field/name parity mismatches without excluding DRC rules. An NC name change is not a new electrical connection.

## Pin mapping and footprint checks

| Area | Reviewed result | Remaining limit |
|---|---|---|
| U5 TLV7032DGKR | Bottom footprint follows the device pin table: OUTA=1, INA−=2, INA+=3, GND=4, INB+=5, INB−=6, OUTB=7, VBUS=8. Cold and hot comparisons command separate FET gates. | Correct connectivity is not proof of all supply-loss, stuck-output or sensor-fault behavior. |
| Q3/Q4 2N7002,215 | Bottom-side transformation preserves 1 gate, 2 source, 3 drain. Q3 source=CE_MID/drain=CE_N; Q4 source=GND/drain=CE_MID. Source-to-drain diodes do not form a positive CE_N-to-ground bypass when either FET is off. | A gate is passively held off only while its connection to an intact pulldown remains. |
| U1 LCD bias | Pins 7/8/9 connect to LCD_R13/R23/R33 and C14/C15/C16 respectively. Pump capacitor C8 remains across pins 10/11, LCDCAP1/0. | Native route, capacitance, drive waveform and actual glass response still require checking. |
| U3 | Exact TPS7A0230PDBVR is recorded, including active output discharge; 1 IN/2 GND/3 EN/4 NC/5 OUT mapping is retained. | Retain output-collapse, reverse-current and startup tests. |
| U5 DGK lands | Full TI example: 1.4×0.45 mm lands, 0.65 mm pitch, 4.4 mm row-center span, R0.05 corners. Copper gap 0.20 mm; with 0.05 mm mask margin, nominal mask web 0.10 mm. | Vendor acceptance of actual mask/paste geometry remains open. |
| Copied footprint library | Q2 uses project-local copies; `source_footprint` records provenance. The reviewed current model/native pad nets, sides and rotations agreed. | Copies preserve Q1 modifications, including stripped silk; they are not claimed identical to a current stock library or physically qualified. |

Primary pin/polarity sources: [TI TLV7032/42 Table 4-2 and DGK drawing 4214862/A](https://www.ti.com/lit/ds/symlink/tlv7032.pdf), [Nexperia 2N7002 pinning](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf), [TI TPS7A02 Table 5-1](https://www.ti.com/lit/gpn/TPS7A02). The detailed tolerance/fault analysis is in [q2-power-independent-review.md](q2-power-independent-review.md); the vendor mask question and complete TI land-pattern comparison are in [q2-solder-mask-review.md](q2-solder-mask-review.md).

The MCU is on **F.Cu**; the reviewed capacitors and enable FETs are on **B.Cu**. A short projected pad distance therefore often needs a via. The LCD's 2.2 mm through-hole pads at y=15.25 also constrain the space below the MCU. Review via-to-pad clearance and solder-wicking exposure when shortening connections; do not assume a straight connection drawn in projection is physically valid.

## Routing corrections — native PCB checks passed

The critical capacitor and gate paths are now explicitly routed and locked by `scripts/preroute_q2.py`. General routing uses this existing copper as a fixed starting point. `scripts/finish_q2_board.py --import-route` preserves the locked paths while importing the matching incremental SES; it must not replace them with an unrelated full route. The following **fresh 2026-09-15 route extraction** confirms that the earlier capacitor detours were shortened:

| Explicit connection | Revised length (mm) | Through vias | Preliminary length (mm) |
|---|---:|---:|---:|
| C7.1 → U1.15 DVCC | **2.733** | **1** | 9.457 |
| C8.1 → U1.10 LCDCAP1 | **3.287** | **1** | 4.241 |
| C8.2 → U1.11 LCDCAP0 | **3.080** | **1** | 4.393 |
| C14.1 → U1.7 LCD_R13 | **2.981** | **1** | 4.619 |
| C15.1 → U1.8 LCD_R23 | **3.171** | **1** | 11.102 |
| C16.1 → U1.9 LCD_R33 | **3.913** | **1** | 8.519 |
| C9.1 → U5.8 VBUS | **1.941** | **0** | 8.459 |
| R14.1 → Q3.1 gate | **1.738** | **0** | 1.738 |
| R15.1 → Q4.1 gate | **1.800** | **0** | 1.800 |

Local ground returns were added. Explicit trace distances from each ground pad to its nearest ground via are now **C7 1.312 mm, C9 0.910 mm, C14 1.144 mm, C15 1.312 mm, C16 0.885 mm, R14 0.950 mm and R15 0.950 mm**. These figures stop at the via; they exclude the through-via barrel and ground-plane spreading path. The extraction's longer trace-only capacitor-to-IC ground routes are not the complete or shortest return paths through the filled planes. Neither set of lengths establishes loop impedance or measured transient behavior.

### Plane connections and via clearance

J1's shell pads and **SW2 pad 2** now use deliberate **solid GND plane connections** to resolve isolated thermal-relief islands. This is a pad-specific connection change, not a disabled thermal DRC rule. The assembler must account for the increased soldering heat demand and confirm its process; no solder-quality result has been measured.

A separate same-net via/land check found approximately **0.025 mm overlap** between the Q4 source land and the ground via formerly at **(19.05,27.55)**. The final correction moves the via to **(19.05,26.80)** and moves the attached GND endpoints together, including when the existing SES is reimported. The layout audit reports at least **0.208 mm conservative clearance** there to all other-net copper and solderable lands, with no remaining via/land overlap. Same-net manufacturing clearance is a separate check because ordinary electrical-clearance DRC can permit same-net overlap.

Fresh native DRC **after the final move**, saved at **2026-09-15 06:48:00 EDT (10:48:00 UTC)**, reports **0 physical violations / 0 unconnected / 0 schematic-parity issues**. The board SHA-256 at this check is:

`c80cf17a1d36d74e4c7c8f7cc4e14f5f42169fe0c3224811856b8bff0e5d0867`

The independently read native DRC report SHA-256 is:

`2ad98d6f19547710c3820496b2a7569505426a7050dbaab119f18ee0304b0451`

The complete Q2 validation/export manifest is a separate finalization step. Future board edits invalidate this exact-file result; rerun native checks and update the corresponding hashes.

The same audit found eight nearby, non-overlapping via/land pairs. These are conservative **bounding-land-to-via-copper gaps**, not measured finished mask webs or hole clearances:

| SMD land | Gap (mm) |
|---|---:|
| R17.1 | 0.0659 |
| C11.1 | 0.0380 |
| D1.5 | 0.0944 |
| C1.1 | 0.0720 |
| R2.1 | 0.0684 |
| J2.1 | 0.0816 |
| J2.2 | 0.0928 |
| R12.2 | 0.0777 |

Through vias are tented on both sides. **Vendor acceptance of the exact mask/tenting geometry and registration tolerance remains open.** Filling/capping is not specified as a requirement by this review. Do not treat nominal non-overlap or a tenting setting as proof that fabrication will prevent solder wicking. Preserve this DFM question in the quote/assembly scope.

## Preliminary route snapshot — corrections were still required

The following measurements refer only to native board SHA-256:

`00f0a1bcfc18963eee4a62284d075563a19e20de66f26d2171fcbcca7c2ca353`

This board was handed back for routing completion on 2026-09-15. It is **not the final routed-board acceptance record**.

Lengths below are sums of explicit planar track segments and pad-center connections; via counts are unique traversed through vias. They exclude vertical barrel length, parasitics and filled-plane spreading paths. Ground-only trace distances must not be interpreted as the shortest complete return path through the planes.

| Explicit connection | Length (mm) | Through vias | Assessment at snapshot |
|---|---:|---:|---|
| C7.1 → U1.15 DVCC | 9.457 | 2 | Material decoupling detour; shorten. |
| C8.1 → U1.10 LCDCAP1 | 4.241 | 1 | Review together with pump return. |
| C8.2 → U1.11 LCDCAP0 | 4.393 | 1 | Review together with pump outgoing path. |
| C14.1 → U1.7 LCD_R13 | 4.619 | 1 | Review local bias routing. |
| C15.1 → U1.8 LCD_R23 | 11.102 | 2 | Material bias detour; shorten. |
| C16.1 → U1.9 LCD_R33 | 8.519 | 1 | Material bias detour; shorten. |
| C9.1 → U5.8 VBUS | 8.459 | 2 | Material comparator decoupling detour; shorten. |
| R14.1 → Q3.1 gate | 1.738 | 0 | Local gate trace achieved. |
| R15.1 → Q4.1 gate | 1.800 | 0 | Local gate trace achieved. |

Nearest ground-via distances along **explicit traces only** were C7=7.196 mm, C9=15.377 mm, C14=5.728 mm, C15=4.128 mm, C16=5.596 mm, R14=6.953 mm and R15=12.799 mm. Local ground returns should be reviewed and improved with the corresponding signal route. No impedance or transient result is inferred from these lengths.

The native DRC saved at **2026-09-15 06:09:02 EDT** reported **one physical violation, one unconnected item and zero schematic-parity issues** before the later anchor-symbol change:

- J1 SH at (35.795,17.62): incomplete thermal relief on In1.Cu; one spoke connected to an isolated island. Resolve copper/zone geometry or use a deliberately reviewed pad connection and assembly process. No global thermal-rule disabling was applied.
- J2's two `MP` anchors at (6.875,14.0) and (6.875,19.6): missing connection caused by the duplicate pin representation described above.

An earlier R15/TP9 courtyard overlap was corrected by moving R15 from y=29.9 to **29.6**. The last checked route had no such overlap. The LCD_R13 unconnected item and dangling vias seen in an earlier route were absent from this snapshot; rerouting still requires a fresh complete check.

## Programming, unused pins and open qualifications

The existing test-pad map remains TP1=GND, TP2=V3 sense, TP3=SBWTDIO and TP4=SBWTCK. R16 is 47 kΩ; C10 is 1 nF ±5%. TI limits the reset pulldown capacitance to 1.1 nF for its programming tools. Including 1.05 nF component tolerance leaves roughly 50 pF for other loading before that bound; fixture/trace loading and actual programming remain unmeasured. [TI §7.4 and §10.1.3–10.1.4](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf).

The firmware selects REFO for ACLK and initializes unused P4 GPIO outputs low (`firmware/main_msp430.c`). Thus leaving P4.2/XOUT and P4.1/XIN physically open is consistent with the chosen internal-clock implementation. U1 P1.1/P1.0 are button inputs, despite their secondary UART functions; no UART connector is required by the current interface. USB remains charging-only. These observations do not qualify clock timing, button behavior or programming on hardware.

The requested native stackup is 1.0 mm nominal with outer copper 35 µm, inner copper 17.5 µm, proposed FR4 dielectric thicknesses 0.200/0.495/0.200 mm, green mask and ENIG. Copper plus dielectric sums to 1.0 mm. This is a **proposed construction pending fabricator acknowledgement**, not a verified material stackup. The measured outline's centerline is 42×40 mm; the 0.05 mm edge stroke yields 42.05×40.05 mm graphic bounds. Do not silently substitute stroke bounds for the intended finished outline.

No review here closes the cell/protector temperature range, low-current charging, installed NTC response, LDO behavior, effective capacitance, LCD waveforms/response, physical fit or first-article tests. Retain all engineering gaps and the concrete-order approval gate. Fresh ERC/DRC, connectivity/field parity and export hashes are necessary before quote artifacts are described as checked; those checks still do not constitute hardware qualification.
