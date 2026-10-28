from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from helpers import REPO, codebox, release_repo


def _digest(root: Path, rel: str, skip=()) -> str:
    h = hashlib.sha256()
    base = Path(root) / rel
    for f in sorted(p for p in base.rglob("*") if p.is_file()):
        r = f.relative_to(base)
        if "__pycache__" in r.parts or r.as_posix() in skip:
            continue
        h.update(r.as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def version_violations(root: Path, tag: str) -> list:
    try:
        new = codebox.load_plugins(root)
    except ValueError as e:
        return [f"manifest error: {e}"]
    with tempfile.TemporaryDirectory() as t:
        codebox.export_tree(root, tag, Path(t))
        old = codebox.load_plugins(Path(t))
        out = []
        old_plugins = {p["name"]: p for p in old}
        old_skills = {s: i for p in old for s, i in p["skills"].items()}
        for p in new:
            o = old_plugins.get(p["name"])
            if o and _digest(root, p["dir"], {"plugin.json"}) != _digest(t, o["dir"], {"plugin.json"}) \
                    and codebox.parse_version(p["version"]) <= codebox.parse_version(o["version"]):
                out.append(f"{p['name']}: files changed since {tag} but version is still {p['version']}")
            for s, i in p["skills"].items():
                if s in old_skills:
                    if _digest(root, i["dir"]) != _digest(t, old_skills[s]["dir"]) \
                            and codebox.parse_version(i["version"]) <= codebox.parse_version(old_skills[s]["version"]):
                        out.append(f"{s}: files changed since {tag} but version is still {i['version']}")
        return out


class TestGuard(unittest.TestCase):
    def _repo(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        root = release_repo(t.name)
        with open(root / "plugins/board/skills/codebox-next/SKILL.md", "a") as f:
            f.write("\nMore.\n")
        return root

    def test_current_tree_is_honest(self):
        tag = codebox.newest_tag(REPO)
        if tag is None:
            self.skipTest("no release tag yet")
        self.assertEqual(version_violations(REPO, tag), [])

    def test_detects_unbumped_change(self):
        v = "\n".join(version_violations(self._repo(), "v0.2.0"))
        self.assertIn("codebox-next: files changed since v0.2.0", v)
        self.assertIn("board: files changed since v0.2.0", v)

    def test_bumped_change_is_clean(self):
        root = self._repo()
        f = root / "plugins/board/plugin.json"
        m = json.loads(f.read_text())
        m["version"] = "1.2.0"
        m["changes"]["1.2.0"] = "more"
        m["skills"]["codebox-next"]["version"] = "1.2.0"
        m["skills"]["codebox-next"]["changes"]["1.2.0"] = "more"
        f.write_text(json.dumps(m))
        self.assertEqual(version_violations(root, "v0.2.0"), [])

    def test_missing_note_is_violation(self):
        root = self._repo()
        f = root / "plugins/board/plugin.json"
        m = json.loads(f.read_text())
        m["version"] = "1.2.0"
        f.write_text(json.dumps(m))
        self.assertEqual(len(version_violations(root, "v0.2.0")), 1)


if __name__ == "__main__":
    unittest.main()
