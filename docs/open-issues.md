# Open issues

## Q5 status — 25 September 2026

GitHub issues #2–#9, #12 and #13 from the Q4 simulation review are resolved in the Q5 design files. See the per-issue table in [REVIEW-Q5](REVIEW-Q5-2026-09-25.md). The following remain open as physical gates. They are not closed by any file in this repository:

| ID | Q5 open item | Required closure |
|---|---|---|
| E28 | Soft power latch: minimum press to latch, U7 release, USB unplug during Stop | Scope SYS_ON/SYS_LOAD with a real MX contact; confirm the board never half-powers |
| E29 | Battery sense and gauge | Calibrate PA4 through the 75 kΩ source; check the 3.95/3.80/3.70/3.55/3.35 V thresholds against a real LIR2032 under display load; measure ~8 µA off current |
| E30 | Cell holder and first connection | Holder contact resistance and retention; cell insertion with USB present; the retained cold-insertion counterexample (E25) on real cells; TH1 coupling to the cell |
| E31 | Display module supply (#8) | Module power tree; VBAT/pump/current at 3.15–3.26 V; 200 × NRST with the display on |
| E32 | Enclosure | USB-C plugs in both orientations; printed keycap fit/travel; pinhole reach to SW3; load supports |
| P06 | ~~Binding JLC PCBA quote~~ **Done 26 Sep 2026:** quoted and ordered (5 boards, variant B, Standard PCBA, $298.08). Remaining: approve JLC's placement photos, then run the first-article plan | Owner approval of the placement photos |
| E33 | Hot-swap sockets and printed tolerances | Socket solder/seating (G2b), tolerance coupon (G0), M2 × 6 self-tapping thread life (G5) |

Q4 design choices addressed E26 (the common regulated rail) and E27 (superseded by external FRAM); their physical verification remains among the Q4 gates in `REVIEW-Q4-2026-09-24.md`, which still apply to Q5 wherever the circuit is unchanged.

## MCU follow-up — 23 September 2026

[The options study](mcu-options-2026-09-23.md) recommends STM32L072CBT6 for the next candidate. It does not alter Q3 or close any issue below. New ngspice subcircuits reproduce E21/E25 under explicitly hypothetical parameters; a whole-board simulation has not been performed.

| ID | Candidate issue | Required closure |
|---|---|---|
| E26 | Native USB needs a supply above the current nominal 3.0 V rail's tolerance floor; separate VDD_USB has sequencing constraints, while OLED logic limits prevent an unreviewed common 3.3 V substitution | Coordinate all STM32 supply domains, mixed-rail I²C/reset, boot/reset access, VBUS detection, USB protection/routing, regulator dropout and power-up/down behavior; implement and verify the revised native design |
| E27 | STM32 EEPROM has different endurance, write latency, bank-execution and ECC behavior from MSP430 FRAM | Design a wear-distributed journal, preserve input handling during writes, validate interrupted-write recovery and factory/update separation, then test on the real target |

The complete revised board still needs an inventory/assembly check; a stocked MCU and regulator do not establish both-vendor support. Quote activity remains paused until explicitly authorized.

## Active Q3 status

**22 September 2026: engineering review only; vendor quotations are paused.** The DE188 replacement is implemented as X087-2832TSWIG02-H14/C18723015 on a two-layer board. Fresh inventory checking found40 of43 exact PCB MPNs with positive JLC available quantity; J1, Q1/Q2/Q6 and R13 have ordering restrictions there, but all three exact MPNs have independent DigiKey stock. That provides a source path, not JLC/PCBWay allocation or accepted sourcing. See the [dated review](REVIEW-Q3-2026-09-22.md) and its stock evidence.

The new deterministic software harness found no additional confirmed production-code defect in its bounded scenarios. Conditional hardware analysis does not close OLED acknowledgement/rise-time, current budget, startup or the retained qualification gaps below. Historical Q1/Q2 issues remain evidence for those revisions, not a claim that the removed LCD circuit is present in Q3.

| ID | Q3 finding / state | Required closure |
|---|---|---|
| E20 | OLED power/process changes:4V TPS63900 supply, internal9V pump, gatedVBAT, exact14-pin FPC | Vendor-approved lot/land/mask/heat/support section; physical rail/start-stop/current/optics and low-cell/USB handover tests |
| E21 |4.7k I²C pull-ups draw more than the controller's stated100µA VOL test current; increasing to33k would leave only10.6pF for the300ns rise-time limit | Obtain sink/capacitance evidence or measure actual ACK low level and rise time. Do not infer margin from100kHz operation alone |
| E22 | Original Q3 foreground work could miss short presses; independent ISR tests exposed and fixed it with a timestamped63-entry input queue and visible persisted ERR state | Physical bounce/timing, queue-overflow and power-loss tests. Abrupt power loss before the foreground error marker write remains a gap |
| E23 | Independent Q3 mechanics found initial shell collisions, one-piece cover assembly trap and0.1mm keeper-head clearance | Corrected split cover and raised PCB model; final source-bound CAD checks plus actual print/assembly/clip/lap/harness/USB/pack qualification required |
| E24 | One exact J1 shell-pad/SW2 courtyard projection exception; rotated-pad nominal separation0.905mm, flange5mm high, checked top fillet≤0.5mm | Vendor3D/tolerance and solder-height confirmation; no electrical-clearance waiver |
| P05 | September22: OLED available1,052;40/43 exact MPNs have positive JLC available quantity. Exact J1, DMN2056U-7 and R13 have verified DigiKey stock but JLC ordering restrictions | Choose accepted exact-part sourcing/allocation when vendor activity is explicitly reauthorized. No preorder, DNP or new quote now |
| E25 | Deterministic battery-insertion sensitivity model can hold protector sense above0.4V for179.45µs, exceeding the125µs minimum short-circuit delay; assumes4.2V,20µF effective SYS capacitance and1Ω other series resistance | Establish actual cell impedance/BATFET slew and instrument insertion/recovery, or design bounded precharge. Converter input limiting does not bound input-capacitor charging; this is a conditional counterexample, not a measured failure |

Q3 retains E01/E03–E05/E07–E09/E11/E12/E14/E18/E19 where applicable. E02/E15/E17 concern the removed DE188/LCD drive and remain historical; Q3 needs its own OLED qualification. E06 consistency requires fresh Q3 native evidence. E10 now has visible MAX/ERR behavior and adversarial tests; the watchdog strategy and hardware recovery remain review gates. No board is physically qualified.

## Historical Q1/Q2 findings

Q1 is on engineering hold after the 15 September independent review. Separate Q2 circuitry, schematic, layout and enclosure corrections are recorded below; a correction in files does not establish measured behavior. A quotation, host test or re-read of a DRC file does not close these findings. See `adversarial-review-Q2.md` and its linked audits.

| ID | Issue / evidence | Closure |
|---|---|---|
| E01 | Protector nominal UV 2.8 V versus EEMB 2.75 V endpoint; the retrieved TI BQ2970 Rev. I table gives ±50 mV at 25°C, so the older blanket ±0.1 V assertion is not substantiated by that source | Establish full-temperature limits, recovery/depleted-cell charging behavior and cell-maker approval, or redesign/validate protection; the corrected citation does not close compatibility review |
| E02 | DE188 440 ms combined optical response | Current exact-part data and sample response/waveform/visibility tests; change display if needed |
| E03 | Custom cell/NTC pack unapproved; Q1 excitation gives 0.250 mA at 25°C. Q2 changes R10 to57.6 kΩ, bounding modeled current below97.45 µA at5.5 V with intact R10; installed heating/lag remains unmeasured | Vendor drawing, genuine cell/NTC data, welded-tab insulation, actual attached-sensor self-heating/thermal contact, strain relief and shipping approval |
| E04 | 18.2 mA low-current charging unqualified | CC/CV, tolerances, termination, stability and power-path measurements |
| E05 | Nominal thermal window not tested | Worst-case review; open/short/resistance-sweep tests; attached cell-temperature test |
| E06 | Q1 native schematic/ERC missing; Q2 six-sheet native schematic now exists with62 refs/features,195 connected pin assignments and28 explicit unused pins | Fresh native PCB checks now have zero violations, disconnected items and schematic mismatches; hash-bound final ERC/DRC evidence is under verification/q2-*. Schematic consistency does not qualify real component behavior |
| E07 | MCU/FRAM/LCD hardware tests missing | First-article programming, pin mux, LCD bias/DC, oscillator, brownout, retention and current tests |
| E08 | Confirmed enclosure study mismatches: rear mounts 1.118 mm off, front mounts absent, LCD pocket 1.25 mm off, USB opening 2.1 mm off, 20.9 mm tray below 21.0 mm allowed pack; wrong-side MCU envelope; see `review-mechanical-Q2.md` | Separate mechanical/q2 CAD now follows the controlled board and modeled envelopes; verify actual part/sample fit, travel, clips, solder tails, pack preparation, print retention and drop behavior |
| E09 | Mass/runtime unmeasured | Actual part masses, slicer output and assembled measurements; active/sleep current/endurance |
| E10 | Firmware robustness/overflow | Watchdog disabled; overflow flag not displayed |
| E11 | Placement/DFM/sample fit | Vendor pad-1 and rotation review; LCD flat-lead holes, standoff and 1 mm switch support checks |
| E12 | NTC legacy/NRND choice | Confirm stock/lifecycle; qualify replacement for repeat builds if needed |
| E13 | Q1 Gerber-job metadata differed from quote specification. Q2 native exports now state ENIG, 1.0 mm board and 0.0175 mm inner copper; graphic bounds remain 42.05 × 40.05 mm for the 42 × 40 mm centerline profile | Vendor acknowledgment of RFQ/native proposed stack and 42 × 40 mm finished profile centerline; confirm actual material, copper, mask, finished thickness and tolerances. Proposed copper/dielectric total is 1.0 mm; KiCad additionally records provisional 0.01 mm mask per side. These are quote assumptions, not accepted fabrication construction |
| E14 | Q1 U3 exact BOM TPS7A0230DBVR is unmatched. Q2 intentionally selects TPS7A0230PDBVR, whose P denotes active output discharge (functional feature, sections 7.3.2/9.1.1), not packaging; [TI TPS7A02 datasheet](https://www.ti.com/lit/gpn/TPS7A02), `procurement/JLCPCB-IMPORT-ADAPTER-Q1.md` | Q2 ordering identity and circuit consequences documented in q2-power-design.md; retain actual brownout/FRAM, output-capacitance, reverse-current and fixture tests. Selection is not sourcing allocation or qualification |
| E15 | Confirmed: selected LCD mode requires reservoir capacitors on U1 R13/R23/R33 pins 7/8/9, absent from Q1 | Q2 adds100 nF C14/C15/C16 on pins7/8/9 with checked short native routes; verify actual bias levels, DC balance, contrast and current. C8 remains100 nF per device specification |
| E16 | Q1 build provenance was incomplete, but alleged source/binary drift is refuted: TI's LCD4MUX includes LCDSON and unmodified source reproduces the shipped application bytes | Provenance improvement implemented for the separate Q2 candidate; preserve exact Q1 comparison and source/toolchain/flags/output manifest for future builds. This is not a remaining segment-enable defect |
| E17 | Q1 LCD frame rate is nominally 64 Hz at the MCU specification limit; positive REFO tolerance can exceed it | Separate Q2 candidate now uses verified nominal 32 Hz; physical bias/contrast/optical qualification remains. Firmware timing changes do not fix E15 |
| E18 | Thermal fault inference: loss of U5 supply while the TEMP_OK pull-up remains powered can leave charging enabled with the charger's TS pin fixed in its normal range | Q2 splits TLV7032 outputs, uses series Q3/Q4 and local100 kΩ gate pulldowns. The powered-pullup mechanism is removed by connectivity; test real startup/supply loss/leakage/disable timing and remaining single faults. See q2-power-design.md; no measured guarantee |
| E19 | Newly confirmed inherited MCU supply-capacitance gap: Q1 V3 has2.2 µF +100 nF; TI §8.3 recommends4.7 µF minimum/10 µF nominal at DVCC. Q2 C6 becomes10 µF GRM21BR61E106KA73L and C7 moves near U1 supply pins | Confirm at least4.7 µF effective at3 V after bias, temperature, aging and tolerance; inspect local return paths and measure rail transients/brownout with selected U3P regulator |
| P01 | Q2 four-file PCBWay submission verified 2026-09-15 11:51:09 UTC: PCB W914112AS1N6 / assembly T-1N7W914112A, five units, both Subject to audit. JLCPCB Q2 Gerbers/RFQ/BOM/CPL processed in a saved draft, current quantity ten and 50 refs, with no placement advancement or complete quote. Q1 entries remain historical and on hold | Obtain technical acceptance of the identified Q2 revision and complete separate 5/10 prices. File upload is not manufacturing release; keep all physical qualification gates |
| P02 | JLCPCB Q2 ten-unit draft: 39 confirmed/10 shortage/1 unmatched required DE188. Shortages affect C1/C3/C5, R3, R9, R11, R16, SW1/SW2 and U5. Corrected U3 TPS7A0230PDBVR and exact J1 are matched; no parts were omitted. Next requires unselected parts to be excluded | Resolve complete sourcing without DNP or silent substitutions. Manual matching requires a $10 payment before review under [JLCPCB terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-parts-selection-service), so it was not activated. Use the existing Frank case for a full written quote or explicit fee waiver; retained DE188 alternatives have no verified stock advantage |
| P03 | JLCPCB battery and test-pricing exclusions | Written scope and priced completion plan; no payment merely to unlock quoting |
| P04 | Neither vendor has a complete landed quote. PCBWay Q2 automatic estimates are $143.93/5 and $184.31/10, excluding components and advanced services; ten is calculator-only. JLCPCB Q2 PCB-only estimates are $32.41/5 and $39.81/10, plus $27.63 estimated freight. PCBWay form has 1 oz inner copper versus requested 0.5 oz; JLCPCB forces Plugged versus requested tenting. These differences are recorded for review | Full 5/10-unit component/assembly/harness/programming/test/freight/tax comparison and explicit acceptance of stack/process. PCBWay's form says SMD Parts but saved detail says SMT Pads: 47 entered is placements, so vendor must calculate solder points from the BOM/board |

E10 requires a deliberate watchdog strategy and visible saturation behavior review. First-article acceptance and purchase approval are separate; do not build remaining units around a failed first article. Read the RFQ for the exact protocol and numeric targets.

An OLED alternative requires a new current budget: the present 3.3 Ω sense resistor and FETs imply a nominal discharge trip near 30 mA. A display in the 23–29 mA range could approach it. This does not establish the candidate's actual application current or authorize changing protection thresholds.

PCBWay's proposed combined mask openings are **not approved**. Q2 uses the TI U5 land pattern (0.20 mm copper gap,0.10 mm nominal mask web); vendor process acceptance is pending. Q2 sharing and the specific PCBWay quotation notice were approved. Both Q2 emails were verified in Sent and revised files were uploaded through both portals. Use portal workflows directly and existing email cases only for unresolved sourcing, DFM and service scope. No full quote, paid sourcing or manufacturing release is established.
