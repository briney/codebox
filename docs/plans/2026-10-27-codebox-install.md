# codebox install, update, and plugins: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn codebox into versioned plugins with a `bootstrap.sh` one-liner and a `codebox` command (`install [--harness H]`, `update`, `uninstall`) that wires them into Claude Code, Codex and OpenCode with plain symlinks.

**Architecture:** The board moves to `plugins/board/`, with its skills renamed `codebox-*` and every version and change note in one `plugin.json`. `bin/codebox` is one Python stdlib script: pure functions that compute the links an install needs and classify what already sits at each destination, plus thin commands that apply the result all-or-nothing and keep an install record. `update` reads the new release's tree with `git archive` before it moves the checkout.

**Tech Stack:** Python 3.8+ stdlib, git, bash (bootstrap and the trigger check only), `unittest`.

**Spec:** `docs/specs/2026-10-27-codebox-install-design.md`. Read it before any task. Board card: briney/codebox#1.

## Global Constraints

- Runtime dependencies: `git`, `python3` ≥ 3.8 (stdlib only), and `gh` with the `project` scope for the board. Use `from __future__ import annotations`; no `match`, no runtime `X | Y`.
- `codebox` follows `board`'s conventions: one-line errors on stderr, exit code 1, no tracebacks.
- Never overwrite, shadow, or remove a path codebox didn't create. Never edit `~/.claude/settings.json`, any global CLAUDE.md or AGENTS.md, or Codex or OpenCode config.
- Plain links only. No marketplace registration (Bryan confirmed this after reviewing the design).
- Skill names: `codebox-defer`, `codebox-next`, `codebox-board-setup`.
- Harness → skills folder: `claude` → `~/.claude/skills/`; `codex` and `opencode` → `~/.agents/skills/`. Commands → `~/.local/bin/`.
- Home: `$CODEBOX_HOME`, else `~/.codebox`. Install record: `~/.local/state/codebox/installed.json`.
- `bin/codebox` stays at that path permanently.
- Versions are `X.Y.Z`. Release tags are `vX.Y.Z`. The first release is `v0.1.0`; the board plugin and its skills start at `1.0.0`.
- Nothing may assume Bryan's username or machine paths. The only Bryan-specific value is the default repo URL in `bootstrap.sh`.
- Tests: `python3 -m unittest discover -s tests` (run from the repo root; the single-file form picks up a stray site-packages `tests` package in some environments).
- Tests never touch the real home directory. Every `codebox` function that touches the filesystem takes `user_home: Path` explicitly.

## Rulings (planner's calls made while planning)

- **Version record and changelog:** one JSON file, `plugins/<name>/plugin.json`, holds the plugin version, the skill versions, and every version's one-line note. It is one file to bump, and stdlib reads it.
- **Tests stay in top-level `tests/`.** Only the paths inside them change.
- **`board setup` and the stale-section hint:** `setup` already rewrites the section. When it does so it prints `AGENTS.md updated (board section was out of date)`. Only `board activity` prints the stderr hint.
- **`bootstrap.sh` with an existing home:** it fetches tags and re-links `codebox`, but doesn't move the checkout. It tells the user to run `codebox update`. Moving the checkout there would skip `update`'s conflict check and leave the install record wrong.
- **`uninstall` deletes the home only when it is `~/.codebox`.** It never deletes a `CODEBOX_HOME` checkout such as `~/git/codebox`; it prints that it was left in place.
- **`install` links `codebox` itself** (`~/.local/bin/codebox` → `<home>/bin/codebox`), so the record covers it and `uninstall` removes it.
- **Harnesses accumulate.** `install --harness X` wires X in addition to the harnesses already recorded.
- **Plugin text says "the user", not "Bryan".** This covers the skills, the AGENTS section and the Status option descriptions.

## Review Focus

1. **A fresh machine where `~/.local/bin`, `~/.agents/skills` or `~/.local/state` don't exist.** Expected: install creates them. Test: Task 4 `test_install_fresh`.
2. **Running `install` twice.** Expected: the second run changes nothing and prints no `+`/`-` lines. Test: Task 4 `test_install_idempotent`.
3. **A user's own file or directory at a destination** (their own `board` binary, their own `codebox-next` skill folder). Expected: nothing changes anywhere, including links that had no conflict, and the paths are named. Test: Task 4 `test_install_conflict_changes_nothing`, Task 5 `test_update_conflict_leaves_checkout`.
4. **`uninstall` with `CODEBOX_HOME` pointing at a development checkout.** Expected: the checkout survives. Test: Task 4 `test_uninstall_keeps_dev_home`.
5. **An install interrupted midway, or a lost install record.** Expected: re-running `install` adopts the links already pointing into a codebox checkout instead of reporting them as conflicts. Test: Task 4 `test_install_migrates_old_links` (a missing record is the same case).

---

### Task 1: Move the board into `plugins/board/` and rename its skills

**Files:**
- Move: `bin/board` → `plugins/board/bin/board`; `board/agents-section.md` → `plugins/board/agents-section.md`; `skills/defer` → `plugins/board/skills/codebox-defer`; `skills/next` → `plugins/board/skills/codebox-next`; `skills/board-setup` → `plugins/board/skills/codebox-board-setup`
- Create: `plugins/board/plugin.json`
- Delete: `install.sh`
- Modify: `tests/test_board.py:7` (loader path), `tests/e2e.sh` (`BOARD=` path)

**Interfaces:**
- Produces: the plugin layout every later task reads:
  - `plugins/<plugin>/plugin.json`
  - `plugins/<plugin>/skills/<skill>/SKILL.md`
  - `plugins/<plugin>/bin/<command>`
- `board` still finds its section via `Path(__file__).resolve().parent.parent / "agents-section.md"` (one path component shorter than today).

- [ ] **Step 1: Move the files with `git mv` and delete `install.sh`**

- [ ] **Step 2: Update paths and text**
  - `tests/test_board.py` loads `plugins/board/bin/board`, and `tests/e2e.sh` runs it.
  - `cmd_setup` reads `parent.parent / "agents-section.md"`.
  - Rename each SKILL.md's `name:` and `# heading` to its new folder name.
  - Update cross-references: `defer` says "tell the user to run codebox-board-setup". In `agents-section.md`, "the `defer` skill" becomes "the `codebox-defer` skill".
  - Replace "Bryan"/"Bryan's"/"his" with "the user"/"the user's"/"their" in the three SKILL.md files and in `STATUS_DESCRIPTIONS["Planned"]` (it becomes "Decided it's worth doing. Top-to-bottom order = priority.").

- [ ] **Step 3: Write `plugins/board/plugin.json`**

```json
{
  "name": "board",
  "version": "1.0.0",
  "changes": {
    "1.0.0": "first versioned release; skills renamed codebox-*; in repos that already have a board, run `board setup` to refresh the AGENTS.md section"
  },
  "skills": {
    "codebox-defer": {"version": "1.0.0", "changes": {"1.0.0": "renamed from defer"}},
    "codebox-next": {"version": "1.0.0", "changes": {"1.0.0": "renamed from next"}},
    "codebox-board-setup": {"version": "1.0.0", "changes": {"1.0.0": "renamed from board-setup"}}
  }
}
```

- [ ] **Step 4: Verify**

Run: `python3 -m unittest discover -s tests && grep -rn 'Bryan\|install\.sh\|`defer`\|skills/defer' plugins tests`
Expected: 26 tests OK; grep prints nothing.

- [ ] **Step 5: Commit** `board: move into plugins/board, rename skills codebox-*, add plugin.json`

---

### Task 2: Stale AGENTS.md section hint in `board`

**Files:**
- Modify: `plugins/board/bin/board` (`cmd_setup`, `cmd_activity`, new helpers)
- Test: `tests/test_board.py`

**Interfaces:**
- Produces: `section_text() -> str` (the installed `agents-section.md`, trailing newlines stripped; `cmd_setup` uses it too), and `stale_section(agents: str, section: str) -> bool`.
- Produces: `STALE_HINT = "AGENTS.md board section is out of date; run \`board setup\` (or the codebox-board-setup skill) to update it"`.

- [ ] **Step 1: Write the failing tests**

```python
def test_stale_section(self):
    cur = board.splice_section("", "new text")
    self.assertFalse(board.stale_section(cur, "new text"))
    self.assertTrue(board.stale_section(board.splice_section("", "old text"), "new text"))
    self.assertFalse(board.stale_section("# no markers\n", "new text"))  # no section: nothing to hint
    self.assertFalse(board.stale_section(S + "\nx\n", "new text"))      # orphan start: setup reports it
```

- [ ] **Step 2: Run, expect FAIL** (`AttributeError: ... 'stale_section'`)

- [ ] **Step 3: Implement**
  - `stale_section`: true only when both markers are present and the text between them, with the newlines `splice_section` adds stripped, differs from `section`.
  - `cmd_activity`: after printing, read `git_toplevel() / "AGENTS.md"` if it exists, and when it is stale print `STALE_HINT` to stderr.
  - `cmd_setup`: when the splice changes an existing section, print `AGENTS.md updated (board section was out of date)` instead of `AGENTS.md updated`.

- [ ] **Step 4: Run the tests, expect all PASS**

- [ ] **Step 5: Commit** `board: hint when a repo's AGENTS.md board section is stale`

---

### Task 3: `bin/codebox` core: plugins, harnesses, links, classification, planning

**Files:**
- Create: `bin/codebox` (executable, `#!/usr/bin/env python3`)
- Create: `tests/helpers.py` (shared fixtures; not a `test_` file)
- Test: `tests/test_codebox.py`

**Interfaces (all in `bin/codebox`; tests load it the way `test_board.py` loads `board`):**
- `HARNESSES = ("claude", "codex", "opencode")`
- `OLD_DIRS = (".claude/skills", ".agents/skills", ".local/bin", ".claude/commands", ".config/opencode/skills")`: the folders scanned for old codebox links, relative to `user_home`.
- `parse_version(v: str) -> tuple`: `"1.10.0"` → `(1, 10, 0)`. Raises `ValueError` on anything that isn't `X.Y.Z`.
- `load_plugins(root: Path) -> list`: sorted by name. Each entry is:

  ```
  {"name", "version", "changes": {ver: note}, "dir": "plugins/<name>",
   "skills": {skill: {"version", "changes", "dir": "plugins/<name>/skills/<skill>"}},
   "commands": {cmd: "plugins/<name>/bin/<cmd>"}}
  ```

  All paths are relative to `root`. If `root/plugins` is missing, it returns `[]`. It raises `ValueError` naming the plugin or skill when:
  - the manifest's `name` differs from the folder name;
  - a skill folder isn't in the manifest, or a manifest skill has no folder;
  - a SKILL.md frontmatter `name:` differs from its folder name;
  - a `version` has no `changes` entry;
  - any version is malformed.
- `detect_harnesses(user_home: Path, which=shutil.which) -> list`: in `HARNESSES` order. A harness counts when its command is on PATH or its folder exists: `.claude`, `.codex`, `.config/opencode`.
- `desired_links(plugins: list, root: Path, harnesses: list, user_home: Path) -> dict`: maps a destination path string to `{"target": str, "harnesses": [..]}`.
  - Each skill → `~/.claude/skills/<skill>` with `["claude"]`, when claude is chosen.
  - Each skill → `~/.agents/skills/<skill>` with the chosen subset of `["codex", "opencode"]`, when either is chosen.
  - Each command, plus `codebox` → `root/bin/codebox`, → `~/.local/bin/<cmd>` with `[]`.
  - Targets are absolute paths under `root`.
- `is_codebox_tree(path: Path) -> bool`: true when `git -C <path or its parent> remote get-url origin` succeeds and the URL contains `codebox`.
- `classify(dest: Path, recorded: set) -> str`, one of `"absent" | "ours" | "old" | "foreign"`:
  - `absent`: nothing there, and not a dangling link.
  - `ours`: a symlink whose path string is in `recorded`.
  - `old`: a symlink whose resolved target is in a codebox tree, or a dangling link whose `os.readlink` text contains `codebox`.
  - `foreign`: anything else, including real files and directories.
- `plan(desired: dict, record, user_home: Path) -> tuple`, returning `(creates, removes, conflicts)`:
  - `creates`: a dict of destination to target, for destinations that are absent, or ours/old with a different target.
  - `removes`: a sorted list. It holds recorded links not in `desired` that are still symlinks, and links in `OLD_DIRS` that classify as `old` and aren't in `desired`.
  - `conflicts`: a sorted list of desired destinations that classify `foreign`.
  - `record` is the parsed install record or `None`.
- `tests/helpers.py`:
  - `REPO`: the repo root.
  - `codebox`: the loaded module.
  - `fake_codebox_tree(dest: Path, origin="https://github.com/briney/codebox.git") -> Path`: copies `REPO/plugins` and `REPO/bin` into `dest`, runs `git init`, commits, sets `origin`, and returns `dest`.

- [ ] **Step 1: Write the failing tests**

```python
def test_load_plugins_real_repo(self):
    (p,) = codebox.load_plugins(REPO)
    self.assertEqual((p["name"], p["version"]), ("board", "1.0.0"))
    self.assertEqual(set(p["skills"]), {"codebox-defer", "codebox-next", "codebox-board-setup"})
    self.assertEqual(p["commands"], {"board": "plugins/board/bin/board"})

def test_load_plugins_rejects(self):
    # each case: fake tree, one mutation, then assertRaisesRegex(ValueError, <name>)
    #   extra folder plugins/board/skills/stray            -> "stray"
    #   manifest board version "1.1.0" with no 1.1.0 note  -> "board"
    #   codebox-next/SKILL.md name: next                   -> "codebox-next"

def test_detect_harnesses(self):
    (h / ".codex").mkdir()
    which = lambda n: "/usr/bin/claude" if n == "claude" else None
    self.assertEqual(codebox.detect_harnesses(h, which), ["claude", "codex"])
    self.assertEqual(codebox.detect_harnesses(h / "empty", lambda n: None), [])

def test_desired_links(self):
    d = codebox.desired_links(codebox.load_plugins(REPO), REPO, ["claude", "opencode"], h)
    self.assertEqual(d[str(h / ".claude/skills/codebox-next")],
                     {"target": str(REPO / "plugins/board/skills/codebox-next"), "harnesses": ["claude"]})
    self.assertEqual(d[str(h / ".agents/skills/codebox-next")]["harnesses"], ["opencode"])
    self.assertEqual(d[str(h / ".local/bin/codebox")]["target"], str(REPO / "bin/codebox"))
    self.assertEqual(len(d), 3 + 3 + 2)
    only_claude = codebox.desired_links(codebox.load_plugins(REPO), REPO, ["claude"], h)
    self.assertFalse(any(".agents" in k for k in only_claude))

def test_classify(self):
    # absent; recorded symlink -> ours; symlink into fake_codebox_tree -> old;
    # dangling link to "/gone/codebox/x" -> old; dangling to "/gone/other" -> foreign;
    # symlink to a non-git tmp dir -> foreign; real directory -> foreign;
    # symlink into fake_codebox_tree(origin="https://github.com/x/other.git") -> foreign

def test_plan(self):
    # desired ~/.local/bin/board where a regular file exists -> conflicts == [that path]
    # old link ~/.claude/skills/defer into a codebox tree -> in removes
    # link ~/.claude/skills/mine -> /elsewhere -> not in removes
    # recorded link no longer desired -> in removes
    # ours link already at the desired target -> not in creates
```

- [ ] **Step 2: Run, expect FAIL** (`bin/codebox` doesn't exist)

- [ ] **Step 3: Implement the interfaces above.** Parse SKILL.md frontmatter with a regex for `^name:\s*(\S+)` between the leading `---` lines; no YAML library.

- [ ] **Step 4: Run all the tests, expect PASS**

- [ ] **Step 5: Commit** `codebox: plugin manifests, harness detection, link planning`

---

### Task 4: `codebox install` and `codebox uninstall`

**Files:**
- Modify: `bin/codebox`
- Test: `tests/test_codebox.py`

**Interfaces:**
- Consumes: everything from Task 3.
- Produces:
  - `record_path(user_home) -> Path` (`user_home/.local/state/codebox/installed.json`);
  - `read_record(user_home) -> dict | None`;
  - `write_record(user_home, rec: dict)`: atomic, with a temp file then `os.replace`;
  - `codebox_home(env: dict, user_home: Path) -> Path`;
  - `release_of(root: Path) -> str | None`: `git describe --tags --exact-match` matching `vX.Y.Z`, else `None`;
  - `apply(creates: dict, removes: list)`: removes first, then `mkdir -p` the parents and replace the symlink;
  - `install(root: Path, user_home: Path, harness: str | None, which=shutil.which) -> int`, which `update` reuses;
  - `main(argv=None, user_home=None, env=None, which=shutil.which) -> int`.
- Record format: `{"home": str, "release": str|null, "harnesses": [..], "links": [{"path", "target", "harnesses"}]}`, with links sorted by path.

**Behavior:**
- **`install`:**
  - Chooses harnesses: the recorded ones plus `--harness X`, or plus the detected ones when no `--harness` is given.
  - With none: `codebox: no supported harness found (looked for claude, codex, opencode); use --harness NAME`, exit 1.
  - When some aren't detected: `skipped (not found): opencode`.
  - On conflicts: `codebox: nothing changed; these paths exist and weren't created by codebox:`, then one indented path per line, exit 1.
  - Otherwise it applies the plan, printing `+ DEST -> TARGET` / `- DEST`, writes the record, and prints `codebox installed for claude, codex`.
  - If `~/.local/bin` isn't on `PATH`, it prints `add to your shell profile: export PATH="$HOME/.local/bin:$PATH"`.
- **`--harness`** accepts only `HARNESSES` (argparse `choices`).
- **`uninstall`:**
  - Without a record: `codebox: not installed`, exit 1.
  - Removes each recorded link that is still a symlink to its recorded target, and prints `left DEST (no longer codebox's link)` for any that isn't.
  - Deletes the home only if it equals `user_home/.codebox`; otherwise prints `left HOME in place`.
  - Deletes the record.
- **`main`:** catches `ValueError` from `load_plugins` and prints it as a one-line `codebox: ...` error.

- [ ] **Step 1: Write the failing tests.** Run them through `codebox.main([...], user_home=h, env={"CODEBOX_HOME": str(tree), "PATH": ""}, which=lambda n: None)`, with `(h/".claude").mkdir()` so claude is detected unless the test says otherwise.

```python
def test_install_fresh(self):           # every desired link exists and resolves to its target; record harnesses == ["claude"]
def test_install_idempotent(self):      # second run: record unchanged, output has no line starting "+ " or "- "
def test_install_conflict_changes_nothing(self):  # regular file at ~/.local/bin/board -> rc 1, stderr names it,
                                                  # no ~/.claude/skills/codebox-next, no record file
def test_install_migrates_old_links(self):  # with no record: ~/.claude/skills/defer and ~/.claude/skills/codebox-next
                                            # link into an old fake_codebox_tree -> defer removed, codebox-next -> new tree
def test_install_harness_flag(self):    # nothing detected; --harness codex -> only ~/.agents links and the bin links;
                                        # then --harness claude -> record harnesses == ["claude", "codex"]
def test_install_none_detected(self):   # rc 1, stderr contains "no supported harness found"
def test_uninstall_keeps_dev_home(self):       # CODEBOX_HOME=tree: links and record gone, tree still exists
def test_uninstall_removes_default_home(self): # env without CODEBOX_HOME, fake tree at h/".codebox": home gone
def test_uninstall_leaves_replaced_link(self): # replace a recorded link with a regular file -> file survives, "left" printed
```

- [ ] **Step 2: Run, expect FAIL**
- [ ] **Step 3: Implement**
- [ ] **Step 4: Run all the tests, expect PASS.** Then smoke-test against a throwaway home: `HOME=$(mktemp -d) CODEBOX_HOME=$PWD bin/codebox install --harness claude`, which should print `+` lines and `codebox installed for claude`.
- [ ] **Step 5: Commit** `codebox: install and uninstall with an all-or-nothing conflict check`

---

### Task 5: `codebox update`

**Files:**
- Modify: `bin/codebox`
- Test: `tests/test_codebox.py`, `tests/helpers.py`

**Interfaces:**
- Produces:
  - `newest_tag(root: Path) -> str | None`: the highest `vX.Y.Z` by `parse_version`; other tags are ignored.
  - `export_tree(root: Path, rev: str, dest: Path)`: `git archive rev`, extracted with `tarfile` in stream mode `"r|"`.
  - `version_diff(old: list, new: list) -> list`: output lines, without the header.
  - `notes_between(changes: dict, old: str | None, new: str) -> str`: the notes for versions `> old` and `<= new`, ascending, joined with `"; "`.
- `tests/helpers.py` gains `release_repo(tmp: Path) -> Path`. It builds a `fake_codebox_tree` tagged `v0.1.0`, then a second commit that:
  - edits `codebox-next/SKILL.md`;
  - bumps `codebox-next` to `1.1.0` (note `show blocked cards last`) and `board` to `1.1.0` (note `next: shows blocked cards last`);
  - adds plugin `newplugin` at `0.1.0` (note `first release`) with one skill, `codebox-new`.

  That commit is tagged `v0.2.0`.

**Behavior:**
- With no record: `codebox: not installed; run codebox install`.
- The home must be clean (`git status --porcelain` empty) and at a release tag (`release_of`). Otherwise: `codebox: update needs HOME to be a clean checkout of a release tag; for a development checkout, re-run codebox install`.
- `git fetch --tags --quiet origin`. On failure: `codebox: could not fetch: <last stderr line>`.
- If the newest tag is the current one: `codebox vX.Y.Z is up to date`.
- Otherwise:
  1. Export the new tag to a temp dir and load its plugins.
  2. Plan with `desired_links(new_plugins, root=home, ...)`, so targets are under the home and not the temp dir. On conflicts, use the same message and exit as install, and leave the checkout untouched.
  3. `git checkout --quiet <tag>`, then run `install(home, user_home, None)`.
  4. Print `codebox OLD → NEW` and the `version_diff` lines, or `  (no plugin changes)`.
- **Diff format.** Unchanged plugins and skills are omitted, and plugins are sorted by name.

  ```
  codebox v0.1.0 → v0.2.0
    board 1.0.0 → 1.1.0  next: shows blocked cards last
      codebox-next 1.0.0 → 1.1.0  show blocked cards last
    + newplugin 0.1.0  first release
  ```

  A removed plugin is `  - name OLDVER`. A skill added to an existing plugin is `    + skill VER  note`, and a removed skill is `    - skill`.
- `# ponytail:` comment on the re-wire: the old release's code wires the new tree; if the manifest format ever changes, re-exec the new `bin/codebox` instead.

- [ ] **Step 1: Write the failing tests**

```python
def test_newest_tag(self):   # tags v0.9.0, v0.10.0, vfoo -> "v0.10.0"; no tags -> None
def test_notes_between(self):
    ch = {"1.0.0": "a", "1.1.0": "b", "1.2.0": "c"}
    self.assertEqual(codebox.notes_between(ch, "1.0.0", "1.2.0"), "b; c")
    self.assertEqual(codebox.notes_between(ch, None, "1.0.0"), "a")
def test_version_diff(self):  # load_plugins of release_repo exported at v0.1.0 and v0.2.0 ->
                              # exactly the three body lines in the format block above
def test_update_end_to_end(self):  # clone release_repo to h/".codebox", checkout v0.1.0, install;
                                   # update -> rc 0, `release_of` == "v0.2.0", ~/.claude/skills/codebox-new exists,
                                   # stdout starts "codebox v0.1.0 → v0.2.0", record release == "v0.2.0"
def test_update_up_to_date(self):  # second update -> "is up to date"
def test_update_refuses_dirty(self):  # touch an untracked file in the home -> rc 1, "clean checkout"
def test_update_conflict_leaves_checkout(self):  # real dir at ~/.claude/skills/codebox-new -> rc 1, still at v0.1.0
```

Clone with `origin` set to the `release_repo` path, so `fetch` works offline.

- [ ] **Step 2: Run, expect FAIL**
- [ ] **Step 3: Implement**
- [ ] **Step 4: Run all the tests, expect PASS**
- [ ] **Step 5: Commit** `codebox: update to the newest release with version notes`

---

### Task 6: Version-honesty guard

**Files:**
- Create: `tests/test_versions.py`

**Interfaces:**
- Consumes: `load_plugins`, `export_tree`, `newest_tag`, `parse_version`, and `tests/helpers.release_repo`.
- Produces: `version_violations(root: Path, tag: str) -> list`, defined in the test module. Each violation is a string naming the plugin or skill.

**Rules**, comparing the working tree at `root` with the tree at `tag` and matching plugins and skills by name:
- A plugin whose files differ, excluding its own `plugin.json` and `__pycache__`, must have a version greater than at the tag.
- A skill whose folder differs must have a version greater than at the tag.
- Every current version must have a note. `load_plugins` already enforces this, so a failure to load counts as a violation.
- Names new since the tag need no bump.

Compare folders with a digest over sorted relative paths and file bytes.

- [ ] **Step 1: Write the tests**

```python
class TestGuard(unittest.TestCase):
    def test_current_tree_is_honest(self):
        tag = codebox.newest_tag(REPO)
        if tag is None:
            self.skipTest("no release tag yet")
        self.assertEqual(version_violations(REPO, tag), [])

    def test_detects_unbumped_change(self):
        # release_repo checked out at v0.2.0; edit codebox-next/SKILL.md without bumping
        # -> violations mention "codebox-next" and "board"
    def test_bumped_change_is_clean(self):
        # same edit plus codebox-next 1.2.0 and board 1.2.0 with notes -> []
```

- [ ] **Step 2: Run.** Expect the two fixture tests to FAIL until `version_violations` exists, then implement it, then expect PASS. `test_current_tree_is_honest` is skipped (no tags yet).
- [ ] **Step 3: Commit** `tests: guard that changed plugins and skills bump their versions`

---

### Task 7: `bootstrap.sh`

**Files:**
- Create: `bootstrap.sh` (repo root, executable, `#!/usr/bin/env bash`, `set -euo pipefail`)
- Test: `tests/test_bootstrap.py`

**Behavior:**
- Variables: `REPO_URL="${CODEBOX_REPO:-https://github.com/briney/codebox.git}"` and `HOME_DIR="${CODEBOX_HOME:-$HOME/.codebox}"`.
- Missing `git` or `python3`: `codebox bootstrap: needs git and python3`, exit 1.
- **No home yet:**
  1. `git clone --quiet`.
  2. Pick the newest `v*` tag with `git tag --list 'v[0-9]*' --sort=-v:refname | head -1`. With none, print `codebox bootstrap: REPO_URL has no release tags yet`, remove the fresh clone, and exit 1.
  3. `git checkout --quiet <tag>`.
- **Home exists:**
  - If it isn't a git checkout: `codebox bootstrap: HOME_DIR exists and is not a codebox checkout; remove it and re-run`, exit 1.
  - Otherwise, `git fetch --tags --quiet` (failure is only a warning), and leave the checkout where it is.
- **Linking `~/.local/bin/codebox`** (`mkdir -p` the folder first):
  - If something exists there that isn't a symlink: `codebox bootstrap: ~/.local/bin/codebox exists and isn't a link; move it and re-run`, exit 1.
  - Otherwise `ln -sfn "$HOME_DIR/bin/codebox" ~/.local/bin/codebox`.
- **Output:** the PATH hint (same text as Task 4) when needed, then `next: codebox install` for a new home, or `next: codebox update` for an existing one.

- [ ] **Step 1: Write the failing tests.** Run `bash bootstrap.sh` with `env={"HOME": tmp_home, "CODEBOX_REPO": str(release_repo(...)), "PATH": os.environ["PATH"]}`.

```python
def test_fresh(self):         # rc 0; h/.codebox at v0.2.0 (release_of); h/.local/bin/codebox resolves into it; "codebox install" in stdout
def test_no_tags(self):       # source repo without tags -> rc 1, "no release tags", h/.codebox absent
def test_rerun_keeps_checkout(self):  # checkout v0.1.0 by hand, re-run -> still v0.1.0, "codebox update" in stdout
def test_refuses_foreign_bin(self):   # regular file at h/.local/bin/codebox -> rc 1, file unchanged
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** `bootstrap.sh: one-line install of the codebox command`

---

### Task 8: On-demand trigger check

**Files:**
- Create: `tests/triggers.sh` (executable; not run by `unittest`)

**Behavior:**
- Usage: `tests/triggers.sh [claude|codex|opencode ...]`, defaulting to every one of the three on PATH.
- It makes a temp git repo with no remote, so any `board` call fails harmlessly with "no board". Inside it, it links each `plugins/*/skills/*` folder into `.claude/skills/` and `.agents/skills/` (project-level skill folders that all three harnesses read).
- Phrasings:

  | Phrasing | Skill |
  |---|---|
  | `park this idea for later: add retries to the uploader` | `codebox-defer` |
  | `what's next on the board?` | `codebox-next` |
  | `set up the board for this repo` | `codebox-board-setup` |
  | `what does git status do?` | none (negative control) |

- Runs each phrasing headless with `timeout 300`:
  - `claude -p --output-format stream-json --verbose`
  - `codex exec --json`
  - `opencode run --format json`
- It decides whether the expected skill fired from a harness-specific match on the event output: Claude's `Skill` tool input, or Codex and OpenCode reading `<skill>/SKILL.md`. Don't match on the skill name alone, because session-init events list every skill.
- For each harness and phrasing it prints `PASS`, `FAIL` or `SKIP`, and exits 1 if any `FAIL`.

- [ ] **Step 1: Write the script.**
- [ ] **Step 2: Verify the matchers** with one harness at a time: `tests/triggers.sh claude`, then `codex`, then `opencode`. Expected: each prints three PASS lines and a PASS for the negative control. Paste the output into the task report. If a phrasing misfires, tighten that skill's `description:` first. A description change is a skill change, so bump that skill and the board plugin, with notes. During this unreleased work, editing the 1.0.0 note is enough.
- [ ] **Step 3: Commit** `tests: on-demand natural-language trigger check`

---

### Task 9: README and this repo's own board section

**Files:**
- Modify: `README.md`, `AGENTS.md` (this repo's board section)

- [ ] **Step 1: Rewrite `README.md`.** Cover what codebox is (harness-neutral plugins for Claude Code, Codex, OpenCode) and requirements. Then:
  - **Install:** the `curl -fsSL https://raw.githubusercontent.com/briney/codebox/main/bootstrap.sh | bash` line, then `codebox install [--harness claude|codex|opencode]`.
  - **Update, uninstall, and what codebox never touches.** For a development checkout: `CODEBOX_HOME=~/git/codebox codebox install`.
  - **Plugins:** board, with its skills, invoked by plain language or `/codebox-next` and `$codebox-next`, plus the existing `board` command reference.
  - **Releasing:** bump versions and notes in `plugin.json`, run the tests (the guard checks you), then tag `vX.Y.Z` and push the tag.
  - **Tests:** unit tests, `tests/e2e.sh`, `tests/triggers.sh`.

  Keep the tone and length of today's README.
- [ ] **Step 2: Refresh this repo's section.** From the worktree root, run `plugins/board/bin/board setup`. Expected: `AGENTS.md updated (board section was out of date)`, and its section now names `codebox-defer`. It only reads the existing board.
- [ ] **Step 3: Final check.** Run `python3 -m unittest discover -s tests`, expecting all tests to pass (the guard skips). Then run `grep -rn 'install\.sh\|skills/defer\|Bryan' README.md plugins bin tests bootstrap.sh`, expecting no output.
- [ ] **Step 4: Commit** `README: bootstrap, install, update, plugins; refresh AGENTS board section`

---

## After the plan (needs Bryan, not part of the task loop)

1. Open the PR with `Closes #1`.
2. After merge, Bryan tags and pushes `v0.1.0`.
3. On this machine, run the bootstrap one-liner, then `codebox install`. This migrates the old `defer`/`next`/`board-setup` links.
4. In oplm, run `board setup` to refresh its section, and commit through the normal flow.
5. Repeat on loki and the cluster, checking `python3 --version` first.
