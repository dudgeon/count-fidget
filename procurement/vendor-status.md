# Vendor status and website resume procedure

Snapshot: last verified in the September 14, 2026 cloud session. No complete quote, paid order, paid parts pre-order, or manufacturing release exists. Neither website has a confirmed Q1 upload or submission number. The repo migration does not change those facts.

## JLCPCB

- Website: https://cart.jlcpcb.com/quote
- Website chat representative Gan required Gerber/BOM/CPL review. Battery assembly is unsupported. Programming/testing can be offered, but functional-test review was available only after payment; a prepayment exception was requested and declined. Do not pay to unlock quoting.
- Complete original Q1 RFQ ZIP emailed to verified representative Frank Chen on **2026-09-14 at 18:32:33 UTC**. SENT status and a **275,486-byte** attachment were verified.
- Frank's **2026-09-14 21:23:46 UTC** reply acknowledges receiving/reviewing the package. It flags BAT1/K1/K2 without CPL positions, unspecified part shortages, and unmatched parts requiring manual matching.
- That reply refers to a rough 5-piece PCB/PCBA price excluding all missing/shortfall/unmatched lines. Four embedded external images contain offboard/import errors, stock/matching information and rough price details. **Those images have not been read; their amounts and exact shortage MPNs remain unknown.** It is not a final complete quote.
- No approved substitute, paid pre-order, or private-parts-library procurement exists.

The BOM/CPL complaint is clarified locally: BAT1 is a supplied cell/NTC harness and K1/K2 are loose caps. They have no PCB coordinates. `BOM-PCBA-Q1.csv` now contains exactly the 46 PCB refs present in the CPL; `OFFBOARD-items-Q1.csv` lists the rest. This correction has **not** been uploaded or emailed. Do not add fake placements or omit offboard items from commercial scope.

Next: open the authenticated quote workflow, upload Gerber ZIP, PCB-only BOM and CPL, inspect/manual-match each part, resolve exact quantities/stock/MOQs, and attach full RFQ/offboard notes. Ask whether caps can be supplied loose. Keep battery/test exclusions visible. If the website cannot price required work, obtain written exclusions and document what a separately priced completion path would require; don't declare a supported subtotal complete.

## PCBWay

- Assembly entry: https://www.pcbway.com/quotesmt.aspx
- Account cart: https://member.pcbway.com/Order/CartList
- Website chat representative Assistant05 (US) said the specified battery harness, programming and testing can be reviewed/quoted after receiving files through the existing account; stated turnaround **1–2 days after receipt**, not guaranteed.
- Full original Q1 RFQ emailed to PCBWay customer service **2026-09-14 at 18:33:59 UTC**. SENT and **275,486-byte** attachment verified. No full quote or subsequent reply had been found at the last check (approximately 21:24 UTC).
- **PCBWay sign-in succeeded and the signed-in account was observed.** Earlier notes saying sign-in was still the blocker are superseded. Assigned representative was **Remi**; use the current account's displayed contact details.
- Account cart contained an unrelated July `companion_carrier_v0` item. It is not Count Fidget, was not modified and its assembly price is not relevant. Verify filename/project before editing any existing item.
- A new Q1 assembly form was filled but the **Calculate** action timed out. All later observation/navigation/screenshot/manual-handoff recovery attempts failed with `CDP operation refresh tabs timed out after 20000ms`. No file chooser was reached and no upload success or RFQ number was observed.

### Last confirmed form values

| Field | Value |
|---|---|
| Assembly | Turnkey, single pieces, both sides, quantity 5; separate quantity-10 alternative in notes |
| Existing PCB order | None selected |
| PCB specifications | Included/checked |
| Design / panel | 1 design, single pieces; vendor tooling if needed and deliver separated boards |
| Size / thickness | 42 × 40 mm / 1.0 mm |
| Layers / material | 4 / S1000H TG150 |
| Copper | 1 oz outer / 1 oz inner (form minimum); request preferred 0.5 oz inner separately |
| Features | 5/5 mil, 0.3 mm minimum plated drill |
| Finish | ENIG 1 microinch, green mask, white silk |

Selecting four layers opened a modal for layer order; it was filled and submitted:

1. `click-counter-Q1-F_Cu.gtl`
2. `click-counter-Q1-In1_Cu.g1`
3. `click-counter-Q1-In2_Cu.g2`
4. `click-counter-Q1-B_Cu.gbl`

Quantity was a read-only dropdown; select a listed quantity rather than type into it. These are past observations, not stable selectors. Inspect the live UI in the local session and check whether any draft survived before creating another.

### Scope to enter/attach again if needed

> CLICK-COUNTER Q1 — QUOTATION ONLY. Quote 5 and 10 complete units separately. 42 × 40 × 1.0 mm, four layers. Full turnkey sourcing, both-side SMT and THT LCD/Cherry switches, custom CC-BAT-001 LIR2032 + NTC four-wire JST harness, two loose keycaps per unit, firmware loading via SBW, fixture/first-article engineering and functional tests per RFQ-Q1. BAT1/K1/K2 are supplied offboard and have no placement coordinates. Include all components/MOQs, soldering, programming/test, packaging, lithium freight and taxes/duties to postal code 20815 USA. No customer soldering. Prototype qualification and first-article hold required; open display/protection items are disclosed. Do not purchase parts, charge the account or manufacture before separate approval. Contact via the authenticated customer account.

PCB note: standard form quote is 1 oz outer/1 oz inner; explicitly ask for availability and price/weight difference of preferred 0.5 oz inner. Follow Gerber outline/masks and identify actual stackup, tooling and finished thickness tolerance. Do not present unequal stacks as identical quotes.

## Upload file map

| Vendor field | Repository file |
|---|---|
| PCB Gerbers | `procurement/click-counter-Q1-Gerbers.zip` |
| Automatic BOM importer | `procurement/BOM-PCBA-Q1.csv` |
| JLCPCB CPL | `procurement/CPL-JLCPCB-Q1.csv` |
| Generic/KiCad placement file | `procurement/placements-KiCad-Q1.csv` |
| Full technical/commercial attachments | `dist/click-counter-Q1-RFQ.zip` |
| Offboard supply | `procurement/OFFBOARD-items-Q1.csv` plus `RFQ-Q1.md`/HTML |
| Full commercial BOM | `procurement/BOM-Q1.csv` |
| Clarification | `procurement/WEBSITE-IMPORT-NOTES-Q1.md` |

Do not upload the full RFQ ZIP to a Gerber-only field. After accepting files, verify all 46 PCB refs are represented, identify manual THT handling/rotation exceptions, and confirm offboard scope is associated with the same RFQ. Capture the actual project filename and submission number.

## Mail and scheduled-work continuity

Private email/message IDs, attachment download tokens and account identifiers are deliberately not public. In Geoff's connected Gmail search for `"click-counter"` with `from:jlcpcb.com`, `from:pcbway.com`, or `in:sent`, around September 14, 2026. Initial subjects began **“Budget RFQ: Click-counter fidget — 5/10 fully assembled and programmed units”**, with vendor name; subsequent full-package replies use the same project wording. Find Frank's later reply by sender/date if it is in a separate thread. Use the observed sender/account rep for replies, not a guessed address. Public general vendor addresses are support@jlcpcb.com and service@pcbway.com.

A one-time cloud task titled **Click-counter vendor quotes** (title may appear as “Click-counter vendor quotes” without punctuation) was enabled for **2026-09-15 18:35:03 UTC** (14:35 Eastern). It checks vendor replies and may continue quotation work. No successful run was known at handoff; it was not paused during migration. Inspect current task state before further outreach to avoid duplicate cloud/local action. Do not claim continuous background work.

## Package version distinction

- Original emailed ZIP: **275,486 bytes**, SHA-256 `a466023de8ad41de98c0b33f86140ed7ca76bd34908660f1e451e3b740217e0b`.
- Later cloud import-corrected ZIP: **278,820 bytes**, SHA-256 `724e8561cdf35d701c3b65d125a6b082fcedce1af7ca87d215ec258098cf6363`; added PCB-only/offboard BOM and import notes; not sent/uploaded.
- GitHub's `dist/` ZIP is a rebuilt public-safe package with the same technical inputs and corrected BOM split. Contact text/packaging differ, so it has its own manifest/hash; it is not either historical emailed ZIP. See `docs/migration.md`.

Historical bare-board/promotion calculator amounts are preserved only in `archive/rev0/website-quotes.md`. They exclude essential scope and are not current complete quotations.
