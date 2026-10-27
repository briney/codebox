---
name: defer
description: Park an idea for later as a card on the current repo's board. Use when the user says defer, park this, later, "add to the board", or otherwise sets work aside for the future.
---

# defer

File the idea as a card that stands on its own weeks later, then get back to the main task.

1. **Draft the card** from the current conversation while the context is fresh:
   - **Title:** short and specific. Never "fix the thing".
   - **Body:**
     ```
     **Why:** what prompted it and what problem it solves.
     **Context:** relevant files, commits, PRs, W&B/HF links, constraints already known.
     **Done when:** one concrete, checkable line.
     ```
2. **File it without duplicating.** Run `board search` with two or three key terms (it finds open and closed issues).
   - Open match: add the new context there with `board comment N --body -` (text on stdin).
   - Closed as not planned, and Bryan is raising it again: `board move N triage --comment -` (reopens it into Triage).
   - Otherwise: `board add --title "TITLE" --body -` with the body on stdin. A match closed as completed is past work; file a new card and mention it under Context.

   ```
   board add --title "TITLE" --body - <<'EOF'
   **Why:** ...
   **Context:** ...
   **Done when:** ...
   EOF
   ```
3. **Reply with one line:** `#N Title`.

If you can hand work to a background subagent (e.g. Claude Code's Agent tool with `run_in_background`), give it the drafted title and body and steps 2–3, then continue the main task; otherwise do it inline.

If `board` reports no board for this repo, tell Bryan to run board-setup.
