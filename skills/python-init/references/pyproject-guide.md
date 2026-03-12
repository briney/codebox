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
    "mypy>=1.0",
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
profile = "black"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.hatch.build.targets.wheel]
packages = ["src/<package_name>"]
```

## Notes

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
