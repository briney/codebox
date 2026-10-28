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
