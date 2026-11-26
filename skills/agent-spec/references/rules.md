# Spec rules

Every rule has an ID. The linter prints the ID with each finding. `scripts/spec_lint.py` owns the S, L and G2 rules. Vale owns G1, G3, G4 and G5. `scripts/lint.sh` runs both.

## Structure

| ID | Rule |
|---|---|
| S1 | Line 1 is `# Spec: <title>`. The status line has `**Status:**`, `**Decider:**` and `**Links:**`. A comment before Why gives a warning. Status is one of: Draft, In review, Approved, Implemented, Superseded. |
| S2 | The sections are, in this sequence: Why, Example, Check, Requirements, Design, Cases. Design is optional. No other `##` sections. |
| S3 | Requirements has a table `ID \| Requirement`. IDs are `R<number>` and unique. Each requirement is one sentence in an EARS pattern, with exactly one of MUST, SHOULD, MAY. |
| S4 | Example has one worked example in a code block, with real values. |
| S5 | Cases has one or more tables `Given \| When \| Then \| Covers`. Every requirement ID appears in Covers. A row that protects existing behaviour has "Unchanged" in Covers; a spec with no such row gets a warning. |
| S6 | Check is a numbered list. Each step starts with a verb (Send, Open, Run) and gives the result to expect. |
| S7 | An open item is written `OPEN (owner): question`, as a list item directly under the status line, and nowhere else (the Decider field may hold one). A spec with Status Approved or Implemented has no open item. |
| S8 | With `--repo`, each file path in the spec exists. |
| S9 | Requirements, Design and Cases each sit in one `<details>` block. Its `<summary>` starts with "Show" and says what opens ("Show the 8 requirements"). A number in the summary matches the content. Why, Example and Check are never collapsed. |
| S10 | Each fact in the status line and in Why is in the sources file, `<spec-name>.sources.md`: each word of the Decider's name, each link, and each number, month, weekday and ticket ID. An OPEN item is exempt. A spec with no sources file gets a warning. |

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
| L1 | A sentence has at most 25 words; more than 20 gives a warning. A requirement sentence has at most 40, so that the trigger and the response stay together. A code span counts as one word. |
| L2 | A paragraph has at most 4 sentences. A bullet has at most 3 sentences, after an optional bold label. |
| L3 | Why has at most 100 words. |
| L4 | The spec has at most 1200 words outside code blocks. |
| L5 | At most 16 requirements. More than 12 gives a warning. Split a larger spec. |
| L6 | A group has at most 4 items: 4 rows in a table, 4 items in a list, 4 `###` groups in a section. Split a longer one into groups under `###` sub-headings. |

## Language

| ID | Level | Rule |
|---|---|---|
| G1 | Error | No vague words: etc, and/or, TBD, appropriate, properly, gracefully, robust, scalable, user-friendly, simply, easily, quickly, fast, best practice, "as needed". No "e.g." or "i.e.". No lowercase "should" or "may". |
| G2 | Error | Use glossary terms. A word in the "Do not use" column of `glossary.md` is an error. |
| G3 | Warning | Use the active voice. Name who acts: the client, the API, the job. |
| G4 | Warning | Do not open a sentence with "It is", "This is", "There is" or "There are". Name the thing that acts. |
| G5 | Warning | No weak verbs: occur, happen, take place. Name the actor and use an exact verb. |

These are the Simplified Technical English writing rules that change how a model reads a spec. The STE dictionary is not used; the project glossary replaces it.

## Rules that a person checks

The linter cannot check these. Review them before the status becomes Approved.

- Invented facts: S10 checks the status line and Why against the sources file. Read the sources file yourself: each quote must be words that the person gave. Check also for a claim in words that S10 cannot see ("most owners", "a common complaint").
- Invented decisions: a requirement or a Design line that the person did not give is a proposal. Accept or reject each one before the status becomes Approved.
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

The build layer is collapsed. Each build section is a `<details>` block, so a Markdown viewer shows one line ("Show the 8 requirements") until the reader opens it. An agent reads the source and sees all of it. `scripts/view.py` renders the same layers as an HTML page.

## Chunks

Each part of the spec is a small chunk with a label, so that a reader can scan for the part they need.

- One idea for each sentence, one behaviour for each requirement, one fact for each bullet.
- Short paragraphs. Use a list when a paragraph holds several separate facts.
- A bold label at the start of a Design bullet names the topic.
- Groups of four. A reader holds about four new items at one time, so a table has at most 4 rows, a list has at most 4 items, and a section has at most 4 groups.
- Requirements, Design bullets and Cases go in groups under `###` sub-headings that name the group.
- Check is a numbered list of steps.

L2 and L6 enforce the limits. The labels and the grouping are for a person to judge.

## The techniques behind the rules

| Technique | What it asks for | Where the spec applies it |
|---|---|---|
| Chunking | Small labelled units; about 4 items in a group | L2, L6, bold labels in Design, `###` groups of four |
| Progressive disclosure | The essential part first, detail on demand behind a labelled control, no repeated text between layers | S2 and S9: the skim layer is open, the build layer is collapsed; one copy of each fact |
| Bottom line up front | The most important information first, at every level | Why is first; a label starts each Design bullet; the result is in each Check step |
| Clear sentences | Active voice, exact verbs, one idea, 20 words or fewer | L1, G3, G4, G5 |
| One term for one concept | No synonyms for a technical term | G2 and the glossary |
| Parallel lists | Every step starts with an imperative verb | S6 |
| Separate document types (Diataxis) | Do not mix explanation, procedure and reference | Why explains; Check is a procedure; Requirements and Cases are reference |
| Minimalism | Only text that supports the task | L3, L4, and the review for filler |
| Controlled language | Restricted grammar and vocabulary | EARS patterns in S3; the Simplified Technical English writing rules |

One piece of guidance does not apply: a line width of 50 to 75 characters. A viewer sets the width of rendered Markdown, and a table row cannot wrap in the source.

## Where the sections come from

The content is what 13 published templates and guides have in common. All of them have the reason for the change and the change itself. Every source written for coding agents also states the change as behaviour that can be checked. The sections that only some sources have were cut: summary, goals and non-goals, alternatives, cross-cutting concerns, rollout, open questions, file maps. Their useful content has a place in the sections that remain:

| Cut section | Where the content goes |
|---|---|
| Summary | The title, Why and Example. |
| Non-goals | One scope sentence at the end of Why. |
| Must not change | A case with "Unchanged" in Covers, so that a test protects it. |
| Alternatives | A Design line that forbids the tempting approach and gives the reason. |
| Security, privacy, rollout | A requirement when it is behaviour; a Design line when it is a constraint. |
| Open questions | A list of `OPEN (owner): question` items under the status line. None can remain when the status is Approved. |
| File map | A Design line, only for a fact that the agent cannot find in the code. |
