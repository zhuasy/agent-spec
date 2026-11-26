#!/usr/bin/env python3
"""linecount.py FILE... - print the number of lines in each file."""
import sys


def main(argv):
    if not argv:
        print("usage: linecount.py FILE...", file=sys.stderr)
        return 2
    status = 0
    for name in argv:
        try:
            with open(name, encoding="utf-8", errors="replace") as f:
                print("%d %s" % (sum(1 for _ in f), name))
        except OSError as exc:
            print("linecount: %s: %s" % (name, exc.strerror), file=sys.stderr)
            status = 2
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
