# codebox

Personal toolkit for AI-assisted development. Contains:

- **`skills/`** — Reusable skill definitions for Claude Code / Codex / other coding agents
- **`notebook/`** — Lab notebook tracking work, decisions, and next steps across projects
- **`setup/`** — Shell scripts for configuring dev environments

## Setup

Clone this repo to `~/codebox` on each machine:

```bash
git clone git@github.com:briney/codebox.git ~/codebox
```

Add the skills to your global Claude Code settings so they're available in all projects.
See `CLAUDE.md` in this repo for the global directives that should be added to your
Claude Code configuration.

## Skills

| Skill | Description |
|-------|-------------|
| `lab-notebook` | Session logging, project status tracking, and work history |
| `python-init` | Scaffold a new Python project with modern best practices |

## Notebook

The `notebook/` directory is a flat collection of project directories, each containing
session logs and living documents. See `skills/lab-notebook/SKILL.md` for full conventions.
