# Instructions for agents

Read `PROJECT.md`, `HANDOFF.md`, `docs/product-spec.md`, `docs/user-research.md`, `docs/decisions.md`, `docs/open-issues.md`, and `procurement/vendor-status.md`. The user's current instructions take precedence over this handoff.

## Authorization and expectations

Continue engineering, reversible fixes, quote preparation, vendor website uploads and the established quotation correspondence with JLCPCB and PCBWay. Geoff has repeatedly authorized this work; do not ask again whether to upload or obtain quotes. Present a concrete, itemized order for approval before spending, preordering chargeable parts, or releasing manufacture. Quote quantities are 5 and 10; no budget cap or final order quantity is established.

**Latest explicit user approval (15 September 2026):** share the finished Q2 package and technical follow-up with both existing vendor cases. This resolves the earlier specific disclosure-approval blocker; do not ask for the same approval again. The user also requires choosing email or portal correspondence, not both. After rereading the latest vendor emails, use **email only for both vendors**: PCBWay Remi explicitly requested email only; JLCPCB Mitchell directed follow-up to the existing Frank email case. Use portals only for required file imports and form workflow, with no duplicate portal chat/messages. Approval to share Q2 is not spending, paid sourcing or manufacturing approval. Q2 email dispatch is verified to PCBWay Remi at **2026-09-15 11:12:50 UTC** and to the existing JLCPCB Frank case at **11:17:46 UTC**, each with four checked attachments. Vendor acknowledgment, Q2 portal acceptance and complete quotes remain pending. Record email dispatch, portal upload and vendor acknowledgment separately; one does not establish the others.

Persist to a verifiable result, provide meaningful updates, and ask one focused question only when genuinely blocked. Do not invent user preferences, repeat the interview, or rebuild unchanged artifacts as a substitute for completing uploads. A calculator subtotal, email dispatch or local ZIP is not a website submission or complete quote. Record accepted filenames, quantity, submission number, timestamp and scope after each actual upload. Inspect account state to avoid duplicates and unrelated orders. Geoff authorizes removing PCBWay cart entries from previous projects after verifying their filenames/project identity; preserve Count Fidget entries. This permission does not establish that any removal occurred.

Confirm the new session exposes the intended local browser. Use that session's supported browser/authentication tools. Cloud tab IDs, runtime handles and file paths are not portable. Do not copy cloud-specific setup into a local session or circumvent browser controls. Do not delegate to subagents unless explicitly authorized by the user or higher-priority instructions.

## Engineering truthfulness

- Q1 is on engineering hold after the 15 September independent review. Read `docs/adversarial-review-Q2.md` and linked audits before further engineering or final quotations. Preserve submitted Q1 archives/binaries as historical evidence; corrections belong in an identified revision. The alleged source/binary mismatch was refuted by exact TI rebuild: LCD4MUX includes LCDSON. The missing LCD capacitors remain a real hardware issue.
- Q1 is a quotation prototype. Historical DRC is clear and firmware compiled; no board has been physically tested. Q1 has no native schematic/ERC; the separate Q2 native schematic/PCB and current checks live under `electronics/q2/` and `verification/q2-*`. Never use Q1 reports as Q2 evidence.
- Retain the LCD, charger/thermal, protection and fit caveats in RFQs. Resolve release gates before manufacture/use.
- Current MCU is **48-pin MSP430FR4133IG48R**. Rev0's 64-pin wiring, charging settings and compensation statements are obsolete.
- `BOM-PCBA-Q1.csv` is the controlling 46-ref PCB BOM and PCBWay upload. For JLCPCB's importer use the separate `BOM-JLCPCB-Q1.csv` adapter with unchanged `CPL-JLCPCB-Q1.csv`; read `procurement/JLCPCB-IMPORT-ADAPTER-Q1.md` and verify exact MPN/manufacturer matches. The adapter is a supplement, not part of the existing RFQ ZIP. BAT1/K1/K2 are supplied offboard; never invent CPL coordinates. Attach offboard items and full RFQ separately.
- Top-level `mechanical/` is an obsolete Rev0 fit study. Separate `mechanical/q2/` is a coordinated engineering fit candidate with simplified envelopes and explicit physical-print/retention limitations; it is not physically qualified.
- USB charges only. Programming uses Spy-Bi-Wire; ordinary firmware updates must preserve the information-FRAM journal.
- Do not overwrite routed PCB or approved HEXs just to get a quote. `electronics/build_pcb.py` generates an unrouted board and overwrites Q1 files; intentional rebuilds belong in a working branch.
- Separate Q2 export/package tools are `scripts/export_q2.py` and `scripts/package_q2.py`; they require current native checks and preserve Q1. Q2 has 50 fitted PCB refs with offboard BAT1/K1/K2 kept separate.
- Current shared firmware source is the separate Q2 LCD candidate. Do not run the Q1 RFQ packager against it: that would mix newer source with frozen Q1 binaries. Read `docs/build-and-verify.md`; future engineering packages need a coordinated revision.

## Repository maintenance

Update project status, vendor ledger and open issues after meaningful progress. Distinguish planned, attempted, sent, acknowledged, uploaded, quoted, approved and paid. This repo is public: keep credentials, personal delivery/contact details, private email screenshots and account metadata out of commits; ignored `private/` can hold local working files. Do not publish signed attachment URLs.

Run `python3 scripts/verify_project.py` for package changes; use existing host tests where firmware or migration integrity warrants them. Reading historical DRC is not a new DRC run. Use `scripts/package_rfq.py`, not archived builders. A quote request, technical release and purchase approval are separate states.
