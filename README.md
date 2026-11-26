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

1. In the local environment, archive a project as its owner with `curl`.
2. `GET /v1/projects` does not list the project.
3. `GET /v1/projects?include_archived=true` lists the project.
4. A `PATCH` request to the project returns 409.
```

The rest is for the build: requirements, design decisions and test cases. The full example is
[`golden-example.md`](skills/agent-spec/references/golden-example.md).

- **Skim first, detail after.** Why, Example and Check fit on one screen. Requirements, Design and Cases follow.
- **Only what sources agree on.** The sections are what 13 published design-doc templates and agent-spec guides
  have in common. Summary, non-goals, alternatives, rollout and open questions are not sections.
- **Requirements an agent cannot misread.** One sentence each, in an EARS pattern, with exactly one of MUST,
  SHOULD or MAY.
- **Every requirement has a case.** Cases use real values, and a case marked "Unchanged" protects behaviour that
  works today.
- **Linted.** Structure, length, chunk size, glossary terms and prose style are checked by a script and Vale.

## The six sections

| Layer | Section | What it holds |
|---|---|---|
| Skim | Why | What happens today, what is true afterwards, and the scope in one sentence |
| Skim | Example | One real request and its real response |
| Skim | Check | Numbered steps that prove the change works |
| Build | Requirements | A table of behaviours with IDs, one sentence each |
| Build | Design | Optional. Only what the agent cannot find in the code or decide alone |
| Build | Cases | Tables of `Given`, `When`, `Then`, in groups of at most 8 rows |

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
spec.md:63: E L6 table has 15 rows, maximum is 8; split it under ### sub-headings
spec.md:65: E S7 a spec with Status Approved has no OPEN item
spec.md:99:21:AgentSpec.Vague:G1: 'quickly' is not specific. Give a value, a list or a behaviour.
```

| Rules | Check |
|---|---|
| S1 to S8 | Title and status line, section order, requirement patterns, a worked example, case coverage, open items, file paths |
| L1 to L6 | 25 words a sentence (40 for a requirement), 4 sentences a paragraph, 80 words in Why, 1,200 words in the spec, 20 requirements, 8 rows a table |
| G1 to G4 | No vague words, glossary terms only, active voice, no sentence that opens with "It is" |

The full list is in [`rules.md`](skills/agent-spec/references/rules.md). The language rules are the Simplified
Technical English writing rules that change how a model reads a spec; a project glossary replaces the STE
dictionary.

## Install

```sh
npx skills add zhuasy/agent-spec        # add -g for every project
pnpm dlx skills add zhuasy/agent-spec   # or bunx skills add zhuasy/agent-spec
```

Works with Claude Code, Codex, Cursor and other agents that read skills. Needs `python3` and `bash`. The prose
style rules (G1, G3, G4) need [Vale](https://vale.sh/docs/install); without it the structure, length and glossary
rules still run through `spec_lint.py`.

## What is in the skill

| File | Purpose |
|---|---|
| [`SKILL.md`](skills/agent-spec/SKILL.md) | How to write, lint, review and implement from a spec |
| [`assets/spec-template.md`](skills/agent-spec/assets/spec-template.md) | The blank template |
| [`assets/glossary-template.md`](skills/agent-spec/assets/glossary-template.md) | A blank project glossary |
| [`references/golden-example.md`](skills/agent-spec/references/golden-example.md) | A complete spec that passes the linter |
| [`references/rules.md`](skills/agent-spec/references/rules.md) | Every rule with its ID |
| [`scripts/lint.sh`](skills/agent-spec/scripts/lint.sh) | Runs both linters |

## License

MIT.
