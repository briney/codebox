---
name: next
description: Bring the current repo's board up to date and show it. Use when the user asks "what's next?", "show the board", "what should I work on", or wants to reprioritize deferred work.
---

# next

1. **Reconcile.** Run `board activity` (default window: since the last run in this clone, else 14 days; `--since 7d` overrides). It lists merged PRs with their bodies, updated open PRs, commits on the default branch, status mismatches, and open issues not on the board. Decide what the facts imply and apply the moves without asking:
   - a merged PR that completes a card → `board move N done`
   - a PR or commits that only partly advance a card → `board move N in-progress --comment - <<'EOF'` with what changed and what's left as the text, then `EOF`
   - a status mismatch → run the command printed after `->` on its line (closed but not Done → `board move N done`; open but Done → `board move N in-progress`, or `board move N done` if the work really is finished). Never reopen a closed issue because of a mismatch alone.
   - an open issue not on the board → `board add N` (it goes into Triage)

   A run with `--since` does not advance the saved window; only a plain `board activity` does.

   Quote titles with single quotes and send bodies/comments through a quoted heredoc so backticks and $ aren't expanded.

   Report the moves in one line: `Board: #12 → Done (PR #49), #15 → In Progress, #20 → Triage`.
2. **Show the board.** Run `board list` and show its output: Planned (in priority order, blocked items marked), In Progress, Triage. A card added seconds ago may not show up yet; that's GitHub lag, not a failure, so don't add it again.
3. **Apply Bryan's reply.** Turn his plain language into `board` calls, then report them in one `Board:` line:
   - "promote 51" → `board move 51 planned`; "start 51" → `board move 51 in-progress`; "48 is done" → `board move 48 done`
   - "put 53 on top" → `board order 53 --before <first Planned>`; "53 after 51" → `board order 53 --after 51`
   - "drop 48" → `board drop 48 --comment - <<'EOF'` with the reason as the text (closes it as not planned)
   - "50 depends on 47" → `board block 50 --by 47`
