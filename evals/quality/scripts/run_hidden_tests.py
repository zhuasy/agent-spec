#!/usr/bin/env python3
"""Run the hidden acceptance tests (and the starter's own tests) against an
implementation. No model.

    python3 scripts/run_hidden_tests.py RUN_DIR
        scores every 2_implementer/impl_K/ and writes scores/outcome_impl_K.json

    python3 scripts/run_hidden_tests.py --problem p3 --repo DIR [--out FILE]
        scores any repo folder (used for checks outside a run)

The implementation is copied to a temporary folder first; the hidden tests are
never written into the run folder. Each test runs in its own process with a
timeout, so one hang or crash costs one test. WARNING: this executes code
written by the implementer agent. Run it where that is acceptable.

Reported for each implementation:
  new_behaviour_pass_rate  hidden tests that fail on the untouched starter
  regression_pass_rate     hidden tests that pass on the untouched starter
  visible_pass_rate        the starter's own tests (pristine copies)
  plus what the implementer wrote in IMPL_NOTES.json: number of guesses, and
  contradictions / false statements about the repo whose quotes are really in
  the spec.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import common as c  # noqa: E402


def read_notes(work, spec_norm):
    path = os.path.join(work, "IMPL_NOTES.json")
    try:
        notes = c.load_json(path)
    except ValueError:
        notes = None
    if not isinstance(notes, dict):
        return {"notes_missing": True, "finished": None, "guesses": None,
                "contradictions_verified": None, "wrong_about_repo_verified": None}

    def items(key):
        value = notes.get(key, [])
        return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []

    contradictions = items("contradictions")
    wrong = items("wrong_about_repo")
    return {
        "notes_missing": False,
        "finished": bool(notes.get("finished")),
        "guesses": len(items("guesses")),
        "guess_list": items("guesses"),
        "contradictions_reported": len(contradictions),
        "contradictions_verified": sum(
            c.quote_found(x.get("quote_a"), spec_norm) and c.quote_found(x.get("quote_b"), spec_norm)
            and c.normalise(x.get("quote_a")) != c.normalise(x.get("quote_b"))
            for x in contradictions),
        "wrong_about_repo_reported": len(wrong),
        "wrong_about_repo_verified": sum(c.quote_found(x.get("quote"), spec_norm) for x in wrong),
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?")
    ap.add_argument("--problem")
    ap.add_argument("--repo")
    ap.add_argument("--out")
    args = ap.parse_args(argv)

    if args.problem and args.repo:
        result = c.score_repo(c.problem_dir(args.problem), args.repo)
        if args.out:
            c.dump_json(args.out, result)
        print(json.dumps(result["summary"], indent=2))
        for t in result["hidden"] + result["visible"]:
            if t["status"] != "pass":
                print("  %-8s %s" % (t["status"], t["id"]))
        return 0
    if not args.run_dir:
        ap.error("give RUN_DIR, or --problem and --repo")

    run_dir = os.path.abspath(args.run_dir)
    meta = c.run_meta(run_dir)
    pdir = c.problem_dir(meta["problem"])
    spec_norm = c.normalise(c.spec_text(c.frozen_spec(run_dir)))
    impl_root = os.path.join(run_dir, "2_implementer")
    for name in sorted(os.listdir(impl_root)):
        work = os.path.join(impl_root, name)
        result = c.score_repo(pdir, os.path.join(work, "repo"))
        result["notes"] = read_notes(work, spec_norm)
        leaks = c.has_canary(work)
        result["canary_in_implementation"] = leaks
        result["void"] = bool(leaks)
        c.dump_json(os.path.join(run_dir, "scores", "outcome_%s.json" % name), result)
        s = result["summary"]
        print("%s %s: hidden %d/%d (new behaviour %s, regression %s), starter tests %s, guesses %s%s"
              % (meta["run_id"], name, s["hidden_passed"], s["hidden_total"],
                 s["new_behaviour_pass_rate"], s["regression_pass_rate"], s["visible_pass_rate"],
                 result["notes"]["guesses"], "  LEAK - VOID" if leaks else ""))
        for t in result["hidden"] + result["visible"]:
            if t["status"] != "pass":
                print("    %-8s %s" % (t["status"], t["id"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
