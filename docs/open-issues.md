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
| P01 | No complete website submissions or formal IDs; JLCPCB Gerbers/RFQ supplements accepted locally, BOM/CPL pending; PCBWay pre-upload agreement pending | Complete both site workflows after pending agreement confirmations; record accepted files and formal RFQ numbers |
| P02 | Historical JLCPCB images read: SW2 incorrectly matched to E-Switch C5798268 with 5 shortfall; twelve refs unmatched; rough totals exclude these lines | Correct SW1/SW2 to Cherry MX1A-E1NW and resolve current exact MPNs/quantities/prices/MOQs/lead times in live importer |
| P03 | JLCPCB battery and test-pricing exclusions | Written scope and priced completion plan; no payment merely to unlock quoting |
| P04 | No complete landed totals | Full 5/10-unit component/assembly/harness/programming/test/freight/tax comparison |

E10 requires a deliberate watchdog strategy and visible saturation behavior review. First-article acceptance and purchase approval are separate; do not build remaining units around a failed first article. Read the RFQ for the exact protocol and numeric targets.
