# Local continuation handoff

Continue [dudgeon/count-fidget](https://github.com/dudgeon/count-fidget) without restarting requirements. Read `AGENTS.md`, `PROJECT.md`, product/user-research/decisions, `docs/open-issues.md`, `docs/adversarial-review-Q2.md` and the Q2 design documents.

## Working revision and authority

- Branch: `codex/q2-engineering-audit`; [draft PR #1](https://github.com/dudgeon/count-fidget/pull/1). Main's vendor checkpoint is `a8128ec`; the first audit/firmware checkpoint is `fe9aa6b`.
- The user said “What's next? Keep pushing forward.” Separate Q2 hardware/schematic/enclosure correction and quote files are complete and checked. Do not return to a requirements interview or merely restate the audit.
- Engineering, reversible fixes, quote preparation, website submissions and the established vendor correspondence are authorized. **The user explicitly approved sharing the finished Q2 package/technical follow-up with both vendors on 15 September 2026.** Obtain a **concrete approved order before money, chargeable part preorder or manufacture**. Quantities remain 5 and 10 separately.
- **Latest user correction: portal workflows first.** Proactively upload revised Q2 files to both portals and progress automatic quotes as far as available. Do not wait for email file-replacement instructions when the portal supports the action. Use email only for matters the portals cannot accomplish; avoid duplicate messages across channels. This supersedes the earlier email-only workflow guidance.
- The original Q1 board/firmware/BOM/CPL/Gerber/RFQ files are historical evidence. Do not run their destructive builders or the Q1 RFQ packager against the current Q2 firmware source.

## Engineering facts

1. **Source/binary mismatch was refuted.** TI support1.212 defines LCD4MUX to include LCDSON; unmodified source reproduces the entire frozen Q1 HEX. Both vendors received an explicit retraction around02:17UTC. Do not repeat the allegation.
2. Q1 really lacks Mode2 LCD reservoirs on U1 pins7/8/9. Q2 adds C14/C15/C16=100nF. C8 remains100nF, consistent with TI's device specification; the LaunchPad's1µF example does not make1µF mandatory here.
3. Separate firmware under `firmware/q2-lcd-check/` changes one loaded byte for divider8/32Hz nominal. Its manifest covers sources, exact compiler/support, flags and outputs. Q1 compiled/factory files remain unchanged; ordinary updates preserve the information-FRAM journal.
4. Q2 keeps exact DE1883V, nominal13.0mm rows and existing1.7mm drills pending lead/sample fit. Alternatives did not establish a JLC stock benefit. Eight digits/current dimensions were assumptions, not user requirements.
5. Charger combined ILIM/VSET pin7 with24k and ISETpin8 with16.5k are correct:4.2V/100mA input option/~18.18mA nominal charging. Optionalstatuspins3/9 are NC. Keep low-current and cell approval gates.
6. Q2 intentionally selects TPS7A0230PDBVR. Thermal U5 becomes TLV7032DGKR with independent outputs, series Q3/Q4 and local100k gate pulldowns; do not join push-pull outputs. Reduced NTC excitation/thresholds and uncovered faults are in `docs/q2-power-design.md`.
7. Newly found E19: Q1 V3 bulk2.2µF is below TI's4.7µFminimum/10µFnominal recommendation. Q2 C6 becomes10µF GRM21BR61E106KA73L; effective capacitance after bias/temp/tolerance and real rail behavior remain unqualified.
8. Native six-sheet schematic, PCB, project-local libraries and per-pin comparison are under `electronics/q2/`. Local copied footprints explicitly preserve Q1's modified geometry; matching a library is not a new land-pattern qualification. Fresh native ERC/DRC/parity reports and hash binding belong under `verification/q2-*`.
9. Separate `mechanical/q2/` replaces the obsolete Rev0 geometry for this candidate. It uses actual board/key/mount/USB/LCD/pack positions, simplified component envelopes and explicit physical-print/retention limitations. Do not label Rev0 files final.
10. Physical battery/protector/thermal/LCD/FRAM/current/fit/retention tests are still open. A clear ERC/DRC report is not measured safety or performance.

## Rebuild and verify

- `python3 scripts/verify_project.py`: frozen Q1 package and separate Q2 firmware provenance.
- `python3 scripts/run_host_tests.py`: existing portable firmware tests, relevant when firmware changes.
- `scripts/build_q2_model.py` / `build_q2_schematic.py` / `build_q2_board.py`: separate controlled model/native design. The PCB builder intentionally clears routing and requires `--replace-candidate` to overwrite an existing Q2 candidate. Preserve routed outputs unless intentionally rebuilding.
- KiCad10.0.6 and Freerouting2.4.1 were obtained from official publishers and checksum-verified in a temporary runtime. Native PCB calls used KiCad's bundled Python. Headless Freerouting requires analytics disabled and a temporary user-data directory. Do not install global settings or launch a GUI as a substitute for unavailable browser control.
- `scripts/preroute_q2.py` adds and locks the short capacitor/gate paths on a fresh unrouted candidate. `scripts/finish_q2_board.py --import-route` preserves that seed while importing the matching incremental SES, synchronizes schematic fields/NC semantics and fills planes. SES omits locked seed routes: never clear all tracks before importing it. `--refill-only` preserves current routes. Fresh native DRC/parity is required afterward.
- `python3 scripts/verify_q2.py --kicad-cli /path/to/kicad-cli` runs fresh native checks and saves hash-bound evidence. Read-only default rejects stale input/report hashes. `--semantic-only` is not proof of fresh ERC/DRC.
- `scripts/export_q2.py` and `package_q2.py` create separate quote exports/archive after successful verification. They must never overwrite Q1 artifacts. Include50 fitted PCB refs, separate offboard BAT1/K1/K2, and complete test/quotation scope.

## Current Q2 portal checkpoint

- **JLCPCB:** Re-Upload processed Q2 Gerbers as 4 layers/finished42×40 mm and Q2 BOM/CPL as50refs. RFQ is attached in both Function Test and Assembly Remark. Five-unit draft observed about11:36UTC; the same saved revision is now10PCB/10PCBA, Standard/both sides, observed about11:46UTC. Current labels39confirmed/10shortage/1notselected; J1 restored exactGCTUSB4105-GF-A/C3020560 and selected. DS1 unmatched; DE188/DE 188 searches returnedNoResult with stockfiltersunchecked. Next offersDo not place/Select parts; Select parts chosen, noDNP, Quote & Order blocked. JLCPCB manual matching requires $10 and starts 1–2 working days after payment under its [service terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-parts-selection-service); it was not activated.
- **JLCPCB estimates only:** PCB$32.41/5 and$39.81/10; DHLDDP$27.63 shown each, with ten-unit freight2–4businessdays/0.24kg. The10PCBsubtotal is$13specialoffer+$17.60ENIG+$8.17material+$1.04fileconfirmation. Assembly/component totals are dashes; J1's10-piece line$10.8220 is not a complete components total. Ten-unit shortages: C1/C3/C5combined34;R3=4;R9=1;R11=20;R16=4;SW1/SW2combined20;U5=10.
- **JLCPCB form/process:**1.0mm,S1000HTg155,ENIG1microinch,1ozouter/0.5ozinner,DepanelYes, forced70×70mmsupportpanel andPlugged (Tenteddisabled). PCBnote requestsRFQtenting review; process difference remains open. After specification changes cleared remarks,193-characterPCBnote (explicitfinished42×40×1) and485-characterassemblyscope+RFQattachment were restored/verified. FunctionTestRFQ retained. ProductionNoautoconfirm reapplied+confirmed; placementYes verified selected. The no-auto placement checkbox was verified at the earlier5-unit step, not separately rechecked at10.
- **PCBWay:** Q2 form calculated5=$143.93 and10=$184.31, excluding components/advancedservices. RespectivelyPCB$55.93/$81.36,assembly$88/$102.95,DHL$27.27 with−$27.27discount each,weight0.52/0.54kg;PCB4–5days,freight2–4businessdays. Bothsides/turnkey/noChinesealternatives;32types,47SMT,0BGA-QFP,4THincludinghybridUSB (50physicalPCBrefs). Depanel/test/programming/harness requested but unpriced online.1.0mm,Tg150–160,5/5mil,.3mmdrill,ENIG1microinch,tenting,1ozouter; formminimum1ozinner, with0.5ozalternative requested explicitly inPCBremark.
- **PCBWay Q2 submission:** the user approved the specific quotation notice, accepted before cart creation at11:48:56UTC. All four Q2 files showed100%Success and Submit the File Now completed. Verified11:51:09UTC: PCB **W914112AS1N6** / assembly **T-1N7W914112A**, quantity5, PO **COUNT-FIDGET-Q2-RFQ-5**, both **Subject to audit**. Cart counters: UnderReview4/AwaitingPayment0/Production0, including unchanged Q1 entries. Ten is calculator-only; the saved scope requests separate5/10 full prices. No outstanding agreement question.

Neither portal has a complete quote. NoDNP,paidpreorder,spending ormanufacturingrelease. See the vendor ledger/tracker for detailed timestamped evidence; private draft IDs remain omitted.

## Existing vendor cases — avoid duplicates

**PCBWay:** five-unit Q1 submission **W914112AS1N4 / T-1N5W914112A**, 2026-09-15 01:46:47 UTC. All four files accepted/submitted. Ten-unit alternate requested. Historical refresh around 02:00 UTC showed Subject to audit. Fresh native website inspection at **10:36 UTC** shows **Under Review 2, Awaiting Payment 0, Production 0**. No payment or manufacturing release. The incomplete $84.93 calculator amount had zero components.

Remi's website reply, now freshly read, is timestamped **2026-09-15 10:25:22 China time = 02:25:22 UTC**. Follow the supplied Gerbers/BOM/online parameters and include notes in the files. Programming/testing is additional; provide a step-by-step process. Testing starts at **$75**, then **$10/hour**, charged after the process. No hours, accepted full test scope or fixed complete quote were supplied.

At 03:07:50 UTC Remi emailed a DFM question: green mask requires at least 0.19 mm IC-pad spacing; the attachment identifies U5 pads 6/7 with Q1 gap 0.15 mm. At 03:23:59 UTC Remi requested **email only** for further follow-up and said the website reply had already been sent. No whole-row mask opening was approved.

Q2 TI DGK0008A geometry:1.40×0.45mmlands,0.65mmpitch,4.40mmrowcenters,0.05mmpad-to-maskmargin;0.20mmcoppergap and0.10mmnominalmaskweb. Vendor acceptance is pending. Do not confuse copper spacing with finished mask web.

**Historical JLCPCB Q1 draft before the Q2 Re-Upload:** Gerber/RFQ supplements/final exact-MPN adapter/CPL accepted;46refs,38confirmed/7shortage/2unselected (R9overlaps). Required parts kept withSelectparts; noDNP. No placement advancement/formalquoteID. Mitchell refuses to quote non-stock parts. He suggested U3TPS7A0230PDBVR/C3747031 and paid GlobalSourcing forDE188; no stocked alternative to the requestedLCD and no supportcaseID supplied. No paid preorder authorized. Battery assembly unsupported; functional-test review/pricing beforepayment refused. Use the existing Frank email case only for unresolved matters the portal cannot accomplish; do not duplicate messages across channels.

The saved Q1 draft and late chat were freshly inspected after access was restored. Mitchell's **22:18 Eastern chat on September 14 (approximately 02:18 UTC September 15)** says programming/testing is quoted only after order; **$15.70 engineering** and **$7.86/hour labor** are additional. These are rates, with no hours, accepted complete scope or full total; battery assembly remains excluded. Do not place/pay for an order to unlock the quote.

Q2 U3 identity is resolved, while exact TLV7032DGKR also has no verified JLC stock. External sourcing leads are in the Q2 documents; stock observations are not allocations. Display replacement alone does not produce a complete delivered JLC quote. Historical134.83/5 and157.82/10 were incomplete and included an incorrectoldSW2match.

## Restored local access and approved Q2 sharing

**Native Chrome access is restored**, and the PCBWay/JLCPCB pages and replies above were freshly verified; PCBWay counters were checked at **2026-09-15 10:36 UTC**. The continuation initially encountered a locked Mac, failed automatic unlock and unavailable app/browser surfaces; a separate browser connector also failed initialization. Those are historical observations, not the current native-access blocker. Use fresh supported UI state. Earlier sign-in and both site-agreement acceptances were completed by Geoff; do not ask for them again without evidence.

The user has now **explicitly approved sharing the finished Q2 package and technical follow-up with both existing vendor cases**. Earlier, automatic approval review rejected the prepared Remi pad-pattern/file-replacement email because specific disclosure approval was missing; that attempt was not sent. The approval blocker is resolved. The original local draft remains ignored under `private/pcbway-q2-reply.txt`; it is not delivery evidence. Both Q2 dispatches are verified in Gmail Sent on **2026-09-15**: PCBWay at **11:12:50 UTC** in the existing Remi engineering-question thread for W914112AS1N4, and JLCPCB at **11:17:46 UTC** in the existing Frank Budget RFQ email case. Neither vendor has technically acknowledged Q2. JLCPCB subsequently processed Q2 imports in its saved draft; PCBWay Q2 files were subsequently submitted under W914112AS1N6 / T-1N7W914112A, both Subject to audit.

At **2026-09-15 11:06:51 UTC**, the latest four vendor emails were reread before the email sends. No email was newer than Remi's **2026-09-15 03:23:59 UTC** email-only reply or Frank's **2026-09-14 21:23:46 UTC** rough quote/import reply. **The subsequent user correction now directs portal actions first:** upload revised files and advance automatic quote steps; email is the fallback only for matters the portals cannot accomplish. No duplicate correspondence and no need to await email instructions for supported portal actions.

The user also authorizes removing verified previous-project PCBWay cart items; preserve CountFidget. Last pre-submission cart wasempty and no deletion occurred. No complete quotes have been received. No money or manufacture.

## Finish the work

The coordinated Q2 files are now complete: fresh native ERC/DRC/connectivity/parity all zero; 62 refs/50 fitted/195 connected pins/28 NC agree; 21 negative checks rejected; 50-ref BOM/CPL and exported Gerbers checked; three valid/manifold enclosure print parts with zero modeled intersections. The SW2 thermal issue and Q4 via-to-pad overlap were corrected; final board SHA256 is `c80cf17a1d36d74e4c7c8f7cc4e14f5f42169fe0c3224811856b8bff0e5d0867`. The website response has been read and native access is available. Both Q2 email dispatches are verified. **Continue from the completed PCBWay Q2 submission and saved JLCPCB Q2 draft.** Both quantity calculations were captured; JLCPCB cannot advance with the required unmatched LCD, and its manual matching requires payment. Do not activate paid services to obtain a quote. Use supported portal actions directly without waiting for email replies; record actual acceptance rather than treating calculators as submissions. Use the existing Remi/Frank cases only for unresolved matters the portals cannot accomplish. Capture actual file acceptance and separate 5/10 quote results; avoid duplicate requests. Published service rates do not fill the missing hours/scope/landed totals. Unsupported lines need explicit exclusions and a priced completion plan. Present a concrete order/first-article scope for Geoff's approval before spending.

Update `PROJECT.md`, vendor ledger, structured tracker and open issues; commit/push project work to the existing draft PR when appropriate. This is a public repo: never commit private draft IDs/URLs, mail IDs, credentials, personal account details or private email images. The historical cloud follow-up was scheduled September15at18:35:03UTC; its current status remains unverified. Do not claim continuous background work or create a duplicate schedule.

Historical Q1 cart read at **10:48:59 UTC**: PCB **Awaiting reply**, assembly **Being reviewed**, all four Q1 filenames present; $55.93 PCB/$29.00 assembly with component pricing absent. Only Count Fidget entries observed; no cart removal. No payment/order/manufacture.

## Finished Q2 quote artifact

Ready at commit `c1240b9`. `dist/q2/click-counter-Q2-RFQ.zip`: 1,930,577 bytes, 124 files, SHA256 `29512016b9f83003bf416642617bfb0f8bbc76ea2ca64ba1c31d07e6df0b9438`. `dist/q2/manifest-Q2.json` binds each member; `procurement/q2/export-manifest-Q2.json` binds native exports. ZIP CRC and every member hash passed. This package is complete and approved for sharing. Both email dispatches are verified. JLCPCB Q2 draft imports are processed, but Quote & Order remains blocked; PCBWay Q2 files are submitted for review, with its agreement gate resolved. Vendor technical acknowledgment/full quotes remain pending. Recheck current evidence before changing it.


## Verified Q2 Sent-mail records

**PCBWay — 2026-09-15 11:12:50 UTC:** Gmail Sent confirms dispatch to Remi in the existing W914112AS1N4 engineering-question thread. Four attachment filenames and byte sizes were verified:

| Attachment | Bytes |
|---|---:|
| click-counter-Q2-RFQ.zip | 1,930,577 |
| click-counter-Q2-Gerbers.zip | 87,741 |
| BOM-PCBA-Q2.csv | 7,017 |
| placements-KiCad-Q2.csv | 4,389 |

The email recorded the then-current email-only correspondence choice, before the user's later portal-first correction; it requests exact U5 pattern/process acceptance, association of all four files with the existing case and instructions for required portal replacement; asks for complete separate 5/10-unit RFQ prices and hours/scope behind the $75 plus $10/hour test rates. It retains all physical gates and prohibits charges, paid parts procurement or manufacture without a concrete approved order. No combined opening was approved. Dispatch is not vendor acknowledgment, Q2 portal acceptance or a complete quote.

**JLCPCB — 2026-09-15 11:17:46 UTC:** Gmail Sent confirms dispatch in the existing Frank Budget RFQ email case. Four attachment filenames and byte sizes were verified:

| Attachment | Bytes |
|---|---:|
| click-counter-Q2-RFQ.zip | 1,930,577 |
| click-counter-Q2-Gerbers.zip | 87,741 |
| BOM-JLCPCB-Q2.csv | 8,006 |
| CPL-JLCPCB-Q2.csv | 2,295 |

Preserve this Sent-mail record. The Q2 portal imports/submission are now recorded above; continue from those states. Use this email case only for issues the portal cannot accomplish. No Q2 acknowledgment, portal replacement/import acceptance, complete quote, paid preorder or manufacturing release is established by the email send; record later portal results separately. Avoid duplicate correspondence.
