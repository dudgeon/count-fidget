---
name: board-bring-up
description: Walk the operator through bringing up one assembled Count Fidget Q5 board (inspection, shorts check, first power, flashing, commissioning, cell and enclosure checks) per docs/board-bring-up.md and fill in its log in verification/first-article/. Use when the user says a board arrived, wants to bring up, test or commission board CF-0N, or asks what the next board step is.
---

# Bring up one Q5 board

The procedure is `docs/board-bring-up.md`; the logs are `verification/first-article/CF-0N.md` with the summary in `verification/first-article/README.md`. Do not improvise steps that are not in the doc. If the doc is wrong or missing something, fix the doc in the same change.

1. Read `docs/board-bring-up.md` and `verification/first-article/README.md`. Pick the board: the one the user names, else the first NOT STARTED or partly filled log. Only one board at a time; if an earlier board is HOLD, ask whether the fault could be common before powering another.
2. Go stage by stage. For each stage, tell the user what to do and what values to read out, wait for their answers, then write the measured values (not just ticks) into the board's log. Apply the stop rules exactly: on a STOP, mark the board HOLD, record why, and do not tell the user to power it again.
3. Stage 6: **you run all flashing yourself; the user never types flasher commands.** It runs on the user's Mac over Remote Control, from a separate worktree (not the user's own checkout), following the `flash-clickers` skill's sequence exactly: preflight, wait, probe, backup (read-only), `flash --no-leave`, verify-device, leave, record-check, summary. Only one session may drive the Mac at a time. Ask the user to enter DFU holding RESET until after the pinhole is released, to keep USB connected 5 s after the first start, then ask the four commissioning questions one at a time. Record the DFU serial and answers in the log. A failed backup read on a new board is a STOP; never unprotect.
4. Always repeat the two safety rules when they apply: press the pinhole before unplugging a board in DFU, and LIR2032 only, inserted with USB connected.
5. At the end, set the status in the log and the summary table, and commit the log on a branch (never the flasher CSV or private photos). Then tell the user the result and which board is next.

A flash PASS or a bring-up PASS is not hardware qualification; the sampled tests B–F in `docs/q5-first-article-test-plan.md` still decide that.
