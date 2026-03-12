---
name: python-init
description: >
  Scaffold a new Python project with modern best practices. Use when the user wants to
  create a new Python package, library, tool, or application from scratch. Triggers include:
  "start a new python project", "initialize a python package", "set up a new repo for
  <something> in python", "create a python project", "scaffold", or any request to create
  a fresh codebase that will be a Python package. Also use when the user asks about modern
  Python project structure, pyproject.toml setup, or best practices for packaging. Do NOT
  use for adding features to an existing project or for non-Python projects.
---

# Python Project Initializer

Scaffold a new Python project using modern conventions. The output is a ready-to-use
repository with a `pyproject.toml`-based build, src layout, dev tooling, and
pre-configured instructions for coding agents.

## What Gets Created

```
<project-name>/
  src/
    <package_name>/
      __init__.py
      py.typed
  tests/
    __init__.py
    test_placeholder.py
  .github/
    workflows/
      ci.yaml
  pyproject.toml
  README.md
  LICENSE
  .gitignore
  .python-version
  CLAUDE.md
  AGENTS.md
```

## Step-by-Step

### 1. Gather Information

You need at minimum:
- **Project name** (kebab-case, used for the repo directory and package distribution name)
- **Package name** (snake_case, used for the importable Python package — default: project name with hyphens replaced by underscores)
- **One-line description**
- **Python version** (default: `3.11`; prefer 3.11+ for modern typing syntax)

Optional:
- License (default: MIT)
- Initial dependencies
- Whether it's a CLI tool (adds a `[project.scripts]` entry)
- Author name and email

### 2. Create the Project

Read the templates in `templates/` and references in `references/` for content.
Adapt templates based on user answers from step 1.

Key files and their purposes:

#### pyproject.toml

Refer to `references/pyproject-guide.md` for the full annotated example. Key points:
- Use `[build-system]` with `hatchling` (simple, standards-compliant, no setup.py needed)
- Pin Python version with `requires-python`
- Define `[project.optional-dependencies]` for dev/test/docs extras
- Configure all tools (ruff, pytest, mypy) in pyproject.toml — no separate config files

#### CLAUDE.md

This file gives Claude Code project-specific context. Start with the template in
`templates/CLAUDE.md.template`, which includes:
- Build and test commands
- Project structure orientation
- Code style preferences
- Common workflows

The user should update this as the project evolves.

#### AGENTS.md

This file gives broader agent instructions (not Claude-specific). Start with the
template in `templates/AGENTS.md.template`, which includes:
- Architecture overview placeholder
- Contribution conventions
- Testing expectations
- What not to do

### 3. Initialize Git and Install

```bash
cd <project-name>
git init
git add -A
git commit -m "Initial project scaffold"

# Create a virtual environment and install in editable mode
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 4. Create Notebook Entry

If the lab notebook is set up at `~/codebox/notebook/`, create a project entry:

```bash
mkdir -p ~/codebox/notebook/projects/<project-name>/sessions
```

Write an initial STATUS.md and add the project to PROJECTS.md.

### 5. Verify

Run the following to confirm everything works:

```bash
python -c "import <package_name>; print(<package_name>.__version__)"
pytest
ruff check src/
```

## Conventions

- **Always use src layout**. It prevents accidental imports from the working directory.
- **Always include `py.typed`**. Signals PEP 561 compliance for downstream type checkers.
- **No setup.py, setup.cfg, or requirements.txt**. Everything lives in `pyproject.toml`.
- **Ruff for linting and formatting**. Replaces black, isort, flake8, and pyflakes.
- **Pytest for testing**. Configured in pyproject.toml, not pytest.ini or conftest.py (conftest.py is fine for fixtures, just not config).
