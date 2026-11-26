#!/usr/bin/env python3
"""Score the readers' quiz answers against the answer key. No model.

    python3 scripts/score_quiz.py RUN_DIR

Reads 3_reader/full/answers*.json and 3_reader/skim/answers*.json (one file
per reader; more than one reader is averaged) and writes scores/quiz.json.

Each answer lands in exactly one bin:
  correct      right option, and the quote is really in the text      1 point
  not_stated   reader answered NS: the text does not say              0
  misstated    wrong option, with a real quote: the text says
               something else than the brief                          0
  invented     an option the key marks as a fact or decision the
               brief never gave, with a real quote                    0
  conflict     reader answered CONFLICT and both quotes are real      0
  unverified   a quote is missing or not in the text (reader error
               or guess; says nothing about the spec)                 0
  invalid      no answer, or not one of the options                   0

score = correct / questions.
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import common as c  # noqa: E402

BINS = ["correct", "not_stated", "misstated", "invented", "conflict", "unverified", "invalid"]


def grade(item, answer, haystack):
    if not isinstance(answer, dict):
        return "invalid"
    choice = str(answer.get("choice", "")).strip().upper()
    if choice in ("NS", "NOT STATED"):
        return "not_stated"
    if choice == "CONFLICT":
        both = c.quote_found(answer.get("quote"), haystack) and c.quote_found(answer.get("quote2"), haystack)
        return "conflict" if both else "unverified"
    if choice not in item["options"]:
        return "invalid"
    if not c.quote_found(answer.get("quote"), haystack):
        return "unverified"
    if choice in item["correct"]:
        return "correct"
    if choice in item["invented"]:
        return "invented"
    return "misstated"


def score_file(path, items, haystack):
    try:
        data = c.load_json(path) or {}
    except ValueError:
        data = {}
    answers = data.get("answers", {}) if isinstance(data, dict) else {}
    per_item = {item["id"]: grade(item, answers.get(item["id"]), haystack) for item in items}
    counts = {b: sum(v == b for v in per_item.values()) for b in BINS}
    return {"file": os.path.basename(path), "score": round(counts["correct"] / len(items), 4),
            "counts": counts, "per_item": per_item}


def score_part(run_dir, part, items, haystack):
    files = sorted(glob.glob(os.path.join(run_dir, "3_reader", part, "answers*.json")))
    readers = [score_file(f, items, haystack) for f in files]
    if not readers:
        return {"readers": 0, "questions": len(items)}
    n = len(readers)
    out = {
        "readers": n,
        "questions": len(items),
        "score": round(sum(r["score"] for r in readers) / n, 4),
        "score_min": min(r["score"] for r in readers),
        "score_max": max(r["score"] for r in readers),
        "counts_mean": {b: round(sum(r["counts"][b] for r in readers) / n, 2) for b in BINS},
        "by_reader": readers,
    }
    if n > 1:
        agree = sum(len({r["per_item"][i["id"]] for r in readers}) == 1 for i in items)
        out["items_all_readers_agree"] = round(agree / len(items), 4)
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    args = ap.parse_args(argv)
    run_dir = os.path.abspath(args.run_dir)
    meta = c.run_meta(run_dir)
    quiz = c.load_json(os.path.join(c.problem_dir(meta["problem"]), "quiz.json"))
    full_text = c.normalise(c.spec_text(c.frozen_spec(run_dir)))
    skim_text = c.normalise(c.read_text(os.path.join(run_dir, "3_reader", "skim", "SPEC_OPENING.txt")))
    result = {
        "full": score_part(run_dir, "full", quiz["full"], full_text),
        "skim": score_part(run_dir, "skim", quiz["skim"], skim_text),
    }
    c.dump_json(os.path.join(run_dir, "scores", "quiz.json"), result)
    for part in ("full", "skim"):
        r = result[part]
        if not r["readers"]:
            print("%s %s quiz: no answers file yet" % (meta["run_id"], part))
        else:
            print("%s %s quiz: %.2f (%d reader(s), %d questions) %s"
                  % (meta["run_id"], part, r["score"], r["readers"], r["questions"],
                     {k: v for k, v in r["counts_mean"].items() if v}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
