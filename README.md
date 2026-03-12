# codebox

Personal toolkit for AI-assisted development. Contains:

- **`skills/`** — Reusable skill definitions for Claude Code / Codex / other coding agents
- **`notebook/`** — Lab notebook tracking work, decisions, and next steps across projects
- **`setup/`** — Shell scripts for configuring dev environments

## Setup

Clone this repo to `~/codebox` on each machine. Use `--recurse-submodules` to pull the
lab notebook alongside the main repo:

```bash
git clone --recurse-submodules git@github.com:briney/codebox.git ~/codebox
```

If you cloned without `--recurse-submodules`, initialize the notebook submodule after:

```bash
cd ~/codebox
git submodule update --init
```

> **Forking?** The `notebook/` directory is a
> [separate private repo](https://github.com/briney/codebox-notebook) included as a git
> submodule. If you fork codebox, the submodule will still point to the original notebook repo
> (which you won't have access to). Two options:
>
> *Local notebook (not version controlled):* Remove the submodule and create a plain directory:
> ```bash
> cd ~/codebox
> git submodule deinit -f notebook
> git rm -f notebook
> rm -rf .git/modules/notebook
> mkdir -p notebook/projects notebook/experiments
> echo "notebook/" >> .gitignore
> ```
>
> *Your own notebook repo:* Create a new repo on GitHub (e.g. `your-username/codebox-notebook`),
> then re-point the submodule:
> ```bash
> cd ~/codebox
> git submodule deinit -f notebook
> git submodule set-url notebook git@github.com:<your-username>/codebox-notebook.git
> git submodule update --init
> ```

### Claude Code

Copy the global instruction files to `~/.claude/`:

```bash
cp ~/codebox/setup/claude/CLAUDE.md ~/.claude/CLAUDE.md
cp ~/codebox/setup/claude/WEB.md ~/.claude/WEB.md
cp ~/codebox/setup/claude/COMPILED.md ~/.claude/COMPILED.md
```

`CLAUDE.md` is the primary directive file (loaded automatically). `WEB.md` and `COMPILED.md`
are supplementary guidelines referenced by `CLAUDE.md` when working on web or compiled-language
projects.

### Codex

Copy the Codex-specific instruction files to `~/.codex/`:

```bash
cp ~/codebox/setup/codex/AGENTS.md ~/.codex/AGENTS.md
cp ~/codebox/setup/codex/WEB.md ~/.codex/WEB.md
cp ~/codebox/setup/codex/COMPILED.md ~/.codex/COMPILED.md
```

`AGENTS.md` is the Codex equivalent of `CLAUDE.md`. The supplementary `WEB.md` and `COMPILED.md`
files serve the same role as their Claude Code counterparts.

## Skills

| Skill | Description |
|-------|-------------|
| `lab-notebook` | Session logging, project status tracking, and work history |
| `python-init` | Scaffold a new Python project with modern best practices |

## Notebook

The `notebook/` directory is a [separate repo](https://github.com/briney/codebox-notebook)
included as a git submodule. It contains a flat collection of project directories, each with
session logs and living documents. See `skills/lab-notebook/SKILL.md` for full conventions.
