# Instructions for agents

Read `PROJECT.md`, `HANDOFF.md`, `docs/product-spec.md`, `docs/user-research.md`, `docs/decisions.md`, `docs/open-issues.md`, and `procurement/vendor-status.md`. The user's current instructions take precedence over this handoff.

## Authorization and expectations

Continue engineering, reversible fixes, quote preparation, vendor website uploads and the established quotation correspondence with JLCPCB and PCBWay. Geoff has repeatedly authorized this work; do not ask again whether to upload or obtain quotes. Present a concrete, itemized order for approval before spending, preordering chargeable parts, or releasing manufacture. Quote quantities are 5 and 10; no budget cap or final order quantity is established.

Persist to a verifiable result, provide meaningful updates, and ask one focused question only when genuinely blocked. Do not invent user preferences, repeat the interview, or rebuild unchanged artifacts as a substitute for completing uploads. A calculator subtotal, email dispatch or local ZIP is not a website submission or complete quote. Record accepted filenames, quantity, submission number, timestamp and scope after each actual upload. Inspect account state to avoid duplicates and unrelated orders. Geoff authorizes removing PCBWay cart entries from previous projects after verifying their filenames/project identity; preserve Count Fidget entries. This permission does not establish that any removal occurred.

Confirm the new session exposes the intended local browser. Use that session's supported browser/authentication tools. Cloud tab IDs, runtime handles and file paths are not portable. Do not copy cloud-specific setup into a local session or circumvent browser controls. Do not delegate to subagents unless explicitly authorized by the user or higher-priority instructions.

## Engineering truthfulness

- Q1 is a quotation prototype. Historical DRC is clear and firmware compiled; no board has been physically tested. There is no native schematic/ERC.
- Retain the LCD, charger/thermal, protection and fit caveats in RFQs. Resolve release gates before manufacture/use.
- Current MCU is **48-pin MSP430FR4133IG48R**. Rev0's 64-pin wiring, charging settings and compensation statements are obsolete.
- Upload `BOM-PCBA-Q1.csv` with the 46 PCB refs. BAT1/K1/K2 are supplied offboard; never invent CPL coordinates. Attach offboard items and full RFQ separately.
- `mechanical/` is an obsolete fit study, not Q1's finished enclosure.
- USB charges only. Programming uses Spy-Bi-Wire; ordinary firmware updates must preserve the information-FRAM journal.
- Do not overwrite routed PCB or approved HEXs just to get a quote. `electronics/build_pcb.py` generates an unrouted board and overwrites Q1 files; intentional rebuilds belong in a working branch.

## Repository maintenance

Update project status, vendor ledger and open issues after meaningful progress. Distinguish planned, attempted, sent, acknowledged, uploaded, quoted, approved and paid. This repo is public: keep credentials, personal delivery/contact details, private email screenshots and account metadata out of commits; ignored `private/` can hold local working files. Do not publish signed attachment URLs.

Run `python3 scripts/verify_project.py` for package changes; use existing host tests where firmware or migration integrity warrants them. Reading historical DRC is not a new DRC run. Use `scripts/package_rfq.py`, not archived builders. A quote request, technical release and purchase approval are separate states.
