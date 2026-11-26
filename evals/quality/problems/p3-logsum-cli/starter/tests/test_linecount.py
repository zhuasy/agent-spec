import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import linecount


class LinecountTest(unittest.TestCase):
    def test_counts(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.txt")
            with open(path, "w") as f:
                f.write("one\ntwo\n")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(linecount.main([path]), 0)
            self.assertEqual(out.getvalue(), "2 %s\n" % path)

    def test_missing_file(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(linecount.main(["/no/such/file"]), 2)
        self.assertIn("linecount:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
