<h1 align="center">agent-spec</h1>

<p align="center">
  <b>One short spec that a person writes and a coding agent builds from.</b><br>
  A PRD and a design doc merged into six sections, with a linter that keeps it short, concrete and unambiguous.
</p>

<p align="center">
  <code>npx skills add zhuasy/agent-spec</code>
</p>

Ask your agent for a spec: *"turn this ticket into a spec an agent can build from"*. It interviews you for the
decisions only you know, writes the spec, and lints it. A person can stop after the first three sections:

```markdown
# Spec: Archive a project instead of deleting it

## Why

The project list shows every project of an account and has no filter. Owners delete finished
projects to shorten the list. Deleting a project also removes its tasks. Support restored 41
deleted projects from backups in October.

After this change, an owner can archive a project. An archived project leaves the default list
and rejects write requests. Archiving preserves the project and its tasks.

## Example

POST /v1/projects/prj_301/archive   →   200 {"id": "prj_301", "archived_at": "2026-03-04T10:15:00Z"}

## Check

1. Archive a project as its owner with `curl`, in the local environment.
2. Send `GET /v1/projects`. The list does not have the project.
3. Send `GET /v1/projects?include_archived=true`. The list has the project.
4. Send a `PATCH` request to the project. The response is 409.
```

The rest is for the build: requirements, design decisions and test cases, each collapsed behind a "Show…" line.
The full example is
[`golden-example.md`](skills/agent-spec/references/golden-example.md).

- **Skim first, detail on demand.** Why, Example and Check fit on one screen. Requirements, Design and Cases are
  collapsed until the reader opens them.
- **Groups of four.** A table has at most 4 rows, a list 4 items, a section 4 groups.
- **A page to read.** `view.py` turns a spec into one HTML page with a sidebar, light and dark themes, glossary
  hovers, and links from each case to its requirements.
- **Only what sources agree on.** The sections are what 13 published design-doc templates and agent-spec guides
  have in common. Summary, non-goals, alternatives, rollout and open questions are not sections.
- **Requirements an agent cannot misread.** One sentence each, in an EARS pattern, with exactly one of MUST,
  SHOULD or MAY.
- **Every requirement has a case.** Cases use real values, and a case marked "Unchanged" protects behaviour that
  works today.
- **Nothing invented.** Each name, number, date and ticket in the status line and in Why must be in a sources
  file that holds the person's own words. The linter fails the spec if one is not.
- **Linted.** Structure, length, chunk size, glossary terms and prose style are checked by a script and Vale.

## The six sections

| Layer | Section | What it holds |
|---|---|---|
| Skim | Why | What happens today, what is true afterwards, and the scope in one sentence |
| Skim | Example | One real request and its real response |
| Skim | Check | Numbered steps, each one a verb and the result to expect |
| Build | Requirements | A table of behaviours with IDs, one sentence each |
| Build | Design | Optional. Only what the agent cannot find in the code or decide alone |
| Build | Cases | Tables of `Given`, `When`, `Then`, in groups of at most 4 rows |

## The linter

```sh
skills/agent-spec/scripts/lint.sh path/to/spec.md            # structure, lengths, glossary, prose style
skills/agent-spec/scripts/lint.sh path/to/spec.md --repo .   # also check that each file path exists
skills/agent-spec/scripts/lint.sh path/to/spec.md --strict   # warnings fail too
```

Each finding names a rule:

```
spec.md:20: E S3 R4 must be one sentence in an EARS pattern (see references/rules.md)
spec.md:20: E G2 "server" is not a glossary term; use "API"
spec.md:63: E L6 table has 8 rows, maximum is 4; split it into groups under ### sub-headings
spec.md:43: E S9 start the summary with "Show" and say what opens, for example "Show the 8 requirements"
spec.md:65: E S7 a spec with Status Approved has no OPEN item
spec.md:99:21:AgentSpec.Vague:G1: 'quickly' is not specific. Give a value, a list or a behaviour.
```

| Rules | Check |
|---|---|
| S1 to S10 | Title and status line, section order, requirement patterns, a worked example, case coverage, verb-first check steps, open items, file paths, a collapsed build layer, facts that are in the sources file |
| L1 to L6 | 25 words a sentence (40 for a requirement, a warning above 20), 4 sentences a paragraph, 100 words in Why, 1,200 words in the spec, 16 requirements, and groups of four: 4 rows a table, 4 items a list, 4 groups a section |
| G1 to G5 | No vague words, glossary terms only, active voice, no "It is" or "There is" openers, no weak verbs |

The full list is in [`rules.md`](skills/agent-spec/references/rules.md). The language rules are the Simplified
Technical English writing rules that change how a model reads a spec; a project glossary replaces the STE
dictionary.

## The viewer

```sh
python3 skills/agent-spec/scripts/view.py path/to/spec.md --open
```

Writes `spec.html` next to the spec: one self-contained file, no network requests. The skim layer is open, each
build section opens from its "Show…" control, a pointer on a requirement lights the cases that cover it, and a
glossary term shows its meaning on hover.

## Install

```sh
npx skills add zhuasy/agent-spec        # add -g for every project
pnpm dlx skills add zhuasy/agent-spec   # or bunx skills add zhuasy/agent-spec
```

Works with Claude Code, Codex, Cursor and other agents that read skills. Needs `python3` and `bash`. The prose
style rules (G1, G3, G4, G5) need [Vale](https://vale.sh/docs/install); without it the structure, length and glossary
rules still run through `spec_lint.py`.

## Updates

The skill updates itself. Before each use the agent runs `scripts/self_update.sh`, which runs
`npx skills update agent-spec` at most once a day and never blocks the task. Set `AGENT_SPEC_NO_UPDATE=1` to
switch it off, or run `npx skills update agent-spec` yourself.

## Evals

`evals/` holds two eval sets. `evals/briefs` with `evals/grade.py` checks that a spec written from a brief
passes the linter and invents nothing. `evals/quality` compares any way of writing a spec on six problems: hidden
tests score what an agent builds from the spec, and quizzes score how clear the spec is and what a reader gets
from its first 150 words. Each folder has a README with the steps.

## What is in the skill

| File | Purpose |
|---|---|
| [`SKILL.md`](skills/agent-spec/SKILL.md) | How to write, lint, review and implement from a spec |
| [`assets/spec-template.md`](skills/agent-spec/assets/spec-template.md) | The blank template |
| [`assets/glossary-template.md`](skills/agent-spec/assets/glossary-template.md) | A blank project glossary |
| [`references/golden-example.md`](skills/agent-spec/references/golden-example.md) | A complete spec that passes the linter |
| [`assets/sources-template.md`](skills/agent-spec/assets/sources-template.md) | A blank sources file |
| [`references/rules.md`](skills/agent-spec/references/rules.md) | Every rule with its ID |
| [`scripts/lint.sh`](skills/agent-spec/scripts/lint.sh) | Runs both linters |
| [`scripts/view.py`](skills/agent-spec/scripts/view.py) | Renders a spec as one HTML page |
| [`scripts/self_update.sh`](skills/agent-spec/scripts/self_update.sh) | Updates the skill, at most once a day |

## License

MIT.
