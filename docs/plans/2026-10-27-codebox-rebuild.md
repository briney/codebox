# Codebox Rebuild + Deferred-Work Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `briney/codebox` with a fresh, harness-neutral agent toolkit whose first feature is a per-repo GitHub Projects board (`board` CLI + `defer` / `next` / `board-setup` skills + AGENTS.md upkeep rules), then roll it out to `briney/oplm`.

**Architecture:** One Python-stdlib script, `bin/board`, is the only code that talks to GitHub (via `gh api graphql` / `gh api` subprocesses). Three `SKILL.md` files are short prose wrappers around it, identical across Claude Code, Codex, and OpenCode. `install.sh` symlinks the skills and the script into place.

**Tech Stack:** Python 3 stdlib, `gh` CLI, bash (install only), `unittest` (stdlib, no pytest dependency).

**Spec:** `docs/specs/2026-10-27-board-design.md` (copied in Task 1 from `/tmp/claude-1000/-home-bryanbriney-git-oplm/e799ac12-43c7-464c-a611-1a5010d8d0a9/scratchpad/2026-10-27-board-design.md`). Read it before starting any task.

## Global Constraints

- Only external dependency: `gh`. Runtime: `python3`, stdlib only. Floor: Python 3.8 (planner's call; confirm `python3 --version` on loki and a cluster node before Task 2, and lower the floor if needed). Use `from __future__ import annotations`; no `match`, no `X | Y` at runtime.
- Status options, exactly, in this order: `Triage`, `Planned`, `In Progress`, `Done`.
- Board owner = repo owner. One board per repo, linked to the repo. Title of a newly created board = repo name.
- Dropped = closed as **not planned**, never deleted. Blocked = native issue dependency (`addBlockedBy`), never a column.
- Card body sections: **Why**, **Context**, **Done when:** (one concrete, checkable line).
- Agents make board moves without asking and report them in one line: `Board: #12 → Done (PR #49), #15 → In Progress`.
- Missing `project` scope → print exactly: `gh auth refresh -h github.com -s project`.
- No hooks, no session-end triggers, no Claude-only machinery. Skills are identical files across harnesses.
- Nothing from old codebox is carried over except `LICENSE` (planner's call: keep the license).
- New `main` is an orphan history. **Ask Bryan immediately before the force-push.** Don't touch `briney/codebox-notebook`. Leave visibility public.
- Creating any GitHub repo, project, or issue outside the scratch repo needs Bryan's OK first.

## Review Focus

1. **Running against an adopted board that's already in use** (brineylab Flyloft, or any board with its own options or items). Expected: `board setup` never rewrites or deletes existing Status options or items. If all four options exist, it changes nothing. If some are missing, it exits non-zero and names the missing ones so Bryan can add them in the UI. Test: Task 3, `test_plan_status_options_*`.
2. **Boards with more than 100 items, or with issues from other repos.** Expected: `list`, `activity`, and the not-on-board sweep paginate through every item. Issues from another repo show as `owner/repo#N` and are never mistaken for the local `#N`. Test: Task 2, `test_render_list_foreign_repo`; Task 4 live check with a pagination page size forced to 2.
3. **Loose status names and moves on closed issues.** Expected: `in-progress`, `in_progress`, `IN PROGRESS` and `planned` all resolve, and unknown names list the valid ones. Moving a closed issue to a non-Done status reopens it. `move N done` closes it as completed. Test: Task 2, `test_status_option_*`; Task 4 live check.
4. **Re-running `board setup` on a repo whose AGENTS.md or CLAUDE.md already exists.** Expected: the marker block is replaced in place, never duplicated, and the text outside the markers is byte-identical. A CLAUDE.md that doesn't mention AGENTS.md gets one `@AGENTS.md` line appended. A missing CLAUDE.md is created as `@AGENTS.md\n`. Test: Task 2, `test_splice_*` and `test_claude_pointer_*`.
5. **Running `board` where there's no board, no GitHub remote, no git repo, or no `project` scope.** Expected: a one-line error, a non-zero exit, and no traceback. "No board" points at `board-setup`, and the scope error prints the refresh command. Test: Task 3 live check, run in `/tmp` and in the scratch repo before setup.

---

## File Structure

```
LICENSE                          kept from old repo
README.md                        what codebox is, install, contents (Task 7)
install.sh                       symlinks skills + board; prunes dead old-codebox links (Task 6)
bin/board                        the CLI; executable Python, no extension (Tasks 2–4)
board/agents-section.md          single source text of the AGENTS.md upkeep block (Task 5)
skills/defer/SKILL.md            (Task 5)
skills/next/SKILL.md             (Task 5)
skills/board-setup/SKILL.md      (Task 5)
tests/test_board.py              unittest; pure helpers only (Task 2)
tests/e2e.sh                     scripted live run against a scratch repo (Task 7)
docs/specs/2026-10-27-board-design.md
docs/plans/2026-10-27-codebox-rebuild.md   (this file)
```

`bin/board` stays one file. Pure helpers (parsing, rendering, splicing) sit at the top, the GitHub calls in the middle, and `main()` with argparse subcommands at the bottom. Tests load it with `importlib.machinery.SourceFileLoader("board", "bin/board")`.

**Scratch repo for live checks:** `briney/board-scratch` (private), created in Task 3 **after Bryan OKs it**. The token can't delete repos, so Bryan deletes it by hand when done.

---

### Task 1: Orphan branch with the spec and plan

**Files:**
- Create: `docs/specs/2026-10-27-board-design.md` (copy of the scratchpad spec)
- Keep: `LICENSE`, `docs/plans/2026-10-27-codebox-rebuild.md`
- Create: `.gitignore` (`__pycache__/`, `*.pyc`)

- [ ] **Step 1:** `git switch --orphan rebuild`, then remove everything from the index and working tree except `LICENSE` and `docs/`. That includes `notebook/`, `.gitmodules` and `.gitattributes`. Check: `git ls-files` is empty and `ls` shows only `LICENSE docs`.
- [ ] **Step 2:** Copy the spec into `docs/specs/` and write `.gitignore`.
- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "codebox: start fresh as a harness-neutral agent toolkit"
```

---

### Task 2: `board` pure helpers (TDD)

**Files:**
- Create: `bin/board` (executable, `#!/usr/bin/env python3`)
- Test: `tests/test_board.py`

**Interfaces (Produces):**
- `STATUSES = ["Triage", "Planned", "In Progress", "Done"]`
- `MARK_START = "<!-- codebox:board:start -->"`, `MARK_END = "<!-- codebox:board:end -->"`
- `parse_since(s: str, now: datetime) -> datetime`: accepts `14d`, `2w`, `36h`, or ISO date `2026-10-01` (UTC). Anything else raises `ValueError`.
- `status_option(name: str) -> str`: normalizes case, `-` and `_` to the canonical name in `STATUSES`. Unknown names raise `ValueError` whose message lists `STATUSES`.
- `parse_issue_ref(s: str) -> int`: accepts `12`, `#12`, and `https://github.com/o/r/issues/12`.
- `splice_section(text: str, section: str) -> str`: wraps `section` in the markers. Replaces the existing marked block if there is one. Otherwise appends it after one blank line, or returns just the block if `text` is empty.
- `claude_pointer(text: str | None) -> str | None`: `None` (no file) gives `"@AGENTS.md\n"`. Text already containing `AGENTS.md` gives `None` (no change). Otherwise it returns the text with `@AGENTS.md\n` appended, after a newline if one is missing.
- `render_list(items: list[dict], repo: str, show_done: bool = False) -> str`. Item dict: `{"number": int, "title": str, "status": str | None, "state": "OPEN" | "CLOSED", "repo": "owner/name", "blocked_by": [str]}`, where `blocked_by` holds already formatted refs of *open* blockers. It groups under the headers `Planned`, `In Progress`, `Triage`, `(no status)`, and `Done` only when `show_done`, keeping input order inside each group. Empty groups are omitted. Line format: `  #12 Title`, with ` [blocked by #47]` appended when blocked. Foreign-repo items print as `owner/name#12`. Closed items appear only under Done, and only when `show_done`.

- [ ] **Step 1: Write the failing tests** in `tests/test_board.py`:
  - `test_parse_since`: with `now = datetime(2026,10,27,tzinfo=utc)`, `14d` gives Oct 13, `2w` gives Oct 13, `36h` gives Oct 25 12:00, `2026-10-01` gives Oct 1 00:00 UTC, and `soon` raises `ValueError`.
  - `test_status_option_variants`: `in-progress`, `in_progress`, `IN PROGRESS`, `In Progress` all give `"In Progress"`, and `planned` gives `"Planned"`.
  - `test_status_option_unknown`: `"Backlog"` raises `ValueError` whose message contains `Triage`.
  - `test_parse_issue_ref`: the three forms give 12, and `abc` raises `ValueError`.
  - `test_splice_append`: `splice_section("# Repo\n", "rules")` equals `"# Repo\n\n<!-- codebox:board:start -->\nrules\n<!-- codebox:board:end -->\n"`.
  - `test_splice_replace_idempotent`: splicing `"new"` into the output above leaves exactly one start marker, puts `new` inside, keeps the bytes outside the markers identical, and gives the same result when run twice.
  - `test_splice_empty`: `""` gives just the block.
  - `test_claude_pointer_*`: three cases. `None` gives `"@AGENTS.md\n"`, `"See AGENTS.md\n"` gives `None`, and `"# x"` gives `"# x\n@AGENTS.md\n"`.
  - `test_render_list_groups_and_order`: Planned items #3 then #1, keep that order. Planned is printed before In Progress, which is before Triage. Done is hidden by default.
  - `test_render_list_blocked`: `"  #1 A [blocked by #2]"` appears.
  - `test_render_list_foreign_repo`: an item with `repo="brineylab/other"` renders as `brineylab/other#5`.
- [ ] **Step 2:** Run `python3 -m unittest tests/test_board.py -v`. Expected: errors, because the functions are not defined.
- [ ] **Step 3:** Implement the helpers in `bin/board`. Give `main()` a stub that prints usage.
- [ ] **Step 4:** Run `python3 -m unittest tests/test_board.py -v`. Expected: all pass.
- [ ] **Step 5: Commit:** `git add bin/board tests/test_board.py && git commit -m "board: pure helpers with tests"`

---

### Task 3: GitHub plumbing, `board find`, `board setup`

**Files:** Modify `bin/board`. Test: `tests/test_board.py` (one more pure test) plus a live check.

**Interfaces (Produces):**
- `gh(*args: str, stdin: str | None = None) -> str`: runs `gh`, and on failure prints the stderr line and exits with code 1. If stderr mentions `INSUFFICIENT_SCOPES` or `project` scope, it prints `Missing project scope. Run: gh auth refresh -h github.com -s project`.
- `graphql(query: str, **variables) -> dict`: `gh api graphql --input -` with JSON `{"query", "variables"}`. Returns `data`, and exits with a one-line message if the response has `errors`.
- `current_repo() -> dict`: `{"owner": str, "name": str, "id": str, "owner_id": str, "owner_type": "User" | "Organization", "owner_db_id": int}`, from `gh repo view --json owner,name` plus one GraphQL query. Outside a git repo, or in one with no GitHub remote, it gives a one-line error.
- `find_board(repo: dict) -> dict`: `{"id", "number", "title", "url", "status_field_id", "status_field_db_id", "options": {name: option_id}}`. Linked projects come from `repository.projectsV2(first: 20)`. Zero linked → error: `No board linked to owner/name. Run board-setup.`. More than one → prefer the one whose title equals the repo name, otherwise error listing `#number title` for each.
- `plan_status_options(existing: list[str], has_items: bool) -> list[str] | None`: returns `None` when every name in `STATUSES` is already present, extra options allowed. Returns `STATUSES` only when `has_items` is false and `existing` is the fresh default (`["Todo", "In Progress", "Done"]`) or empty, since replacing options would wipe item values. Otherwise raises `ValueError` naming the missing options.

GraphQL and REST calls the implementer needs (verified names):
- `createProjectV2(input: {ownerId, title, repositoryId})` creates the board and links it.
- `updateProjectV2Field(input: {fieldId, singleSelectOptions: [{name, color, description}]})`. Colors: Triage `GRAY`, Planned `BLUE`, In Progress `YELLOW`, Done `GREEN`. Descriptions: the "Meaning" column of the spec's table.
- Existing views: `ProjectV2.views(first: 20) { nodes { layout } }`. If none has `BOARD_LAYOUT`, `POST /users/{owner_db_id}/projectsV2/{number}/views` (or `/orgs/{owner}/projectsV2/{number}/views`) with `{"name": "Board", "layout": "board", "vertical_group_by": [status_field_db_id]}`.

- [ ] **Step 1: Write the failing test** `test_plan_status_options_*`:
  - `(["Todo","In Progress","Done"], False)` gives `STATUSES`.
  - `(["Todo","In Progress","Done"], True)` raises `ValueError` naming `Triage`.
  - The four statuses plus `"Icebox"`, with `True`, give `None`.
  - `(["Backlog","Done"], False)` raises `ValueError` naming `Triage`.
- [ ] **Step 2:** Run it and confirm it fails. Implement `plan_status_options`, then run it again and confirm it passes.
- [ ] **Step 3:** Implement `gh`, `graphql`, `current_repo`, `find_board`, and the subcommands:
  - `board find`: prints `#<number> <title> <url>`.
  - `board setup`: find or create the board, then apply `plan_status_options` (only call `updateProjectV2Field` when it returns a list). Then make sure a Board view exists. Then write the AGENTS.md block from `board/agents-section.md` (resolved via `Path(__file__).resolve().parent.parent`) with `splice_section`, and apply `claude_pointer` to `CLAUDE.md`. Both files live at the git toplevel. Print one line per thing it did or found already in place.
- [ ] **Step 4: Ask Bryan** to OK creating the private `briney/board-scratch` repo. Then run `gh repo create briney/board-scratch --private --add-readme`, clone it to the scratchpad, and create `board/agents-section.md` as a one-line placeholder (Task 5 writes the real text).
- [ ] **Step 5: Live check**, all from the scratch clone unless noted:
  - In `/tmp`, `board find` prints a one-line error, exits 1, no traceback.
  - In the scratch clone before setup, `board find` prints `No board linked to briney/board-scratch. Run board-setup.`
  - `board setup` creates the board.
  - Running `board setup` a second time reports everything as already in place.
  - The web UI shows a Board view with four columns in order.
  - `AGENTS.md` has one marker block, and `CLAUDE.md` is `@AGENTS.md`.
- [ ] **Step 6: Commit:** `git commit -am "board: find and idempotent setup"` (add new files explicitly).

---

### Task 4: Card subcommands

**Files:** Modify `bin/board`. Live check against the scratch board.

**Interfaces (Consumes):** `graphql`, `current_repo`, `find_board`, `status_option`, `parse_issue_ref`, `render_list` from Tasks 2–3.

**Interfaces (Produces):**
- `board_items(board: dict, page_size: int = 100) -> list[dict]`: every item, paginated with `items(first: $n, after: $cursor)`, in project order, as `render_list` item dicts plus `"item_id"` and `"issue_id"`. Draft issues and PRs are skipped. Use `fieldValueByName(name: "Status")`, and `blockedBy(first: 10)` on Issue, keeping only blockers whose `state` is `OPEN`. Set the env `BOARD_PAGE_SIZE` to override `page_size`; it exists only so the pagination check below can run.
- `ensure_item(board, issue_id) -> str` via `addProjectV2ItemById` (idempotent, returns the item id).
- `set_status(board, item_id, status: str)` via `updateProjectV2ItemFieldValue` with `{singleSelectOptionId}`.

Subcommands. Every one that takes text reads it from stdin when stdin isn't a TTY and `--body`/`--comment` isn't given, so agents can use heredocs.
- `board add --title T [--body B]`: `createIssue`, then `ensure_item`, then status Triage, then print `#N Title URL`.
- `board add N`: puts an existing issue on the board in Triage, if it isn't on the board already.
- `board move N STATUS [--comment C]`:
  - Moving to Done closes the issue (`closeIssue`, `stateReason: COMPLETED`).
  - Moving a closed issue to any other status reopens it (`reopenIssue`).
  - The comment, if given, is posted before the move.
  - Prints `#N → Status`.
- `board order N (--before M | --after M)`: `updateProjectV2ItemPosition(projectId, itemId, afterId)`. For `--before M`, `afterId` is the item just before M in `board_items` order, or omitted when M is first.
- `board block N --by M`: `addBlockedBy(input: {issueId, blockingIssueId})`.
- `board drop N [--comment C]`: `closeIssue` with `stateReason: NOT_PLANNED`.
- `board comment N [--body B]`: `addComment`.
- `board search TERMS`: `search(type: ISSUE, query: "repo:o/n is:issue TERMS")`, both open and closed. Prints `#N [open|closed|not planned] Title`.
- `board list [--all]`: `render_list(board_items(...), show_done=--all)`.

- [ ] **Step 1:** Implement the subcommands.
- [ ] **Step 2: Live check** on the scratch board, run in this order:
  1. `add` three cards, A, B and C. Each one appears under Triage.
  2. `move` A to `planned` and B to `in-progress`.
  3. `move` C to `planned`, then `order` C `--before` A. `list` shows C above A under Planned. This proves the items connection returns positions in order; if it doesn't, stop and report.
  4. `block` A `--by` B. `list` shows `[blocked by #B]`.
  5. `move` B to `done`. The issue is closed, and A is no longer marked as blocked.
  6. `move` B to `triage`. The issue reopens.
  7. `drop` C. `search` shows C as `not planned`.
  8. Run `BOARD_PAGE_SIZE=2 board list` and confirm it matches the default `board list`.
- [ ] **Step 3: Commit:** `git commit -am "board: add, move, order, block, drop, comment, search, list"`

---

### Task 5: `board activity`, the skills, and the AGENTS.md section

**Files:**
- Modify: `bin/board` (`activity`)
- Create: `board/agents-section.md`, `skills/defer/SKILL.md`, `skills/next/SKILL.md`, `skills/board-setup/SKILL.md`

**`board activity [--since S]`** (Consumes `parse_since`, `board_items`). The window is `--since` if given. Otherwise it's the timestamp in `$(git rev-parse --git-common-dir)/board-last-activity`, falling back to `14d` (the "since the last `next`" choice, kept per clone). After a successful run, it writes the current UTC time to that file. It prints five plain-text sections, each with a header and `(none)` when empty:
1. `Merged PRs`: `#N title (merged DATE)` followed by the full body, indented. Search query: `repo:o/n is:pr is:merged merged:>=DATE`.
2. `Open PRs updated`: same format, for `is:pr is:open updated:>=DATE`.
3. `Commits on <default branch>`: `sha7 subject`, from `defaultBranchRef.target.history(since:)`.
4. `Status mismatches`: board items that are closed but not Done, or open but Done.
5. `Open issues not on the board`: every open issue in the repo (paginated) minus the board item numbers for this repo.

**Skill frontmatter:** `name` plus a `description` that triggers on plain language. For defer: "defer, park, later, add to the board". For next: "what's next, show the board". For board-setup: "set up the board". Bodies stay short; the spec is the source for content:
- **defer:**
  1. Draft the title and a body with **Why / Context / Done when:** from the current conversation. Context means files, commits, PRs, and W&B/HF links.
  2. Run `board search` with two or three key terms. If an open match exists, run `board comment` on it. If it was closed as not planned and Bryan is raising it again, run `board move N triage --comment …`. Otherwise run `board add`.
  3. Reply with one line: `#N Title`.
  4. "If you can hand work to a background subagent (e.g. Claude Code's Agent tool with `run_in_background`), give it the drafted title and body and steps 2–3, then continue the main task; otherwise do it inline."
- **next:** Run `board activity`. Apply the implied moves with `board move` (unboarded open issues go in with `board add N`), and report them in one `Board:` line. Then run `board list` and show it. Then turn Bryan's reply into `move`, `order`, `drop` and `block` calls. "Put X on top" means `order X --before <first Planned>`.
- **board-setup:** Run `board setup`. Show what changed, and leave AGENTS.md/CLAUDE.md uncommitted for Bryan's normal commit flow.
- **`board/agents-section.md`:** rules 1–3 from the spec, almost word for word, plus:
  - the card format;
  - the `board` commands those rules use (`move`, `comment`, `add`);
  - "make moves without asking, report in one line" with the example line from Global Constraints.

  Keep it under about 30 lines.

- [ ] **Step 1:** Implement `activity`. Live check on the scratch repo:
  1. Open a PR whose body has `Closes #A`, then merge it.
  2. Create an issue with `gh issue create` (it isn't on the board).
  3. `board activity --since 1d` lists the merged PR with its body and the unboarded issue. A shows as Done (GitHub's default workflow) or appears under Status mismatches.
  4. `board activity` with no flag uses the stamp written by the previous run.
- [ ] **Step 2:** Write the three skills and `board/agents-section.md`. Re-run `board setup` in the scratch clone. AGENTS.md now has the real text, still in a single block.
- [ ] **Step 3: Commit:** `git add -A && git commit -m "board: activity, skills, AGENTS.md upkeep section"`

---

### Task 6: `install.sh` and per-harness verification

**Files:** Create `install.sh` (bash, `set -euo pipefail`).

Behavior. It resolves `CODEBOX_ROOT` from its own location, which isn't necessarily `~/codebox`; on this laptop it's `~/git/codebox`. Then:
1. Prune dead codebox links. In `~/.claude/commands`, `~/.claude/skills`, `~/.agents/skills`, `~/.config/opencode/skills`, and `~/.local/bin`, it removes symlinks that are dangling (`[ -L x ] && [ ! -e x ]`) and whose `readlink` target contains `codebox`. It leaves every other link alone, for example the omarchy skill links.
2. Install skills. For each `skills/*/`, it runs `ln -sfn` into `~/.claude/skills/<name>` and `~/.agents/skills/<name>`.
3. Install the script: `ln -sfn "$CODEBOX_ROOT/bin/board" ~/.local/bin/board`. If `~/.local/bin` isn't on `PATH`, it prints a warning.
4. It prints one `✓` line per link. Running it again gives the same result.

- [ ] **Step 1:** Write `install.sh`. Make a fake dangling link, `~/.claude/commands/lab-notebook.md`, pointing to `$CODEBOX_ROOT/skills/lab-notebook/SKILL.md`. Run the installer twice. Check that the fake link is gone, the omarchy links are untouched, and `board --help` runs from a fresh shell.
- [ ] **Step 2: Harness check**, in the scratch clone:
  - **Claude Code:** `/defer test idea` files a card.
  - **Codex:** `$defer test idea` files a card.
  - **OpenCode:** check two things.
    - Does `/defer` work? If it doesn't, add `opencode/commands/{defer,next,board-setup}.md`, each one line: `Use the <name> skill. $ARGUMENTS`. Have `install.sh` link them into `~/.config/opencode/commands/`.
    - Does the skill list show `defer` twice (it's read from both `~/.claude/skills` and `~/.agents/skills`)? If it does, and the duplicate causes wrong behavior, stop linking into one of the two directories for OpenCode's sake and record which one in the README. If the duplicate is harmless, record that.

  Write down the results for Task 7's README.
- [ ] **Step 3: Commit:** `git add -A && git commit -m "install.sh: link skills and board for Claude Code, Codex, OpenCode"`

---

### Task 7: README and e2e script

**Files:** Create `README.md` and `tests/e2e.sh`.

- `README.md`:
  - what codebox is (Bryan's harness-neutral agent toolkit; the board is its first feature);
  - requirements (`gh` with `project` scope, `python3 ≥ 3.8`);
  - install (`git clone https://github.com/briney/codebox.git ~/codebox && ~/codebox/install.sh`);
  - what's in it (the three skills, the `board` subcommands, and how each harness invokes them, from Task 6's findings);
  - how to run the tests.
- `tests/e2e.sh OWNER/REPO`: refuses to run unless the repo name contains `scratch`. It clones the repo to a temp dir and runs the Task 4 check sequence, using `grep` assertions on `board list`. Exit 0 means pass.

- [ ] **Step 1:** Write both. Run `tests/e2e.sh briney/board-scratch` and `python3 -m unittest tests/test_board.py`. Both should pass.
- [ ] **Step 2: Commit:** `git add -A && git commit -m "docs: README; tests: e2e script"`
- [ ] **Step 3:** Run a whole-branch review (superpowers:requesting-code-review) before Task 8.

---

### Task 8: Replace `main`

- [ ] **Step 1:** Show Bryan `git log --oneline rebuild` and the file tree. **Ask for explicit confirmation to force-push.**
- [ ] **Step 2:** After he says yes, run `git push --force origin rebuild:main`. Check that `gh repo view briney/codebox --json visibility` still says `PUBLIC` and the README renders.
- [ ] **Step 3:** Make the local `main` match: `git switch main && git reset --hard origin/main && git branch -D rebuild`. Then remove the leftover `notebook/` directory and the `.git/modules/notebook` entry. Re-run `install.sh`.

---

### Task 9: OPLM rollout

Work in `~/git/oplm` (the `briney/oplm` repo).

- [ ] **Step 1:** Run the `board-setup` skill. Commit AGENTS.md/CLAUDE.md on a branch, following oplm's usual PR flow.
- [ ] **Step 2:** Read every file in `~/.claude/projects/-home-bryanbriney-git-oplm/memory/` and list the deferred items. Known items:
  - the AdamW no-weight-decay growth investigation;
  - M2c cluster runs, paused pending the LM protocol fix. That expands to tagging `fold-m2c-runs` plus cluster Tasks 8–9.

  Show Bryan the list before filing anything.
- [ ] **Step 3:** File each item with the `defer` card format through `board add`. Set the real status with `board move`, and run `board block` where a blocker card exists (e.g. M2c runs blocked by the LM protocol fix card).
- [ ] **Step 4:** Trim those memory entries to a one-line pointer to their issue, and update `MEMORY.md` to match.
- [ ] **Step 5:** Run `next` in oplm so Bryan can review the Triage pile.
