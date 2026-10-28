import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import subprocess

from helpers import REPO, codebox, fake_codebox_tree, git, release_repo


def _branch(path):
    return subprocess.run(["git", "-C", str(path), "symbolic-ref", "-q", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


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
        self.assertEqual(c(h / "nothing", {}), "absent")
        ours = h / "ours"
        ours.symlink_to(plain)
        self.assertEqual(c(ours, {str(ours): str(plain)}), "ours")
        old = h / "old"
        old.symlink_to(tree / "plugins")
        self.assertEqual(c(old, {}), "old")
        repointed = h / "repointed"
        repointed.symlink_to(plain)
        self.assertEqual(c(repointed, {str(repointed): "/was/here"}), "foreign")
        dang = h / "dang"
        dang.symlink_to("/gone/codebox/x")
        self.assertEqual(c(dang, {}), "old")
        dang2 = h / "dang2"
        dang2.symlink_to("/gone/other")
        self.assertEqual(c(dang2, {}), "foreign")
        nongit = h / "nongit"
        nongit.symlink_to(plain)
        self.assertEqual(c(nongit, {}), "foreign")
        self.assertEqual(c(h / "d", {}), "foreign")
        oth = h / "oth"
        oth.symlink_to(other / "plugins")
        self.assertEqual(c(oth, {}), "foreign")


    def test_classify_ignores_git_env(self):
        h = self.tmp
        tree = fake_codebox_tree(h / "tree")
        plain = h / "plain"
        plain.mkdir()
        link = h / "link"
        link.symlink_to(plain)
        with mock.patch.dict(os.environ, {"GIT_DIR": str(tree / ".git")}):
            self.assertEqual(codebox.classify(link, {}), "foreign")


class TestPlanRepointed(Tmp):
    def test_repointed_link_is_untouched(self):
        h = self.tmp
        mine = h / "mine"
        mine.symlink_to(h)
        rec = {"links": [{"path": str(mine), "target": "/was/here"}]}
        self.assertEqual(codebox.plan({}, rec, h), ({}, [], []))
        _, _, conflicts = codebox.plan({str(mine): {"target": "/t", "harnesses": []}}, rec, h)
        self.assertEqual(conflicts, [str(mine)])


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
        record = {"links": [{"path": str(good), "target": str(tree / "bin/codebox")},
                            {"path": str(stale), "target": "/elsewhere2"},
                            {"path": str(wrong), "target": "/old/place"}]}
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

class TestInstall(Tmp):
    def setUp(self):
        super().setUp()
        self.h = self.tmp / "home"
        (self.h / ".claude").mkdir(parents=True)
        self.tree = fake_codebox_tree(self.tmp / "tree")

    def run_cb(self, *argv, env=None, which=lambda n: None):
        env = {"CODEBOX_HOME": str(self.tree), "PATH": ""} if env is None else env
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = codebox.main(list(argv), user_home=self.h, env=env, which=which)
            except SystemExit as e:
                rc = e.code
        return rc, out.getvalue(), err.getvalue()

    def record(self):
        return json.loads(codebox.record_path(self.h).read_text())

    def test_install_fresh(self):
        rc, out, err = self.run_cb("install")
        self.assertEqual(rc, 0, err)
        rec = self.record()
        self.assertEqual(rec["harnesses"], ["claude"])
        self.assertEqual(rec["home"], str(self.tree))
        self.assertEqual([l["path"] for l in rec["links"]], sorted(l["path"] for l in rec["links"]))
        for l in rec["links"]:
            self.assertEqual(os.readlink(l["path"]), l["target"])
            self.assertTrue(Path(l["path"]).exists())
        self.assertIn("codebox installed for claude", out)
        self.assertIn("skipped (not found): codex, opencode", out)
        self.assertIn('export PATH="$HOME/.local/bin:$PATH"', out)

    def test_install_idempotent(self):
        self.run_cb("install")
        before = codebox.record_path(self.h).read_text()
        rc, out, err = self.run_cb("install")
        self.assertEqual(rc, 0, err)
        self.assertEqual(codebox.record_path(self.h).read_text(), before)
        self.assertFalse([l for l in out.splitlines() if l.startswith(("+ ", "- "))])

    def test_install_conflict_changes_nothing(self):
        (self.h / ".local/bin").mkdir(parents=True)
        board = self.h / ".local/bin/board"
        board.write_text("mine")
        rc, out, err = self.run_cb("install")
        self.assertEqual(rc, 1)
        self.assertIn(str(board), err)
        self.assertIn("nothing changed", err)
        self.assertFalse((self.h / ".claude/skills/codebox-next").exists())
        self.assertFalse(codebox.record_path(self.h).exists())
        self.assertEqual(board.read_text(), "mine")

    def test_install_migrates_old_links(self):
        old = fake_codebox_tree(self.tmp / "old")
        (self.h / ".claude/skills").mkdir()
        (self.h / ".local/bin").mkdir(parents=True)
        defer = self.h / ".claude/skills/defer"
        defer.symlink_to(old / "plugins/board/skills/codebox-defer")
        nxt = self.h / ".claude/skills/codebox-next"
        nxt.symlink_to(old / "plugins/board/skills/codebox-next")
        board = self.h / ".local/bin/board"
        board.symlink_to(old / "plugins/board/bin/board")
        rc, out, err = self.run_cb("install")
        self.assertEqual(rc, 0, err)
        self.assertFalse(defer.is_symlink())
        self.assertEqual(os.readlink(nxt), str(self.tree / "plugins/board/skills/codebox-next"))
        self.assertEqual(os.readlink(board), str(self.tree / "plugins/board/bin/board"))

    def test_install_harness_flag(self):
        import shutil
        shutil.rmtree(self.h / ".claude")
        rc, out, err = self.run_cb("install", "--harness", "codex")
        self.assertEqual(rc, 0, err)
        self.assertTrue((self.h / ".agents/skills/codebox-next").is_symlink())
        self.assertFalse((self.h / ".claude/skills").exists())
        self.assertTrue((self.h / ".local/bin/board").is_symlink())
        self.assertEqual(self.record()["harnesses"], ["codex"])
        rc, out, err = self.run_cb("install", "--harness", "claude")
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.record()["harnesses"], ["claude", "codex"])

    def test_install_none_detected(self):
        import shutil
        shutil.rmtree(self.h / ".claude")
        rc, out, err = self.run_cb("install")
        self.assertEqual(rc, 1)
        self.assertIn("no supported harness found", err)

    def test_bad_harness_and_no_command(self):
        self.assertNotEqual(self.run_cb("install", "--harness", "vim")[0], 0)
        self.assertNotEqual(self.run_cb()[0], 0)

    def test_bad_manifest_is_one_line_error(self):
        (self.tree / "plugins/board/skills/stray").mkdir()
        rc, out, err = self.run_cb("install")
        self.assertEqual(rc, 1)
        self.assertTrue(err.startswith("codebox: "))
        self.assertEqual(len(err.splitlines()), 1)

    def test_missing_git(self):
        with mock.patch.object(codebox.subprocess, "run", side_effect=FileNotFoundError):
            rc, out, err = self.run_cb("install")
        self.assertEqual((rc, err), (1, "codebox: needs git\n"))
        self.assertFalse((self.h / ".claude/skills/codebox-next").exists())
        self.assertFalse(codebox.record_path(self.h).exists())

    def test_relative_codebox_home(self):
        cwd = os.getcwd()
        os.chdir(self.tree.parent)
        self.addCleanup(os.chdir, cwd)
        rc, out, err = self.run_cb("install", env={"CODEBOX_HOME": "tree", "PATH": ""})
        self.assertEqual(rc, 0, err)
        self.assertTrue((self.h / ".claude/skills/codebox-next/SKILL.md").exists())
        self.assertTrue((self.h / ".local/bin/board").resolve().exists())

    def test_uninstall_leaves_repointed_link(self):
        self.run_cb("install")
        nxt = self.h / ".claude/skills/codebox-next"
        nxt.unlink()
        nxt.symlink_to(self.tmp)
        rc, out, err = self.run_cb("uninstall")
        self.assertEqual(rc, 0, err)
        self.assertTrue(nxt.is_symlink())
        self.assertIn("left", out)

    def test_uninstall_not_installed(self):
        rc, out, err = self.run_cb("uninstall")
        self.assertEqual((rc, err), (1, "codebox: not installed\n"))

    def test_uninstall_keeps_dev_home(self):
        self.run_cb("install")
        links = [l["path"] for l in self.record()["links"]]
        rc, out, err = self.run_cb("uninstall")
        self.assertEqual(rc, 0, err)
        self.assertFalse(any(os.path.lexists(p) for p in links))
        self.assertFalse(codebox.record_path(self.h).exists())
        self.assertTrue(self.tree.exists())
        self.assertIn("left", out)

    def test_uninstall_removes_default_home(self):
        fake_codebox_tree(self.h / ".codebox")
        env = {"PATH": ""}
        self.assertEqual(self.run_cb("install", env=env)[0], 0)
        rc, out, err = self.run_cb("uninstall", env=env)
        self.assertEqual(rc, 0, err)
        self.assertFalse((self.h / ".codebox").exists())

    def test_uninstall_leaves_replaced_link(self):
        self.run_cb("install")
        board = self.h / ".local/bin/board"
        board.unlink()
        board.write_text("mine")
        rc, out, err = self.run_cb("uninstall")
        self.assertEqual(rc, 0, err)
        self.assertEqual(board.read_text(), "mine")
        self.assertIn(f"left {board} (no longer codebox's link)", out)

    def test_install_refuses_non_checkout_home(self):
        self.run_cb("install")
        before = codebox.record_path(self.h).read_text()
        links = [l["path"] for l in self.record()["links"]]
        rc, out, err = self.run_cb("install", env={"CODEBOX_HOME": str(self.tmp / "missing"), "PATH": ""})
        self.assertEqual(rc, 1)
        self.assertIn("is not a codebox checkout", err)
        self.assertTrue(all(os.path.islink(p) and os.path.exists(p) for p in links))
        self.assertEqual(codebox.record_path(self.h).read_text(), before)

    def test_install_partial_failure_is_conflict_not_traceback(self):
        self.run_cb("install")
        before = codebox.record_path(self.h).read_text()
        (self.h / ".codex").mkdir()
        (self.h / ".agents").write_text("a file")
        rc, out, err = self.run_cb("install")
        self.assertEqual(rc, 1)
        self.assertIn(str(self.h / ".agents"), err)
        self.assertNotIn("Traceback", err)
        self.assertTrue(os.path.islink(self.h / ".claude/skills/codebox-next"))
        self.assertEqual(codebox.record_path(self.h).read_text(), before)

    def test_corrupt_record_is_one_line_error(self):
        p = codebox.record_path(self.h)
        p.parent.mkdir(parents=True)
        p.write_text('{"home": "x"}')
        rc, out, err = self.run_cb("uninstall")
        self.assertEqual(rc, 1)
        self.assertTrue(err.startswith("codebox: ") and err.count("\n") == 1, err)

    def test_install_accepts_matching_unrecorded_link(self):
        fork = fake_codebox_tree(self.tmp / "fork", origin="https://example.com/fork.git")
        link = self.h / ".local/bin/codebox"
        link.parent.mkdir(parents=True)
        link.symlink_to(fork / "bin/codebox")
        rc, out, err = self.run_cb("install", env={"CODEBOX_HOME": str(fork), "PATH": ""})
        self.assertEqual(rc, 0, err)

    def test_uninstall_reports_failed_home_delete(self):
        fake_codebox_tree(self.h / ".codebox")
        env = {"PATH": ""}
        self.run_cb("install", env=env)
        with mock.patch.object(codebox.shutil, "rmtree", side_effect=OSError("denied")):
            rc, out, err = self.run_cb("uninstall", env=env)
        self.assertEqual(rc, 1)
        self.assertIn("could not fully remove", err)
        self.assertFalse(codebox.record_path(self.h).exists())


class TestUpdate(Tmp):
    def setUp(self):
        super().setUp()
        self.h = self.tmp / "home"
        (self.h / ".claude").mkdir(parents=True)
        self.rel = release_repo(self.tmp)
        self.home = self.h / ".codebox"
        subprocess.run(["git", "clone", "-q", str(self.rel), str(self.home)], check=True)
        git(self.home, "checkout", "-q", "v0.1.0")

    def run_cb(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = codebox.main(list(argv), user_home=self.h, env={"PATH": ""}, which=lambda n: None)
        return rc, out.getvalue(), err.getvalue()

    def test_newest_tag(self):
        r = self.tmp / "r"
        self.assertIsNone(codebox.newest_tag(fake_codebox_tree(r)))
        for t in ("v0.9.0", "v0.10.0", "vfoo"):
            git(r, "tag", t)
        self.assertEqual(codebox.newest_tag(r), "v0.10.0")

    def test_notes_between(self):
        ch = {"1.0.0": "a", "1.1.0": "b", "1.2.0": "c"}
        self.assertEqual(codebox.notes_between(ch, "1.0.0", "1.2.0"), "b; c")
        self.assertEqual(codebox.notes_between(ch, None, "1.0.0"), "a")

    def test_version_diff(self):
        old, new = self.tmp / "old", self.tmp / "new"
        old.mkdir(), new.mkdir()
        codebox.export_tree(self.rel, "v0.1.0", old)
        codebox.export_tree(self.rel, "v0.2.0", new)
        self.assertEqual(codebox.version_diff(codebox.load_plugins(old), codebox.load_plugins(new)), [
            "  board 1.0.0 \u2192 1.1.0  next: shows blocked cards last",
            "    codebox-next 1.0.0 \u2192 1.1.0  show blocked cards last",
            "  + newplugin 0.1.0  first release"])

    def test_update_end_to_end(self):
        self.assertEqual(self.run_cb("install")[0], 0)
        rc, out, err = self.run_cb("update")
        self.assertEqual(rc, 0, err)
        self.assertEqual(codebox.release_of(self.home), "v0.2.0")
        self.assertTrue((self.h / ".claude/skills/codebox-new").exists())
        self.assertIn("codebox v0.1.0 \u2192 v0.2.0\n  board 1.0.0 \u2192 1.1.0  next: shows blocked cards last", out)
        self.assertEqual(json.loads(codebox.record_path(self.h).read_text())["release"], "v0.2.0")
        rc, out, err = self.run_cb("update")
        self.assertEqual((rc, out.strip().splitlines()[-1]), (0, "codebox v0.2.0 is up to date"))

    def test_update_not_installed(self):
        rc, out, err = self.run_cb("update")
        self.assertEqual((rc, err), (1, "codebox: not installed; run codebox install\n"))

    def test_update_refuses_dirty(self):
        self.run_cb("install")
        (self.home / "junk").write_text("x")
        rc, out, err = self.run_cb("update")
        self.assertEqual(rc, 1)
        self.assertIn("clean checkout", err)

    def test_update_refuses_branch_at_release(self):
        self.run_cb("install")
        git(self.home, "checkout", "-q", "-b", "dev")
        rc, out, err = self.run_cb("update")
        self.assertEqual(rc, 1)
        self.assertIn("clean checkout", err)
        self.assertEqual(_branch(self.home), "dev")

    def test_update_conflict_leaves_checkout(self):
        self.run_cb("install")
        before = codebox.record_path(self.h).read_text()
        links = sorted(os.readlink(l["path"]) for l in json.loads(before)["links"])
        (self.h / ".claude/skills/codebox-new").mkdir()
        rc, out, err = self.run_cb("update")
        self.assertEqual(rc, 1)
        self.assertIn("codebox-new", err)
        self.assertEqual(codebox.release_of(self.home), "v0.1.0")
        self.assertEqual(codebox.record_path(self.h).read_text(), before)
        self.assertEqual(links, sorted(os.readlink(l["path"]) for l in json.loads(before)["links"]))

    def test_update_conflict_from_newly_detected_harness(self):
        self.run_cb("install")
        before = codebox.record_path(self.h).read_text()
        (self.h / ".codex").mkdir()
        (self.h / ".agents/skills").mkdir(parents=True)
        (self.h / ".agents/skills/codebox-new").write_text("mine")
        rc, out, err = self.run_cb("update")
        self.assertEqual(rc, 1)
        self.assertIn(".agents/skills/codebox-new", err)
        self.assertEqual(codebox.release_of(self.home), "v0.1.0")
        self.assertEqual(codebox.record_path(self.h).read_text(), before)

    def test_update_rolls_back_checkout_when_install_fails(self):
        self.run_cb("install")
        with mock.patch.object(codebox, "install", return_value=1):
            self.assertEqual(self.run_cb("update")[0], 1)
        self.assertEqual(codebox.release_of(self.home), "v0.1.0")
        with mock.patch.object(codebox, "install", side_effect=ValueError("boom")):
            rc, out, err = self.run_cb("update")
        self.assertEqual((rc, err), (1, "codebox: boom\n"))
        self.assertEqual(codebox.release_of(self.home), "v0.1.0")


if __name__ == "__main__":
    unittest.main()
