# Native Q2 schematic candidate

Open `click-counter-Q2.kicad_sch` in KiCad 10. The index links five functional sheets: MCU/LCD, USB/charger/regulator, battery/protection, temperature window and keys. `schematic-Q2.pdf` and `schematic-svg/` are native KiCad exports, visually reviewed. Global labels connect sheets; all physical IC/connector pins are explicit, including crosses on unused pins. Custom symbols and all footprint references are project-local.

The circuit is an **engineering candidate, not manufacturing release**. A clean ERC does not establish analog operation, protection limits, power sequencing, physical fit or safe battery behavior. Q1's submitted package and native board remain separate and unchanged.

## Reproduce and inspect

From the repository root, with a KiCad 10 CLI available:

```sh
python3 scripts/build_q2_schematic.py --kicad-cli /path/to/kicad-cli
```

The generator reads `scripts/build_q2_model.py` and the preserved Q1 connectivity baseline. It creates deterministic root/sheet/symbol UUIDs, six native sheets and `CountFidgetQ2.kicad_sym`; it does not edit the PCB. `schematic-paths-Q2.json` supplies each footprint's complete native schematic path. Changing the model requires regeneration and fresh validation before using the artifacts.

The optional CLI argument performs native netlist export, ERC with all severities, PDF and SVG exports **sequentially** (macOS CLI instances share a lock). It then checks the exported references, Value, MPN, footprint identity and every model pin/net. KiCad's absolute source-path metadata is normalized to the repository-relative schematic path in the public XML. No connectivity data is normalized away. Runtime configuration can be isolated using KiCad's documented `KICAD_CONFIG_HOME`; the current session's mounted tool paths are temporary, not portable dependencies.

`schematic-validation-Q2.json` records source/artifact hashes, command arguments, check results, exact NC nets and limitations. `erc-Q2.json` is the native detailed check report. The final observed results are:

- **6 sheets; 62 references**: 50 fitted PCB components, 10 pogo lands, 2 mounting holes.
- **195 connected pin assignments** match the model.
- **28 explicit unused physical pins** each have a unique exported no-connect net; none joins another reference/pin. J2's independent mechanical anchors have separate `MP1` and `MP2` no-connect identities, so no copper connection between them is implied.
- **0 ERC violations** under the recorded KiCad 10.0.6 configuration. Native PCB physical pad-number sets were separately compared against the schematic and matched for every footprint.

KiCad's recorded default ignored checks are `single_global_label`, `four_way_junction`, `simulation_model_issue` and `footprint_filter`. No electrical error was hidden to obtain the zero result. Footprint association is still checked against the exported model field. The report is not a SPICE simulation or proof that a component is safe outside its ratings.

## Symbol and supply conventions

The 48-pin MCU uses the [TI DGG pin diagram](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf). Regulator, charger, protector and comparator names/types follow their primary TI pin tables: [TPS7A02](https://www.ti.com/lit/ds/symlink/tps7a02.pdf), [BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf), [BQ2970](https://www.ti.com/lit/ds/symlink/bq2970.pdf) and [TLV7032](https://www.ti.com/lit/ds/symlink/tlv7032.pdf). Symbols distinguish power inputs/outputs, digital/analog inputs, push-pull outputs, open-drain status outputs and bidirectional GPIO. U2's BAT pin is passive because the power path is bidirectional. U3 pad 4 is labeled `NC/GND-permitted` and connected as allowed by its datasheet. U2 status outputs and U4's NC pin are explicitly unused.

Four visible **SUPPLY ASSERTION** markers describe sources that ERC cannot infer through connectors/passive components: external USB VBUS, system return GND, raw cell return CELL_N_RAW, and filtered cell supply BAT_SENSE through R7. They are not fitted components, added electrical connections or approval of the protection topology. In particular, CELL_N_RAW and GND remain distinct nets. U2 SYS and U3 OUT retain actual power-output types; comparator outputs remain separate. Unresolved protection, thermal, first-article and purchase gates still apply.

## Complete board validation

See [VALIDATION-README.md](VALIDATION-README.md) for the independent model/schematic/PCB checker and fresh native DRC/ERC/parity evidence. Schematic-only success does not establish routed-board consistency.
