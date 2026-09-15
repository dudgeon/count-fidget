# Vendor status and website resume procedure

## Current engineering hold — 15 September 2026

Q1 remains available for **sourcing/budgetary review only**. Its missing LCD bias capacitors and frame-rate margin require a controlled revision before final production quotations. The alleged source/binary mismatch was independently **refuted** by an exact TI rebuild; the initial mistaken claim was explicitly corrected with both vendors. Read [the consolidated review](../docs/adversarial-review-Q2.md). No revised manufacturing package has been submitted, and no money, paid preorder or manufacturing release is authorized.

| Existing case | Verified subsequent correspondence |
|---|---|
| PCBWay, W914112AS1N4 / T-1N5W914112A, Remi | Engineering hold sent **02:11:11 UTC**; correction of the firmware claim sent **02:17:56 UTC**, verified in site history. Preserve these references. Any Q1 pricing needs reconfirmation against a reviewed revision. |
| JLCPCB saved import draft, Mitchell Chen / existing Frank email case | Around **02:07 UTC**, Mitchell identified TPS7A0230PDBVR / C3747031 as stocked and suggested paid Global Sourcing preorder for DE188. Around **02:15 UTC**, he said there was no stocked alternative to the requested LCD. He directed follow-up to the existing colleague's email case; no separate case ID was returned. Engineering hold and explicit firmware-claim correction were visibly sent, the latter around **02:17 UTC**. No U3 substitution or paid preorder was accepted. |

The latest native browser read reconfirmed the hold/correction messages and JLCPCB's saved BOM state (46 detected, 38 confirmed, 7 shortage, 2 unselected). This was a correspondence/draft read, not a fresh PCBWay cart audit. Continue engineering and sourcing against these existing cases; do not repeat the resolved agreement or import steps. The timeline below records the earlier Q1 submission state.

PCBWay update: **2026-09-15 01:47:22 UTC** (September 14 Eastern). Its four-file website submission succeeded at **01:46:47 UTC**, with linked five-unit **PCB W914112AS1N4** and **assembly T-1N5W914112A**, both **Subject to audit**; the linked full-scope message to Remi was sent and verified at **01:47:22 UTC**. JLCPCB accepted the final 46-reference importer adapter and unchanged CPL; remaining shortages and two required unmatched parts need manual vendor resolution. A full-scope live-chat request was visibly sent to Chian at approximately **01:56 UTC**, transferred to Mitchell Chen and acknowledged around **01:56:30 UTC**. Around **02:02 UTC**, he refused to quote an order including non-stock parts; the complete Q1 quote is blocked on that basis. Geoff manually advanced both site-agreement gates. Neither vendor has a complete quote. No checkout, paid order, paid parts pre-order or manufacturing release exists.

## Local website progress and evidence

Local native Chrome control was verified; the browser-tab connector fails initialization. Intermittent native stale state recovered after refreshing the page observation and user interaction. The local checkout matches GitHub; integrity and portable host tests passed once. No fresh DRC/hardware validation occurred.

### PCBWay website submission — Subject to audit

- Geoff completed local sign-in. Before the Q1 submission, the local cart showed no listings/zero orders, unlike the historical cloud-cart observation; no unrelated item was changed.
- Geoff subsequently authorized clearing PCBWay cart entries from previous projects. Verify filenames/project identity before removing entries and preserve Count Fidget. Before the Q1 submission, native Chrome cart recheck and refresh showed **Cart 0**, **All Orders 0**, **Under Review 0**, **Awaiting Payment 0**, empty search fields and no listings. There was nothing to remove; no deletion was performed. The authorization remains applicable if previous-project entries appear later.
- Five-unit form completed, requesting separate 10-unit alternative in the assembly notes. Full turnkey/both sides; 42 × 40 × 1.0 mm, four layers, S1000H Tg150, ENIG 1 microinch, green/white, 1 oz outer/inner standard with preferred 0.5 oz inner alternative explicitly requested. Four Gerber layer names were submitted to the layer-order dialog.
- Counts entered: 32 unique types, 43 SMT placements, 0 BGA/QFP, 4 physical parts requiring through-hole soldering (3 THT-only plus USB tabs). The note explains 46 total physical PCB parts and 28 THT joints.
- Calculate succeeded. Draft calculator showed PCB **$55.93**, assembly **$29.00**, components **$0.00**, shipping **$27.27** and a **-$27.27** discount, subtotal **$84.93**. Zero components means component pricing is absent, not free. This excludes parts/full reviewed scope and customs/VAT, and is not a complete or vendor-reviewed quote.
- Geoff manually accepted **Special Notes / Agree** before the upload step. All four files individually reached **100% Success**. **Submit File Now** then completed, and the cart showed all four accepted file links at **2026-09-15 01:46:47 UTC**: `click-counter-Q1-Gerbers.zip`, `BOM-PCBA-Q1.csv`, `placements-KiCad-Q1.csv` and `click-counter-Q1-RFQ.zip` (**278,870 bytes**, current public-safe package).
- The linked entries are **PCB W914112AS1N4** and **assembly T-1N5W914112A**, quantity **5**, both **Subject to audit**. This is an actual website file submission, not a reviewed quote, checkout or manufacturing release. Separate quantity-10 pricing is requested under the same RFQ; no separate ten-unit submission number is established.
- A message linked to this submission was sent to **Remi** and verified in message history and a full-message screenshot at **2026-09-15 01:47:22 UTC** (site display 09:47:22 China time). It requests itemized complete 5/10-unit prices including every component/MOQ, both-side SMT and THT/manual soldering, LCD/switch/USB work, prepared battery/NTC harness, loose caps, SBW programming, fixtures/setup, first-article engineering, recurring tests, packaging, lithium freight, tax/duty/brokerage and explicit exclusions/completion paths. It preserves quote-only/no-charge/no-manufacture restrictions and asks for the preferred **0.5 oz inner** versus form-standard **1 oz inner** alternative. Delivery is confirmed; vendor review and prices remain pending. The earlier stated review time was **1–2 days after file receipt**, not guaranteed.
- Form notes carry quotation-only/no-charge/no-manufacture restrictions, all RFQ scope, offboard distinction, first-article hold and preserved engineering gates. Both textarea fields are within the site's 600-character limit; the assembly note is 581 characters.

A PCBWay refresh around **2026-09-15 02:00 UTC** still showed both linked entries **Subject to audit**, **zero unread messages** and **zero awaiting payment**; no new quote or payment state was observed.

A display-options question was sent and verified in the existing **Remi** thread at **2026-09-15 02:04:31 UTC**. It requests a readily sourced low-power numeric LCD as a separately identified alternative, including exact MPN, stock, assembly cost, lead time and power tradeoff. PCBWay was instructed to continue quoting uploaded Q1, with no automatic replacement or manufacture. Both vendors have now been asked for display suggestions; evaluation does not approve a substitution or redesign.

Next: follow the existing linked submission and Remi message for vendor audit, exact sourcing/DFM review and complete separate 5/10-unit quotes. Do not duplicate the submission or treat the calculator subtotal as a complete quote. All documented engineering release gates remain open.

### JLCPCB accepted import — full quote blocked by non-stock-part refusal

- Already signed in; orders showed none, and saved Quotes showed **No files yet** before this new upload.
- **Accepted:** `procurement/click-counter-Q1-Gerbers.zip` (85,741 bytes; SHA-256 `f5e88b602ae17b81dd4745eb1f1715504f1baafe69ee0a844f275cde5b0be212`). Native chooser selection followed by completed processing and detection of a four-layer **42 × 40 mm** board were observed. No formal quote/submission number yet.
- **Accepted:** `dist/click-counter-Q1-RFQ.zip` (278,870 bytes; SHA-256 `79f633ba625e66e39d76e7fbf77db87a0d13eb99414107857d6a8c11ef63616d`) in the **Assembly remark** attachment dialog, filename verified and Save clicked. The same package was accepted in the separate **Function test** attachment field; filename verified there too. These acceptance observations occurred in this local session, by the snapshot time above. They are uploads to a draft, not a completed RFQ submission.
- Form: quantity 5, 1.0 mm, S1000H Tg155, ENIG/1 microinch, 1 oz outer/0.5 oz inner, Standard PCBA/Both Sides. Standard PCBA automatically adds a **70 × 70 mm handling panel**; **Depanel boards & edge rail before delivery = Yes**. Finished circuit outline remains 42 × 40 mm. Vendor DFM/stack confirmation still required.
- **Confirm Production file** and **Confirm Parts Placement** are Yes, with **Do not confirm automatically** checked in both dialogs. Function test = Yes. Assembly remarks request complete separate 5/10 pricing, full scope, battery exclusion/completion path, existing engineering gates and no charge/preorder/manufacture before separate approval.
- Geoff manually advanced JLCPCB's assembly-service terms gate. The original **BOM-PCBA-Q1.csv** import detected **46 references** but ignored the MPN column; an intermediate adapter retaining original comments also produced incorrect generic matches. The **final accepted `BOM-JLCPCB-Q1.csv`** places exact MPNs in `Comment` and retains source wording in `Source Label`, correcting that importer problem. SHA-256: **`f9ee94d67b7c9b908563e4461acd866a7702c9557c117fae1b217782b816e8e7`**. The unchanged **CPL-JLCPCB-Q1.csv** was accepted with it; all **46 PCB references** were detected. The adapter is separate from the RFQ archive; **BOM-PCBA-Q1.csv** remains the controlling PCB BOM and accepted PCBWay upload. No manufacturing package rebuild occurred.
- Q3's wrong CJ **C8545** match was manually corrected to intended **Nexperia 2N7002,215 / C65189**, after verifying the suffix is manufacturer packing information. J1 was matched to **GCT USB4105-GF-A / C3020560**. These are exact identity corrections, not permission for electrical substitutions. See `JLCPCB-IMPORT-ADAPTER-Q1.md` for the packing evidence and U3 variant distinction.
- Live site counts: **46 detected**, **38 confirmed**, **7 shortage**, **2 unselected**. These labels overlap: R9 has some available stock and also a shortage, so their sum is not a distinct-reference total. The quantities below are the site's live sourcing requirements, not changes to the per-board BOM.

| Live unresolved item | References | Exact part / catalog code | Site shortage or matching state |
|---|---|---|---|
| 2.2 µF capacitors | C1, C3, C5, C6 | Murata GRM21BR71E225KA73L / C469542 | 24 pieces short |
| 3.3 Ω resistor | R9 | Yageo RC0603FR-073R3L / C137725 | Requires 20; 19 available; 1 short |
| Both clicky switches | SW1, SW2 | Cherry MX1A-E1NW / C5120587 | 10 pieces short |
| Required LCD | DS1 | Display Elektronik DE188-RU-30/7,5/V(3V) | Unselected/unmatched; required |
| Required regulator | U3 | Texas Instruments TPS7A0230DBVR | Exact MPN unselected/unmatched; do not silently replace with a functional variant |

- **Next** offered **Do not place** or **Select parts** for missing parts. **Select parts** was chosen, preserving required DS1/U3 and the full build scope. No do-not-populate authorization was given. Placement review has not been advanced, and no formal JLCPCB order/quote reference or complete submission exists.
- At approximately **2026-09-15 01:56 UTC**, a request was visibly sent in live chat to **Chian**, including the saved-draft link, for manual engineering/sales resolution and complete itemized separate **5/10-unit** quotes. It identifies all shortages and required unmatched parts, full RFQ scope, battery/test exclusions and a priced completion path, with no charges or manufacture authorized. Chat transferred to **Mitchell Chen**, who acknowledged receipt around **01:56:30 UTC** and asked for time to investigate. Around **02:02 UTC**, Mitchell stated that JLCPCB cannot quote the order with non-stock parts included. Required components were retained; Do not place was not accepted. A support case ID was requested but not returned. The private draft link is deliberately omitted from this public repository. This is a vendor refusal to include unavailable parts in the quote, not a complete or supported-scope price.
- **U3 ordering discrepancy (E14):** the exact BOM **TPS7A0230DBVR** remains unmatched, while TI's current ordering addendum lists **TPS7A0230PDBVR**. TI sections 7.3.2 and 9.1.1 identify **P as active output discharge**, a functional feature, not merely packaging. Do not silently substitute it. Resolve the ordering identity and electrical consequences through controlled review; no design/BOM change has been made. Sources: [TI TPS7A02 datasheet](https://www.ti.com/lit/gpn/TPS7A02) and `JLCPCB-IMPORT-ADAPTER-Q1.md`.

Next: retain the accepted adapter/CPL and full Q1 draft; the vendor will not quote non-stock parts. Follow up on the requested case ID and stocked-display suggestions. Geoff has asked to evaluate an easier-to-source display; JLCPCB was asked for stocked eight-digit, 3 V passive LCD suggestions around 35 × 13 mm for a potential revision. Low-power alternatives and redesign consequences are being evaluated, with no replacement display selected. Preserve submitted Q1, no-DNP and no-charge/no-manufacture limits.

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

The BOM/CPL complaint is clarified locally: BAT1 is a supplied cell/NTC harness and K1/K2 are loose caps. They have no PCB coordinates. `BOM-PCBA-Q1.csv` contains exactly the 46 PCB refs present in the CPL; `OFFBOARD-items-Q1.csv` lists the rest. The correction is included in JLCPCB's uploaded RFQ supplement, and the separate final adapter/CPL import has now been accepted as documented above; no corrected email was sent. Do not add fake placements or omit offboard items from commercial scope.

Current continuation supersedes this historical upload procedure: JLCPCB has refused to quote non-stock parts in the order. Preserve the Q1 draft/full scope, pursue the requested case ID and candidate-display suggestions, and keep battery/test exclusions explicit. No supported subtotal is a complete quote.

## PCBWay

- Assembly entry: https://www.pcbway.com/quotesmt.aspx
- Account cart: https://member.pcbway.com/Order/CartList
- Website chat representative Assistant05 (US) said the specified battery harness, programming and testing can be reviewed/quoted after receiving files through the existing account; stated turnaround **1–2 days after receipt**, not guaranteed.
- Full original Q1 RFQ emailed to PCBWay customer service **2026-09-14 at 18:33:59 UTC**. SENT and **275,486-byte** attachment verified. No full quote or subsequent reply had been found at the last check (approximately 21:24 UTC).
- **PCBWay sign-in succeeded and the signed-in account was observed.** Earlier notes saying sign-in was still the blocker are superseded. Assigned representative was **Remi**; use the current account's displayed contact details.
- Account cart historically contained an unrelated July `companion_carrier_v0` item. It is not Count Fidget, was not modified in that historical session and its assembly price is not relevant. Geoff's latest authorization permits removing previous-project cart entries after verifying filename/project identity; preserve Count Fidget entries.
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
| Controlling PCB BOM / PCBWay importer | `procurement/BOM-PCBA-Q1.csv` |
| JLCPCB importer adapter (separate; not in RFQ archive) | `procurement/BOM-JLCPCB-Q1.csv` |
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
