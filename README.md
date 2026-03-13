# codebox

Personal toolkit for AI-assisted development. Contains:

- **`skills/`** — Reusable skill definitions for Claude Code / Codex / other coding agents
- **`notebook/`** — Lab notebook tracking work, decisions, and next steps across projects
- **`setup/`** — Shell scripts for configuring dev environments

## Setup

### Configure your notebook
The `notebook/` directory is a [separate private repo](https://github.com/briney/codebox-notebook) included as a git submodule. If you just cloned this repo, the submodule will still point to the original notebook repo (which you won't have access to). To fix, you need to first fork the repo, and then clone your fork to `~/codebox`:

```bash
git clone --recurse-submodules https://github.com/<your-username>/codebox.git ~/codebox
```

Now you have two options depending on how you want to configure your notebook:

*Local notebook (not version controlled):*  
Remove the submodule and create a plain directory:
```bash
cd ~/codebox
git submodule deinit -f notebook
git rm -f notebook
rm -rf .git/modules/notebook
mkdir -p notebook/projects notebook/experiments
echo "notebook/" >> .gitignore
```

*Your own notebook repo:*  
Create a new repo on GitHub (e.g. `your-username/codebox-notebook`), then re-point the submodule:
```bash
cd ~/codebox
git submodule deinit -f notebook
git submodule set-url notebook git@github.com:<your-username>/codebox-notebook.git
git submodule update --init
```

Once you configure your notebook and push the changes back to your fork, any future clones of your 
repository will have your notebook initialized the way you configured it. So every future install can 
skip the submodule configuration step and install directly as described below.

### Installation

Using this repository as an example (for your fork, replace `briney` with your GitHub username), just 
clone to `~/codebox`:

```bash
git clone --recurse-submodules https://github.com/briney/codebox.git ~/codebox
```

If you cloned without `--recurse-submodules` but still want to initialize the notebook submodule, you can run:

```bash
cd ~/codebox
git submodule update --init
```

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
