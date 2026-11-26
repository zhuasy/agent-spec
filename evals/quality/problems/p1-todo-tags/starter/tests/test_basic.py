import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from todo.cli import main
from todo.store import Store


def run(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--file", path, *argv])
    return code, out.getvalue(), err.getvalue()


class BasicTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, "todo.json")

    def test_add_list_done(self):
        self.assertEqual(run(self.path, "add", "buy milk")[1], "added 1\n")
        self.assertEqual(run(self.path, "add", "call mum")[1], "added 2\n")
        self.assertEqual(run(self.path, "done", "1")[0], 0)
        self.assertEqual(run(self.path, "list")[1], "[ ] 2 call mum\n")
        self.assertEqual(
            run(self.path, "list", "--all")[1], "[x] 1 buy milk\n[ ] 2 call mum\n"
        )

    def test_empty_title_is_an_error(self):
        code, out, err = run(self.path, "add", "   ")
        self.assertEqual(code, 1)
        self.assertIn("error", err)
        self.assertEqual(Store(self.path).list(include_done=True), [])

    def test_done_unknown_id(self):
        self.assertEqual(run(self.path, "done", "9")[0], 1)


if __name__ == "__main__":
    unittest.main()
