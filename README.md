# codebox

A harness-neutral agent toolkit: skills and small tools that work the same in Claude Code, Codex and OpenCode. The repo board is its first feature.

Each repo gets one GitHub Projects board with statuses Triage → Planned → In Progress → Done. Order within Planned is priority. A dropped card is an issue closed as not planned; a blocked card has a native issue dependency. The upkeep rules live in each repo's `AGENTS.md`, written by `board-setup`.

## Requirements

- `gh`, authenticated with the `project` scope (`gh auth refresh -s project`)
- `python3` 3.8 or newer

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/briney/codebox/main/bootstrap.sh | bash
codebox install                    # or: codebox install --harness claude|codex|opencode
```

Bootstrap clones codebox into `~/.codebox` at the newest release tag and links `codebox` into `~/.local/bin`. Re-running it only fetches; it doesn't move the checkout, and tells you to run `codebox update`.

`codebox install` links skills into `~/.claude/skills` (Claude Code) and `~/.agents/skills` (Codex, OpenCode), and plugin commands into `~/.local/bin`.

- `codebox update` moves to the newest release, re-links, and prints each plugin and skill version change with its notes. It refuses if `~/.codebox` isn't a clean release-tag checkout.
- `codebox uninstall` removes only the links it recorded in `~/.local/state/codebox/installed.json`, and deletes `~/.codebox` (never a `CODEBOX_HOME` checkout).

Install and update are all-or-nothing: if a path they would link already exists and codebox didn't create it, they stop and name it. codebox never touches `~/.claude/settings.json`, your global `CLAUDE.md` or `AGENTS.md`, or Codex and OpenCode config.

To work from a development checkout, link from it instead; before any tag exists, the first run is `CODEBOX_HOME=~/git/codebox ~/git/codebox/bin/codebox install`. `codebox install` is safe to re-run.

## Plugins

### board

Skills:

- `codebox-defer`: park an idea as a card on the current repo's board ("park this for later").
- `codebox-next`: bring the board up to date and show it ("what's next?").
- `codebox-board-setup`: create the repo's board and write the upkeep rules into `AGENTS.md` ("set up the board here").

Say it in plain language, or use `/codebox-next` in Claude Code and OpenCode, `$codebox-next` in Codex (same for the others). OpenCode reads both `~/.claude/skills` and `~/.agents/skills` and dedupes by name, so the double install is harmless.

For a repo that already has a board, run `board setup` there to refresh its `AGENTS.md` section; `board activity` hints when it's stale.

The `board` command (`plugins/board/bin/board`) works on the repo in the current directory:

- `board find`, `board setup`: show the linked board; create or verify it.
- `board add --title T [--body B]`, `board add N`: create a card, or board an existing issue.
- `board move N STATUS [--comment C]`: set status; Done closes the issue, moving out of Done reopens it.
- `board order N (--before M | --after M)`: reposition a card.
- `board block N --by M`: mark N as blocked by M.
- `board drop N [--comment C]`: close as not planned.
- `board comment N [--body B]`, `board search TERMS`, `board list [--all]`, `board activity`.

Text flags take `-` to read stdin, e.g. `board add --title T --body - <<'EOT'`. Stdin is never read implicitly.

## Releasing

Bump the version and add a one-line note in `plugins/<name>/plugin.json` for each changed plugin and skill, run the tests (`tests/test_versions.py` fails on a changed plugin or skill without a bump), then tag `vX.Y.Z` and push the tag.

## Tests

```sh
python3 -m unittest discover -s tests
tests/e2e.sh OWNER/REPO   # live check against a scratch repo; the name must contain "scratch"
tests/triggers.sh [harness...]   # on demand: checks skills trigger from plain language; costs model calls
```
