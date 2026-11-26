#!/usr/bin/env python3
"""Check and tally the judge's output. No model.

    python3 scripts/score_judge.py RUN_DIR

Reads 4_judge/judge*.json (one file per judge; several are averaged) and
writes scores/judge.json with two things kept apart:

  findings  counts of contradictions, ambiguities, unsupported claims,
            contradictions of the brief, and omissions - only those whose
            quotes are really in the spec (or, for omissions, in the brief).
  rubric    the judge's 0-3 scores: clarity (4 lines, max 12) and
            readability (4 lines, max 12). These are opinion.
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import common as c  # noqa: E402

CLARITY = ["actionable", "single_reading", "limits", "faithful"]
READABILITY = ["orientation", "findability", "economy", "plain_language"]


def tally(path, spec_norm, brief_norm):
    try:
        data = c.load_json(path)
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return {"file": os.path.basename(path), "valid": False, "problems": ["not a JSON object"]}
    problems = []

    def rows(key):
        value = data.get(key, [])
        return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []

    def count(key, check):
        listed = rows(key)
        return {"reported": len(listed), "verified": sum(bool(check(x)) for x in listed)}

    findings = {
        "contradictions": count("contradictions", lambda x: (
            c.quote_found(x.get("quote_a"), spec_norm) and c.quote_found(x.get("quote_b"), spec_norm)
            and c.normalise(x.get("quote_a")) != c.normalise(x.get("quote_b")))),
        "ambiguities": count("ambiguities", lambda x: c.quote_found(x.get("quote"), spec_norm)),
        "unsupported_claims": count("unsupported_claims", lambda x: c.quote_found(x.get("quote"), spec_norm)),
        "contradicts_brief": count("contradicts_brief", lambda x: c.quote_found(x.get("quote"), spec_norm)),
        "missing_from_brief": count("missing_from_brief", lambda x: c.quote_found(x.get("brief_quote"), brief_norm)),
    }
    rubric = {}
    for group, names in (("clarity", CLARITY), ("readability", READABILITY)):
        scores = data.get(group, {}) if isinstance(data.get(group), dict) else {}
        for name in names:
            value = scores.get(name)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 3:
                problems.append("%s.%s is not an integer 0-3" % (group, name))
                value = None
            rubric[name] = value
    def total(names):
        values = [rubric[n] for n in names]
        return None if None in values else sum(values)

    return {"file": os.path.basename(path), "valid": not problems, "problems": problems,
            "findings": findings, "rubric": rubric,
            "clarity_total": total(CLARITY), "readability_total": total(READABILITY)}


def mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 3) if values else None


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    args = ap.parse_args(argv)
    run_dir = os.path.abspath(args.run_dir)
    meta = c.run_meta(run_dir)
    spec_norm = c.normalise(c.spec_text(c.frozen_spec(run_dir)))
    brief_norm = c.normalise(c.read_text(os.path.join(c.problem_dir(meta["problem"]), "brief.md")))
    judges = [tally(f, spec_norm, brief_norm)
              for f in sorted(glob.glob(os.path.join(run_dir, "4_judge", "judge*.json")))]
    good = [j for j in judges if "findings" in j]
    result = {"judges": len(good), "by_judge": judges}
    if good:
        result["findings_verified_mean"] = {
            key: mean([j["findings"][key]["verified"] for j in good]) for key in good[0]["findings"]}
        result["clarity_total"] = mean([j["clarity_total"] for j in good])
        result["readability_total"] = mean([j["readability_total"] for j in good])
        result["rubric_mean"] = {n: mean([j["rubric"][n] for j in good]) for n in CLARITY + READABILITY}
        if len(good) > 1:
            for key in ("clarity_total", "readability_total"):
                values = [j[key] for j in good if j[key] is not None]
                result[key + "_spread"] = (max(values) - min(values)) if values else None
    c.dump_json(os.path.join(run_dir, "scores", "judge.json"), result)
    if not good:
        print("%s judge: no usable judge*.json yet" % meta["run_id"])
    else:
        print("%s judge: clarity %s/12, readability %s/12, verified findings %s"
              % (meta["run_id"], result["clarity_total"], result["readability_total"],
                 result["findings_verified_mean"]))
    for j in judges:
        for p in j.get("problems", []):
            print("    %s: %s" % (j["file"], p))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
