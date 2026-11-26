# HIDDEN ACCEPTANCE TESTS - EVAL-CANARY-7f3a9c1e-quality
# Never show this file to the spec-writer, implementer, reader or judge.
#
# "now" is 2026-06-01. The retention default is undecided in the brief (30 or
# 90 days), so default-setting tests only use tickets closed 200 days ago
# (archived under either) or 5 days ago (kept under either).
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

NOW = "2026-06-01T00:00:00Z"
D200 = "2025-11-13T00:00:00Z"   # 200 days before NOW
D100 = "2026-02-21T00:00:00Z"   # 100 days before NOW
D15 = "2026-05-17T00:00:00Z"    # 15 days before NOW
D5 = "2026-05-27T00:00:00Z"     # 5 days before NOW


def ticket(tid, title, status="closed", closed_at=D200, **extra):
    t = {"id": tid, "title": title, "status": status,
         "created_at": "2025-10-01T08:00:00Z", "closed_at": closed_at}
    t.update(extra)
    return t


class Base(unittest.TestCase):
    TICKETS = []

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.data = os.path.join(self.dir.name, "tickets.json")
        with open(self.data, "w", encoding="utf-8") as f:
            json.dump(self.TICKETS, f)

    def cli(self, *argv, config=None, now=NOW):
        full = [sys.executable, "-m", "helpdesk", "--data", self.data, "--now", now]
        if config is not None:
            path = os.path.join(self.dir.name, "config.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f)
            full += ["--config", path]
        p = subprocess.run(full + list(argv), capture_output=True, text=True, timeout=20)
        return p.returncode, p.stdout, p.stderr

    def archive(self, **kw):
        code, out, err = self.cli("archive", **kw)
        self.assertEqual(code, 0, err)
        m = re.search(r"\d+", out)
        self.assertIsNotNone(m, "archive printed no count: %r" % out)
        return int(m.group())

    def ids(self, *argv):
        code, out, err = self.cli("search", *argv)
        self.assertEqual(code, 0, err)
        return [int(l.split("\t")[0]) for l in out.splitlines() if l.strip()]


class CoreArchive(Base):
    TICKETS = [
        ticket(1, "Old closed"),
        ticket(2, "Fresh closed", closed_at=D5),
        ticket(3, "Still open", status="open", closed_at=None),
    ]

    def test_old_closed_ticket_is_archived_and_count_printed(self):
        self.assertEqual(self.archive(), 1)
        self.assertEqual(self.ids(), [2, 3])

    def test_include_archived_brings_it_back(self):
        self.archive()
        self.assertEqual(self.ids("--include-archived"), [1, 2, 3])

    def test_show_still_works_for_archived(self):
        self.archive()
        code, out, err = self.cli("show", "1")
        self.assertEqual(code, 0, err)
        shown = json.loads(out)
        self.assertEqual((shown["id"], shown["title"], shown["closed_at"]), (1, "Old closed", D200))

    def test_setting_shortens_the_period(self):
        with open(self.data, "w", encoding="utf-8") as f:
            json.dump([ticket(1, "a", closed_at=D15), ticket(2, "b", closed_at=D5)], f)
        self.assertEqual(self.archive(config={"archive_after_days": 10}), 1)
        self.assertEqual(self.ids(), [2])

    def test_setting_lengthens_the_period(self):
        with open(self.data, "w", encoding="utf-8") as f:
            json.dump([ticket(1, "a", closed_at=D200), ticket(2, "b", closed_at=D100)], f)
        self.assertEqual(self.archive(config={"archive_after_days": 150}), 1)
        self.assertEqual(self.ids(), [2])


class EdgeArchive(Base):
    TICKETS = [
        ticket(1, "Old closed"),
        ticket(2, "On legal hold", legal_hold=True),
        ticket(3, "Reopened, stale closed_at", status="open"),
        ticket(4, "Old closed too"),
    ]

    def test_legal_hold_is_never_archived(self):
        self.archive()
        self.assertIn(2, self.ids())
        self.archive(config={"archive_after_days": 1})
        self.assertIn(2, self.ids())

    def test_reopened_ticket_is_not_archived(self):
        self.assertEqual(self.archive(), 2)
        self.assertEqual(self.ids(), [2, 3])

    def test_reclose_restarts_the_clock(self):
        self.cli("reopen", "1")
        self.cli("close", "1", now=D5)
        self.assertEqual(self.archive(), 1)
        self.assertEqual(self.ids(), [1, 2, 3])

    def test_second_run_archives_nothing_more(self):
        self.assertEqual(self.archive(), 2)
        self.assertEqual(self.archive(), 0)
        self.assertEqual(self.ids("--include-archived"), [1, 2, 3, 4])

    def test_status_filter_combines_with_archive_flag(self):
        self.archive()
        self.assertEqual(self.ids("--status", "closed"), [2])
        self.assertEqual(self.ids("--status", "closed", "--include-archived"), [1, 2, 4])
        self.assertEqual(self.ids("--text", "old closed"), [])

    def test_nothing_is_deleted(self):
        self.archive()
        for tid, title in ((1, "Old closed"), (4, "Old closed too")):
            code, out, _ = self.cli("show", str(tid))
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["title"], title)


class KeepExisting(Base):
    TICKETS = [
        ticket(1, "Printer on fire", status="open", closed_at=None),
        ticket(2, "Password reset", closed_at=D5),
    ]

    def test_search_output_format_unchanged(self):
        code, out, _ = self.cli("search")
        self.assertEqual(out, "1\topen\tPrinter on fire\n2\tclosed\tPassword reset\n")
        self.assertEqual(self.cli("search", "--status", "closed")[1], "2\tclosed\tPassword reset\n")

    def test_overdue_and_sla_setting_unchanged(self):
        self.assertEqual(self.cli("overdue")[1], "1\n")
        self.assertEqual(self.cli("overdue", config={"sla_hours": 48, "page_size": 10})[1], "1\n")

    def test_unknown_setting_still_rejected(self):
        code, _, err = self.cli("overdue", config={"slaa_hours": 2})
        self.assertEqual(code, 1)
        self.assertIn("unknown setting", err)

    def test_close_reopen_unchanged(self):
        self.cli("close", "1")
        self.assertEqual(json.loads(self.cli("show", "1")[1])["closed_at"], NOW)
        self.cli("reopen", "1")
        self.assertEqual(json.loads(self.cli("show", "1")[1])["status"], "open")


if __name__ == "__main__":
    unittest.main()
