# HIDDEN ACCEPTANCE TESTS - EVAL-CANARY-7f3a9c1e-quality
# Never show this file to the spec-writer, implementer, reader or judge.
import json
import os
import subprocess
import sys
import tempfile
import unittest


def line(path, status=200, ms=10, method="GET"):
    return "2026-03-01T12:00:01Z %s %s %d %dms" % (method, path, status, ms)


class Base(unittest.TestCase):
    def run_raw(self, argv, stdin=None):
        return subprocess.run([sys.executable, "logsum.py", *argv], input=stdin,
                              capture_output=True, text=True, timeout=20)

    def summarise(self, lines, *extra):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "access.log")
            with open(path, "w", encoding="utf-8") as f:
                f.write("".join(l + "\n" for l in lines))
            p = self.run_raw([path, *extra])
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)


class CoreSummary(Base):
    def test_counts_and_shape(self):
        out = self.summarise([
            line("/a"), line("/a", 404), line("/a", 500), line("/b", 503), line("/b", 201),
        ])
        self.assertEqual(out["requests"], 5)
        self.assertEqual(out["errors"], 2)
        self.assertEqual(out["skipped"], 0)
        self.assertEqual([(r["path"], r["count"]) for r in out["by_path"]], [("/a", 3), ("/b", 2)])
        for row in out["by_path"]:
            self.assertEqual(set(row), {"path", "count", "p95_ms"})

    def test_query_string_is_stripped(self):
        out = self.summarise([line("/api/users?id=7"), line("/api/users?id=8"), line("/api/users")])
        self.assertEqual(out["by_path"], [{"path": "/api/users", "count": 3, "p95_ms": 10}])

    def test_p95_is_nearest_rank(self):
        out = self.summarise([line("/x", ms=m) for m in range(20, 0, -1)])
        self.assertEqual(out["by_path"][0]["p95_ms"], 19)
        out = self.summarise([line("/x", ms=m * 10) for m in range(1, 101)])
        self.assertEqual(out["by_path"][0]["p95_ms"], 950)
        out = self.summarise([line("/x", ms=5), line("/x", ms=100), line("/x", ms=7)])
        self.assertEqual(out["by_path"][0]["p95_ms"], 100)

    def test_top_default_is_ten_and_flag_limits(self):
        lines = []
        for i in range(15):
            lines += [line("/p%02d" % i)] * (15 - i)
        out = self.summarise(lines)
        self.assertEqual(len(out["by_path"]), 10)
        self.assertEqual(out["by_path"][0], {"path": "/p00", "count": 15, "p95_ms": 10})
        out5 = self.summarise(lines, "--top", "5")
        self.assertEqual([r["path"] for r in out5["by_path"]],
                         ["/p00", "/p01", "/p02", "/p03", "/p04"])

    def test_garbage_lines_are_skipped_and_counted(self):
        out = self.summarise([
            line("/a"),
            "2026-03-01T12:00:04Z GET /api/us",
            "\x00\x00 not a log line at all",
            "2026-03-01T12:00:04Z GET /a abc 12ms",
            "2026-03-01T12:00:04Z GET /a 200 fastms",
            line("/a", 500),
        ])
        self.assertEqual((out["requests"], out["errors"], out["skipped"]), (2, 1, 4))
        self.assertEqual(out["by_path"], [{"path": "/a", "count": 2, "p95_ms": 10}])


class EdgeCli(Base):
    def test_missing_file_exits_2_without_traceback(self):
        self.assertEqual(self.summarise([line("/a")])["requests"], 1)
        p = self.run_raw(["/no/such/dir/access.log"])
        self.assertEqual(p.returncode, 2)
        self.assertTrue(p.stderr.strip())
        self.assertNotIn("Traceback", p.stderr)

    def test_dash_reads_stdin(self):
        p = self.run_raw(["-"], stdin=line("/a") + "\n" + line("/b?x=1", 502) + "\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout)
        self.assertEqual((out["requests"], out["errors"]), (2, 1))

    def test_empty_file(self):
        out = self.summarise([])
        self.assertEqual(out, {"requests": 0, "errors": 0, "skipped": 0, "by_path": []})

    def test_ties_are_alphabetical(self):
        out = self.summarise([line("/b"), line("/c"), line("/a"), line("/c"), line("/a"), line("/b")])
        self.assertEqual([r["path"] for r in out["by_path"]], ["/a", "/b", "/c"])

    def test_totals_cover_the_whole_file_not_just_top(self):
        out = self.summarise([line("/a"), line("/a"), line("/b", 500), line("/c", 500)],
                             "--top", "1")
        self.assertEqual(len(out["by_path"]), 1)
        self.assertEqual((out["requests"], out["errors"]), (4, 2))

    def test_4xx_is_not_an_error_and_599_is(self):
        out = self.summarise([line("/a", 499), line("/a", 400), line("/a", 599)])
        self.assertEqual(out["errors"], 1)

    def test_sample_file(self):
        p = self.run_raw([os.path.join("sample", "access.log")])
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout)
        self.assertEqual((out["requests"], out["errors"], out["skipped"]), (9, 2, 1))
        self.assertEqual(out["by_path"][0]["count"], 3)
        self.assertEqual(out["by_path"][0]["path"], "/api/users")
        self.assertEqual(out["by_path"][0]["p95_ms"], 2004)


class KeepExisting(Base):
    def test_linecount_still_works(self):
        p = subprocess.run([sys.executable, "linecount.py", os.path.join("sample", "access.log")],
                           capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(p.stdout.startswith("10 "))


if __name__ == "__main__":
    unittest.main()
