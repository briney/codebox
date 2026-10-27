# codebox

Bryan's harness-neutral agent toolkit: skills and small tools that work the same in Claude Code, Codex and OpenCode. The repo board is its first feature.

Each repo gets one GitHub Projects board with statuses Triage → Planned → In Progress → Done. Order within Planned is priority. A dropped card is an issue closed as not planned; a blocked card has a native issue dependency. The upkeep rules live in each repo's `AGENTS.md`, written by `board-setup`.

## Requirements

- `gh`, authenticated with the `project` scope (`gh auth refresh -s project`)
- `python3` 3.8 or newer

## Install

```sh
git clone https://github.com/briney/codebox.git ~/codebox && ~/codebox/install.sh
```

This links the skills into `~/.claude/skills` and `~/.agents/skills` and `board` into `~/.local/bin`. It is safe to re-run, and it removes dangling links left by the old codebox install.

## What's in it

Skills, in `skills/`:

- `defer`: park an idea as a card on the current repo's board.
- `next`: bring the board up to date and show it.
- `board-setup`: create the repo's board and write the upkeep rules into `AGENTS.md`.

Invoke them with `/defer` in Claude Code and OpenCode, or `$defer` in Codex (same for `next` and `board-setup`). They also trigger from plain language, such as "defer this" or "what's next?". OpenCode reads both `~/.claude/skills` and `~/.agents/skills` and dedupes by name, so the double install is harmless.

The `board` command (`bin/board`) works on the repo in the current directory:

- `board find`, `board setup`: show the linked board; create or verify it.
- `board add --title T [--body B]`, `board add N`: create a card, or board an existing issue.
- `board move N STATUS [--comment C]`: set status; Done closes the issue, moving out of Done reopens it.
- `board order N (--before M | --after M)`: reposition a card.
- `board block N --by M`: mark N as blocked by M.
- `board drop N [--comment C]`: close as not planned.
- `board comment N [--body B]`, `board search TERMS`, `board list [--all]`, `board activity`.

Text flags take `-` to read stdin, e.g. `board add --title T --body - <<'EOT'`. Stdin is never read implicitly.

## Tests

```sh
python3 -m unittest discover -s tests
tests/e2e.sh OWNER/REPO   # live check against a scratch repo; the name must contain "scratch"
```
