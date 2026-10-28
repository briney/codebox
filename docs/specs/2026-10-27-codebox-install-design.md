# codebox install, update, and plugins: design

Date: 2026-10-27. Board card: briney/codebox#1.

## Intent

Installing codebox today means cloning the repo to a path of your choosing and running `./install.sh`. That script links every skill into every harness's skill folder, whether or not the harness is installed. Bryan wants the onboarding Entire uses:

1. One `curl … | bash` line installs a `codebox` command.
2. `codebox install` puts codebox's tooling into every supported coding harness on the machine. `codebox install --harness <name>` targets just one.
3. `codebox update` brings in new plugins and new versions of existing ones, and prints what changed.

It is only for Bryan at first. Opening it up to others (lab members) is expected later, so nothing in it should depend on being Bryan.

codebox also becomes a collection of **plugins**. The board (the `board` command plus its skills) is the first one, and more will follow.

## Goals

- A bootstrap one-liner: `curl -fsSL https://raw.githubusercontent.com/briney/codebox/main/bootstrap.sh | bash`.
- `codebox install [--harness claude|codex|opencode]`: wire every plugin into the detected harnesses, or into the named one.
- `codebox update`: move to the newest release, re-wire, and print per-plugin and per-skill version changes, each with a one-line note.
- `codebox uninstall`: remove everything codebox put in place.
- Every codebox skill is named with a shared `codebox-` prefix and works mainly through natural language.
- Existing boards keep working across releases, with a migration path when a release changes what they depend on.

## Non-goals

- Picking which plugins to install. Every plugin installs, for now.
- Harnesses other than Claude Code, Codex, and OpenCode (no Antigravity, Cursor, or Copilot yet).
- Registering codebox in each harness's own plugin marketplace (see "Install mechanism" below).
- Windows. Linux and macOS only, matching where Bryan works (his machines, loki, cluster nodes).
- A release-cutting tool. Releases are cut by hand: bump versions, write notes, tag.

## Anti-goals

- **Breaking other plugins.** Bryan runs superpowers and ponytail and is looking at Google's egm. codebox must never overwrite, shadow, or remove anything it didn't create. It must never edit shared config: `~/.claude/settings.json`, the global CLAUDE.md or AGENTS.md, Codex or OpenCode config files.
- **Stranding existing boards.** A release that changes anything boards depend on (status columns, the AGENTS.md upkeep section, skill names that section mentions, card format) must ship a way to bring existing boards forward. Boards live on GitHub and in each repo's AGENTS.md, so the migration runs per repo.
- **A version number that lies.** If a skill or plugin changed, its version changed and the change has a note. Nothing ships without the bump.

## Decided

### Releases and versions

- codebox ships as tagged releases of the whole repo: `vX.Y.Z` git tags on `briney/codebox`. Commits on `main` between tags reach no one.
- Each plugin has its own semantic version, and so does each skill inside it.
- Every version bump, of the plugin or of a skill, has a one-line changelog note. The notes live with the plugin.
- Any change worth shipping, including a one-skill edit, gets a version bump and a new release tag.

This mirrors how superpowers and ponytail ship through Claude Code's plugin system: a version number in metadata gates updates, and there are no release branches.

### `codebox update` output

`update` compares versions between the installed release and the new one and prints what moved, with each change's note. For example:

```
codebox v0.3.0 → v0.4.0
  board 1.2.0 → 1.3.0   next: shows blocked cards at the bottom of Planned
    codebox-next 1.0.0 → 1.1.0  show blocked cards last
  + newplugin 0.1.0     first release
```

When several versions were skipped, the notes for every version in between are shown.

### Naming and invocation

- The skills are renamed `codebox-defer`, `codebox-next`, and `codebox-board-setup`. Future skills get the same prefix.
- Natural language is the primary way in ("park this for later", "what's next?", "set up the board here"). Slash forms (`/codebox-next`, `$codebox-next`) are a fallback.
- Skill descriptions are written for reliable triggering in all three harnesses. A check confirms that a few plain phrasings fire the right skill in each harness, run headlessly the way the earlier `/defer` harness test was. It costs model calls, so it runs on demand, not in the unit tests.

### Harnesses and where things go

| Harness | Detected when (planner's call) | Skills linked into |
|---|---|---|
| Claude Code | `claude` on PATH or `~/.claude/` exists | `~/.claude/skills/` |
| Codex | `codex` on PATH or `~/.codex/` exists | `~/.agents/skills/` |
| OpenCode | `opencode` on PATH or `~/.config/opencode/` exists | `~/.agents/skills/` (OpenCode also reads `~/.claude/skills/` and dedupes by name; checked in the board rollout) |

Plugin commands such as `board` and `codebox` itself are linked into `~/.local/bin/`. If that folder isn't on PATH, the tool prints the line to add, as Entire's installer does.

### Install mechanism (planner's call)

codebox installs plain links into the shared skill folders. It does not register as a marketplace in each harness's plugin system. Three reasons:

- the `codebox-` prefix already prevents name clashes;
- OpenCode has no plugin marketplace;
- one install path covers all three harnesses.

(Checked: superpowers, ponytail, and egm skill names don't overlap codebox's. Ponytail and egm also use name prefixes.)

### Safety rules for install, update, and uninstall

- codebox keeps a record of every link it created, with its harness and target.
- Before making any change, `install` and `update` check every destination. If a path exists and isn't a link codebox recorded, nothing changes. The tool names the conflicting paths and exits non-zero. This is all-or-nothing.
- `update` removes links for skills a new release dropped or renamed. `uninstall` removes only recorded links, then the codebox home.
- None of these touch repos, boards, or GitHub.

### Existing installs on Bryan's machines

The first `codebox install` replaces the old `install.sh` setup. On this machine that is unprefixed `defer`, `next`, and `board-setup` links in `~/.claude/skills` and `~/.agents/skills`, plus `~/.local/bin/board`, all pointing into `~/git/codebox`. Other machines may still have links from the original lab-notebook codebox.

- It removes links that point into a codebox checkout under names codebox no longer ships, and adopts or replaces its own current names.
- It still never touches a link that points anywhere else.
- `install.sh` is removed from the repo.

### Board migration (the first real case)

Repos that already have a board (oplm and codebox) carry an AGENTS.md upkeep section that names "the `defer` skill". After the rename, that section is stale.

- Re-running `board setup` already rewrites the section in place between its markers.
- What's needed is for stale sections to be noticed. When `board` runs in a repo whose AGENTS.md section differs from the installed plugin's current text, it prints a one-line hint to run `board setup` (or the `codebox-board-setup` skill).
- The release note for the rename says existing boards migrate this way.
- Future migrations that need more than rewriting the section, such as changing a board's status options, ship as an explicit, idempotent step inside `board setup`. It follows the existing rule of never rewriting what it can't change safely.

### Codebox home

- codebox lives in `~/.codebox`, a git clone of `briney/codebox` checked out at a release tag (planner's call).
- The `CODEBOX_HOME` environment variable overrides that location. This is how Bryan uses an unreleased working tree: `CODEBOX_HOME=~/git/codebox codebox install` links from his development checkout. It needs no special dev mode.
- `update` moves the home's checkout to the newest tag, which also updates `codebox` itself.

### Bootstrap

`bootstrap.sh` lives at the repo root and is served from `main` through raw.githubusercontent.com.

- It checks for `git` and `python3`.
- It clones (or, if already present, fetches) into `~/.codebox` and checks out the newest release tag.
- It links `codebox` into `~/.local/bin` and prints the PATH hint if needed.
- It tells the user to run `codebox install`. It does not install into harnesses itself.
- Running it again is safe and repairs a broken install.

## Constraints

- Runtime dependencies: `git`, `python3` ≥ 3.8 (stdlib only), and `gh` with the `project` scope for the board. Nothing else.
- Nothing may assume Bryan's username or machine paths. The only Bryan-specific value is the default repository URL in `bootstrap.sh`, which a fork edits.
- The `codebox` command follows `board`'s conventions: Python stdlib, one-line errors on stderr, exit code 1, no tracebacks.

## Detailed rules (planner's calls, settled after a builder review)

- **Stale AGENTS.md section.** A section is stale when its text between the markers isn't byte-identical to the installed plugin's current text. The marker format doesn't change. The hint goes to stderr and is printed by `board activity` (what `codebox-next` runs) and by `board setup`, not by every subcommand, so it shows up where Bryan looks and doesn't nag on every card move.
- **Recognizing an old codebox link.** A link counts as old codebox when either of these holds:
  - its target resolves inside a git work tree whose `origin` URL contains `codebox`;
  - it is dangling and its target path contains `codebox`, the old `install.sh` rule, which covers the lab-notebook era.

  The known lab-notebook-era links are `~/.claude/commands/{lab-notebook,python-init}.md` and `~/.config/opencode/skills/{lab-notebook,python-init}`. Old-codebox links for names codebox no longer ships are removed. Links for current names are replaced. Everything else counts as a foreign path, so the all-or-nothing conflict check applies to it.
- **Install record.** A fixed per-user file, `~/.local/state/codebox/installed.json`, records the home path, the installed release, the harnesses, and each link with the harnesses that use it. A link shared by Codex and OpenCode in `~/.agents/skills/` is recorded once, and removing it requires that no recorded harness still needs it. Uninstall is whole-install only; `--harness` applies to `install`.
- **`update` and `CODEBOX_HOME`.** `update` refuses, with a one-line reason, when the home isn't a clean checkout at a release tag, for example a dev checkout. Against a dev home you re-run `codebox install` instead. Before moving the checkout, `update` runs the conflict check against the new tag's tree (via `git ls-tree` or a temporary worktree), so a failed check leaves everything as it was. The "from" release comes from the install record.
- **Harness detection.** Harnesses that aren't detected are skipped, with a one-line note listing which were found. If none are found, `install` exits with an error. `--harness X` installs into X even if X isn't detected.
- **First release and version baseline.**
  - The first release tag is `v0.1.0`. It is the release that introduces plugins and the `codebox-` rename.
  - The board plugin and each skill start at `1.0.0` there.
  - The version guard compares against the newest release tag, matching plugins and skills by name rather than path. It is skipped when no release tag exists yet.
  - `bootstrap.sh` fails with a clear message if the repo has no release tags.
- **Stable entry point.** `codebox` lives at `bin/codebox` at the repo root, permanently. Moving it would break every bootstrapped install, so treat it as fixed.

## Left to the builder

- The plugin folder layout. For example, `plugins/<name>/` holding `skills/`, `bin/`, the changelog, and plugin files such as the AGENTS section text. Also how `bin/board`, `tests/`, and `board/agents-section.md` move into it.
- Where plugin and skill versions are recorded. A plugin manifest, and `metadata.version` in SKILL.md frontmatter (the Agent Skills format allows a `metadata` field), are natural fits. Also the changelog file format.
- The format and location of the install record. Inside the codebox home is fine, as long as `uninstall` doesn't delete it before it has been read.
- The guard that keeps version numbers honest: a test that fails when a plugin's or skill's files differ from the last release tag without a version bump and a changelog note.
- Whether the codebox command is one script or a thin CLI over plugin modules.
- The exact phrasings in the natural-language trigger check, and how its results are reported.
- The README rewrite: bootstrap, install, update, uninstall, `CODEBOX_HOME`, plugin list.
