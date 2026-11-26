#!/usr/bin/env python3
"""Create a run folder and stage 1 (the spec-writer's working folder).

    python3 scripts/new_run.py --runs-dir DIR --problem p1 --method NAME
        [--rep 1] [--method-instructions FILE] [--baseline brief]

One run = one problem x one method x one repetition of the spec-writer.
The folder name is a random id, so nothing a role sees names the method;
the mapping is in run.json, which no role is given.

--method-instructions FILE  text placed in the spec-writer prompt under
                            "How to write the spec" (for example "Use the X
                            skill", a template, or a one-line plain prompt).
                            Default: "Write it the way you judge best."
--baseline brief            no spec-writer: the brief itself is used as the
                            spec. This is the floor every method must beat.
"""
import argparse
import datetime
import os
import secrets
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import common as c  # noqa: E402


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs-dir", required=True)
    ap.add_argument("--problem", required=True)
    ap.add_argument("--method")
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--method-instructions")
    ap.add_argument("--baseline", choices=["brief"])
    ap.add_argument("--allow-inside-eval", action="store_true",
                    help="allow a runs dir inside the eval folder (roles could then reach hidden files)")
    args = ap.parse_args(argv)

    runs_dir = os.path.abspath(args.runs_dir)
    if os.path.commonpath([runs_dir, c.ROOT]) == c.ROOT and not args.allow_inside_eval:
        sys.exit("refusing: --runs-dir is inside the eval folder, where hidden tests and answer "
                 "keys live. Use a folder elsewhere (or --allow-inside-eval).")
    method = args.method or ("baseline-brief" if args.baseline else None)
    if not method:
        ap.error("--method is required (or use --baseline brief)")

    pdir = c.problem_dir(args.problem)
    run_id = "r-" + secrets.token_hex(4)
    run_dir = os.path.join(runs_dir, run_id)
    stage = os.path.join(run_dir, "1_spec_writer")
    os.makedirs(os.path.join(stage, "spec"))
    shutil.copyfile(os.path.join(pdir, "brief.md"), os.path.join(stage, "BRIEF.md"))
    c.copy_tree(os.path.join(pdir, "starter"), os.path.join(stage, "repo"))

    instructions = "Write it the way you judge best."
    if args.method_instructions:
        instructions = c.read_text(args.method_instructions).strip()
    if args.baseline == "brief":
        shutil.copyfile(os.path.join(pdir, "brief.md"), os.path.join(stage, "spec", "brief.md"))
    else:
        c.write_text(os.path.join(stage, "PROMPT.md"),
                     c.fill("spec_writer.md", WORKDIR=stage, METHOD_INSTRUCTIONS=instructions))

    c.dump_json(os.path.join(run_dir, "run.json"), {
        "run_id": run_id,
        "problem": os.path.basename(pdir),
        "method": method,
        "rep": args.rep,
        "baseline": args.baseline,
        "created": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    print(run_dir)
    if args.baseline:
        print("baseline run: spec/ already holds the brief. Next: stage_run.py %s" % run_dir,
              file=sys.stderr)
    else:
        print("next: start the spec-writer in %s with PROMPT.md as its prompt, then run "
              "stage_run.py %s" % (stage, run_dir), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
