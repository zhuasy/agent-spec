#!/usr/bin/env python3
"""Prove every problem is sound, and record which hidden tests are new behaviour.

For each problem:
  1. the starter's own tests pass on the starter;
  2. hidden tests are run on the untouched starter: the ones that FAIL are
     'new' (they need the change), the ones that PASS are 'regression'
     (behaviour that must survive). Every Core test must be 'new';
  3. the reference (starter + reference/ overlay) passes every hidden test and
     every starter test;
  4. the quiz key is well formed; the canary string is in every secret file
     and in nothing a role is given.

Writes problems/<name>/baseline.json. Exit code 1 on any failure.

    python3 scripts/verify_problems.py [problem ...]
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import common as c  # noqa: E402


def check_quiz(pdir, problems):
    quiz = c.load_json(os.path.join(pdir, "quiz.json"))
    seen = set()
    for part in ("full", "skim"):
        if not quiz.get(part):
            problems.append("quiz: no %s questions" % part)
        for item in quiz.get(part, []):
            if item["id"] in seen:
                problems.append("quiz: duplicate id %s" % item["id"])
            seen.add(item["id"])
            letters = set(item["options"])
            if len(item["correct"]) != 1 or not set(item["correct"]) <= letters:
                problems.append("quiz %s: bad correct" % item["id"])
            if not set(item["invented"]) <= letters - set(item["correct"]):
                problems.append("quiz %s: bad invented" % item["id"])
    return len(quiz["full"]), len(quiz["skim"])


def verify(name):
    pdir = c.problem_dir(name)
    problems = []
    starter = os.path.join(pdir, "starter")

    on_starter = c.run_test_modules(starter, c.hidden_modules(pdir))
    visible_starter = c.run_test_modules(starter, c.visible_modules(pdir))
    kind = {t["id"]: ("regression" if t["status"] == "pass" else "new") for t in on_starter}
    for t in on_starter:
        if t["category"] == "core" and t["status"] == "pass":
            problems.append("Core test passes on the untouched starter: %s" % t["id"])
    if not all(t["status"] == "pass" for t in visible_starter):
        problems.append("starter's own tests do not pass on the starter")

    c.dump_json(os.path.join(pdir, "baseline.json"), {
        "note": "Written by verify_problems.py. 'new' = fails on the untouched starter.",
        "kind": kind})

    with tempfile.TemporaryDirectory(prefix="spec-eval-ref-") as tmp:
        ref = os.path.join(tmp, "repo")
        c.copy_tree(starter, ref)
        c.copy_tree(os.path.join(pdir, "reference"), ref)
        on_ref = c.score_repo(pdir, ref)
    for t in on_ref["hidden"] + on_ref["visible"]:
        if t["status"] != "pass":
            problems.append("reference fails %s: %s" % (t["id"], t["detail"][-300:]))

    n_full, n_skim = check_quiz(pdir, problems)

    for secret in ("hidden", "reference"):
        for base, _, files in os.walk(os.path.join(pdir, secret)):
            for f in files:
                if f.endswith(".py") and c.CANARY not in c.read_text(os.path.join(base, f)):
                    problems.append("no canary in %s/%s" % (secret, f))
    if c.CANARY not in c.read_text(os.path.join(pdir, "quiz.json")):
        problems.append("no canary in quiz.json")
    if c.has_canary(starter) or c.CANARY in c.read_text(os.path.join(pdir, "brief.md")):
        problems.append("canary found in starter or brief")

    n = len(on_starter)
    fails = sum(t["status"] != "pass" for t in on_starter)
    core = [t for t in on_starter if t["category"] == "core"]
    print("%-24s hidden tests: %2d | on starter: %2d fail, %2d pass (core %d/%d fail) | "
          "on reference: %2d/%d pass | starter's own tests: %d/%d on starter, %d/%d on reference | "
          "quiz %d+%d | %s"
          % (os.path.basename(pdir), n, fails, n - fails,
             sum(t["status"] != "pass" for t in core), len(core),
             on_ref["summary"]["hidden_passed"], n,
             sum(t["status"] == "pass" for t in visible_starter), len(visible_starter),
             sum(t["status"] == "pass" for t in on_ref["visible"]), len(on_ref["visible"]),
             n_full, n_skim, "OK" if not problems else "PROBLEMS"))
    for p in problems:
        print("    - " + p)
    return not problems


def main(argv):
    names = argv or c.list_problems()
    ok = [verify(n) for n in names]
    print("all problems verified" if all(ok) else "VERIFICATION FAILED")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
