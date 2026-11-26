---
name: agent-spec
description: Write, lint, review or implement an agent spec - one short document that merges a PRD and a high-level design doc, written by a person and handed to a coding agent to build. Use this whenever the user wants a spec, PRD, design doc, RFC, tech spec or feature brief that an AI agent will implement, asks to turn an idea or ticket into something an agent can code from, asks to check or tighten such a document, or hands over a file that starts with "# Spec:" to build. Includes a template that discloses in layers (skim first, build detail after), a golden example, a glossary format, controlled-language rules based on Simplified Technical English and EARS, and a linter.
compatibility: Needs python3 and bash. The prose style checks need Vale (https://vale.sh); the structure checks run without it.
---

# Agent spec

An agent spec is one document that replaces a PRD plus a design doc for a single change. A person makes the decisions and writes them down; a coding agent builds from the result.

It uses progressive disclosure and chunking: the first three sections tell a person who skims what changes and how to see it work, and the last three hold the detail for the build.

| Layer | Section | What it holds |
|---|---|---|
| Skim | **Why** | What happens today, what is true afterwards, and the scope in one sentence. This is how the agent settles choices the spec did not foresee. |
| Skim | **Example** | One real request and its real response. |
| Skim | **Check** | The steps and the result that prove the change works. |
| Build | **Requirements** | A table of behaviours with IDs, one sentence each. |
| Build | **Design** | Optional. Only what the agent cannot find in the code or decide alone. |
| Build | **Cases** | A table of cases with real values. Every requirement has a row. |

The content is what published design-doc templates and agent-spec guides all share: the reason for the change, the change itself, and, in every source written for agents, a way to check it. Everything else that templates usually carry (summary, non-goals, alternatives, rollout, open questions, file maps) was cut as a section. An agent treats spec text as something to act on, so a section that exists to be filled in turns into speculative code. The useful content of those sections still has a place; [references/rules.md](references/rules.md) lists where each one goes.

## Before you start

Run `scripts/self_update.sh`. It checks the skill's source at most once a day and never blocks the task.

- `updated`: the skill changed. Read this file again before you continue, and tell the user that the skill updated.
- `current` or `skipped: ...`: continue.

A user who does not want this sets `AGENT_SPEC_NO_UPDATE=1`.

## Files

| File | Use it for |
|---|---|
| [assets/spec-template.md](assets/spec-template.md) | Copy this to start a spec. The comments say what each section needs. |
| [assets/glossary-template.md](assets/glossary-template.md) | Copy this to start a project glossary. |
| [assets/sources-template.md](assets/sources-template.md) | Copy this to record where each fact in a spec came from. |
| [references/golden-example.md](references/golden-example.md) | A complete spec that passes the linter. Read it before you write your first spec, and imitate its level of detail. |
| [references/golden-example-glossary.md](references/golden-example-glossary.md) | The glossary for the golden example. |
| [references/golden-example.sources.md](references/golden-example.sources.md) | The sources file for the golden example. |
| [references/rules.md](references/rules.md) | Every rule with its ID. Read it when the linter reports an ID you need to understand. |
| [scripts/lint.sh](scripts/lint.sh) | Runs both linters. |
| [scripts/view.py](scripts/view.py) | Renders a spec as one HTML page for a person to read. |
| [scripts/self_update.sh](scripts/self_update.sh) | Updates the skill from its source, at most once a day. |

## Writing a spec

The person owns the decisions. Your job is to get those decisions out of their head, check them against the code, and write them in a form an agent cannot misread.

1. **Place the files.** Use the repository's convention for specs if it has one; otherwise `docs/specs/<short-name>.md`. Put `glossary.md` in the same folder, because the linter looks for it there.
2. **Ask for what only the person knows.** The problem and its cost, the scope, what must keep working, and any decision already made. Ask these together, not one at a time. Do not invent a decision to fill a gap: write `- OPEN (owner): question` in a list directly under the status line, and name the requirement that it blocks. A reader then sees first what is not decided. The linter refuses an open item in any other place, and refuses an Approved spec that still has one.
3. **Invent nothing. Record where each fact came from.** Write `<spec-name>.sources.md` beside the spec, from [assets/sources-template.md](assets/sources-template.md). Copy the person's words into it exactly, and list each fact that you took from the repository or a ticket with its path or link. Never write a quote that the person did not give. The linter then checks that each name, number, date, ticket and link in the status line and in Why is in that file. If a fact is not there, ask the person, or write `OPEN (owner): question` in its place. A Why with no number is correct. A Decider with only a first name is correct when the person gave only a first name. Values in Example and Cases are test data that you choose; they must be exact, and they are not claims about the world.
4. **Write Why, Example and Check so that they stand alone.** A person who reads only those three sections must come away knowing what changes and how to see it work. Many readers stop after the first 150 words, so put nothing before Why except the title, the status line and the open items. Why says four things in at most 100 words: what happens today, what is true afterwards, the one behaviour that must not change or must never happen, and the scope. The first line of Example shows how a user reaches the change: the command, the option or the request.
5. **Write each requirement as one EARS sentence.** One response for each row. If a sentence needs two modal words, it is two requirements. When a requirement prints a message or returns an error, give the exact text in a case, or say that the wording is free; an implementer otherwise has to guess it.
6. **Write the cases with real values.** A date, an amount, an ID. Every requirement needs a row. Add a row marked "Unchanged" for each behaviour that works today and must keep working; a test then protects it, which a sentence in a scope list cannot do. Include the case that is easiest to get wrong: empty, duplicate, no permission, two at the same time, too large, old data.
7. **Keep Design to what the agent cannot work out.** Before each line, ask whether the agent could find the fact in the code, and whether it would look. If both are yes, leave the line out. What belongs: a schema or interface other code depends on, a decision with its reason, an approach the agent must not use, a deploy or rollback step. Leave function layout, naming and file structure to the agent.
8. **State each fact once.** A value that appears in a requirement and again in Design will drift, and the agent cannot tell which copy is right.
9. **Add glossary terms as you go.** When you notice two words for one thing, pick one and add the other to "Do not use".
10. **Collapse the build layer.** Put all of Requirements, Design and Cases each in one `<details>` block. Start its `<summary>` with "Show" and say what opens: "Show the 8 requirements". Leave Why, Example and Check open.
11. **Write in chunks, with the main point first.** One idea for each sentence and one fact for each bullet. Start each Design bullet with a bold label and each Check step with a verb. Use groups of four: at most 4 rows in a table, 4 items in a list and 4 `###` groups in a section, because a reader holds about four new items at one time. A reader scans the first words of each chunk, finds the one they need, and skips the rest.
12. **Run the linter and fix the findings.** Then do the review below, because the linter cannot find a missing failure mode.
13. **Say what you decided.** When you hand over the spec, list each requirement and each Design line that the person did not give you. Those are your proposals. The status stays Draft until the person accepts them; only the person sets Approved.

Build commands, test commands and standing rules for agents do not belong in a spec. They belong in the repository's agent file (`AGENTS.md` or `CLAUDE.md`), because a copy in each spec goes stale.

## Linting

```bash
scripts/lint.sh path/to/spec.md                # structure, lengths, requirements, glossary, prose style
scripts/lint.sh path/to/spec.md --repo .       # also check that each file path in the spec exists
scripts/lint.sh path/to/spec.md --strict       # warnings fail too
scripts/lint.sh path/to/spec.md --glossary g.md --sources s.md
```

The script exits 0 when the spec passes, 1 when a check fails, and 2 when Vale is missing. Each finding has a rule ID that [references/rules.md](references/rules.md) explains. If Vale is not installed, `python3 scripts/spec_lint.py` still runs the structure, length and glossary rules; tell the user that the prose style rules did not run.

Fix a finding by changing the text, not by working around the rule. A requirement over 40 words usually hides two behaviours. A passive sentence usually hides which component acts.

## Viewing a spec

```bash
python3 scripts/view.py path/to/spec.md            # writes path/to/spec.html
python3 scripts/view.py path/to/spec.md --open     # and opens it in a browser
```

The page is one self-contained file with no network requests. Offer it when a person wants to read or review a spec:

- The skim layer is open and each build section opens from a "Show…" control.
- A sidebar lists the sections and their groups.
- A pointer on a requirement lights the cases that cover it, and each case links back to its requirements.
- A glossary term shows its meaning on hover or focus.
- A badge shows the result of the structure linter. Light and dark themes follow the system.

## Reviewing a spec

Run the linter first, then check what it cannot:

- **Failure modes.** For each requirement that writes data or calls another system, ask what happens if the process stops halfway, if two requests arrive together, and if the data is old.
- **Contradictions and duplicates.** Compare each Design line with the requirements and each case with its requirement.
- **Filler.** For each sentence, ask whether the agent would build something different without it. If not, cut it.

Report findings with the requirement ID or line, the problem, and a suggested fix. Skip style preferences: a reviewer who is asked for problems always finds some, and fixing every one adds bloat.

## Implementing from a spec

1. **Read the whole spec before you write code.**
2. **When parts disagree, the cases win,** then the requirements, then Design, then Why. If the spec and the code disagree about how something behaves today, trust the code and report the difference.
3. **Ask before you code, in one batch,** when the spec leaves open something that changes user-visible behaviour, permissions, stored data or a shared interface, when two requirements conflict, or when a case cannot pass as written. Decide routine, reversible details yourself from the surrounding code.
4. **Write one test for each row of the cases table,** then run the Check.
5. **Report** what you ran, what passed, the assumptions you made, and anything you could not verify.
