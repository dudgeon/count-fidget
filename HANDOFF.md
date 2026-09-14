# Local-session handoff

You are continuing Geoff's Count Fidget project in `https://github.com/dudgeon/count-fidget`. Read `AGENTS.md` and `PROJECT.md`, then the product spec, user-research evidence, decisions, open issues and vendor ledger. Do not restart the design or ask Geoff to repeat the interview.

## Why this handoff exists

The user wants a local session after repeated cloud browser failures. Switching the ChatGPT client to desktop did not switch the old session's browser: only cloud CDP Chrome was exposed. PCBWay login had succeeded, but a Calculate action and later navigation, screenshots, fresh-tab observations and manual handoff repeatedly failed with `CDP operation refresh tabs timed out after 20000ms`. A tab could sometimes be created without being usable. No Q1 upload succeeded. Cloud execution is the user's suspected cause, not a confirmed diagnosis.

Use the capabilities documented in this new session to verify actual local browser access. Do not import the old cloud runtime setup, assume cookies transferred, reuse old tab IDs, or execute lower-level browser workarounds. If no usable local connection is exposed, explain that specific capability gap and ask for one concrete setup action. Do not send Geoff through another sign-in attempt unless the current page actually requires it.

## First actions

1. Inspect the working tree and current branch; preserve any local work. If not already cloned, clone the linked repo into an appropriate local project folder. Follow repository instructions.
2. Run `python3 scripts/verify_project.py`. With a C compiler available, run `python3 scripts/run_host_tests.py` once. Neither requires KiCad/TI tooling nor changes the design. `bash scripts/resume-local.sh` prints context and runs integrity checks.
3. Verify the local browser can list/open/read a vendor page. Inspect existing account/cart state before creating submissions. Authentication should use the supported secure mechanism or the user's local account; never ask for secrets in chat.
4. In the user's connected Gmail, check established Click-counter threads for new replies. Find Frank's JLCPCB reply at September 14, 2026 21:23:46 UTC; embedded images contain stock/matching/rough-price details that remain unread. Use `procurement/vendor-status.md` for search terms and dates. Do not guess numeric prices.
5. Check the existing one-time cloud follow-up titled Click-counter vendor quotes, scheduled September 15 at 18:35:03 UTC, before duplicate outreach. It was not disabled in the migration and may since have run. Inspect current status rather than assuming background work happened.
6. Resume PCBWay website submission first, then JLCPCB. Capture accepted filenames and real submission/quote number. The complete procedure, prior form values and distinctions between archive versions are in `procurement/vendor-status.md`.

## Immediate goal

Get **complete vendor-reviewed quotes for 5 and 10 units from both JLCPCB and PCBWay using their websites**. This is already authorized. Include every component, both-side SMT and THT/manual soldering, LCD/switch installation, USB tabs, prepared battery/NTC harness, two loose caps, programming/verification, fixtures/setup, first-article engineering, recurring tests, packaging, lithium delivery and tax/duty/brokerage to postal code 20815. Geoff prints/fits the enclosure; no electrical soldering left to him. Do not present a calculator amount, emailed ZIP or supported-scope subtotal as completion.

PCBWay signed-in account had a different July `companion_carrier_v0` item: leave it alone. New Q1 form was filled for five units and separate ten-unit alternative but Calculate failed before upload. Rep Remi was shown in the account. Current form may have changed or may not have saved.

JLCPCB acknowledged the emailed original Q1 package but cannot assemble batteries and declined test review/pricing before payment. The rough 5-unit quote excludes shortfall/unmatched parts. Resolve manual matching and exact stock/MOQs; preserve exclusions and explain any remaining complete-scope gap. Do not prepay or preorder chargeable parts simply to get pricing.

## Exact files

- `procurement/click-counter-Q1-Gerbers.zip` for Gerber-only input.
- `procurement/BOM-PCBA-Q1.csv` for automatic importer: **46 PCB components**.
- `procurement/CPL-JLCPCB-Q1.csv` for JLCPCB; `placements-KiCad-Q1.csv` for generic placement.
- `dist/click-counter-Q1-RFQ.zip` for full technical/commercial supplement.
- `procurement/OFFBOARD-items-Q1.csv`, `BOM-Q1.csv`, `WEBSITE-IMPORT-NOTES-Q1.md` and RFQ include battery harness/caps and full costs.

BAT1 and K1/K2 are supplied offboard and have no CPL coordinates. The earlier all-scope BOM triggered this importer issue; the corrected split is already prepared. Do not invent coordinates or drop these items from the quote. GitHub RFQ ZIP has its own hash because personal contact text was removed and packaging refreshed; it has not been sent/uploaded. Use the authenticated vendor account for contact/delivery details. Keep private account/mail data out of this public repo.

## Design facts to preserve

Q1 is a routed KiCad 10, 42 × 40 × 1.0 mm four-layer PCB with 46 fitted parts, 10 pogo lands and two mounts. Recorded DRC reports zero violations/unconnected items under its saved check configuration; no native schematic/ERC exists. Firmware targets **MSP430FR4133IG48R, 48-pin TSSOP**; source/HEX/ELF/map/checksums and portable tests exist. Do not use old 64-pin Rev0 pin assignments.

Current interface: two Cherry MX Blue keys, eight-digit reflective DE188, 8 ms debounce, single-press reset with priority, no auto-repeat, 30-second LCD-off sleep, first wake click counted, saturation at 99,999,999 and per-change CRC-protected two-record FRAM journal. Interrupted newest update can lose that click; previous committed record is recovery target. Visible overflow cue is not implemented. Watchdog is disabled in this prototype.

Power: EEMB LIR2032 45 mAh custom insulated four-wire NTC/JST pack, BQ25185 4.2 V / 18.2 mA charger and 100 mA input limit, TPS7A02 3 V rail, hardware thermal comparator and independent BQ29700/FET protection. USB charges only; program via Spy-Bi-Wire. Do not overwrite info FRAM on normal firmware updates; factory-only HEX starts at 88,888,888 for segment inspection and must be reset before shipping.

## Work still owed

- Complete actual website submissions and itemized quotes.
- Resolve protector UV tolerance versus EEMB endpoint; approve exact battery/NTC pack and low-current charge/thermal/protection behavior.
- Qualify DE188's 440 ms optical response or select a better display with required redesign.
- Create/review native schematic and ERC; validate actual MCU/LCD/FRAM/brownout/power behavior on a first article.
- Revise enclosure to Q1 rear mounts/right USB and actual component/lead/pack geometry. Existing STEP/STLs/renders are an obsolete fit study, not final print files.
- Measure mass/runtime, finish robustness/overflow decisions, and obtain safe physical fit/retention before children use it.

All of these are documented as open, not newly discovered reasons to stall quotes. Obtain quotations with disclosed prototype/first-article conditions while advancing necessary engineering. Present a concrete order for approval before any money or manufacture. A quoted price does not qualify the circuit.

## Close each work session

Update `PROJECT.md`, `procurement/vendor-status.md`, the structured quote tracker and open issues with evidence and timestamps. Commit/push approved project work. Report what actually succeeded, what remains, and the next concrete action. Do not claim continuous work outside a session or a scheduled task.
