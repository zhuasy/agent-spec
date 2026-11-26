# HIDDEN ACCEPTANCE TESTS - EVAL-CANARY-7f3a9c1e-quality
# Never show this file to the spec-writer, implementer, reader or judge.
# Class name prefix sets the category: Core / Edge / Keep.
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, "todo.json")

    def todo(self, *argv):
        p = subprocess.run(
            [sys.executable, "-m", "todo", "--file", self.path, *argv],
            capture_output=True, text=True, timeout=20,
        )
        return p.returncode, p.stdout, p.stderr

    def ok(self, *argv):
        code, out, err = self.todo(*argv)
        self.assertEqual(code, 0, "todo %s failed: %s" % (" ".join(argv), err))
        return out

    def lines(self, *argv):
        return [l for l in self.ok(*argv).splitlines() if l.strip()]

    def tag_counts(self):
        pairs = []
        for line in self.lines("tags"):
            m = re.match(r"^\s*#?([A-Za-z0-9-]+)\s*:?\s+(\d+)\s*$", line)
            self.assertIsNotNone(m, "cannot read tags line %r" % line)
            pairs.append((m.group(1), int(m.group(2))))
        return pairs


class CoreTags(Base):
    def test_add_with_tags_shows_them_in_list(self):
        self.ok("add", "buy milk", "--tag", "home", "--tag", "errands")
        (line,) = self.lines("list")
        self.assertTrue(line.startswith("[ ] 1 buy milk"), line)
        self.assertIn("#home", line.split())
        self.assertIn("#errands", line.split())

    def test_list_filters_by_tag(self):
        self.ok("add", "buy milk", "--tag", "home")
        self.ok("add", "write report", "--tag", "work")
        self.ok("add", "no tags here")
        lines = self.lines("list", "--tag", "home")
        self.assertEqual(len(lines), 1)
        self.assertIn("buy milk", lines[0])

    def test_two_tags_on_list_means_both(self):
        self.ok("add", "a", "--tag", "home")
        self.ok("add", "b", "--tag", "home", "--tag", "urgent")
        self.ok("add", "c", "--tag", "urgent")
        lines = self.lines("list", "--tag", "home", "--tag", "urgent")
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("[ ] 2 b"), lines[0])

    def test_tags_ignore_case_and_are_shown_lowercase(self):
        self.ok("add", "buy milk", "--tag", "Home")
        (line,) = self.lines("list", "--tag", "HOME")
        self.assertIn("#home", line.split())

    def test_tags_command_counts_open_tasks_biggest_first(self):
        self.ok("add", "a", "--tag", "work")
        self.ok("add", "b", "--tag", "home")
        self.ok("add", "c", "--tag", "home", "--tag", "work")
        self.ok("add", "d", "--tag", "home")
        self.assertEqual(self.tag_counts(), [("home", 3), ("work", 2)])

    def test_invalid_tag_is_error_and_nothing_saved(self):
        for bad in ("to do", "#home", "a_b"):
            code, out, err = self.todo("add", "task", "--tag", bad)
            self.assertEqual(code, 1, "tag %r should be rejected" % bad)
            self.assertTrue(err.strip(), "expected a message on stderr")
        self.assertEqual(self.lines("list", "--all"), [])


class EdgeTags(Base):
    def test_all_combines_with_tag_filter(self):
        self.ok("add", "a", "--tag", "home")
        self.ok("add", "b", "--tag", "home")
        self.ok("add", "c", "--tag", "work")
        self.ok("done", "1")
        self.assertEqual(len(self.lines("list", "--tag", "home")), 1)
        lines = self.lines("list", "--tag", "home", "--all")
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("[x] 1 a"), lines[0])

    def test_same_tag_twice_is_stored_once(self):
        self.ok("add", "a", "--tag", "home", "--tag", "Home")
        (line,) = self.lines("list")
        self.assertEqual(line.split().count("#home"), 1, line)
        self.assertEqual(self.tag_counts(), [("home", 1)])

    def test_tags_command_ignores_done_tasks(self):
        self.ok("add", "a", "--tag", "home")
        self.ok("add", "b", "--tag", "home")
        self.ok("add", "c", "--tag", "old")
        self.ok("done", "1")
        self.ok("done", "3")
        counts = dict(self.tag_counts())
        self.assertEqual(counts.get("home"), 1)
        # a tag with no open tasks may be left out or shown as 0 (brief does not say)
        self.assertIn(counts.get("old", 0), (0,))

    def test_tags_command_on_empty_store_succeeds(self):
        self.assertEqual(self.todo("tags")[0], 0)

    def test_digits_and_dashes_are_valid(self):
        self.ok("add", "a", "--tag", "q3-2026")
        self.assertEqual(len(self.lines("list", "--tag", "q3-2026")), 1)


class KeepOldBehaviour(Base):
    OLD_FILE = {
        "next_id": 3,
        "tasks": [
            {"id": 1, "title": "old open", "done": False},
            {"id": 2, "title": "old done", "done": True},
        ],
    }

    def write_old(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.OLD_FILE, f)

    def test_old_file_lists_exactly_as_before(self):
        self.write_old()
        self.assertEqual(self.ok("list", "--all").splitlines(),
                         ["[ ] 1 old open", "[x] 2 old done"])

    def test_old_file_with_tag_filter_does_not_crash(self):
        self.write_old()
        self.assertEqual(self.lines("list", "--tag", "home", "--all"), [])
        self.assertEqual(self.todo("tags")[0], 0)

    def test_old_file_accepts_new_tagged_task(self):
        self.write_old()
        self.ok("add", "new one", "--tag", "home")
        lines = self.lines("list")
        self.assertEqual(lines[0], "[ ] 1 old open")
        self.assertTrue(lines[1].startswith("[ ] 3 new one"), lines[1])
        self.assertEqual(len(self.lines("list", "--tag", "home")), 1)

    def test_untagged_task_line_unchanged(self):
        self.assertEqual(self.ok("add", "buy milk"), "added 1\n")
        self.assertEqual(self.ok("list").splitlines(), ["[ ] 1 buy milk"])

    def test_done_and_errors_unchanged(self):
        self.ok("add", "buy milk", "--tag", "home")
        self.assertEqual(self.ok("done", "1"), "done 1\n")
        self.assertEqual(self.todo("done", "9")[0], 1)
        self.assertEqual(self.todo("add", "  ")[0], 1)


if __name__ == "__main__":
    unittest.main()
