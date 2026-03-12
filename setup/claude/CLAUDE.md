# CLAUDE.md

## Environment Overview

This is a polyglot research/engineering environment. The primary language is **Python** (~85%), with secondary use of **web technologies** (React, Django, Tailwind CSS) and occasional **C++/Rust** for performance-critical components.

The work spans computational biology, machine learning, structural biology tooling, and web applications for scientific workflows.

### Supplementary Guidelines
 
For web or compiled-language work, consult the relevant supplementary file before writing code:
 
- **`WEB.md`** — React, TypeScript, Django, Tailwind CSS, Next.js conventions
- **`COMPILED.md`** — C++, Rust, Python bindings (pybind11, PyO3), build systems

---

## Lab Notebook

This environment uses a lab notebook at `~/codebox/notebook/`. If this directory does not exist, pull the `codebox` repo:

```bash
git clone git@github.com:briney/codebox.git ~/codebox
```

- **Start of session**: Read `~/codebox/notebook/projects/<project>/STATUS.md` before doing work. If unsure which project, check `~/codebox/notebook/PROJECTS.md`.
- **End of session**: Write a session log, update STATUS.md, commit and push. Follow the lab-notebook skill at `~/codebox/skills/lab-notebook/SKILL.md` for templates and conventions.

---

## Python

### Style & Standards

- **Python 3.11+**. Use modern syntax: `match` statements, `type` aliases, `X | Y` union syntax, `Self`, `override`.
- Type hints on all function signatures. Use `from __future__ import annotations` for forward references.
- Prefer `pathlib.Path` over `os.path`. Use `Path` objects throughout; only call `str()` at IO boundaries.
- f-strings over `.format()` or `%`. Use `=` specifier for debug prints: `f"{value=}"`.
- Docstrings: Google style. Required on all public classes and functions. One-liner docstrings for trivial helpers are fine.
- Max line length: 100 characters (not 79).
- Imports: `isort` with `profile = black`. Group order: stdlib → third-party → local. Absolute imports only.
- Formatter: `ruff format`. Linter: `ruff check`. Config lives in `pyproject.toml`.

### Patterns & Preferences

- **Dataclasses and Pydantic models** over raw dicts for structured data. Use `dataclasses.dataclass` for internal data; `pydantic.BaseModel` for anything touching serialization, validation, or API boundaries.
- Use `Enum` / `StrEnum` for categorical constants, not string literals.
- Prefer **composition over inheritance**. Mixins are acceptable when they encapsulate a single orthogonal behavior.
- Use **context managers** (`with` blocks) for any resource that needs cleanup.
- For iteration: prefer comprehensions and generator expressions for simple transforms; use explicit loops when logic is nontrivial. Never nest more than two comprehensions.
- Error handling: catch specific exceptions. Never bare `except:`. Use `except Exception` only at top-level entry points with proper logging.
- Logging: use `logging` stdlib (or `loguru` if already in the project). No `print()` in library code.
- Avoid mutable default arguments. Use `None` sentinel + assignment in body.

### Scientific Python Conventions

- **NumPy**: use explicit dtypes on array creation. Prefer `np.asarray` over `np.array` when no copy is needed. Document array shapes in docstrings using `(N, D)` notation.
- **Pandas**: prefer `.loc` / `.iloc` over chained indexing. Use `assign()` for column creation in chains. Avoid `inplace=True`.
- **PyTorch**: models go in their own modules. Keep `forward()` clean — factor heavy logic into named helper methods. Always set `torch.no_grad()` / `model.eval()` for inference. Use `torch.amp` for mixed-precision, not manual casting.
- Shape comments on tensor operations: `# (B, L, D) -> (B, H, L, D_head)`.
- Molecular dynamics / structural biology: OpenMM, BioPython, MDAnalysis are common. Follow their respective conventions for unit handling (OpenMM uses its own unit system — always be explicit).

### Testing

- **pytest** for everything. No `unittest.TestCase` unless interfacing with legacy code.
- Test files mirror source layout: `src/foo/bar.py` → `tests/foo/test_bar.py`.
- Use `pytest.fixture` for setup. Parametrize over inputs with `@pytest.mark.parametrize`.
- Always ensure that tests cover end-to-end runs of models, pipelines and workflows. For example, for biological language models,test that a very small pilot-scale model trains without errors (tensor shape mismatches, etc) on a test dataset for at least a few train steps and one eval.
- Wherever possible, use REAL data (not synthetic) for tests. If necessary, prompt the user to provide real data for tests, and specify the folder into which it should be copied.
- Fixtures that load large data (PDB files, model weights, datasets) should be session-scoped.
- Mark slow tests with `@pytest.mark.slow` so they can be skipped during fast iteration.

### Project Structure

Prefer `src/` layout:

```
project-name/
├── pyproject.toml
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── models/
│       ├── data/
│       └── utils/
├── tests/
├── scripts/          # CLI entry points, one-off analyses
├── notebooks/        # Jupyter, exploratory only
└── configs/          # YAML/TOML config files
```

### Dependency Management

- `pyproject.toml` is the single source of truth for metadata and dependencies.
- Pin exact versions in lock files, use ranges in `pyproject.toml`.
- Use `uv` if available, otherwise `pip`. Use `conda`/`mamba` only when a package requires it (e.g., CUDA-linked libs, OpenMM).
- Docker: prefer `pip` inside containers. If conda is needed, use `micromamba` base image.

---

## General Practices

### Git

- Commit messages: imperative mood, ~50 char subject line. Body if needed.
- Branch naming: `feature/short-description`, `fix/short-description`, `exp/short-description` (for experimental/exploratory work).
- Don't commit generated files, model weights, large data, or `.env` files.

### CLI Scripts

- Use `typer` or `click` for CLI tools (prefer `typer` for new code).
- Every script should have a `--help` that explains what it does.
- Use `rich` for progress bars and formatted terminal output.

### Configuration

- YAML or TOML for config files. No JSON for human-edited config.
- Use Pydantic `BaseSettings` for environment-based configuration with validation.
- Secrets go in environment variables, never in config files.

### Docker

- Multi-stage builds. Separate build and runtime stages.
- Pin base image digests for reproducibility in CI; use tags for local dev.
- If GPU support is needed, base on `nvidia/cuda` and install Python tooling on top. Be explicit about CUDA version compatibility.

### Documentation

- README.md at project root: what it does, how to install, how to run.
- For complex projects: `docs/` folder with architecture overview and key decisions.
- Inline comments explain *why*, not *what*. The code should explain what.

---

## LLM / AI-Specific Conventions

When writing or modifying ML training code, model definitions, or inference pipelines:

- **Reproducibility**: always set and log random seeds. Save full configs alongside checkpoints.
- **Checkpointing**: save optimizer state, scheduler state, and epoch/step alongside model weights.
- **Configs**: use a structured config object (Pydantic or dataclass), not loose kwargs.
- **Wandb / logging**: log hyperparams at run start. Log metrics every N steps, not every step.
- **Data loading**: always use `num_workers > 0` in DataLoaders (but respect system limits). Pin memory for GPU training.
- **Mixed precision**: use `torch.amp` autocast + GradScaler (or BF16 natively on Ampere+/Blackwell GPUs).
- For **HuggingFace Transformers/Accelerate**: follow their config patterns. Don't fight the abstractions.

---

## What Not To Do

- Don't add `# type: ignore` without a specific error code and comment explaining why.
- Don't use `os.system()` or `subprocess.call()` with `shell=True`. Use `subprocess.run()` with a list of args.
- Don't silence warnings globally. Fix them or suppress them narrowly with context.
- Don't put business logic in `__init__.py`.
- Don't use wildcard imports (`from module import *`).
- Don't write functions longer than ~50 lines. If it's longer, refactor.
- Don't commit notebooks with output cells. Use `nbstripout` or clear outputs before committing.
