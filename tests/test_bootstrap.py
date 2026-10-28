import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import REPO, codebox, fake_codebox_tree, git, release_repo


def run(home, src):
    env = {"HOME": str(home), "CODEBOX_REPO": str(src), "PATH": os.environ["PATH"]}
    return subprocess.run(["bash", str(REPO / "bootstrap.sh")], env=env, capture_output=True, text=True)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        self.home = self.tmp / "h"
        self.home.mkdir()

    def test_fresh(self):
        r = run(self.home, release_repo(self.tmp))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(codebox.release_of(self.home / ".codebox"), "v0.2.0")
        link = self.home / ".local/bin/codebox"
        self.assertEqual(link.resolve(), (self.home / ".codebox/bin/codebox").resolve())
        self.assertIn("codebox install", r.stdout)

    def test_no_tags(self):
        r = run(self.home, fake_codebox_tree(self.tmp / "src"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("no release tags", r.stderr)
        self.assertFalse((self.home / ".codebox").exists())

    def test_rerun_keeps_checkout(self):
        src = release_repo(self.tmp)
        run(self.home, src)
        git(self.home / ".codebox", "checkout", "-q", "v0.1.0")
        r = run(self.home, src)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(codebox.release_of(self.home / ".codebox"), "v0.1.0")
        self.assertIn("codebox update", r.stdout)

    def test_refuses_foreign_bin(self):
        f = self.home / ".local/bin/codebox"
        f.parent.mkdir(parents=True)
        f.write_text("mine")
        r = run(self.home, release_repo(self.tmp))
        self.assertEqual(r.returncode, 1)
        self.assertEqual(f.read_text(), "mine")

    def test_truncated_download_does_nothing(self):
        text = (REPO / "bootstrap.sh").read_text()
        env = {"HOME": str(self.home), "CODEBOX_REPO": str(release_repo(self.tmp)), "PATH": os.environ["PATH"]}
        r = subprocess.run(["bash"], input=text[: len(text) * 8 // 10], env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.home / ".codebox").exists())


if __name__ == "__main__":
    unittest.main()
