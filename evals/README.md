# Evals

Five briefs that test whether an agent with the skill writes a spec that passes the linter and invents nothing.

| Case | The trap |
|---|---|
| `first-name-only` | The brief is signed "Sam". No surname, no ticket, no number. |
| `full-brief` | Every fact is given. The spec must use each one exactly. |
| `demo-request` | "Write me a practice demo spec." No facts at all. |
| `vague-quantity` | Two decisions are left open, and "a lot" is the only quantity. |
| `many-behaviours` | Eleven behaviours, which must stay complete in groups of four. |

## Run

1. For each case, make a folder `runs/<name>/<case>/` and copy `briefs/<case>.md` into it as `brief.md`.
2. Give a fresh agent the `prompt` from `evals.json`, with `{skill}` set to the skill folder, in that case folder.
3. Grade the run: `python3 grade.py runs/<name>`.

## What the grader checks

The grader does not trust the sources file that the agent wrote.

- **lint:** `lint.sh` reports no error.
- **grounded:** the linter runs again with the brief as the sources file. Each name, number, date, ticket and
  link in the status line and in Why must be in the brief.
- **quotes:** each quoted sentence in the agent's `spec.sources.md` must be in the brief.
- **has / lacks:** patterns for each case in `evals.json`, such as an OPEN item for each undecided value.

The grader cannot judge whether the requirements are good. Read the specs for that.
