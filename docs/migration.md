# Cloud-to-local migration record

Destination: `https://github.com/dudgeon/count-fidget`, existing empty public repository, default branch `main`. The user explicitly requested setup and push, followed by a local-session handoff. No device purchase, vendor upload or manufacturing status changed during migration.

## Included

All recovered project technical assets: current KiCad PCB/project/custom footprint/netlist/generators/DSN/SES/Gerbers, assembly/CPL/BOM files, firmware source/HEX/ELF/map/checksums/tests, historical validation reports, CadQuery/STEP/STL/renders/geometry checks, full RFQ and import correction. Historical Rev0 notes/inquiries/calculator evidence and legacy package/report builders are retained under `archive/`. New docs consolidate user requirements, assumptions, decisions, sources, known gaps, vendor state and local instructions.

The import manifest records each original file's SHA-256, destination and any migration change/curated replacement. Firmware images and Gerber ZIP retain their original hashes. The public RFQ archive is rebuilt from repository files, with its own manifest/hash; it must not be represented as the previously emailed archive.

The checked-in validation configuration includes five ignored DRC checks; these are explicitly listed in `build-and-verify.md`. No fresh KiCad run was performed during migration. Portable firmware tests and archive/HEX/BOM integrity checks were rerun successfully and recorded in `verification/migration-checks.txt`.

## Public repository treatment

Customer personal email and private Gmail/account identifiers are omitted. Original tool-result-shaped quote tracker was replaced with a curated ledger. Vendor messages are summarized with dates, send/acknowledgement distinctions, project search terms and names; private correspondence is recoverable through the owner's authenticated mailbox. Signed image links and unrelated account/order details are not published. Vendor RFQ contact line directs use of the authenticated account. This does not remove technical requirements or cost scope.

The old report HTML was a generated duplicate of source documents; the current RFQ HTML is regenerated and a current design review is provided at `docs/design-review.html`. Old outer source/RFQ ZIPs are not duplicated because they embed private contact data or older import lists; all technical members are retained with provenance. External downloaded reference PDFs/toolchains and browser sessions are not transferred. Sources are indexed so they can be reobtained.

## What does not transfer

Cloud tab IDs, browser handles, login cookies, filechooser state, email app connections, installed compiler/CAD tooling, runtime scratch paths and automation execution. The local session must inspect its own available capabilities. PCBWay login succeeded in cloud but that is not a promise of local authentication. No confirmed Q1 site submission exists to resume by ID.

The existing one-time cloud follow-up was not changed during migration. Its last-known schedule/state and duplicate-outreach caution are in the vendor ledger. The repo contains a context handoff, not a new background agent.
