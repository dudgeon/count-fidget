# Q1 quote import audit

Verified locally on **2026-09-15 at 00:47:55 UTC** (September 14 Eastern). This is a read-only audit of the existing BOM, RFQ, native PCB and Gerber metadata. It does not change the circuit, placement, routed board, firmware or manufacturing package and does not qualify or release the prototype.

## Assembly counts for quotation forms

Counts are per finished board. Identical manufacturer, manufacturer part number and footprint combinations are grouped when counting unique part types; the importer CSV itself has one row per PCB reference.

| Quantity | Verified count | Evidence / interpretation |
|---|---:|---|
| Fitted PCB references / importer rows | 46 | `procurement/BOM-PCBA-Q1.csv` |
| Unique fitted PCB part types | 32 | 30 SMT types plus 2 THT-only types |
| Unique SMT part types | 30 | Grouped manufacturer/MPN/footprint combinations, including mixed-mount J1 |
| SMT placements | 43 | 46 fitted components less DS1, SW1 and SW2 |
| Top SMT placements | 3 | U1, J1, J2 |
| Bottom SMT placements | 40 | All other SMT references |
| THT-only components | 3 | DS1, SW1, SW2; all installed from the top |
| Unique THT-only part types | 2 | One LCD type and one switch type |
| THT electrical leads | 24 | DS1 has 20 leads; SW1 and SW2 have 2 electrical leads each |
| Additional plated USB shell tabs | 4 | J1, explicitly requiring solder in the RFQ |
| Total through-hole solder joints | 28 | 24 component leads plus 4 USB shell tabs |

SMT assembly is **both sides**. J1 is a mixed SMT/THT component with 16 SMT contacts and four plated shell tabs. It is counted once among the 43 SMT placements; the shell joints are additional soldering work, not an additional purchased component. Four physical components require some through-hole soldering (DS1, SW1, SW2 and J1), of which three are THT-only. If a vendor form asks for through-hole pins/joints, include all 28 and explain this split.

The Cherry switch's “5-pin” description includes three unsoldered plastic locating posts. The native footprint contains two plated electrical pads and three nonplated holes per switch; do not count five electrical pins. J1's two nonplated locating holes are also excluded from solder-joint counts.

BAT1 and K1/K2 remain separately supplied offboard items, with no PCB placement coordinates. TP1–TP10 and H1–H2 are PCB features rather than purchased components. None increases the 46-reference PCB count; none removes the battery harness or loose caps from commercial scope.

### Count evidence

- `procurement/BOM-PCBA-Q1.csv`: exact manufacturer/MPN/footprint, reference, quantity and side data.
- `procurement/RFQ-Q1.md`, “PCB fabrication and assembly”: top/bottom assembly scope, 20-lead LCD, switch mounting and all four USB shell tabs.
- `electronics/click-counter-Q1.kicad_pcb`: DS1 pads 1–20; SW1/SW2 plated pads 1–2 and three nonplated holes each; J1's 16 SMD pads, four `SH` plated through-hole pads and two nonplated holes.
- `procurement/OFFBOARD-items-Q1.csv`: BAT1 harness and two loose keycaps outside PCB placement scope.

## Quote specification and metadata discrepancies

The **RFQ and explicitly selected/disclosed website form specifications control the quotation**. The following Gerber-job metadata must not silently override those specifications. Vendor confirmation of the actual finish, stackup, finished dimensions and thickness tolerance is still required. No metadata or manufacturing files were regenerated during this audit.

| Item | RFQ / documented form baseline | Existing Gerber-job metadata | Required quote clarification |
|---|---|---|---|
| Finish | ENIG, nominal 1 microinch gold; green mask and white legends | `GeneralSpecs.Finish` is `None` | Quote ENIG 1 microinch; obtain vendor acknowledgment that `None` does not control the requested finish |
| Copper | RFQ: 1 oz outer, preferred 0.5 oz inner; prior PCBWay form: 1 oz outer / 1 oz inner minimum | All four copper entries in `MaterialStackup` have `Thickness: 0.035` mm | Quote the standard 1/1 oz stack and separately identify availability and price of the preferred 0.5 oz inner alternative; do not present unequal stacks as identical |
| Finished outline | 42 × 40 mm with 2 mm corner radius | `GeneralSpecs.Size` is 42.05 × 40.05 mm | Follow the 42 × 40 mm profile centerline; confirm finished dimensions and tolerance with the vendor |
| Finished thickness / material | 1.0 mm; FR-4 Tg150+; prior PCBWay form S1000H TG150 | Board thickness is 1.0 mm; material entries say FR4 | Confirm actual material/stackup and achievable finished thickness tolerance; metadata does not establish Tg150 compliance |

The native `Edge.Cuts` centerline extends from x=0 to x=42 and y=0 to y=40 mm, with 2 mm corner arcs and a 0.05 mm drawing stroke. `electronics/gerbers/click-counter-Q1-Edge_Cuts.gm1` encodes the same profile using a 0.050000 mm aperture. The Gerber-job's additional 0.05 mm on each overall dimension is consistent with the stroke's bounding box; it is not a requested change to the finished board size. Vendor outline interpretation still needs confirmation.

The documented RFQ, import notes and previous form agree on ENIG 1 microinch, green mask, white legends and lead-free assembly. The finish conflict is in the job metadata. The inner-copper difference is already a disclosed quotation alternative, not an approved substitution or an instruction to rebuild the board.

### Specification evidence

- `procurement/RFQ-Q1.md`, PCB specification table: dimensions, layers, thickness, material, copper, finish, minimum features and assembly process.
- `procurement/WEBSITE-IMPORT-NOTES-Q1.md`: PCBWay standard inner-copper minimum, preferred alternative and stated finish.
- `procurement/vendor-status.md`, “Last confirmed form values”: S1000H TG150, 1 oz outer/inner form baseline and ENIG 1 microinch.
- `electronics/gerbers/click-counter-Q1-job.gbrjob`: `GeneralSpecs` finish/dimensions/thickness and `MaterialStackup` copper/material entries.
- `electronics/click-counter-Q1.kicad_pcb` and `electronics/gerbers/click-counter-Q1-Edge_Cuts.gm1`: finished-outline centerline geometry and stroke width.

Track vendor acknowledgment and any controlled pre-release metadata reconciliation under **E13** in `docs/open-issues.md`. Existing hardware, schematic/ERC, battery/protection, display and enclosure release gates remain open. A quote or a metadata clarification does not authorize paid procurement or manufacture.
