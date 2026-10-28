import json
import os
import tempfile
import unittest
from pathlib import Path

from helpers import REPO, codebox, fake_codebox_tree


class Tmp(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.tmp = Path(t.name).resolve()


class TestVersion(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(codebox.parse_version("1.10.0"), (1, 10, 0))
        for bad in ("1.0", "1.0.0.0", "a.b.c", "1.0.x", ""):
            with self.assertRaises(ValueError):
                codebox.parse_version(bad)


class TestLoadPlugins(Tmp):
    def test_real_repo(self):
        (p,) = codebox.load_plugins(REPO)
        self.assertEqual((p["name"], p["version"]), ("board", "1.0.0"))
        self.assertEqual(set(p["skills"]), {"codebox-defer", "codebox-next", "codebox-board-setup"})
        self.assertEqual(p["commands"], {"board": "plugins/board/bin/board"})
        self.assertEqual(p["dir"], "plugins/board")
        self.assertEqual(p["skills"]["codebox-next"]["dir"], "plugins/board/skills/codebox-next")

    def test_no_plugins_dir(self):
        self.assertEqual(codebox.load_plugins(self.tmp), [])

    def test_rejects(self):
        def tree(name):
            return fake_codebox_tree(self.tmp / name)

        t = tree("a")
        (t / "plugins/board/skills/stray").mkdir()
        with self.assertRaisesRegex(ValueError, "stray"):
            codebox.load_plugins(t)

        t = tree("b")
        m = t / "plugins/board/plugin.json"
        d = json.loads(m.read_text())
        d["version"] = "1.1.0"
        m.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "board"):
            codebox.load_plugins(t)

        t = tree("c")
        s = t / "plugins/board/skills/codebox-next/SKILL.md"
        s.write_text(s.read_text().replace("name: codebox-next", "name: next"))
        with self.assertRaisesRegex(ValueError, "codebox-next"):
            codebox.load_plugins(t)

        t = tree("d")
        m = t / "plugins/board/plugin.json"
        d = json.loads(m.read_text())
        d["name"] = "other"
        m.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "board"):
            codebox.load_plugins(t)

        t = tree("e")
        m = t / "plugins/board/plugin.json"
        d = json.loads(m.read_text())
        d["skills"]["ghost"] = {"version": "1.0.0", "changes": {"1.0.0": "x"}}
        m.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "ghost"):
            codebox.load_plugins(t)

        t = tree("f")
        m = t / "plugins/board/plugin.json"
        d = json.loads(m.read_text())
        d["skills"]["codebox-next"]["version"] = "1.0"
        m.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "codebox-next"):
            codebox.load_plugins(t)


class TestDetect(Tmp):
    def test_detect_harnesses(self):
        h = self.tmp
        (h / ".codex").mkdir()
        which = lambda n: "/usr/bin/claude" if n == "claude" else None
        self.assertEqual(codebox.detect_harnesses(h, which), ["claude", "codex"])
        self.assertEqual(codebox.detect_harnesses(h / "empty", lambda n: None), [])


class TestDesired(Tmp):
    def test_desired_links(self):
        h = self.tmp
        plugins = codebox.load_plugins(REPO)
        d = codebox.desired_links(plugins, REPO, ["claude", "opencode"], h)
        self.assertEqual(d[str(h / ".claude/skills/codebox-next")],
                         {"target": str(REPO / "plugins/board/skills/codebox-next"), "harnesses": ["claude"]})
        self.assertEqual(d[str(h / ".agents/skills/codebox-next")]["harnesses"], ["opencode"])
        self.assertEqual(d[str(h / ".local/bin/codebox")]["target"], str(REPO / "bin/codebox"))
        self.assertEqual(d[str(h / ".local/bin/board")]["harnesses"], [])
        self.assertEqual(len(d), 3 + 3 + 2)
        only_claude = codebox.desired_links(plugins, REPO, ["claude"], h)
        self.assertFalse(any(".agents" in k for k in only_claude))


class TestClassify(Tmp):
    def test_classify(self):
        h = self.tmp
        tree = fake_codebox_tree(h / "tree")
        other = fake_codebox_tree(h / "othertree", origin="https://github.com/x/other.git")
        plain = h / "plain"
        plain.mkdir()
        (h / "d").mkdir()
        c = codebox.classify
        self.assertEqual(c(h / "nothing", set()), "absent")
        ours = h / "ours"
        ours.symlink_to(plain)
        self.assertEqual(c(ours, {str(ours)}), "ours")
        old = h / "old"
        old.symlink_to(tree / "plugins")
        self.assertEqual(c(old, set()), "old")
        dang = h / "dang"
        dang.symlink_to("/gone/codebox/x")
        self.assertEqual(c(dang, set()), "old")
        dang2 = h / "dang2"
        dang2.symlink_to("/gone/other")
        self.assertEqual(c(dang2, set()), "foreign")
        nongit = h / "nongit"
        nongit.symlink_to(plain)
        self.assertEqual(c(nongit, set()), "foreign")
        self.assertEqual(c(h / "d", set()), "foreign")
        oth = h / "oth"
        oth.symlink_to(other / "plugins")
        self.assertEqual(c(oth, set()), "foreign")


class TestPlan(Tmp):
    def test_plan(self):
        h = self.tmp
        tree = fake_codebox_tree(h / "tree")
        for d in (".local/bin", ".claude/skills"):
            (h / d).mkdir(parents=True)
        board = h / ".local/bin/board"
        board.write_text("regular file")
        old = h / ".claude/skills/defer"
        old.symlink_to(tree / "plugins/board/skills/codebox-defer")
        mine = h / ".claude/skills/mine"
        mine.symlink_to("/elsewhere")
        stale = h / ".claude/skills/stale"
        stale.symlink_to("/elsewhere2")
        good = h / ".local/bin/codebox"
        good.symlink_to(tree / "bin/codebox")
        wrong = h / ".claude/skills/codebox-next"
        wrong.symlink_to("/old/place")
        desired = {
            str(board): {"target": str(tree / "plugins/board/bin/board"), "harnesses": []},
            str(good): {"target": str(tree / "bin/codebox"), "harnesses": []},
            str(wrong): {"target": str(tree / "plugins/board/skills/codebox-next"), "harnesses": ["claude"]},
            str(h / ".claude/skills/new"): {"target": "/t/new", "harnesses": ["claude"]},
        }
        record = {"links": [{"path": str(good)}, {"path": str(stale)}, {"path": str(wrong)}]}
        creates, removes, conflicts = codebox.plan(desired, record, h)
        self.assertEqual(conflicts, [str(board)])
        self.assertIn(str(old), removes)
        self.assertNotIn(str(mine), removes)
        self.assertIn(str(stale), removes)
        self.assertEqual(removes, sorted(removes))
        self.assertNotIn(str(good), creates)
        self.assertEqual(creates[str(wrong)], str(tree / "plugins/board/skills/codebox-next"))
        self.assertEqual(creates[str(h / ".claude/skills/new")], "/t/new")
        self.assertNotIn(str(board), creates)
        self.assertEqual(codebox.plan({}, None, h / "empty")[1:], ([], []))


if __name__ == "__main__":
    unittest.main()
