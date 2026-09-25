# Q2 independent native validation

Q2 is an **unreleased engineering candidate**. This verifier checks design-file consistency and native KiCad rules. It does not qualify battery protection, analog thresholds, power sequencing, effective capacitance, LCD waveforms, firmware on hardware, physical fit or manufacturing safety.

## Recheck the saved evidence

From the repository root, using Python 3.9 or later:

```sh
python3 scripts/verify_q2.py
```

This requires no KiCad or `pcbnew` installation. It compares the current model with the exported native schematic and native board, and requires matching hashes for the exact inputs and native reports from the last successful check. A changed board, schematic, model, local library, relevant generator, project/rule configuration or verifier invalidates the evidence. The schematic export manifest and its PDF/SVG drawings are also checked against current source and artifact hashes; a stale drawing is not accepted alongside a newer native design. Added schematic/library files also invalidate the recorded inventory. A missing or stale report is a failure, not an assumed pass.

## Generate fresh native evidence

After finalizing the model, regenerating the schematic and completing the routed PCB:

```sh
python3 scripts/verify_q2.py --kicad-cli /path/to/kicad-cli
```

The validated native workflow uses KiCad 10. It sequentially exports a new XML netlist, runs schematic ERC, then runs PCB DRC with **schematic parity, all track errors and all severities including exclusions**. No board-save or zone-refill option is used. Finish the layout and fill zones first. Runtime configuration can be isolated through `KICAD_CONFIG_HOME`; on this macOS session the official mounted CLI required an approved execution outside the process sandbox for PCB DRC. That is a runtime requirement, not an altered rule configuration.

Successful execution writes:

- `verification/q2-native-netlist.xml`: fresh native schematic export, with only the absolute source-path metadata normalized to a repository-relative path.
- `verification/q2-native-erc.json`: native electrical-rule report.
- `verification/q2-native-drc.json`: native layout, connectivity and schematic-parity report.
- `verification/q2-validation.json`: input/report SHA256 hashes, exact command arguments, executable hash/version, native check configuration and independent check results.

The new XML must agree with the public `schematic-netlist-Q2.xml`. Inputs must remain byte-identical throughout the native runs. All native violation, unconnected and parity arrays must be empty. An empty parity array alone is insufficient: the verifier also requires the recorded command to contain the parity option.

## Independent checks

The verifier uses Python's standard library and the repository's read-only S-expression parser; it does not import `pcbnew` or rely on board-generator success messages. It checks:

- Exact 62-reference sets: 50 fitted parts, ten fixture lands and two mounting holes.
- Exact MPN, Value, local footprint identity and full schematic instance path for every board footprint.
- All 195 connected physical pin assignments and 28 individually isolated no-connect pin nets, including every repeated native pad with the same logical pin number. It rejects copper assigned to those no-connect nets. J2's independent anchors use distinct `MP1`/`MP2` no-connect identities. KiCad's native `{slash}` escape in generated pin/net names is decoded to `/` for comparison with its XML export; this does not alter connectivity or source files.
- Every footprint position, rotation and side against the current model; unique native PCB UUIDs; four copper layers, 1.0 mm thickness and the exact 42 × 40 mm outline with four 2 mm corner arcs (including arc midpoints, so endpoint-only bounds cannot hide a bulging edge).
- U5's TI DGK land dimensions (1.40 × 0.45 mm), 0.65 mm pitch, 4.40 mm row centers, 0.05 mm round corners and 0.05 mm solder-mask expansion. These are file geometry checks; vendor process acceptance remains open.
- DE188's two ten-pad rows at nominal 13.0 mm spacing, 2.54 mm lead pitch and the retained 1.7 mm drill assumption.
- The five isolated LCD reservoir/pump nets retain only locked segments and exactly one locked through via each; total copper trace length is below 5 mm per net. This catches fixed-route loss or long detour replacement during general routing. V3/GND are multi-endpoint rails and are not given a misleading whole-net length limit.
- C14–C16 reservoir connections at MCU pins 7/8/9, the separate C8 charge-pump connection, C6's nominal 10 µF correction and the explicit TPS7A0230PDBVR output-discharge variant.
- Separate TLV7032 push-pull outputs, two series enable FETs with the intended gate/source/drain nets, 100 kΩ gate pulldowns and CE_N pull-up. Each pulldown's signal-pad center must be less than 3 mm from its FET gate-pad center. This measures straight-line placement proximity, not route length or parasitics.

The default ignored-rule allowlists are explicit in the verifier and repeated from the actual native reports in the validation manifest. Any additional ignored rule fails validation. Existing defaults such as missing courtyard or single-use global-label checks do not imply that those properties have been qualified.

For an intermediate consistency check while routing is still in progress:

```sh
python3 scripts/verify_q2.py --semantic-only
```

This mode prints a deliberately limited result. It does **not** check native report freshness, generate a final validation manifest or establish DRC/ERC/parity success.

## Separate release gates

Run `python3 scripts/verify_project.py` separately for the frozen Q1 package. Q2 verification never rebuilds or updates that archive. Existing engineering issues and first-article measurements remain controlling even when every file-level check passes. No validation result authorizes payment or manufacture.

## Recorded final candidate check

The saved native reports for board SHA256 `c80cf17a1d36d74e4c7c8f7cc4e14f5f42169fe0c3224811856b8bff0e5d0867` passed with KiCad 10.0.6: **0 DRC violations, 0 unconnected items, 0 schematic-parity findings and 0 ERC violations**. The default read-only verifier then accepted the saved input/report bindings.

Measured locked copper lengths are 2.981003 mm (LCD_R13), 3.171061 mm (LCD_R23), 3.912805 mm (LCD_R33), 3.079962 mm (LCDCAP0) and 3.287069 mm (LCDCAP1), each with one locked through via. Gate-pulldown pad-center distances are 1.737500 mm for R14/Q3 and 1.743963 mm for R15/Q4.

Temporary copied-file and in-memory negative checks rejected **21 deliberate corruptions**: 13 changes to part/net identity, NC isolation, placement, display/outline/mask geometry, UUID uniqueness or critical route integrity; and eight changes to source/report hash bindings, required native parity invocation, ignored rules, included severities or nonzero native findings. The untouched baseline passed before and after. These checks did not alter repository design artifacts. The result remains a design-file check, with the physical and purchasing holds above unchanged.
