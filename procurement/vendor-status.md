# Vendor status and website resume procedure

## Current portal progress — 15 September 2026

**Latest user direction: use both portals proactively for revised-file uploads and automatic quotes; email is the fallback for matters the portals cannot accomplish.** Do not await email file-replacement instructions when the site already supports the action, and do not duplicate correspondence. This supersedes the earlier email-only workflow choice; both verified Q2 email sends remain historical evidence.

### JLCPCB Q2 saved revision — 5 units approximately 11:36 UTC; 10 units approximately 11:46 UTC

**Imports processed; quote advancement blocked.**

- Used **Re-Upload** to create a saved Q2 revision. `click-counter-Q2-Gerbers.zip` was processed as **4 layers / 42×40 mm**. `BOM-JLCPCB-Q2.csv` and `CPL-JLCPCB-Q2.csv` processed **50 PCB refs**. The private saved-draft identifier is intentionally omitted from this public repo.
- Quantity **5**, **Standard / both sides**, **1.0 mm**, **S1000H Tg155**, **ENIG 1 microinch**, **1 oz outer / 0.5 oz inner** selected. **Depanel before delivery = Yes**. JLCPCB forces a **70×70 mm support panel**; the finished board remains 42×40 mm.
- **Function Test = Yes** and **Assembly Remark = Yes**, with `click-counter-Q2-RFQ.zip` attached in both fields and the filenames verified. **Confirm Production File = Yes** and **Confirm Parts Placement = Yes**, with **Do not confirm automatically** checked for both. These are draft review settings, not release approval.
- **Via process difference remains open:** the portal forces **Plugged**, while **Tented** is disabled. The PCB note requests review against the RFQ's tenting specification. The selected portal option is a quotation input, not confirmation that this process difference is accepted for manufacture.
- J1 was automatically unchecked during import; it was restored manually as exact **GCT USB4105-GF-A / C3020560**. Current labels: **40 confirmed / 10 shortage / 1 unmatched**; they overlap and must not be summed as distinct refs. All **50 required refs are retained**.
- Shortages shown for **C1, C3, C5, R3, R9, R11, R16, SW1, SW2 and U5**. **DS1 remains unmatched**. Catalog searches for `DE188` and `DE 188` returned **No Result**, with all stock filters unchecked. This describes those searches, not proof that every possible sourcing path is unavailable.
- **Next** shows **Project has unselected parts**, offering **Do not place** or **Select parts**. **Select parts** was chosen; no DNP accepted. The **Quote & Order** tab did not advance. No complete formal quote/order exists from this draft.
- Quantity-5 estimates displayed: **PCB subtotal $32.41** and **DHL DDP shipping $27.63**. Components and assembly are not included yet. These are partial calculator estimates, not a complete RFQ, supported lithium-shipping acceptance or final landed quote.

**Subsequent ten-unit saved draft, approximately 11:46 UTC:** the same Q2 revision now has **10 PCB + 10 PCBA**, Standard/both sides. Current labels are **50 detected / 39 confirmed / 10 shortage / 1 not selected**. J1 remains selected: quantity 10, displayed component line **$10.8220**; this is not a full component subtotal. DS1 is still unmatched; Next again showed **Project has unselected parts**, and **Select parts** was chosen, never DNP. JLCPCB manual matching requires $10 and starts 1–2 working days after payment under its [service terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-parts-selection-service); it was not activated. No successful LCD match or Quote & Order advancement is established.

| Ten-unit shortage shown | Pieces short |
|---|---:|
| C1/C3/C5 combined | 34 |
| R3 | 4 |
| R9 | 1 |
| R11 | 20 |
| R16 | 4 |
| SW1/SW2 combined | 20 |
| U5 | 10 |

Ten-unit **PCB estimate $39.81** comprises **$13.00 special offer + $17.60 ENIG + $8.17 material + $1.04 production-file confirmation**. **DHL DDP $27.63**, 2–4 business days, 0.24 kg was shown. Assembly and total component prices remain dashes. Neither this PCB subtotal nor the selected J1 line is a complete quote.

Changing PCB specifications cleared the PCB remark and opened an empty assembly remark modal. Both were restored: a **193-character PCB remark** explicitly identifies the **finished 42×40×1 mm board**, and a **485-character assembly scope plus RFQ attachment** was verified. The Function Test RFQ attachment remained present. The production **Do not confirm automatically** checkbox was reapplied and confirmed; **Confirm Parts Placement = Yes** was verified selected. The earlier no-auto placement setting is part of the five-unit observation; do not claim a fresh ten-unit checkbox recheck that was not recorded.

**Still open at JLCPCB:** resolve the exact required LCD and shortages without DNP or paid preorder using the existing Frank case, and obtain a priced completion path for unsupported battery/test scope. Manual matching requires payment and was not activated.

### PCBWay Q2 form — five- and ten-unit calculations captured

Both quantities were calculated in a fresh Q2 form. The user approved the new Special Notes / Agree notice, accepted before cart creation at **11:48:56 UTC**. All four uploaded Q2 files showed **100% Success**, and **Submit the File Now** completed. Final cart verification at **11:51:09 UTC** showed PCB **W914112AS1N6** / assembly **T-1N7W914112A**, quantity **5**, PO **COUNT-FIDGET-Q2-RFQ-5**, both **Subject to audit**. The Gerber ZIP appears on the PCB entry; all four filenames appear on assembly. **Under Review 4 / Awaiting Payment 0 / Production 0**, including the unchanged Q1 entries. Ten is calculator-only; the submitted scope requests complete separate 5/10 prices.

| Partial online calculation (USD) | 5 units | 10 units |
|---|---:|---:|
| PCB | 55.93 | 81.36 |
| Assembly | 88.00 | 102.95 |
| DHL shipping shown | 27.27 | 27.27 |
| Shipping discount shown | −27.27 | −27.27 |
| **Partial total** | **143.93** | **184.31** |
| Quoted shipping weight (kg) | 0.52 | 0.54 |

**Components and advanced services are excluded from these online costs.** The form requests depaneling, functional testing, firmware loading and cable-harness work; selecting these services does not include their prices in the totals above. The shipping promotion is not a confirmed full-scope lithium/landed quote. PCB lead time shown is **4–5 days**; freight is **2–4 business days**. Neither establishes the complete assembled-product delivery schedule.

The form uses turnkey sourcing, both sides, **no Chinese alternatives**, **32 unique types / 47 SMT placements / 0 BGA-QFP / 4 parts requiring through-hole work**. The four include the hybrid USB connector, already counted among SMT placements; this does not change the **50 fitted PCB references**.

Selected construction: **1.0 mm, Tg150–160, 5/5 mil, 0.3 mm minimum drill, ENIG 1 microinch, tenting, 1 oz outer copper**. The portal's minimum inner copper is **1 oz**, so these calculations do **not** represent the preferred 0.5 oz inner construction. The PCB remark explicitly requests 0.5 oz inner and a separately quoted alternative. Retain the construction difference when comparing with JLCPCB's selected 0.5 oz inner configuration.

The specific Special Notes / Agree gate is resolved by the user’s explicit approval. Saved fabrication details confirm **S1000H TG150**, the construction above and the full no-manufacture/0.5 oz-inner-review note. Saved assembly details confirm both sides, quantity5, counts32/47/0/4, and Yes for depaneling, function test, firmware loading and cable harness. The full assembly remark is present. The form labels47 as SMD Parts but saved detail says SMT Pads:47 is placements, and vendor solder-point pricing remains to be calculated from the board/BOM.

Q2 files are submitted for review; this establishes file acceptance, not technical acceptance or a complete quote. No paid sourcing, purchase or manufacturing release occurred.

## Q2 sharing and Sent-mail records — earlier in this continuation

- **User approval received:** Geoff explicitly approved sharing the finished Q2 package and technical follow-up with both vendors. The previous specific-disclosure approval blocker is resolved. Both Q2 email dispatches are confirmed below. JLCPCB subsequently processed the Q2 draft imports described above; PCBWay Q2 files were subsequently accepted for review; vendor technical acknowledgment/full quotation remain unconfirmed.
- **Historical channel decision:** at **2026-09-15 11:06:51 UTC**, the latest four vendor emails were reread. No newer email was found beyond Remi's 2026-09-15 03:23:59 UTC email-only request and Frank's 2026-09-14 21:23:46 UTC rough quote/import reply. This informed the then-current email-only choice. The user subsequently clarified **portal workflows first, email fallback** as recorded above; do not treat the old choice as a reason to wait for email instructions.
- **Q2 ready at commit `c1240b9`:** `dist/q2/click-counter-Q2-RFQ.zip`, **124 files / 1,930,577 bytes**, SHA-256 `29512016b9f83003bf416642617bfb0f8bbc76ea2ca64ba1c31d07e6df0b9438`. The [manifest](../dist/q2/manifest-Q2.json) binds the members. Native ERC/DRC/connectivity/parity checks are clear; the SW2 thermal and Q4 via issues were corrected. Physical qualification and vendor DFM acceptance remain open.
- **Q2 PCBWay dispatch verified — 11:12:50 UTC:** Gmail Sent confirms the email to Remi in the existing W914112AS1N4 engineering-question thread. Verified attachments: `click-counter-Q2-RFQ.zip` **1,930,577 bytes**, `click-counter-Q2-Gerbers.zip` **87,741 bytes**, `BOM-PCBA-Q2.csv` **7,017 bytes**, `placements-KiCad-Q2.csv` **4,389 bytes**. The body requests exact U5 pattern/process acceptance (not combined openings), association of all four files with the existing case and required portal-replacement instructions, and complete separate 5/10 RFQ prices with test hours/scope behind $75 plus $10/hour. That email recorded the then-current email-only choice. The later portal-first direction changes the workflow; all physical/no-charge/no-paid-parts/no-manufacture gates remain.
- **Q2 JLCPCB dispatch verified — 11:17:46 UTC:** Gmail Sent confirms the email in the existing Frank Budget RFQ case. Verified attachments: `click-counter-Q2-RFQ.zip` **1,930,577 bytes**, `click-counter-Q2-Gerbers.zip` **87,741 bytes**, `BOM-JLCPCB-Q2.csv` **8,006 bytes**, `CPL-JLCPCB-Q2.csv` **2,295 bytes**. Use this existing email case for Q2 issues that the portal cannot accomplish.
- **Subsequent state:** both email sends are verified; JLCPCB later processed Q2 files in the saved draft described above. This does not establish vendor technical acceptance, completed Quote & Order or a full quote. PCBWay Q2 upload/submission is verified above. No spending, paid part preorder, order or manufacturing release.

## Earlier verified website state — 15 September 2026, 10:48:59 UTC

- **Access restored:** supported native Chrome access is available; the existing PCBWay/JLCPCB pages and replies were freshly read. The earlier locked-Mac failure is preserved below as historical evidence, not a current blocker.
- **PCBWay latest cart at 10:48:59 UTC:** PCB **Awaiting reply**, assembly **Being reviewed**; **Under Review 2, Awaiting Payment 0, Production 0**. Existing Q1 references remain W914112AS1N4 / T-1N5W914112A, with all four Q1 filenames present. No Q2 file submission, payment or manufacturing release.
- **PCBWay website reply, 02:25:22 UTC:** Remi's site timestamp is **2026-09-15 10:25:22 China time**. Follow supplied Gerbers/BOM/online parameters and include all notes in the files. Programming/testing is additional and needs step-by-step instructions. Testing starts at **$75**, then **$10/hour**, charged after the process. No hours, complete agreed test scope or fixed 5/10-unit total were supplied. This reply was read after access was restored; its earlier message time is not the verification time.
- **JLCPCB saved Q1 draft:** freshly reconfirmed **46 refs, 38 confirmed, 7 shortage, 2 unselected**; the labels overlap and there is no formal order. Mitchell's late **22:18 Eastern September 14 chat (approximately 02:18 UTC September 15)** says programming/testing is quoted only after order, with **$15.70 engineering** and **$7.86/hour labor** additional. These are rates only; hours, scope and a full total remain absent. Battery assembly remains excluded; non-stock-part quotation refusal is unresolved.
- **Q2 approval context:** the earlier pad-pattern/file-replacement email was rejected by automatic approval review before specific user approval. That attempt was not sent; the user has now supplied the required sharing approval. The subsequent user direction is portal-first with email fallback. No combined mask opening has been approved.
- **Engineering/package:** the finished, checked Q2 package is ready as identified above. At that earlier checkpoint vendor-uploaded files remained Q1. The later JLCPCB Q2 imports are recorded above; all physical qualification/first-article gates remain open.

Neither vendor has supplied a complete quote. Do not spend, preorder parts or release manufacture to obtain missing pricing.

## Historical access failure and email check — 15 September 2026, 10:04 UTC

- **Browser at 10:04 UTC:** initial local inventory reported the Mac locked and no available app/browser surfaces; automatic unlock failed. The separate browser connector also failed initialization. Geoff was asked to unlock the Mac, and no response had arrived at that checkpoint. No website state was inferred or changed during that blocked check. Native access was subsequently restored as recorded above.
- **PCBWay new DFM question, 03:07:50 UTC:** Remi asks permission for whole solder-mask openings because green mask requires at least 0.19 mm IC pad spacing. The actual attachment highlights U5 pads 6/7, whose Q1 copper/mask gap is 0.15 mm. No permission was given and no revised Gerber acceptance was observed. The proposed Q2 TI land pattern has 0.20 mm copper gap and 0.10 mm nominal mask bridge; process acceptance is pending. See `../docs/q2-solder-mask-review.md`.
- **PCBWay channel preference, 03:23:59 UTC:** Remi said the information was already answered on the website and requested **email only** for follow-up. The website reply had not yet been read at the 10:04 UTC locked-Mac checkpoint; it was subsequently read after access returned. Do not duplicate messages across channels.
- **Historical Q2 reply attempt, NOT SENT:** automatic approval review rejected the prepared pad-pattern/file-replacement inquiry because specific revised-detail approval was missing at that checkpoint. A focused question was then pending; the user subsequently approved sharing the finished Q2 package with both vendors. Keep the draft under ignored `private/`; the blocked attempt is not supplier-receipt evidence.
- **Commercial state:** the two new PCBWay emails contain no complete 5/10 quote. No newer JLCPCB/Frank reply was found during this continuation. Existing JLCPCB non-stock-part refusal, battery exclusion and prepayment test-review restriction remain. No money or manufacturing release.
- **Engineering:** separate Q2 native schematic/PCB and enclosure correction are being implemented. Retain the DE188 baseline because researched passive alternatives do not establish a JLC stock advantage. Select U3 TPS7A0230PDBVR intentionally; U5 TLV7032DGKR external sourcing is possible but JLC stock is not established. Existing website files are still Q1; no Q2 submission has occurred.

The 10:04 UTC access/read state above was superseded by the 10:36 UTC native inspection. Other dated observations below retain their original historical context.

## Current engineering hold — 15 September 2026

Q1 remains available for **sourcing/budgetary review only**. Its missing LCD bias capacitors and frame-rate margin require a controlled revision before final production quotations. The alleged source/binary mismatch was independently **refuted** by an exact TI rebuild; the initial mistaken claim was explicitly corrected with both vendors. Read [the consolidated review](../docs/adversarial-review-Q2.md). Q2 has been sent by email for review/quotation and processed in the JLCPCB saved portal revision. Completed quotation, vendor technical acceptance and the PCBWay Q2 portal result remain unverified. No money, paid preorder or manufacturing release is authorized.

| Existing case | Verified subsequent correspondence |
|---|---|
| PCBWay, W914112AS1N4 / T-1N5W914112A, Remi | Engineering hold sent **02:11:11 UTC**; correction of the firmware claim sent **02:17:56 UTC**, verified in site history. Preserve these references. Any Q1 pricing needs reconfirmation against a reviewed revision. |
| JLCPCB saved import draft, Mitchell Chen / existing Frank email case | Around **02:07 UTC**, Mitchell identified TPS7A0230PDBVR / C3747031 as stocked and suggested paid Global Sourcing preorder for DE188. Around **02:15 UTC**, he said there was no stocked alternative to the requested LCD. He directed follow-up to the existing colleague's email case; no separate case ID was returned. Engineering hold and explicit firmware-claim correction were visibly sent, the latter around **02:17 UTC**. No U3 substitution or paid preorder was accepted. |

The earlier native browser read reconfirmed the hold/correction messages and JLCPCB's saved BOM state (46 detected, 38 confirmed, 7 shortage, 2 unselected). That earlier read was not a fresh PCBWay cart audit; the subsequent 10:36 UTC counter inspection is recorded above. Continue engineering and sourcing against these existing cases; do not repeat the resolved agreement or import steps. The timeline below records the earlier Q1 submission state.

PCBWay update: **2026-09-15 01:47:22 UTC** (September 14 Eastern). Its four-file website submission succeeded at **01:46:47 UTC**, with linked five-unit **PCB W914112AS1N4** and **assembly T-1N5W914112A**, both **Subject to audit**; the linked full-scope message to Remi was sent and verified at **01:47:22 UTC**. JLCPCB accepted the final 46-reference importer adapter and unchanged CPL; remaining shortages and two required unmatched parts need manual vendor resolution. A full-scope live-chat request was visibly sent to Chian at approximately **01:56 UTC**, transferred to Mitchell Chen and acknowledged around **01:56:30 UTC**. Around **02:02 UTC**, he refused to quote an order including non-stock parts; the complete Q1 quote is blocked on that basis. Geoff manually advanced both site-agreement gates. Neither vendor has a complete quote. No checkout, paid order, paid parts pre-order or manufacturing release exists.

## Local website progress and evidence

Historical Q1 continuation: local native Chrome control was verified while the browser-tab connector failed initialization. Intermittent native stale state recovered after refreshing the page observation and user interaction. At that checkpoint the checkout matched GitHub; integrity and portable host tests passed once, and no fresh DRC/hardware validation had occurred. Current Q2 engineering/check status is recorded at the top and in the project handoff.

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
- **U3 ordering discrepancy (E14), submitted Q1 context:** the exact Q1 BOM **TPS7A0230DBVR** remains unmatched, while TI's ordering addendum lists **TPS7A0230PDBVR**. TI sections 7.3.2 and 9.1.1 identify **P as active output discharge**, a functional feature, not merely packaging. At the historical import checkpoint no design/BOM change had been made. The separate Q2 now intentionally selects TPS7A0230PDBVR with rail/FRAM qualification gates; the saved Q1 vendor draft is unchanged. Sources: [TI TPS7A02 datasheet](https://www.ti.com/lit/gpn/TPS7A02) and `JLCPCB-IMPORT-ADAPTER-Q1.md`.

Current next step: retain the accepted adapter/CPL and full Q1 draft; the vendor will not quote non-stock parts. Follow the existing Frank email case as Mitchell requested; no separate case ID was provided. The earlier display request asked for stocked eight-digit, 3 V passive LCDs around 35 × 13 mm. Subsequent review retains exact DE188 for Q2 because no researched passive alternative establishes a JLC stock advantage; those digit/size choices were not fixed user requirements. Preserve submitted Q1, no-DNP and no-charge/no-manufacture limits.

### Mail/image continuity checked locally

At that historical mail/image checkpoint, no newer reply or outbound follow-up was found. All four images in Frank's **2026-09-14 21:23:46 UTC** message were read through the actual Gmail image viewer. The email connector alone did not expose usable attachments; direct external image web access failed, but the existing Gmail message displayed them normally.

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

## Latest cart observation — 2026-09-15 10:48:59 UTC

Native Chrome showed existing PCB **W914112AS1N4 — Awaiting reply**, assembly **T-1N5W914112A — Being reviewed**, both quantity 5. The PCB asks for email follow-up on engineering questions. All four accepted Q1 filenames remain present. Displayed PCB $55.93 and assembly $29.00 still omit components (shown as $0.00), so they remain incomplete. Counters: Under Review 2, Awaiting Payment 0, Production 0. Only these Count Fidget entries were observed; no unrelated cart removal was needed or performed. No new files, message, payment or order were submitted.

## Q2 local package ready

The corrected Q2 review archive now contains 124 files (1,930,577 bytes; SHA256 `29512016b9f83003bf416642617bfb0f8bbc76ea2ca64ba1c31d07e6df0b9438`). Native ERC/DRC/connectivity/parity all have zero findings; 50 fitted references match BOM/CPL; enclosure model checks pass. Q1 integrity is preserved. The package has **not been uploaded or accepted**. A focused user approval request now covers disclosing this finished revision and technical follow-up to both existing vendor cases after automatic review rejected the earlier Q2 email. Physical release gates and the no-spend/no-manufacture limit remain.
