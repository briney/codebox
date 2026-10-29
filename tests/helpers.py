import importlib.util
import shutil
import subprocess
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_loader = SourceFileLoader("codebox", str(REPO / "bin" / "codebox"))
_spec = importlib.util.spec_from_loader("codebox", _loader)
codebox = importlib.util.module_from_spec(_spec)
_loader.exec_module(codebox)

_ID = ["-c", "user.name=codebox-test", "-c", "user.email=test@example.com"]


def git(path, *args):
    subprocess.run(["git", *_ID, "-C", str(path), *args], check=True, capture_output=True)


def fake_codebox_tree(dest, origin="https://github.com/briney/codebox.git"):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO / "plugins", dest / "plugins", ignore=shutil.ignore_patterns("__pycache__"))
    if (REPO / "bin").exists():
        shutil.copytree(REPO / "bin", dest / "bin", ignore=shutil.ignore_patterns("__pycache__"))
    git(dest, "init", "-q")
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "init")
    git(dest, "remote", "add", "origin", origin)
    return dest


def release_repo(tmp):
    """A codebox tree tagged v0.1.0, then v0.2.0 (board bumped, plugin newplugin added); left at v0.2.0."""
    import json
    root = fake_codebox_tree(Path(tmp) / "release")
    board = root / "plugins/board/plugin.json"
    m = json.loads(board.read_text())
    m["version"], m["changes"] = "1.0.0", {"1.0.0": m["changes"]["1.0.0"]}  # stable baseline across real bumps
    board.write_text(json.dumps(m, indent=2) + "\n")
    git(root, "commit", "-q", "--allow-empty", "-am", "v0.1.0")
    git(root, "tag", "v0.1.0")
    m["version"] = "1.1.0"
    m["changes"]["1.1.0"] = "next: shows blocked cards last"
    m["skills"]["codebox-next"]["version"] = "1.1.0"
    m["skills"]["codebox-next"]["changes"]["1.1.0"] = "show blocked cards last"
    board.write_text(json.dumps(m, indent=2) + "\n")
    with open(root / "plugins/board/skills/codebox-next/SKILL.md", "a") as f:
        f.write("\nShow blocked cards last.\n")
    skill = root / "plugins/newplugin/skills/codebox-new"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: codebox-new\ndescription: new\n---\nnew\n")
    (root / "plugins/newplugin/plugin.json").write_text(json.dumps({
        "name": "newplugin", "version": "0.1.0", "changes": {"0.1.0": "first release"},
        "skills": {"codebox-new": {"version": "0.1.0", "changes": {"0.1.0": "first release"}}}}, indent=2) + "\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "v0.2.0")
    git(root, "tag", "v0.2.0")
    return root
