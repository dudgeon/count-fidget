# Count Fidget

A lightweight, rechargeable two-key fidget that counts clicks, resets with a second key, and remembers its count while asleep or unpowered. Designed for a home-printed enclosure and professionally assembled electronics.

**Q1 is a prototype quotation package.** The routed PCB, compiled firmware, BOMs, placements, assembly drawings and RFQ exist. No complete vendor quote has been received, no Q1 website upload is confirmed, and no purchase or manufacturing release has occurred. Hardware is unqualified. The enclosure is an older fit study that does not match Q1.

Start with [PROJECT.md](PROJECT.md) for status and [HANDOFF.md](HANDOFF.md) for the new local session.

| Area | Files |
|---|---|
| Product | [Specification](docs/product-spec.md), [user context](docs/user-research.md), [decisions](docs/decisions.md) |
| PCB | [KiCad board](electronics/click-counter-Q1.kicad_pcb), [project](electronics/click-counter-Q1.kicad_pro), [electrical notes](electronics/design.md), [netlist](electronics/netlist.json) |
| Firmware | [Source and status](firmware/README.md), [application HEX](firmware/click-counter-Q1.hex), [factory-only HEX](firmware/factory-display-info.hex) |
| Vendor files | [RFQ ZIP](dist/click-counter-Q1-RFQ.zip), [Gerber ZIP](procurement/click-counter-Q1-Gerbers.zip), [import notes](procurement/WEBSITE-IMPORT-NOTES-Q1.md) |
| Procurement | [Vendor status and upload procedure](procurement/vendor-status.md), [full RFQ](procurement/RFQ-Q1.md), [comparison template](procurement/quote-comparison.md) |
| Enclosure | [Fit-study limitations and required changes](mechanical/README.md), source/STEP/STL/renders in `mechanical/` |
| Verification | [Recorded status](verification/Q1-status.json), [open issues](docs/open-issues.md), [build instructions](docs/build-and-verify.md) |
| Research | [Primary-source index](docs/sources.md) |
| Browser-readable review | [Self-contained design review HTML](docs/design-review.html) (download/open locally) |
| Provenance | [Migration record](docs/migration.md), [import manifest](verification/import-manifest.json) |

Quick checks, with Python 3 and a C compiler:

```sh
python3 scripts/verify_project.py
python3 scripts/run_host_tests.py
```

These verify files, package consistency and portable firmware logic, not physical electronics. Existing upload files can be used without rebuilding the PCB or firmware. Toolchains, credentials, private mailbox content and customer account sessions are not stored in this public repository.
