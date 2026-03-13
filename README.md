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

*Local notebook (not version controlled):* Remove the submodule and create a plain directory:
```bash
cd ~/codebox
git submodule deinit -f notebook
git rm -f notebook
rm -rf .git/modules/notebook
mkdir -p notebook/projects notebook/experiments
echo "notebook/" >> .gitignore
```

*Your own notebook repo:* Create a new repo on GitHub (e.g. `your-username/codebox-notebook`), then re-point the submodule:
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

### Configure coding agents

A shared set of instruction files lives in `setup/instructions/` and is installed to the
correct location for each agent harness. Run the install script to set up all harnesses at once:

```bash
~/codebox/setup/install.sh
```

Or install a specific harness:

```bash
~/codebox/setup/install.sh --claude     # Claude Code only
~/codebox/setup/install.sh --codex      # Codex only
~/codebox/setup/install.sh --opencode   # OpenCode only
```

The script is idempotent and can be re-run after pulling changes to update all config files.

<details>
<summary>What gets installed where</summary>

Each harness receives the same instruction files (`INSTRUCTIONS.md`, `WEB.md`, `COMPILED.md`)
copied to its config directory with the expected filename:

| Harness | Config directory | Instruction file | Skills |
|---------|-----------------|-------------------|--------|
| Claude Code | `~/.claude/` | `CLAUDE.md` | Symlinked as slash commands in `~/.claude/commands/` |
| Codex | `~/.codex/` | `AGENTS.md` | Referenced via `AGENTS.md` |
| OpenCode | `~/.config/opencode/` | `AGENTS.md` | Symlinked as skill directories in `~/.config/opencode/skills/` |

Claude Code also gets `settings.json` (permissions and plugin config) from `setup/claude/`.

> **Note:** OpenCode has a Claude Code compatibility layer and will read `~/.claude/CLAUDE.md`
> as a fallback. The dedicated `~/.config/opencode/AGENTS.md` takes precedence if present.

</details>

## Skills

| Skill | Description |
|-------|-------------|
| `lab-notebook` | Session logging, project status tracking, and work history |
| `python-init` | Scaffold a new Python project with modern best practices |

## Notebook

The `notebook/` directory is a [separate repo](https://github.com/briney/codebox-notebook)
included as a git submodule. It contains a flat collection of project directories, each with
session logs and living documents. See `skills/lab-notebook/SKILL.md` for full conventions.
