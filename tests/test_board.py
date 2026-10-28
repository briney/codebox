import unittest
from datetime import datetime, timezone
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

_loader = SourceFileLoader("board", str(Path(__file__).resolve().parent.parent / "plugins" / "board" / "bin" / "board"))
_spec = importlib.util.spec_from_loader("board", _loader)
board = importlib.util.module_from_spec(_spec)
_loader.exec_module(board)
UTC = timezone.utc
S, E = board.MARK_START, board.MARK_END


def item(n, title, status, repo="o/r", state="OPEN", blocked_by=()):
    return {"number": n, "title": title, "status": status, "state": state,
            "repo": repo, "blocked_by": list(blocked_by)}


class TestCardHelpers(unittest.TestCase):
    def test_after_id(self):
        ids = ["a", "b", "c"]
        self.assertIsNone(board.after_id(ids, "a", True))
        self.assertEqual(board.after_id(ids, "c", True), "b")
        self.assertEqual(board.after_id(ids, "b", False), "b")

    def test_issue_url_repo(self):
        self.assertEqual(board.issue_url_repo("https://github.com/other/x/issues/5"), "other/x")
        self.assertIsNone(board.issue_url_repo("#5"))
        self.assertIsNone(board.issue_url_repo("5"))

    def test_blocker_ref(self):
        self.assertEqual(board.blocker_ref("o/r", 3, "o/r"), "#3")
        self.assertEqual(board.blocker_ref("o/x", 3, "o/r"), "o/x#3")


class TestBoard(unittest.TestCase):
    def test_parse_since(self):
        now = datetime(2026, 10, 27, tzinfo=UTC)
        d13 = datetime(2026, 10, 13, tzinfo=UTC)
        self.assertEqual(board.parse_since("14d", now), d13)
        self.assertEqual(board.parse_since("2w", now), d13)
        self.assertEqual(board.parse_since("36h", now), datetime(2026, 10, 25, 12, tzinfo=UTC))
        self.assertEqual(board.parse_since("2026-10-01", now), datetime(2026, 10, 1, tzinfo=UTC))
        with self.assertRaises(ValueError):
            board.parse_since("soon", now)

    def test_status_option_variants(self):
        for s in ("in-progress", "in_progress", "IN PROGRESS", "In Progress"):
            self.assertEqual(board.status_option(s), "In Progress")
        self.assertEqual(board.status_option("planned"), "Planned")

    def test_status_option_unknown(self):
        with self.assertRaises(ValueError) as cm:
            board.status_option("Backlog")
        self.assertIn("Triage", str(cm.exception))

    def test_parse_issue_ref(self):
        for s in ("12", "#12", "https://github.com/o/r/issues/12"):
            self.assertEqual(board.parse_issue_ref(s), 12)
        with self.assertRaises(ValueError):
            board.parse_issue_ref("abc")

    def test_read_repo_file(self):
        import contextlib, io, tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            self.assertIsNone(board.read_repo_file(p))
            p.write_text("hi\n")
            self.assertEqual(board.read_repo_file(p), "hi\n")
            p.write_bytes(b"\xff\xfe")
            err = io.StringIO()
            with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
                board.read_repo_file(p)
            self.assertEqual(err.getvalue(), "Could not read %s: not UTF-8 text\n" % p)

    def test_stale_section(self):
        cur = board.splice_section("", "new text")
        self.assertFalse(board.stale_section(cur, "new text"))
        self.assertTrue(board.stale_section(board.splice_section("", "old text"), "new text"))
        self.assertFalse(board.stale_section("# no markers\n", "new text"))  # no section: nothing to hint
        self.assertFalse(board.stale_section(S + "\nx\n", "new text"))      # orphan start: setup reports it

    def test_splice_append(self):
        self.assertEqual(board.splice_section("# Repo\n", "rules"), "# Repo\n\n%s\nrules\n%s\n" % (S, E))

    def test_splice_replace_idempotent(self):
        first = board.splice_section("# Repo\n", "rules")
        out = board.splice_section(first, "new")
        self.assertEqual(out.count(S), 1)
        self.assertEqual(out, "# Repo\n\n%s\nnew\n%s\n" % (S, E))
        self.assertEqual(board.splice_section(out, "new"), out)
        tail = board.splice_section("a\n\n%s\nx\n%s\nafter\n" % (S, E), "y")
        self.assertEqual(tail, "a\n\n%s\ny\n%s\nafter\n" % (S, E))

    def test_splice_orphan_start(self):
        with self.assertRaises(ValueError):
            board.splice_section("a\n%s\nold\nUSER\n" % S, "x")

    def test_parse_github_remote(self):
        for u in ("https://github.com/o/n", "https://github.com/o/n.git", "git@github.com:o/n.git",
                  "ssh://git@github.com/o/n", "ssh://git@github.com/o/n.git"):
            self.assertEqual(board.parse_github_remote(u), "o/n", u)
        for u in ("https://gitlab.com/o/n", "", "/tmp/x", "git@github.com:n"):
            self.assertIsNone(board.parse_github_remote(u), u)

    def test_splice_empty(self):
        self.assertEqual(board.splice_section("", "rules"), "%s\nrules\n%s\n" % (S, E))

    def test_claude_pointer_none(self):
        self.assertEqual(board.claude_pointer(None), "@AGENTS.md\n")

    def test_claude_pointer_present(self):
        self.assertIsNone(board.claude_pointer("See AGENTS.md\n"))

    def test_claude_pointer_append(self):
        self.assertEqual(board.claude_pointer("# x"), "# x\n@AGENTS.md\n")

    def test_render_list_groups_and_order(self):
        items = [item(1, "T", "Triage"), item(3, "P3", "Planned"), item(2, "I", "In Progress"),
                 item(4, "N", None), item(1, "P1", "Planned"), item(9, "D", "Done", state="CLOSED")]
        out = board.render_list(items, "o/r")
        self.assertEqual(out, "Planned\n  #3 P3\n  #1 P1\n\nIn Progress\n  #2 I\n\nTriage\n  #1 T\n\n(no status)\n  #4 N")
        self.assertNotIn("Done", out)
        self.assertIn("Done\n  #9 D", board.render_list(items, "o/r", show_done=True))

    def test_render_list_blocked(self):
        out = board.render_list([item(1, "A", "Planned", blocked_by=["#2"])], "o/r")
        self.assertIn("  #1 A [blocked by #2]", out)

    def test_render_list_foreign_repo(self):
        out = board.render_list([item(5, "X", "Planned", repo="brineylab/other")], "o/r")
        self.assertIn("  brineylab/other#5 X", out)

    def test_render_list_done_and_custom_status(self):
        items = [item(1, "A", "Done"), item(2, "B", "Icebox"), item(3, "C", "Triage"),
                 item(4, "D", "Review"), item(5, "E", "Icebox", state="CLOSED"), item(6, "F", None)]
        out = board.render_list(items, "o/r")
        self.assertEqual(out, "Triage\n  #3 C\n\nIcebox\n  #2 B\n\nReview\n  #4 D\n\n(no status)\n  #6 F")
        out = board.render_list(items, "o/r", show_done=True)
        self.assertTrue(out.endswith("Done\n  #1 A\n  #5 E"))

    def test_plan_status_options(self):
        S4 = board.STATUSES
        self.assertEqual(board.plan_status_options(["Todo", "In Progress", "Done"], False), S4)
        self.assertEqual(board.plan_status_options([], False), S4)
        with self.assertRaisesRegex(ValueError, "Triage"):
            board.plan_status_options(["Todo", "In Progress", "Done"], True)
        self.assertIsNone(board.plan_status_options(S4 + ["Icebox"], True))
        with self.assertRaisesRegex(ValueError, "Triage"):
            board.plan_status_options(["Backlog", "Done"], False)

    def test_missing_scope(self):
        err = ("gh: Your token has not been granted the required scopes to execute this query. "
               "The 'id' field requires one of the following scopes: ['read:project'], "
               "but your token has only been granted the: ['repo'] scopes.")
        out = '{"errors":[{"type":"INSUFFICIENT_SCOPES","message":"x"}]}'
        self.assertTrue(board.missing_scope(err, ""))
        self.assertTrue(board.missing_scope("gh: x", out))
        self.assertFalse(board.missing_scope("gh: Not Found (HTTP 404)", ""))


class TestActivity(unittest.TestCase):
    def test_status_mismatches(self):
        items = [item(1, "A", "In Progress", state="CLOSED"), item(2, "B", "Done"),
                 item(3, "C", "Done", state="CLOSED"), item(4, "D", "Planned"),
                 item(5, "E", None, state="CLOSED"), item(6, "F", "Triage", state="CLOSED"),
                 item(7, "G", "Done", repo="o/x")]
        items[5]["state_reason"] = "NOT_PLANNED"
        self.assertEqual(board.status_mismatches(items, "o/r"),
                         ["  #1 A (closed, status In Progress) -> board move 1 done",
                          "  #2 B (open, status Done) -> board move 2 in-progress",
                          "  #5 E (closed, no status) -> board move 5 done"])

    def test_unboarded(self):
        items = [item(1, "A", "Triage"), item(2, "B", "Planned", repo="o/x")]
        issues = [{"number": 1, "title": "A"}, {"number": 2, "title": "B"}, {"number": 3, "title": "C"}]
        self.assertEqual(board.unboarded(issues, items, "o/r"), ["  #2 B", "  #3 C"])

    def test_stamp_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "board-last-activity"
            self.assertIsNone(board.read_stamp(p))
            now = datetime(2026, 10, 27, 13, 5, 9, tzinfo=UTC)
            board.write_stamp(p, now)
            self.assertEqual(board.read_stamp(p), now)
            p.write_text("garbage\n")
            self.assertIsNone(board.read_stamp(p))

    def test_fmt_pr(self):
        pr = {"number": 4, "title": "Fix", "body": "Closes #1\r\n\r\nmore"}
        self.assertEqual(board.fmt_pr(pr, "merged", "2026-10-27T10:00:00Z"),
                         ["  #4 Fix (merged 2026-10-27)", "    Closes #1", "", "    more"])
        self.assertEqual(board.fmt_pr({"number": 5, "title": "T", "body": None}, "updated", "2026-10-26"),
                         ["  #5 T (updated 2026-10-26)"])

    def test_section(self):
        self.assertEqual(board.section("Open PRs updated", []), "Open PRs updated\n  (none)")
        self.assertEqual(board.section("X", ["  a", "  b"]), "X\n  a\n  b")


if __name__ == "__main__":
    unittest.main()
