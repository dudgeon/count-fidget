# Open issues

These are existing unresolved findings. A quotation, host test or re-read of a DRC file does not close them.

| ID | Issue / evidence | Closure |
|---|---|---|
| E01 | Protector UV 2.8 V ±0.1 V versus EEMB 2.75 V endpoint | Cell-maker approval of actual limits or protection redesign/validation |
| E02 | DE188 440 ms combined optical response | Current exact-part data and sample response/waveform/visibility tests; change display if needed |
| E03 | Custom cell/NTC pack unapproved | Vendor drawing, genuine cell/NTC data, welded-tab insulation, thermal contact, strain relief and shipping approval |
| E04 | 18.2 mA low-current charging unqualified | CC/CV, tolerances, termination, stability and power-path measurements |
| E05 | Nominal thermal window not tested | Worst-case review; open/short/resistance-sweep tests; attached cell-temperature test |
| E06 | Native schematic/ERC missing | Create matching schematic, independent pin/net/electrical review and ERC |
| E07 | MCU/FRAM/LCD hardware tests missing | First-article programming, pin mux, LCD bias/DC, oscillator, brownout, retention and current tests |
| E08 | Enclosure mismatch | Revise CAD to Q1 rear holes/right USB and actual parts; verify travel, clips, solder tails, pack clearance, retention and drop behavior |
| E09 | Mass/runtime unmeasured | Actual part masses, slicer output and assembled measurements; active/sleep current/endurance |
| E10 | Firmware robustness/overflow | Watchdog disabled; overflow flag not displayed |
| E11 | Placement/DFM/sample fit | Vendor pad-1 and rotation review; LCD flat-lead holes, standoff and 1 mm switch support checks |
| E12 | NTC legacy/NRND choice | Confirm stock/lifecycle; qualify replacement for repeat builds if needed |
| E13 | Gerber-job metadata differs from quote specification: finish `None`, 0.035 mm inner copper and 42.05 × 40.05 mm stroke bounds; see `docs/quote-import-audit.md` | Vendor acknowledgment that RFQ/form ENIG and disclosed stack alternative control the quote, with 42 × 40 mm finished profile centerline; confirm actual stack/finish/dimensions/tolerances and reconcile metadata under controlled release review |
| E14 | U3 exact BOM TPS7A0230DBVR is unmatched; TI's current ordering addendum lists TPS7A0230PDBVR, whose P denotes active output discharge (functional feature, sections 7.3.2/9.1.1), not packaging; [TI TPS7A02 datasheet](https://www.ti.com/lit/gpn/TPS7A02), `procurement/JLCPCB-IMPORT-ADAPTER-Q1.md` | Resolve ordering identity, sourcing and electrical consequences through controlled qualification review; no silent substitution or design/BOM change |
| P01 | PCBWay four-file submission complete 2026-09-15 01:46:47 UTC: PCB W914112AS1N4 / assembly T-1N5W914112A, five units, both Subject to audit; JLCPCB final adapter/CPL accepted with 46 refs but no placement advancement/formal quote reference | Follow PCBWay submission/Remi message; JLCPCB refuses an order quote including non-stock parts, so preserve full draft scope, pursue the requested case ID and resolve the sourcing path before placement/submission; both agreement gates manually advanced |
| P02 | JLCPCB live sourcing: 38 confirmed/7 shortage/2 unselected, with R9 overlapping categories; shortages are Murata C469542 24 pieces, R9 C137725 1 of 20, Cherry C5120587 10 pieces; required DS1 DE188 and exact U3 TPS7A0230DBVR unmatched | JLCPCB refuses to quote non-stock parts; preserve required Q1 scope and resolve a priced sourcing path without DNP or silent substitutions. Stocked display alternatives are being evaluated at Geoff's request, with no substitute/redesign approved; Q3 Nexperia C65189 and J1 GCT C3020560 corrections remain selected |
| P03 | JLCPCB battery and test-pricing exclusions | Written scope and priced completion plan; no payment merely to unlock quoting |
| P04 | No complete landed totals; JLCPCB explicitly refuses quotes including non-stock parts, PCBWay still Subject to audit | Full 5/10-unit component/assembly/harness/programming/test/freight/tax comparison |

E10 requires a deliberate watchdog strategy and visible saturation behavior review. First-article acceptance and purchase approval are separate; do not build remaining units around a failed first article. Read the RFQ for the exact protocol and numeric targets.
