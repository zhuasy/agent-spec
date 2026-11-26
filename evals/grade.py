#!/usr/bin/env python3
"""Grade one run of the agent-spec evals.

Usage: grade.py RUNS_DIR [--json OUT.json]

RUNS_DIR has one folder for each case in evals.json: RUNS_DIR/<id>/spec.md, glossary.md, spec.sources.md.
The grader does not trust the sources file that the agent wrote. It checks the facts in the spec against the
brief, and checks that each quote in the agent's sources file is in the brief.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "agent-spec" / "scripts"


def norm(text):
    text = text.lower().translate(str.maketrans("‘’“”", "''\"\""))
    return re.sub(r"\s+", " ", text).strip()


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def forged_quotes(sources, brief):
    """Quoted sentences in the agent's sources file that are not in the brief."""
    quote = " ".join(l.lstrip("> ").strip() for l in sources.split("\n") if l.startswith(">"))
    brief = norm(brief)
    bad = []
    for sentence in re.split(r"(?<=[.?!])\s+", quote):
        s = norm(sentence).strip(" .?!\"'")
        if len(s) > 3 and s not in brief:
            bad.append(sentence.strip())
    return bad


def grade(case, folder):
    brief = HERE / "briefs" / f"{case['id']}.md"
    spec = folder / "spec.md"
    if not spec.exists():
        return [("spec.md exists", False, "missing")]
    text = spec.read_text()
    results = []

    code, out = run(["bash", str(SCRIPTS / "lint.sh"), str(spec)])
    results.append(("lint", code == 0, "" if code == 0 else out[-600:]))

    code, out = run([sys.executable, str(SCRIPTS / "spec_lint.py"), str(spec), "--sources", str(brief)])
    s10 = [l.split(" S10 ", 1)[1].split(" is not", 1)[0] for l in out.split("\n") if " S10 " in l]
    results.append(("grounded", not s10, "not in the brief: " + ", ".join(s10) if s10 else ""))

    sources = folder / "spec.sources.md"
    if sources.exists():
        bad = forged_quotes(sources.read_text(), brief.read_text())
        results.append(("quotes", not bad, "not in the brief: " + " | ".join(bad)[:400] if bad else ""))
    else:
        results.append(("quotes", False, "spec.sources.md is missing"))

    for pattern in case.get("must_match", []):
        results.append((f"has /{pattern}/", re.search(pattern, text) is not None, ""))
    for pattern in case.get("must_not_match", []):
        m = re.search(pattern, text)
        results.append((f"lacks /{pattern}/", m is None, m.group(0) if m else ""))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs")
    ap.add_argument("--json")
    args = ap.parse_args()
    cases = json.loads((HERE / "evals.json").read_text())["evals"]
    report, passed, total = {}, 0, 0
    for case in cases:
        results = grade(case, Path(args.runs) / case["id"])
        ok = sum(1 for _, good, _ in results if good)
        passed, total = passed + ok, total + len(results)
        print(f"\n{case['id']}: {ok}/{len(results)}")
        for name, good, detail in results:
            print(f"  {'PASS' if good else 'FAIL'}  {name}" + (f"\n        {detail}" if detail else ""))
        report[case["id"]] = [{"check": n, "pass": g, "detail": d} for n, g, d in results]
    print(f"\n{passed}/{total} checks pass")
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
