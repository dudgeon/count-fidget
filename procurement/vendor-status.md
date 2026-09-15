# Vendor status and website resume procedure

Current local snapshot: **2026-09-15 00:59:30 UTC** (September 14 Eastern). JLCPCB accepted Q1 Gerbers and full-RFQ supplements, but BOM/CPL import and final submission remain pending. PCBWay's form is calculated but remains before upload. Neither vendor has a formal Q1 submission number or complete quote. No paid order, paid parts pre-order or manufacturing release exists.

## Local website progress and evidence

Local native Chrome control was verified; the browser-tab connector fails initialization. Intermittent native stale state recovered after refreshing the page observation and user interaction. The local checkout matches GitHub; integrity and portable host tests passed once. No fresh DRC/hardware validation occurred.

### PCBWay local draft

- Geoff completed local sign-in. The local cart showed no listings/zero orders, unlike the historical cloud-cart observation; no unrelated item was changed.
- Five-unit form completed, requesting separate 10-unit alternative in the assembly notes. Full turnkey/both sides; 42 × 40 × 1.0 mm, four layers, S1000H Tg150, ENIG 1 microinch, green/white, 1 oz outer/inner standard with preferred 0.5 oz inner alternative explicitly requested. Four Gerber layer names were submitted to the layer-order dialog.
- Counts entered: 32 unique types, 43 SMT placements, 0 BGA/QFP, 4 physical parts requiring through-hole soldering (3 THT-only plus USB tabs). The note explains 46 total physical PCB parts and 28 THT joints.
- Calculate succeeded. Draft calculator showed PCB **$55.93**, assembly **$29.00**, shipping **$27.27** and a **-$27.27** discount, subtotal **$84.93**. This excludes parts/full reviewed scope and customs/VAT, and is not a complete or vendor-reviewed quote.
- Save to Cart opened **Special Notes / Agree**, a notice about prohibited/export-controlled/weapon-related/IP-infringing files referencing Terms of Service. User confirmation requested and still pending; no final agreement acceptance or file upload occurred.
- Form notes carry quotation-only/no-charge/no-manufacture restrictions, all RFQ scope, offboard distinction, first-article hold and preserved engineering gates. Both textarea fields are within the site's 600-character limit; the assembly note is 581 characters.

### JLCPCB local upload

- Already signed in; orders showed none, and saved Quotes showed **No files yet** before this new upload.
- **Accepted:** `procurement/click-counter-Q1-Gerbers.zip` (85,741 bytes; SHA-256 `f5e88b602ae17b81dd4745eb1f1715504f1baafe69ee0a844f275cde5b0be212`). Native chooser selection followed by completed processing and detection of a four-layer **42 × 40 mm** board were observed. No formal quote/submission number yet.
- **Accepted:** `dist/click-counter-Q1-RFQ.zip` (278,870 bytes; SHA-256 `79f633ba625e66e39d76e7fbf77db87a0d13eb99414107857d6a8c11ef63616d`) in the **Assembly remark** attachment dialog, filename verified and Save clicked. The same package was accepted in the separate **Function test** attachment field; filename verified there too. These acceptance observations occurred in this local session, by the snapshot time above. They are uploads to a draft, not a completed RFQ submission.
- Form: quantity 5, 1.0 mm, S1000H Tg155, ENIG/1 microinch, 1 oz outer/0.5 oz inner, Standard PCBA/Both Sides. Standard PCBA automatically adds a **70 × 70 mm handling panel**; **Depanel boards & edge rail before delivery = Yes**. Finished circuit outline remains 42 × 40 mm. Vendor DFM/stack confirmation still required.
- **Confirm Production file** and **Confirm Parts Placement** are Yes, with **Do not confirm automatically** checked in both dialogs. Function test = Yes. Assembly remarks request complete separate 5/10 pricing, full scope, battery exclusion/completion path, existing engineering gates and no charge/preorder/manufacture before separate approval.
- JLCPCB assembly-service terms checkbox was unchecked and confirmation requested before **Next**. Still pending. **BOM-PCBA-Q1.csv and CPL-JLCPCB-Q1.csv have not yet been imported; exact matching and formal submission remain unfinished.**

### Mail/image continuity checked locally

No newer reply or outbound follow-up found. All four images in Frank's **2026-09-14 21:23:46 UTC** message are now read through the actual Gmail image viewer. The email connector alone did not expose usable attachments; direct external image web access failed, but the existing Gmail message displayed them normally.

- Original CPL error identifies BAT1/K1/K2, already addressed by the prepared PCB-only/offboard BOM split.
- Historical stock screenshot shows SW2 matched to **E-Switch TL1220S1BBSG-RESET, C5798268**, with **5 shortfall**. This is an incorrect match: required SW2 is **Cherry MX1A-E1NW**, same as SW1. Do not preorder or accept the wrong part. Official catalog identity check is recorded in `quote-comparison.md`; current stock/MOQ remains to be checked.
- Historical unmatched references: **D1, DS1, J1, J2, Q1, Q2, Q3, SW1, U2, U3, U4, U5**. U1's C2053877 identifies the correct MSP430FR4133IG48R.
- Rough totals **$134.83/5** and **$157.82/10** are partial supported-scope estimates, not complete quotes. See the separate historical section in `quote-comparison.md` for itemization. The second image explicitly labels 10 pieces despite the email prose mentioning only five. All missing/shortfall/unmatched parts remain excluded, and the complete battery/programming/test/freight/tax scope is unpriced.
- The scheduled cloud follow-up was not found among the inspected task list; no local automation directory existed. The original cloud conversation was idle. These facts do **not** establish the one-time schedule's current enabled/run status. No automation was changed or duplicated.

## Historical cloud procedure (retained context)

## JLCPCB

- Website: https://cart.jlcpcb.com/quote
- Website chat representative Gan required Gerber/BOM/CPL review. Battery assembly is unsupported. Programming/testing can be offered, but functional-test review was available only after payment; a prepayment exception was requested and declined. Do not pay to unlock quoting.
- Complete original Q1 RFQ ZIP emailed to verified representative Frank Chen on **2026-09-14 at 18:32:33 UTC**. SENT status and a **275,486-byte** attachment were verified.
- Frank's **2026-09-14 21:23:46 UTC** reply acknowledges receiving/reviewing the package. It flags BAT1/K1/K2 without CPL positions, unspecified part shortages, and unmatched parts requiring manual matching.
- That reply refers to a rough 5-piece PCB/PCBA price excluding all missing/shortfall/unmatched lines. The four embedded images were unread at migration; they have now been read locally as described above. They do not establish a final complete quote.
- No approved substitute, paid pre-order, or private-parts-library procurement exists.

The BOM/CPL complaint is clarified locally: BAT1 is a supplied cell/NTC harness and K1/K2 are loose caps. They have no PCB coordinates. `BOM-PCBA-Q1.csv` contains exactly the 46 PCB refs present in the CPL; `OFFBOARD-items-Q1.csv` lists the rest. The correction is included in JLCPCB's uploaded RFQ supplement, but the automated BOM/CPL import is still pending and no corrected email was sent. Do not add fake placements or omit offboard items from commercial scope.

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
