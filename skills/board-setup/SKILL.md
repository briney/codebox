---
name: board-setup
description: Give the current repo its GitHub Projects board and the board upkeep rules in AGENTS.md. Use when the user says "set up the board", or a `board` command reports that the repo has no board.
---

# board-setup

1. Run `board setup` inside the repo. It creates the board (or adopts the one already linked), checks the Status options (Triage, Planned, In Progress, Done) and the Board view, writes the upkeep section into AGENTS.md between marker comments, and points CLAUDE.md at AGENTS.md. It's safe to re-run.
2. Show Bryan what changed: the lines `board setup` printed, plus `git status --short` and `git diff -- AGENTS.md CLAUDE.md`.
3. Leave AGENTS.md and CLAUDE.md uncommitted for Bryan's normal commit flow.

If it fails, relay the one-line error. A missing `project` scope prints the fix (`gh auth refresh -h github.com -s project`). On an adopted board missing some Status options, Bryan adds them in the project UI, then re-run `board setup`.
