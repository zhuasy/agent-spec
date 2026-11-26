#!/usr/bin/env python3
"""After the spec-writer has finished: freeze the spec and build the working
folders for the implementer, the two readers and the judge.

    python3 scripts/stage_run.py RUN_DIR [--impl-reps 1] [--force]

Each role gets its own folder holding only what that role may see:

    2_implementer/impl_K/   spec/ + a fresh repo/         (no brief)
    3_reader/full/          spec/ + QUIZ.md               (no brief, no repo, no key)
    3_reader/skim/          SPEC_OPENING.txt + QUIZ.md    (first 150 words only)
    4_judge/                spec/ + BRIEF.md + repo/      (no method name)

Also writes scores/readability.json and scores/spec_check.json.
"""
import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import common as c  # noqa: E402
import readability  # noqa: E402


def quiz_markdown(items, intro):
    lines = [intro, ""]
    for item in items:
        lines.append("## %s" % item["id"])
        lines.append("")
        lines.append(item["q"])
        lines.append("")
        for letter, text in item["options"].items():
            lines.append("- %s: %s" % (letter, text))
        lines.append("- NS: not stated")
        lines.append("- CONFLICT: the text gives two answers that disagree")
        lines.append("")
    return "\n".join(lines)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--impl-reps", type=int, default=1)
    ap.add_argument("--force", action="store_true", help="rebuild even if already staged")
    args = ap.parse_args(argv)

    run_dir = os.path.abspath(args.run_dir)
    meta = c.run_meta(run_dir)
    pdir = c.problem_dir(meta["problem"])
    writer = os.path.join(run_dir, "1_spec_writer")
    spec_src = os.path.join(writer, "spec")
    frozen = os.path.join(run_dir, "spec_frozen")

    if os.path.exists(frozen):
        if not args.force:
            sys.exit("already staged (spec_frozen/ exists). Use --force to rebuild; "
                     "that discards implementer, reader and judge folders.")
        for name in ("spec_frozen", "2_implementer", "3_reader", "4_judge", "scores"):
            shutil.rmtree(os.path.join(run_dir, name), ignore_errors=True)

    files = c.spec_files(spec_src)
    text = c.spec_text(spec_src)
    if not files or not text.strip():
        sys.exit("no spec found in %s" % spec_src)
    leaks = c.has_canary(spec_src)
    if leaks:
        sys.exit("LEAK: canary string found in the spec (%s). The spec-writer saw hidden "
                 "material; this run is void." % ", ".join(leaks))

    c.copy_tree(spec_src, frozen)
    brief = c.read_text(os.path.join(pdir, "brief.md"))
    starter = os.path.join(pdir, "starter")
    quiz = c.load_json(os.path.join(pdir, "quiz.json"))

    for k in range(1, args.impl_reps + 1):
        work = os.path.join(run_dir, "2_implementer", "impl_%d" % k)
        c.copy_tree(frozen, os.path.join(work, "spec"))
        c.copy_tree(starter, os.path.join(work, "repo"))
        c.write_text(os.path.join(work, "PROMPT.md"), c.fill("implementer.md", WORKDIR=work))

    full = os.path.join(run_dir, "3_reader", "full")
    c.copy_tree(frozen, os.path.join(full, "spec"))
    c.write_text(os.path.join(full, "QUIZ.md"), quiz_markdown(
        quiz["full"], "# Questions about the document in spec/"))
    c.write_text(os.path.join(full, "PROMPT.md"), c.fill("quiz_reader_full.md", WORKDIR=full))

    skim = os.path.join(run_dir, "3_reader", "skim")
    c.write_text(os.path.join(skim, "SPEC_OPENING.txt"), c.first_words(text, c.SKIM_WORDS) + "\n")
    c.write_text(os.path.join(skim, "QUIZ.md"), quiz_markdown(
        quiz["skim"], "# Questions about the text in SPEC_OPENING.txt"))
    c.write_text(os.path.join(skim, "PROMPT.md"),
                 c.fill("quiz_reader_skim.md", WORKDIR=skim, SKIM_WORDS=c.SKIM_WORDS))

    judge = os.path.join(run_dir, "4_judge")
    c.copy_tree(frozen, os.path.join(judge, "spec"))
    c.copy_tree(starter, os.path.join(judge, "repo"))
    shutil.copyfile(os.path.join(pdir, "brief.md"), os.path.join(judge, "BRIEF.md"))
    c.write_text(os.path.join(judge, "PROMPT.md"), c.fill("judge.md", WORKDIR=judge))

    read = readability.measure(frozen, brief)
    c.dump_json(os.path.join(run_dir, "scores", "readability.json"), read)
    c.dump_json(os.path.join(run_dir, "scores", "spec_check.json"), {
        "spec_hash": c.tree_hash(frozen),
        "files": files,
        "entry_file_used": os.path.exists(os.path.join(spec_src, "ENTRY")),
        "spec_writer_changed_repo": c.tree_hash(os.path.join(writer, "repo")) != c.tree_hash(starter),
        "canary_in_spec": False,
        "impl_reps": args.impl_reps,
    })
    print("staged %s: %d spec file(s), %d words, %d implementer folder(s)"
          % (meta["run_id"], len(files), read["words"], args.impl_reps))
    for path in sorted(
            [os.path.join(run_dir, "2_implementer", d) for d in os.listdir(os.path.join(run_dir, "2_implementer"))]
            + [full, skim, judge]):
        print("  start a role in %s (prompt: PROMPT.md)" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
