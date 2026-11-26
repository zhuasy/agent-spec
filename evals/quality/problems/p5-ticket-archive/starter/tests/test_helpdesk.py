import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from helpdesk.__main__ import main

TICKETS = [
    {"id": 1, "title": "Printer on fire", "status": "open",
     "created_at": "2026-05-01T08:00:00Z", "closed_at": None},
    {"id": 2, "title": "Password reset", "status": "closed",
     "created_at": "2026-05-20T08:00:00Z", "closed_at": "2026-05-21T08:00:00Z"},
    {"id": 3, "title": "New laptop", "status": "open",
     "created_at": "2026-05-31T20:00:00Z", "closed_at": None, "legal_hold": True},
]


class HelpdeskTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.data = os.path.join(self.dir.name, "tickets.json")
        with open(self.data, "w") as f:
            json.dump(TICKETS, f)

    def run_cli(self, *argv, config=None):
        full = ["--data", self.data, "--now", "2026-06-01T00:00:00Z"]
        if config is not None:
            path = os.path.join(self.dir.name, "config.json")
            with open(path, "w") as f:
                json.dump(config, f)
            full += ["--config", path]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(full + list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_search(self):
        self.assertEqual(self.run_cli("search", "--status", "closed")[1],
                         "2\tclosed\tPassword reset\n")

    def test_close_and_reopen(self):
        self.run_cli("close", "1")
        self.assertEqual(json.loads(self.run_cli("show", "1")[1])["closed_at"],
                         "2026-06-01T00:00:00Z")
        self.run_cli("reopen", "1")
        self.assertEqual(json.loads(self.run_cli("show", "1")[1])["status"], "open")

    def test_overdue_uses_sla_setting(self):
        self.assertEqual(self.run_cli("overdue")[1], "1\n")
        self.assertEqual(self.run_cli("overdue", config={"sla_hours": 2})[1], "1\n3\n")

    def test_unknown_setting_is_rejected(self):
        code, _, err = self.run_cli("overdue", config={"slaa_hours": 2})
        self.assertEqual(code, 1)
        self.assertIn("unknown setting", err)


if __name__ == "__main__":
    unittest.main()
