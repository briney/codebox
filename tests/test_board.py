import unittest
from datetime import datetime, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path

board = SourceFileLoader("board", str(Path(__file__).resolve().parent.parent / "bin" / "board")).load_module()
UTC = timezone.utc
S, E = board.MARK_START, board.MARK_END


def item(n, title, status, repo="o/r", state="OPEN", blocked_by=()):
    return {"number": n, "title": title, "status": status, "state": state,
            "repo": repo, "blocked_by": list(blocked_by)}


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


if __name__ == "__main__":
    unittest.main()
