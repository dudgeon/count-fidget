# Q3 two-layer routing candidate

This is an unqualified engineering candidate. Native connectivity and copper
checks do not authorize manufacture or establish measured electrical behavior.

## Construction and placement

- Two copper layers, requested 1.0 mm board, 1 oz outer copper. The explicit
  0.93 mm dielectric allocation is provisional pending fabricator stackup.
- All SMT components are on the bottom. The OLED solder lands and two
  vendor-soldered keys are on the top. The display's solder/FPC transition and
  its support need the separate mechanical/process review.
- Display origin is (15.75, 5.5) mm. The original switch centers are retained.
  USB J1 remains (38.9, 15.3) mm; mounts move to (2, 38.2) and (40, 38.2) mm.
- The exact HanElectricity switch uses two 1.50 mm terminal drills and one
  3.95 mm center drill, with no invented locator feet. Its full body courtyard
  replaces the undersized historical Cherry projection.

## Reviewed local routing

`preroute_q3.py` locks the TPS63900 inductor, input/output capacitor branches,
exposed-pad returns, MCU bypass branches, comparator bypass and independent
gate pulldowns before the general route. The Murata inductor's embedded copper
and via keepouts remain intact. Exposed-pad vias sit outside solderable lands.
The native checkpoint has LX1 length 2.374 mm and LX2 length 2.623 mm, with no
via in either switching leg. Both outer layers carry GND pours.

`finish_q3_board.py` retains every locked seed while importing the incremental
SES, removes pointless single-pad no-connect fanout copper, synchronizes the
native schematic fields, and fills both pours. The independently reviewed pump cluster uses ordered short locked escapes
and local bypass/ground connections. A direct local logic-bypass branch avoids
returning through the remote common supply join. A separate bottom trace joins the USB-powered thermal-divider branch around the top of its own
sense trace; the comparator keeps its close local bypass.

The saved native checkpoint reports zero unconnected items, zero schematic
parity issues and zero copper/clearance/edge violations. It retains the single
specific courtyard projection below. The final independent hash-bound
validation report governs package validity; the routing checkpoint is only
supporting history.

## Explicit connector/switch courtyard projection

The native report retains exactly one `pth_inside_courtyard` finding: J1's SH
pad at (35.795, 19.62) mm under SW2's raised flange. No electrical clearance,
short-circuit, hole or board-edge finding is waived. The exact pad and footprint
UUIDs are recorded in the native report and independent verifier.

The rotated shell land is 2.1 by 1.0 mm in board coordinates, ending at
Y=20.12 mm. The Han lower 13.95 mm square housing begins at Y=21.025 mm, giving
0.905 mm nominal separation from that land. The upper flange underside is
5.00 mm above the switch's PCB seating plane. A proposed upper solder-fillet
limit of 0.5 mm fits below that raised flange. Placement, solder and housing
tolerances, access for the assembler and actual first-article fit still require
qualification. The nominal geometry is not a physical-fit claim.

Sources: [GCT USB4105 drawing](https://gct.co/files/drawings/usb4105.pdf) and
[HanElectricity CPG151101D13 drawing](https://atta.szlcsc.com/upload/public/pdf/source/20250618/D1C12809F8EDF275373534C56A4C291D.pdf).
The Han mounting figure's 5 mm dimension reaches the **plate top**, which is
also the flange underside. Its 1.5 mm plate therefore spans 3.5–5.0 mm above
the PCB seating plane; it is not a 5 mm plate-underside dimension.

## Required electrical review and measurements

The final OLED flying-capacitor legs are C2P 3.380 mm, C2N 5.281 mm,
C1P 3.942 mm and C1N 3.489 mm, with one through via per leg. Independent
review identified the earlier avoidable 11 mm detour; the closer capacitor
cluster and locked paths correct it. The DS1 pin5-to-C27 positive path is
3.183 mm with one via; its explicit pin7-to-C27 ground path is 6.178 mm with
two vias. The C20 logic-bypass positive path to DS1 pin8 is 6.329 mm with one
via, and its local ground stub is 1.100 mm to a ground stitch. These are planar
centerline lengths, excluding 1 mm through-via barrel depths and capacitor
internals. They do not establish ground impedance or transient performance.
No numeric maximum PCB trace length was found in the cited OLED documents;
shortening these avoidable paths is engineering judgment about loop area and
parasitics, not a manufacturer-specified length limit. A clean DRC does not
prove charge-pump ripple or transient behavior. Verify the 4 V converter rail,
switched OLED VBAT, internal 9 V rail, local input/output effective capacitance,
startup/current-limit behavior, peak protected-cell current and brightness
under the actual sparse-display firmware before releasing hardware.

Grounded USB shells, U2/U6 exposed pads and D1 pad2 use solid pours. The
D1 ground pad receives a solid connection because its small available copper
area could not support two thermal spokes. Assembly must account
for the resulting solder heat demand. The frozen Q1 and Q2 packages remain
unchanged.

## Native routing inputs

The actual router-input DSN and incremental SES hashes are recorded in
`electronics/q3/routing-checkpoint-Q3.json`. The final preroute source includes
the reviewed relocation of one OLED ground stitch after that DSN was exported;
fixed seed geometry is absent from the SES, so the final board carries the
reviewed seed. `prepare_q3_route.py` can apply model positions and reset routes
while preserving footprint UUIDs. These helpers never modify Q1/Q2. All
reconstructed output still requires fresh independent native validation.
