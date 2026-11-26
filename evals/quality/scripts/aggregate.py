#!/usr/bin/env python3
"""Collect every run under a runs folder into one results table. No model.

    python3 scripts/aggregate.py RUNS_DIR [--compare METHOD_A METHOD_B] [--out DIR]

Writes results.json and results.md (default: into RUNS_DIR).

How numbers are combined:
  run     one problem x one method x one spec-writer repetition. Within a run,
          implementer repetitions and multiple readers/judges are averaged.
  cell    method x problem: mean over that cell's runs.
  method  mean over problems of the cell means, so every problem counts the
          same however many runs it has.

The three headline scores are mechanical. Judge scores are listed in their
own columns and are never mixed into the headline scores.
"""
import argparse
import datetime
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import common as c  # noqa: E402

BASELINE = "baseline-brief"
# key, column title, digits
HEADLINE = [
    ("new_behaviour_pass_rate", "Outcome: new-behaviour tests passed", 2),
    ("regression_pass_rate", "Outcome: regression tests passed", 2),
    ("quiz_full", "Clarity: whole-spec quiz", 2),
    ("quiz_skim", "Readability: opening-only quiz", 2),
    ("reading_minutes", "Reading time (min)", 1),
    ("words", "Words", 0),
]
JUDGE = [
    ("judge_clarity", "Judge clarity (0-12)", 1),
    ("judge_readability", "Judge readability (0-12)", 1),
]
DETAIL = [
    ("all_green_share", "Implementations fully green", 2),
    ("visible_pass_rate", "Starter's own tests passed", 2),
    ("impl_guesses", "Implementer guesses", 1),
    ("quiz_not_stated", "Quiz: not stated", 1),
    ("quiz_misstated", "Quiz: misstated", 1),
    ("quiz_invented", "Quiz: invented", 1),
    ("quiz_conflict", "Quiz: conflicts", 1),
    ("quiz_unverified", "Quiz: unverified", 1),
    ("quiz_points_per_minute", "Quiz points per reading minute", 2),
    ("copied_from_brief_share", "Copied from brief", 2),
    ("length_ratio_to_brief", "Length / brief", 1),
    ("flesch_reading_ease", "Flesch", 0),
    ("avg_sentence_words", "Words per sentence", 1),
    ("duplicate_sentence_share", "Repeated sentences", 2),
    ("judge_contradictions", "Judge: contradictions", 1),
    ("judge_ambiguities", "Judge: ambiguities", 1),
    ("judge_unsupported", "Judge: unsupported claims", 1),
    ("judge_contradicts_brief", "Judge: contradicts brief", 1),
    ("judge_missing", "Judge: missing from brief", 1),
]
COMPARE = [("new_behaviour_pass_rate", True), ("regression_pass_rate", True), ("quiz_full", True),
           ("quiz_skim", True), ("reading_minutes", False), ("judge_clarity", True),
           ("judge_readability", True)]
ALL_KEYS = [k for k, _, _ in HEADLINE + JUDGE + DETAIL]


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def load_run(run_dir):
    meta = c.load_json(os.path.join(run_dir, "run.json"))
    scores = os.path.join(run_dir, "scores")
    m, flags, samples = {}, [], {}

    outcomes = [c.load_json(f) for f in sorted(glob.glob(os.path.join(scores, "outcome_*.json")))]
    void = [o for o in outcomes if o.get("void")]
    if void:
        flags.append("%d implementation(s) void: canary string found" % len(void))
    outcomes = [o for o in outcomes if not o.get("void")]
    if not outcomes:
        flags.append("no implementation scored")
    for key in ("new_behaviour_pass_rate", "regression_pass_rate", "visible_pass_rate"):
        samples[key] = [o["summary"][key] for o in outcomes if o["summary"][key] is not None]
        m[key] = mean(samples[key])
    m["all_green_share"] = mean([1.0 if o["summary"]["all_green"] else 0.0 for o in outcomes])
    m["impl_guesses"] = mean([o["notes"]["guesses"] for o in outcomes])
    if any(o["notes"]["notes_missing"] for o in outcomes):
        flags.append("an implementer left no IMPL_NOTES.json")
    if any(o["summary"]["timeouts"] for o in outcomes):
        flags.append("test timeouts")

    read = c.load_json(os.path.join(scores, "readability.json"), {})
    for key in ("words", "reading_minutes", "flesch_reading_ease", "avg_sentence_words",
                "duplicate_sentence_share", "copied_from_brief_share", "length_ratio_to_brief"):
        m[key] = read.get(key)
    if read.get("placeholders"):
        flags.append("%d placeholder(s) such as TBD/TODO in the spec" % read["placeholders"])
    if (read.get("copied_from_brief_share") or 0) > 0.5 and meta["method"] != BASELINE:
        flags.append("more than half of the spec is copied from the brief")
    check = c.load_json(os.path.join(scores, "spec_check.json"), {})
    if check.get("spec_writer_changed_repo"):
        flags.append("spec-writer changed repo/ (ignored: implementer got a fresh copy)")
    if not check:
        flags.append("not staged")

    quiz = c.load_json(os.path.join(scores, "quiz.json"), {})
    full, skim = quiz.get("full", {}), quiz.get("skim", {})
    m["quiz_full"] = full.get("score")
    m["quiz_skim"] = skim.get("score")
    samples["quiz_full"] = [r["score"] for r in full.get("by_reader", [])]
    samples["quiz_skim"] = [r["score"] for r in skim.get("by_reader", [])]
    for name in ("not_stated", "misstated", "invented", "conflict", "unverified"):
        m["quiz_" + name] = full.get("counts_mean", {}).get(name)
    if m["quiz_full"] is None:
        flags.append("no whole-spec quiz answers")
    if m["quiz_skim"] is None:
        flags.append("no opening-only quiz answers")
    unverified = (full.get("counts_mean", {}).get("unverified", 0) or 0) + \
                 (full.get("counts_mean", {}).get("invalid", 0) or 0)
    if full.get("questions") and unverified / full["questions"] > 0.2:
        flags.append("reader left many answers unusable (missing, or quotes not found in the text): redo the reader")
    correct = full.get("counts_mean", {}).get("correct")
    m["quiz_points_per_minute"] = (correct / m["reading_minutes"]
                                   if correct is not None and m.get("reading_minutes") else None)

    judge = c.load_json(os.path.join(scores, "judge.json"), {})
    m["judge_clarity"] = judge.get("clarity_total")
    m["judge_readability"] = judge.get("readability_total")
    samples["judge_clarity"] = [j["clarity_total"] for j in judge.get("by_judge", [])
                                if j.get("clarity_total") is not None]
    samples["judge_readability"] = [j["readability_total"] for j in judge.get("by_judge", [])
                                    if j.get("readability_total") is not None]
    for j in judge.get("by_judge", []):
        for problem in j.get("problems", []):
            flags.append("judge output unusable in part (%s): redo the judge" % problem)
    if not judge.get("judges"):
        flags.append("no judge output")
    found = judge.get("findings_verified_mean", {})
    m["judge_contradictions"] = found.get("contradictions")
    m["judge_ambiguities"] = found.get("ambiguities")
    m["judge_unsupported"] = found.get("unsupported_claims")
    m["judge_contradicts_brief"] = found.get("contradicts_brief")
    m["judge_missing"] = found.get("missing_from_brief")
    samples["reading_minutes"] = [m["reading_minutes"]] if m.get("reading_minutes") is not None else []

    return {"run_id": meta["run_id"], "problem": meta["problem"], "method": meta["method"],
            "rep": meta.get("rep"), "implementations": len(outcomes), "metrics": m,
            "samples": samples, "flags": flags}


def build(runs):
    cells = {}
    for run in runs:
        cells.setdefault((run["method"], run["problem"]), []).append(run)
    cell_rows = []
    for (method, problem), members in sorted(cells.items()):
        metrics = {k: mean([r["metrics"].get(k) for r in members]) for k in ALL_KEYS}
        samples = {}
        for r in members:
            for key, values in r["samples"].items():
                samples.setdefault(key, []).extend(values)
        spread = {k: (max(v) - min(v) if len(v) > 1 else None) for k, v in samples.items()}
        cell_rows.append({"method": method, "problem": problem, "runs": len(members),
                          "metrics": metrics, "spread": spread,
                          "sample_count": {k: len(v) for k, v in samples.items()}})
    methods = []
    for method in sorted({r["method"] for r in cell_rows}):
        mine = [r for r in cell_rows if r["method"] == method]
        methods.append({"method": method, "problems": len(mine),
                        "runs": sum(r["runs"] for r in mine),
                        "metrics": {k: mean([r["metrics"][k] for r in mine]) for k in ALL_KEYS}})
    return cell_rows, methods


def uplift(cell_rows):
    base = {r["problem"]: r for r in cell_rows if r["method"] == BASELINE}
    out = []
    for method in sorted({r["method"] for r in cell_rows} - {BASELINE}):
        shared = [r for r in cell_rows if r["method"] == method and r["problem"] in base]
        if not shared:
            continue
        row = {"method": method, "problems": len(shared), "metrics": {}}
        for key, _, _ in HEADLINE + JUDGE:
            diffs = [r["metrics"][key] - base[r["problem"]]["metrics"][key] for r in shared
                     if r["metrics"][key] is not None and base[r["problem"]]["metrics"][key] is not None]
            row["metrics"][key] = mean(diffs)
        out.append(row)
    return out


def compare(cell_rows, a, b):
    index = {(r["method"], r["problem"]): r for r in cell_rows}
    problems = sorted({p for (m, p) in index if m == a} & {p for (m, p) in index if m == b})
    rows, tally = [], {}
    for key, higher_better in COMPARE:
        tally[key] = {a: 0, b: 0, "within noise": 0, "single sample": 0, "no data": 0}
        for problem in problems:
            ra, rb = index[(a, problem)], index[(b, problem)]
            va, vb = ra["metrics"][key], rb["metrics"][key]
            if va is None or vb is None:
                verdict, diff, noise = "no data", None, None
            else:
                diff = va - vb
                spreads = [ra["spread"].get(key), rb["spread"].get(key)]
                if key == "reading_minutes":
                    noise = 0.0
                    verdict = "tie" if diff == 0 else None
                elif None in spreads:
                    noise, verdict = None, "single sample"
                else:
                    noise = max(spreads)
                    verdict = "within noise" if abs(diff) <= noise else None
                if verdict is None:
                    verdict = a if (diff > 0) == higher_better else b
                if verdict == "tie":
                    verdict = "within noise"
            tally[key][verdict] += 1
            rows.append({"metric": key, "problem": problem, a: va, b: vb, "difference": diff,
                         "noise": noise, "verdict": verdict})
    return {"a": a, "b": b, "problems": problems, "rows": rows, "tally": tally}


def fmt(value, digits=2):
    if value is None:
        return "-"
    return "%.*f" % (digits, value)


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def markdown(result):
    lines = ["# Spec quality eval: results", "",
             "Generated %s from %d run(s)." % (result["generated"], len(result["runs"])), "",
             "Headline scores are mechanical. Judge columns are a model's opinion against a fixed "
             "rubric and are kept apart. See README.md for what each measure does and does not capture.", ""]
    flagged = [(r["run_id"], r["method"], r["problem"], f) for r in result["runs"] for f in r["flags"]]
    lines += ["## Flags", ""]
    lines += (["- %s (%s, %s): %s" % f for f in flagged] or ["None."]) + [""]

    cols = HEADLINE + JUDGE
    lines += ["## By method (mean over problems)", "",
              table(["Method", "Problems", "Runs"] + [t for _, t, _ in cols],
                    [[m["method"], str(m["problems"]), str(m["runs"])]
                     + [fmt(m["metrics"][k], d) for k, _, d in cols] for m in result["methods"]]), ""]
    if result["uplift_over_brief"]:
        lines += ["## Difference from using the brief itself as the spec", "",
                  "Positive means better than handing the implementer the raw brief "
                  "(for reading time and words, positive means longer).", "",
                  table(["Method", "Problems"] + [t for _, t, _ in cols],
                        [[u["method"], str(u["problems"])]
                         + [("-" if u["metrics"][k] is None else "%+.*f" % (max(d, 1), u["metrics"][k]))
                            for k, _, d in cols] for u in result["uplift_over_brief"]]), ""]
    else:
        lines += ["## Difference from using the brief itself as the spec", "",
                  "No `%s` runs found. Without them you cannot tell how much a spec added." % BASELINE, ""]
    lines += ["## Secondary measures by method", "",
              table(["Measure"] + [m["method"] for m in result["methods"]],
                    [[t] + [fmt(m["metrics"][k], d) for m in result["methods"]] for k, t, d in DETAIL]), ""]
    lines += ["## By problem", ""]
    for problem in sorted({r["problem"] for r in result["cells"]}):
        rows = [r for r in result["cells"] if r["problem"] == problem]
        lines += ["### %s" % problem, "",
                  table(["Method", "Runs"] + [t for _, t, _ in cols] + ["Outcome spread", "Quiz spread"],
                        [[r["method"], str(r["runs"])] + [fmt(r["metrics"][k], d) for k, _, d in cols]
                         + [fmt(r["spread"].get("new_behaviour_pass_rate")), fmt(r["spread"].get("quiz_full"))]
                         for r in rows]), ""]
    comp = result.get("comparison")
    if comp:
        a, b = comp["a"], comp["b"]
        lines += ["## %s against %s" % (a, b), "",
                  "Per problem, a method wins a measure only when the difference is larger than the "
                  "spread between repeated samples of the same cell (implementer repetitions, readers, "
                  "judges). 'single sample' means there was nothing to estimate the spread from, so no "
                  "winner is called.", "",
                  table(["Measure", a + " wins", b + " wins", "Within noise", "Single sample", "No data"],
                        [[k, str(t[a]), str(t[b]), str(t["within noise"]), str(t["single sample"]),
                          str(t["no data"])] for k, t in comp["tally"].items()]), "",
                  table(["Measure", "Problem", a, b, "Difference", "Noise", "Verdict"],
                        [[r["metric"], r["problem"], fmt(r[a]), fmt(r[b]),
                          "-" if r["difference"] is None else "%+.2f" % r["difference"],
                          fmt(r["noise"]), r["verdict"]] for r in comp["rows"]]), ""]
    return "\n".join(lines)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs_dir")
    ap.add_argument("--compare", nargs=2, metavar=("METHOD_A", "METHOD_B"))
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    run_dirs = sorted(os.path.dirname(p) for p in glob.glob(os.path.join(args.runs_dir, "*", "run.json")))
    if not run_dirs:
        sys.exit("no runs under %s" % args.runs_dir)
    runs = [load_run(d) for d in run_dirs]
    cells, methods = build(runs)
    result = {
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "methods": methods, "uplift_over_brief": uplift(cells), "cells": cells, "runs": runs,
    }
    if args.compare:
        known = {m["method"] for m in methods}
        for name in args.compare:
            if name not in known:
                sys.exit("--compare: no runs for method %r (have: %s)" % (name, ", ".join(sorted(known))))
        result["comparison"] = compare(cells, *args.compare)
    out = args.out or args.runs_dir
    c.dump_json(os.path.join(out, "results.json"), result)
    c.write_text(os.path.join(out, "results.md"), markdown(result))
    print(markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
