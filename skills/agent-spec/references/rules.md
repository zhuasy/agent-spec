# Spec rules

Every rule has an ID. The linter prints the ID with each finding. `scripts/spec_lint.py` owns the S, L and G2 rules. Vale owns G1, G3 and G4. `scripts/lint.sh` runs both.

## Structure

| ID | Rule |
|---|---|
| S1 | Line 1 is `# Spec: <title>`. The status line has `**Status:**`, `**Decider:**` and `**Links:**`. Status is one of: Draft, In review, Approved, Implemented, Superseded. |
| S2 | The sections are, in this sequence: Why, Example, Check, Requirements, Design, Cases. Design is optional. No other `##` sections. |
| S3 | Requirements has a table `ID \| Requirement`. IDs are `R<number>` and unique. Each requirement is one sentence in an EARS pattern, with exactly one of MUST, SHOULD, MAY. |
| S4 | Example has one worked example in a code block, with real values. |
| S5 | Cases has one or more tables `Given \| When \| Then \| Covers`. Every requirement ID appears in Covers. A row that protects existing behaviour has "Unchanged" in Covers; a spec with no such row gets a warning. |
| S6 | Check is not empty. |
| S7 | An open item is written `OPEN (owner): question`. A spec with Status Approved or Implemented has no open item. |
| S8 | With `--repo`, each file path in the spec exists. |

## EARS patterns for S3

| Kind | Pattern |
|---|---|
| Event | When *trigger*, the *system* MUST *response*. |
| State | While *state*, the *system* MUST *response*. |
| State and event | While *state*, when *trigger*, the *system* MUST *response*. |
| Unwanted input | If *condition*, then the *system* MUST *response*. |
| Always | The *system* MUST *response*. ("A" or "An" is also valid.) |

MUST NOT and SHOULD NOT are valid. A requirement that needs two modal words is two requirements.

## Length

| ID | Rule |
|---|---|
| L1 | A sentence has at most 25 words. A requirement sentence has at most 40, so that the trigger and the response stay together. A code span counts as one word. |
| L2 | A paragraph has at most 4 sentences. A bullet has at most 3 sentences, after an optional bold label. |
| L3 | Why has at most 80 words. |
| L4 | The spec has at most 1200 words outside code blocks. |
| L5 | At most 20 requirements. More than 15 gives a warning. Split a larger spec. |
| L6 | A table has at most 8 rows. Split a longer table into tables under `###` sub-headings. |

## Language

| ID | Level | Rule |
|---|---|---|
| G1 | Error | No vague words: etc, and/or, TBD, appropriate, properly, gracefully, robust, scalable, user-friendly, simply, easily, quickly, fast, best practice, "as needed". No "e.g." or "i.e.". No lowercase "should" or "may". |
| G2 | Error | Use glossary terms. A word in the "Do not use" column of `glossary.md` is an error. |
| G3 | Warning | Use the active voice. Name who acts: the client, the API, the job. |
| G4 | Warning | Do not open a sentence with "It is", "This is" or a similar pronoun. Name the thing. |

These are the Simplified Technical English writing rules that change how a model reads a spec. The STE dictionary is not used; the project glossary replaces it.

## Rules that a person checks

The linter cannot check these. Review them before the status becomes Approved.

- Failure modes: a crash in the middle of the work, two requests at the same time, expiry, partial failure, missing permission, old data.
- Contradictions: a Design line that says more than its requirement, or a case that disagrees with a requirement.
- Duplicates: a fact that appears in two places. Keep one copy.
- Filler: a sentence that does not change what the agent builds.
- Too much "how": internal structure that the codebase already decides.

## Why the sections are in this sequence

The spec uses progressive disclosure. A reader gets the most with the least reading, and stops when they have enough.

| Layer | Sections | Reader |
|---|---|---|
| Skim | Why, Example, Check | A person who wants to know what changes and how to see it work. About one screen. |
| Build | Requirements, Design, Cases | The agent that implements the change, and the person who reviews the detail. |

Cases is last because it is reference material for tests.

## Chunks

Each part of the spec is a small chunk with a label, so that a reader can scan for the part they need.

- One idea for each sentence, one behaviour for each requirement, one fact for each bullet.
- Short paragraphs. Use a list when a paragraph holds several separate facts.
- A bold label at the start of a Design bullet names the topic.
- Cases go in groups of at most 8 rows, each under a `###` sub-heading that names the group.
- Check is a numbered list of steps.

L2 and L6 enforce the limits. The labels and the grouping are for a person to judge.

## Where the sections come from

The content is what 13 published templates and guides have in common. All of them have the reason for the change and the change itself. Every source written for coding agents also states the change as behaviour that can be checked. The sections that only some sources have were cut: summary, goals and non-goals, alternatives, cross-cutting concerns, rollout, open questions, file maps. Their useful content has a place in the sections that remain:

| Cut section | Where the content goes |
|---|---|
| Summary | The title, Why and Example. |
| Non-goals | One scope sentence at the end of Why. |
| Must not change | A case with "Unchanged" in Covers, so that a test protects it. |
| Alternatives | A Design line that forbids the tempting approach and gives the reason. |
| Security, privacy, rollout | A requirement when it is behaviour; a Design line when it is a constraint. |
| Open questions | An inline `OPEN (owner): question`. None can remain when the status is Approved. |
| File map | A Design line, only for a fact that the agent cannot find in the code. |
