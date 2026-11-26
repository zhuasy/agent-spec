# Spec quality eval

Compares ways of producing a spec (a merged PRD and design doc) that a coding
agent then implements. A "way" can be a skill, a template, a plain prompt or a
person. The eval takes a folder that contains the spec and assumes nothing
about its file names, sections, format or tooling.

It answers three questions about each spec, with three separate scores:

| Score | Question | Headline measure (mechanical) |
|---|---|---|
| Agent outcome | When an agent that sees only the spec and the starter code implements it, how good is the result? | Share of hidden acceptance tests passed |
| Clarity | How complete and unambiguous is the spec as instructions? | Share of a fixed quiz that a reader who sees only the spec answers correctly, each answer backed by a quote the script finds in the spec |
| Readability | How quickly and correctly does a person get what they need? | Share of a 3-question quiz answered from the first 150 words only, read next to reading time |

A judge model also scores a fixed rubric. Its scores are reported in their own
columns and never enter the three headline scores.

## Pipeline

```
brief.md + starter repo
      |
      v
 spec-writer (the thing under test)  ->  spec/
      |
      +--> implementer: spec/ + fresh repo, no brief   -> code  -> hidden tests
      +--> reader (whole spec): spec/ + quiz           -> answers -> answer key
      +--> reader (opening): first 150 words + quiz    -> answers -> answer key
      +--> judge: spec/ + brief + repo, method unknown -> findings + rubric
      +--> script: length, reading time, overlap with the brief
```

The scripts never call a model. You start each role yourself (by hand or from
another harness) in the folder the scripts prepare, with the `PROMPT.md` found
there as its prompt.

## Layout

```
README.md
problems/<name>/
    brief.md          the request, as a person wrote it      -> spec-writer, judge
    starter/          the repo before the change             -> spec-writer, implementer, judge
    problem.json      what the problem tests; what the brief leaves open
    hidden/           hidden acceptance tests                -> nobody
    reference/        files that, copied over starter/, pass every test -> nobody
    quiz.json         quiz questions WITH the answer key     -> nobody
    baseline.json     written by verify_problems.py: which hidden tests fail on the starter
prompts/
    spec_writer.md  implementer.md  quiz_reader_full.md  quiz_reader_skim.md  judge.md
scripts/
    verify_problems.py   prove the problems are sound (run after any edit to problems/)
    new_run.py           create a run folder and the spec-writer's folder
    stage_run.py         freeze the spec; build implementer, reader and judge folders
    run_hidden_tests.py  score implementations
    score_quiz.py        score reader answers
    score_judge.py       check and tally judge output
    readability.py       mechanical text measures (also run by stage_run.py)
    aggregate.py         one table for all runs: results.json and results.md
    common.py            shared code
```

Python 3 standard library only. Everything runs with `python3`.

## Run one problem end to end

Keep runs outside this folder, so that no role can walk to the hidden tests or
answer keys. `new_run.py` refuses a runs folder inside the eval folder.

```
cd evals/quality
python3 scripts/verify_problems.py                 # once; all problems must say OK

# 1. Create the run. Put how the method is invoked in a text file.
echo 'Use the <name> skill to write the spec.' > /tmp/method-a.txt
RUN=$(python3 scripts/new_run.py --runs-dir /tmp/spec-runs --problem p2 \
        --method method-a --method-instructions /tmp/method-a.txt)

# 2. Spec-writer: start an agent in $RUN/1_spec_writer with PROMPT.md as the prompt.
#    It writes into $RUN/1_spec_writer/spec/.

# 3. Freeze the spec and build the other roles' folders.
python3 scripts/stage_run.py $RUN --impl-reps 2

# 4. Start one agent per folder, each with that folder's PROMPT.md. They are
#    independent and can run at the same time.
#      $RUN/2_implementer/impl_1   -> edits repo/, writes IMPL_NOTES.json
#      $RUN/2_implementer/impl_2   -> same, a second independent attempt
#      $RUN/3_reader/full          -> writes answers.json
#      $RUN/3_reader/skim          -> writes answers.json
#      $RUN/4_judge                -> writes judge.json

# 5. Score.
python3 scripts/run_hidden_tests.py $RUN
python3 scripts/score_quiz.py $RUN
python3 scripts/score_judge.py $RUN

# 6. One table for everything under the runs folder.
python3 scripts/aggregate.py /tmp/spec-runs
```

Each role takes a few minutes: the starter repos are under 150 lines, the
briefs under 300 words, the quizzes 8 to 10 plus 3 questions.

A second reader or judge: run the role again and save its output next to the
first as `answers_2.json` or `judge_2.json`. The scorers average all files
named `answers*.json` / `judge*.json` and report how far they differ.

For a human spec-writer: give them `BRIEF.md` and `repo/`, and put what they
write in `spec/`. For a human reader: give them the reader folder and a
stopwatch; the answer format is the same.

## Compare two methods

1. Use the same problems, the same implementer, reader and judge model, and
   the same number of repetitions for both methods.
2. For each method and each problem, make at least 2 runs (`--rep 1`,
   `--rep 2`: two independent spec-writer attempts), each staged with
   `--impl-reps 2`. That is 4 implementations per method per problem. One
   sample per cell cannot separate a real difference from run-to-run noise,
   and the table says so instead of naming a winner.
3. Add the floor, once per problem, with no spec-writer:
   `python3 scripts/new_run.py --runs-dir /tmp/spec-runs --problem p2 --baseline brief`
   then `stage_run.py`, the roles, and the scorers as above. This hands the
   implementer the raw brief as its spec. A method only shows value where it
   beats this.
4. `python3 scripts/aggregate.py /tmp/spec-runs --compare method-a method-b`

`results.md` then holds: flags; a table by method (mean over problems, each
problem weighted equally); each method's difference from the brief-as-spec
floor; secondary measures; a table per problem; and the comparison. In the
comparison a method wins a measure on a problem only when the difference is
larger than the spread between repeated samples in either cell.

Read the comparison per problem before reading the means. Six problems is a
small sample. A method that wins on four problems by more than the noise is a
finding. A 0.03 difference in a mean is not.

## The problems

| Problem | Kind | What it tests in a spec |
|---|---|---|
| p1-todo-tags | New feature in a small existing codebase | Carrying many small rules from a chatty message (AND filter, case, validation, counts) plus one compatibility constraint (old data files) |
| p2-shipping-rule | Behaviour change with things that must not break | Stating a rule change exactly (which amount, which threshold, the boundary); protecting tax, rounding and field names; noticing the second place that duplicates the rule (the cart banner) |
| p3-logsum-cli | Greenfield CLI | Turning a ticket with examples into an exact interface: arguments, JSON shape, p95 definition, error handling |
| p4-duplicate-contacts | Bug-shaped request | Finding the cause behind a symptom; rejecting the reporter's own suggested fix (dedupe by name); keeping the merge rules that work |
| p5-ticket-archive | Brief with undecided points | Two points the brief says are not decided (30 or 90 days; reopening an archived ticket). Right answer: build what is decided, do not block, do not silently settle the rest |
| p6-seat-cap | Concurrency and permission trap | Carrying the context that makes the naive implementation wrong (thread pool, 20 parallel requests, store interface frozen) and a permission rule (admins skip the cap, not the capacity) |

Rules the problems follow:

- A hidden test never needs a fact that the brief does not give and a careful
  engineer reading the brief and the repo would not infer. `problem.json`
  lists, for each problem, what is inferred and what the brief leaves open.
- Where the brief leaves something open, the tests accept every reasonable
  choice or do not test it. Example: p5 tests the default period only with
  tickets closed 200 days ago (archived under 30 or 90) and 5 days ago (kept
  under both).
- Hidden tests fall in three author-chosen groups by class name: `Core`
  (what was asked for), `Edge` (boundaries and the trap), `Keep` (must not
  break). Separately, `verify_problems.py` runs them on the untouched starter
  and records which fail there (`new`) and which pass (`regression`). The
  headline outcome score uses only the `new` tests, so doing nothing scores 0.

`verify_problems.py` proves, for every problem: the starter's own tests pass on
the starter; every `Core` test fails on the starter; the reference passes every
hidden test and every starter test; the quiz key is well formed; the canary
string is in every secret file and in nothing a role is given.

## The measures, and what each one does and does not capture

### Agent outcome

| Measure | What it is | Captures | Does not capture |
|---|---|---|---|
| New-behaviour tests passed (headline) | Share of hidden tests that fail on the untouched starter and pass on the implementation. Mean over implementer repetitions. | Whether the spec got the wanted behaviour, including edges and the trap, into working code | Code quality, design, anything the tests do not exercise. It also depends on the implementer model: use one model for all methods |
| Regression tests passed | Share of hidden tests that pass on the starter and still pass | Whether the spec (or an invented requirement in it) led the implementer to break something | Breakage outside what the tests cover |
| Starter's own tests passed | The pristine copies of the starter's tests, run on the implementation | Same, for behaviour the starter already tested | - |
| Implementations fully green | Share of implementations where every test passes | The all-or-nothing view: could you merge it | - |
| Implementer guesses | Number of entries the implementer listed in `IMPL_NOTES.json` as decisions the spec should have made | Gaps the implementer met in practice | Self-reported: agents differ in how much they report. Compare only between runs of the same implementer model |
| Implementer-reported contradictions, false statements about the repo | Counted only when the quoted words are found in the spec | Internal conflicts and invented facts about the code | Whether the implementer's reading is right. Only the quote is checked |

### Clarity

| Measure | What it is | Captures | Does not capture |
|---|---|---|---|
| Whole-spec quiz (headline) | 8 to 10 multiple-choice questions per problem. Each asks for a decision the hidden tests depend on, or for how the spec treats a point the brief leaves open or rules out. A reader with only the spec answers; `NS` (not stated) and `CONFLICT` are always options. An answer counts only if its quote is found in the spec. | Whether each needed decision is stated in the spec, findable, and says what the brief said | Decisions not in the quiz. Whether the quote really supports the chosen option: the script checks that the quote exists, not what it means. A reader model can still misread |
| Quiz: not stated | Questions the reader answered `NS` | Omissions | - |
| Quiz: misstated | Wrong option chosen, with a real quote | The spec says something different from the brief | Could also be a reader error. Check the item when it matters |
| Quiz: invented | The reader chose an option the key marks as a decision or fact the brief never gave (for example "30 days, given as settled"), with a real quote | The spec settling what the brief left open, or building what the brief ruled out | Only the invention traps written into the quiz (1 or 2 per problem) |
| Quiz: conflicts | Reader answered `CONFLICT` with two real quotes | Contradictions that bear on a needed decision | Contradictions elsewhere |
| Judge findings (counts) | Contradictions, ambiguities, unsupported claims, contradictions of the brief, omissions, each with quotes. Counted only when the quotes are found in the spec (or, for omissions, in the brief). | Problems anywhere in the spec, not only where the quiz looks | A judge's finding is still a judgement; the script verifies the quote, not the claim. Counts rise with spec length |
| Judge clarity rubric (0 to 12) | Four lines scored 0 to 3 against fixed descriptions: actionable, single reading, limits, faithful | An overall reading that counts cannot give | It is an opinion. Kept in its own column |

### Readability

| Measure | What it is | Captures | Does not capture |
|---|---|---|---|
| Opening-only quiz (headline) | The reader gets only the first 150 words of the spec and 3 questions: what is changing, the main constraint, and the main risk or open point. Quotes are checked against those 150 words. | Whether a person who stops after the first screen knows what this is. A spec that opens with a template header, a table of contents or background scores low | Readability of the rest. A reader model is a stand-in for a person |
| Reading time, words | Words in all text files of the spec, divided by 200 words per minute | The cost of reading it. Always read next to the quiz score | Density or difficulty. Code blocks count as words |
| Quiz points per reading minute | Whole-spec quiz points divided by reading time | Information per minute; a long spec must earn its length | Capped by the quiz length, so very short complete specs look best |
| Flesch reading ease, words per sentence, share of sentences over 30 words | Standard formulas on the prose outside code blocks | Long, heavy sentences | Rough on technical text: identifiers and list fragments distort it. Use it to compare specs for the same problem, not as an absolute |
| Repeated sentences, empty sections, placeholders (TBD/TODO), vague terms per 1000 words | Counts | Padding, unfilled templates, soft wording such as "as appropriate" | Whether a given instance is harmful |
| Judge readability rubric (0 to 12) | Four lines scored 0 to 3: orientation, findability, economy, plain language | Layout and wording as a person meets them | Opinion; own column |

No model-based measure replaces a person with a stopwatch. If you can spare
one, have a person do the two reader roles for a sample of runs and compare.

## Guards

| Risk | Guard |
|---|---|
| A spec that restates the brief | The brief-as-spec baseline run gives the floor for every measure; results show each method's difference from it. `copied_from_brief_share` (share of the spec's 5-word runs that occur in the brief) is reported, and a run is flagged above 0.5 |
| A very long spec | Reading time and words sit next to the scores; the opening-only quiz sees 150 words whatever the length; quiz points per reading minute; repeated-sentence share |
| Invented facts | Quiz options marked `invented`; quote-checked judge counts of unsupported claims and contradictions of the brief; quote-checked implementer reports of false statements about the repo; regression tests that fail when an invented requirement reaches the code (for example a higher international flat rate in p2, or stripping `+` addresses in p4) |
| Hidden tests or keys leaking into a prompt | Roles get purpose-built folders that hold only what they may see; runs live outside the eval folder; every secret file carries a canary string; `stage_run.py` stops if the spec contains it and `run_hidden_tests.py` voids an implementation that contains it; hidden tests are copied to a temporary folder for the test run and never into the run folder |
| Judge bias toward a method | Run folders have random names; the judge folder holds no method name; the prompt forbids guessing the origin. The format of a spec can still give its origin away: this is the reason the judge is not a headline score |
| A reader that guesses from common sense | Every answer other than `NS` needs a quote found in the text; option order is shuffled per question; "unverified" answers are counted and a run is flagged when they exceed 20% |
| An implementer that edits or deletes tests | Hidden tests are never in its folder; the starter's own tests are run from pristine copies |
| Run-to-run variance | Repetitions at two levels (spec-writer `--rep`, implementer `--impl-reps`), several readers or judges if wanted; spreads are shown; the comparison names a winner only outside the spread; a single sample is labelled as such |
| A hang or crash in an implementation | Each test runs in its own process with a 30 second limit |

Isolation between roles depends on the roles staying in their folders, which
the prompts tell them to do. Role folders sit next to each other inside the
run folder, so an agent that ignores the instruction could read a sibling
(for example the brief, from the implementer's folder). Each role folder is
self-contained: if your harness can sandbox, mount only that folder, or copy
it elsewhere, run the role, and copy the output file back.

`run_hidden_tests.py` executes code written by the implementer agent. Run it
where that is acceptable.

## Output files of a run

```
<runs>/<run_id>/
    run.json                         problem, method, rep (no role sees this)
    1_spec_writer/                   BRIEF.md, repo/, spec/, PROMPT.md
    spec_frozen/                     the spec as scored
    2_implementer/impl_K/            spec/, repo/, PROMPT.md, IMPL_NOTES.json
    3_reader/full/                   spec/, QUIZ.md, PROMPT.md, answers*.json
    3_reader/skim/                   SPEC_OPENING.txt, QUIZ.md, PROMPT.md, answers*.json
    4_judge/                         spec/, BRIEF.md, repo/, PROMPT.md, judge*.json
    scores/                          spec_check.json, readability.json,
                                     outcome_impl_K.json, quiz.json, judge.json
<runs>/results.json, results.md      written by aggregate.py
```

If a spec has several files, reading order (for the 150-word opening) is: the
file named in an optional one-line `spec/ENTRY` file; otherwise top-level files
whose names start with readme, index, spec, prd, overview or summary; then
alphabetical. The spec-writer prompt asks for `ENTRY` when there is more than
one file. This is the only thing the eval asks of a spec's form.

## Adding or changing a problem

1. Create `problems/<name>/` with `brief.md`, `starter/` (with `tests/`),
   `reference/` (only the files that differ from the starter), `hidden/`
   (unittest files; class names start with `Core`, `Edge` or `Keep`),
   `quiz.json` and `problem.json`. Put the canary string (see `common.py`) in
   a comment in every hidden and reference file and in `quiz.json`.
2. For every hidden test, find the sentence in the brief or the line in the
   starter that justifies it. If there is none, drop the test or widen it.
3. Run `python3 scripts/verify_problems.py`. It must print `OK` for the
   problem.

## Known limits

- Six small problems. Results say how methods compare on small, self-contained
  changes in tiny Python repos. They say little about large codebases, UI
  work, or specs that need research.
- All three headline scores pass through a model in some role (implementer or
  reader). Fix the models, and repeat.
- The quizzes cover the decisions the hidden tests depend on. A spec can be
  clear about those and unclear elsewhere; the judge findings are the only
  measure that looks elsewhere.
- The problems are in this repository. A spec-writer method developed while
  looking at them is tuned to them. Treat them as a held-out set.
