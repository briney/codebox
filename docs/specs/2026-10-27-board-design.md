# Deferred-work board — design

Date: 2026-10-27. Final home: `briney/codebox`, `docs/specs/2026-10-27-board-design.md`
(committed as part of the codebox rebuild).

## Intent

Ideas for future work come up mid-session, often sideways from the task at hand.
Today they get lost or end up scattered in agent memory files, which only the agent
reads. The board gives every repo a per-repo GitHub Projects kanban that:

- **catches deferred ideas cheaply**: one line from Bryan, the agent files a
  well-formed issue, and the session keeps going without losing momentum;
- **answers "what's next?"**: Bryan opens it mostly right after finishing
  something, scans it, and reprioritizes it in his head (and on the board);
- **stays current without Bryan maintaining it**: agents move cards as work
  happens, and `next` reconciles the board before showing it.

Bryan trusts the board if (a) every important deferred item is on it and (b) the
statuses are current. A board that drifts is a failure even if every part of it
technically works.

It has to work in Claude Code, Codex, and OpenCode, and become a standard part
of every repo Bryan works in.

## Goals

- `defer <idea>`: file a rich issue onto the current repo's board in Triage.
- `next`: reconcile statuses, then present the board for reprioritizing, and
  apply Bryan's plain-language decisions.
- `board-setup`: give a repo its board and its upkeep rules, once.
- Upkeep rules in each repo's AGENTS.md so any harness keeps the board current.
- Works identically in Claude Code, Codex, OpenCode.

## Non-goals

- Cross-repo boards or a cross-repo "what's next" view (Bryan chooses within one
  repo).
- Priority, size, or estimate fields. Order within Planned *is* the priority.
- Claude-only machinery: no hooks, no session-end triggers (sessions rarely end
  cleanly, and a session-end hook can't make the agent think back over the session).
- Keeping anything from the old codebox (lab notebook, `python-init`, `setup/`).

## Anti-goals

- Confirmation prompts for status moves. Agents make the moves and say so in one
  line. A wrong status is cheap to fix; friction makes upkeep slip.
- Thin, context-free cards like "fix the thing". Each card must stand on its own
  weeks later.
- Duplicate cards for the same idea.

## Board model (decided)

One GitHub Projects (v2) board per repo, owned by the repo's owner (user or org),
linked to the repo. Status columns:

| Status | Meaning |
|---|---|
| Triage | Captured by `defer`, not yet looked at. The inbox. |
| Planned | Bryan decided it's worth doing. Top-to-bottom order = priority. |
| In Progress | Work has started (fully or partly). |
| Done | Finished. |

- **Dropped ideas** are closed as "not planned" (kept searchable, so they aren't
  filed again), not deleted.
- **Blocked items** use GitHub's native issue dependency ("blocked by #N",
  GraphQL `addBlockedBy`), not a column. `next` shows them marked as blocked
  until the blocker closes.
- Board view: a Board layout grouped by Status (plus GitHub's default table).

## Card contents (decided)

Written by the agent at capture time, while the context is fresh:

- **Title**: short and specific.
- **Why**: what prompted it and what problem it solves.
- **Context**: relevant files, commits, PRs, runs (W&B/HF links), and constraints
  already known.
- **Done when:** a concrete, checkable line (the style the brineylab
  `os-upgrades` issues use).

Before filing, `defer` searches open *and* closed issues for an existing match. If
it finds one, it comments on that issue (or reopens it into Triage if it was
closed as not planned and Bryan is raising it again) instead of filing a new one.

## How statuses stay current (decided)

There is no single "end of session" trigger. Upkeep happens at moments that
reliably occur:

1. **Work starts on a card**: the agent moves it to In Progress immediately.
2. **A PR is opened**: items it completes get `Closes #N` in the PR body (GitHub's
   default "item closed" and "PR merged" workflows move them to Done on merge).
   Items it only partly advances get `Refs #N`, are moved to In Progress, and get
   a short issue comment: what changed, what's left.
3. **Non-PR work** (cluster runs, investigations, dataset publishes): when a
   card's "Done when:" is met, the agent closes the issue with a comment linking
   the evidence (W&B run, HF tag, commit).
4. **`next` reconciles first**: it checks recent activity against open cards and
   applies the likely moves (details below). The board gets corrected at the
   moment Bryan relies on it most.

Agents make every move without asking and report it in one line (e.g. "Board: #12
→ Done (PR #49), #15 → In Progress").

Rules 1–3 live in each repo's AGENTS.md (below). Rule 4 is the `next` skill.

## Components (decided)

### 1. `board` script: the only thing that talks to GitHub

A single CLI on PATH, built on `gh` (GraphQL via `gh api graphql`). All Projects
fiddliness lives here, so every harness gets identical behavior and filing is one
fast command even in harnesses without background agents. Subcommands (names are
the builder's to refine):

- `board find`: locate the current repo's board (projects linked to the repo);
  clear error pointing at `board-setup` if there is none.
- `board setup`: create the board (or adopt an already linked one), set the
  Status options, create the Board view, and link it to the repo. Idempotent.
- `board add`: create an issue from title + body and put it on the board in
  Triage, or add an existing issue.
- `board move <issue> <status>`
- `board order <issue> --before/--after <issue>` (item position; used for
  Planned priority)
- `board block <issue> --by <issue>`
- `board drop <issue>`: close as not planned.
- `board list`: cards by status in board order, with blocked markers, as text
  readable by both the agent and Bryan.
- `board activity --since <duration>`: raw material for reconciling: merged PRs
  (with bodies), closed issues, recent commits, open repo issues that are not on
  the board. The script gathers the facts; the agent decides what they mean.

Requires the `gh` token's `project` scope; when it's missing, the script prints
the fix (`gh auth refresh -h github.com -s project`).

### 2. Skills (Agent Skills `SKILL.md` format)

Short prose wrappers around `board`. One `SKILL.md` per skill, identical across
harnesses:

- **`defer`**: from a one-line request, write the card (format above), check for
  duplicates, run `board add`, reply with one line (issue number + title). In
  Claude Code it should dispatch the filing to a background agent so the main
  session doesn't wait; elsewhere it runs inline (it's one command).
- **`next`**: run `board activity` (default window: since the last `next`, or 14
  days), apply the moves it implies (any open repo issues not on the board go
  into Triage), report the moves in one line each, then show Planned (in order,
  blocked items marked), In Progress, and Triage. Apply Bryan's plain-language
  response ("promote 51 and 53, 53 on top, drop 48, 50 depends on 47") through
  the script.
- **`board-setup`**: run `board setup`, then add the upkeep section to the repo's
  AGENTS.md (creating a CLAUDE.md pointer to AGENTS.md if the repo has none).
  The section sits between marker comments so re-running replaces it in place.

### 3. AGENTS.md upkeep section

A short block, owned by codebox (single source text in the codebox repo), stating
rules 1–3, how to call `board`, the card format, and "make moves without asking,
report in one line."

### 4. Install

`install.sh` in codebox:

- symlinks each skill into `~/.claude/skills/` (Claude Code) and
  `~/.agents/skills/` (Codex and OpenCode both read this);
- puts `board` on PATH (e.g. `~/.local/bin`);
- removes dangling symlinks left in those directories by the old codebox install;
- is safe to re-run.

## The codebox rebuild (decided)

- `briney/codebox` is wiped and rebuilt from scratch as Bryan's harness-neutral
  agent toolkit. Nothing is carried over: lab notebook, `scripts/`,
  `skills/lab-notebook`, `skills/python-init`, and `setup/` all go.
- New history: `main` replaced with a fresh history (orphan commit). **Confirm
  with Bryan immediately before the force-push.**
- Leave `briney/codebox-notebook` untouched. Keep the repo's visibility
  (public) unchanged.
- The README says what codebox is now, how to install it, and what's in it. The
  board is its first feature; more may follow.

## OPLM rollout (decided)

1. Run `board-setup` in `briney/oplm`.
2. Move the deferred items now living in Claude's oplm memory files (under
   `~/.claude/projects/-home-bryanbriney-git-oplm/memory/`) onto the board as
   cards. Examples: AdamW no-weight-decay growth investigation; M2c cluster runs
   paused pending the LM protocol fix, then tagging `fold-m2c-runs` + cluster
   Tasks 8–9. Status follows reality (paused/blocked items get a blocked-by link
   where a blocker card exists). Bryan reviews the resulting Triage via `next`.
3. Trim those memory entries to point at the issues, so the board is the single
   home for deferred work.

## Constraints

- The only external dependency is `gh` (plus whatever runtime the script is
  written in; it must exist on Bryan's laptop, loki, and cluster nodes).
- GitHub's built-in project workflows can't be enabled via the API. That's fine:
  the two that matter ("item closed" → Done, "PR merged" → Done) are on by default
  for new projects, and everything else is done explicitly by the script.
  Auto-add is unnecessary because `defer` adds cards and `next` sweeps up
  unboarded issues.
- Board owner = repo owner (user `briney` for oplm; org `brineylab` for lab
  repos).

## Left to the builder

- Script language (Python stdlib + `gh` subprocess is a natural fit; bash + `jq`
  is fine too) and exact subcommand names and flags.
- How `next` remembers "since the last `next`" (or just use a fixed window).
- Per-harness invocation details: confirm that Claude Code exposes skills as
  `/defer`, Codex as `$defer`, and how OpenCode invokes them. Add a thin
  OpenCode command file only if OpenCode can't invoke a skill directly. Check
  whether OpenCode loading the same skill from both `~/.claude/skills` and
  `~/.agents/skills` causes duplicates, and adjust the install if it does.
- Testing approach: an end-to-end run against a scratch repo and board, plus the
  smallest check that guards the script's parsing logic.
- Adopting an existing board (e.g. brineylab's Flyloft board, which already uses
  these four columns) without clobbering its items or options.
