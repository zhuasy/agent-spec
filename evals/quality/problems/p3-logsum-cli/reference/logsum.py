#!/usr/bin/env python3
"""logsum.py FILE|- [--top N] - summarise an access log as JSON."""
# reference implementation - EVAL-CANARY-7f3a9c1e-quality - never show to a role
import argparse
import json
import math
import sys


def parse_line(line):
    parts = line.split()
    if len(parts) != 5:
        return None
    _, _, target, status, duration = parts
    if not (status.isdigit() and len(status) == 3):
        return None
    if not (duration.endswith("ms") and duration[:-2].isdigit()):
        return None
    return target.split("?", 1)[0], int(status), int(duration[:-2])


def p95(values):
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def summarise(lines, top):
    requests = errors = skipped = 0
    durations = {}
    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            skipped += 1
            continue
        path, status, ms = parsed
        requests += 1
        if status >= 500:
            errors += 1
        durations.setdefault(path, []).append(ms)
    rows = [{"path": p, "count": len(d), "p95_ms": p95(d)} for p, d in durations.items()]
    rows.sort(key=lambda r: (-r["count"], r["path"]))
    return {"requests": requests, "errors": errors, "skipped": skipped, "by_path": rows[:top]}


def main(argv):
    parser = argparse.ArgumentParser(prog="logsum.py")
    parser.add_argument("file")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args(argv)
    if args.file == "-":
        result = summarise(sys.stdin, args.top)
    else:
        try:
            with open(args.file, encoding="utf-8", errors="replace") as f:
                result = summarise(f, args.top)
        except OSError as exc:
            print("logsum: %s: %s" % (args.file, exc.strerror), file=sys.stderr)
            return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
