# pyproject.toml Reference

Annotated example for a modern Python project. Adapt values in `<angle brackets>`.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "<project-name>"
version = "0.1.0"
description = "<One-line description>"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    { name = "<Author Name>", email = "<email>" },
]
dependencies = [
    # Runtime dependencies go here.
    # Pin minimally: "requests>=2.28" not "requests==2.31.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.4",
    "ty>=0.0.40",
    "pre-commit>=3.0",
]

# Uncomment if this is a CLI tool:
# [project.scripts]
# <command-name> = "<package_name>.cli:main"

[project.urls]
Repository = "https://github.com/<user>/<project-name>"

# --- Tool Configuration ---
# Everything below configures dev tools. No separate config files needed.

[tool.ruff]
line-length = 100

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
]

[tool.ruff.lint.isort]
# Ruff's isort is black-compatible by default — there is no `profile` key.
# Set first-party packages so local imports group correctly.
known-first-party = ["<package_name>"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q"

[tool.ty.environment]
# ty infers the Python version from `requires-python`; set explicitly for clarity.
python-version = "3.11"

[tool.hatch.build.targets.wheel]
packages = ["src/<package_name>"]
```

## Notes

- **Why ty (not mypy)?** `ty` is Astral's type checker (same family as ruff/uv),
  configured under `[tool.ty]` in pyproject.toml and run with `ty check`. It is
  pre-1.0 and evolving fast. It has no single `strict` toggle like mypy — it
  infers types and reports via a default ruleset; tune severities under
  `[tool.ty.rules]` if needed. It auto-detects the Python version from
  `requires-python` and the active environment.

- **Why hatchling?** It's the simplest PEP 517 build backend. No setup.py, no
  setup.cfg, no MANIFEST.in for most projects. Alternatives (setuptools, flit,
  pdm-backend) all work but hatchling has the least boilerplate.

- **Why not pin exact versions in dependencies?** Exact pins cause conflicts for
  downstream users. Use minimum version bounds (`>=`) for libraries. For applications
  that aren't installed by others, tighter pins are acceptable.

- **Why src layout?** Prevents a common class of bugs where `import <package>` silently
  imports from the working directory instead of the installed package. The src layout
  forces installation before import.

- **Version management**: For simple projects, a hardcoded version in pyproject.toml is
  fine. For larger projects, consider `hatch-vcs` to derive version from git tags:
  ```toml
  [tool.hatch.version]
  source = "vcs"
  ```
