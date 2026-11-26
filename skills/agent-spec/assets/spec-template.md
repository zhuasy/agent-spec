# Spec: <what changes, in a few words>

**Status:** Draft · **Decider:** <the one person who answers a blocking question> · **Links:** <ticket, incident, design file>

- OPEN (<owner>): <a question that is not decided, and the requirement that it blocks. Delete this line if there is none.>

## Why

<!-- Delete every comment in this file before you finish; a comment above this line gives a lint warning.
     The first three sections are for a person who skims. The last three are for the build, and are collapsed.
     Groups of four: at most 4 rows in a table, 4 items in a list, 4 groups in a section.
     At most 100 words, in this sequence: what happens today; what is true after the change;
     the one behaviour that must not change or must never happen; the scope.
     Give a number only if the person or the repository gave it. Do not invent a name, a count or a link:
     write OPEN (owner): question in its place.
     Record each fact in <spec-name>.sources.md; the linter checks Why and the status line against it. -->

## Example

<!-- One real input and its real output, at the entry point that a client uses.
     One line of introduction that shows how a user reaches the change: the command, the option or the request. -->

```
<request or call, and its response or result>
```

## Check

<!-- The steps that a person or an agent runs, and the result that proves the change works.
     A numbered list. Start each step with a verb, and put the expected result in the same step. -->

1. <Verb> <what to do>. <The result that proves the change.>

## Requirements

<!-- One behaviour for each row. One sentence, one EARS pattern, one of MUST / SHOULD / MAY:
     When <trigger>, the <system> MUST <response>.
     While <state>, the <system> MUST <response>.
     If <condition>, then the <system> MUST <response>.
     The <system> MUST <response>. -->

<details>
<summary>Show the <number> requirements</summary>

### <Group of at most 4 requirements>

| ID | Requirement |
|---|---|
| R1 | When <trigger>, the <system> MUST <response>. |

</details>

## Design

<!-- Optional. Only what the agent cannot find in the code or decide alone:
     a schema or interface that other code depends on, a decision and its reason,
     an approach that the agent must not use, a deploy or rollback step.
     One fact for each bullet, with a bold label that names the topic. Do not repeat a requirement.
     Delete the section if it is empty. -->

<details>
<summary>Show the <number> design decisions</summary>

### <Group of at most 4 decisions>

- **<Topic>.** <decision, and the reason if the agent cannot infer it>

</details>

## Cases

<!-- Real values. Every requirement ID appears in Covers.
     Add a row with "Unchanged" in Covers for each behaviour that works today and that the change must keep.
     Include the case that is easiest to get wrong: empty, duplicate, no permission,
     two at the same time, too large, old data.
     At most 4 rows in one table and at most 4 groups. Group the cases under ### sub-headings. -->

<details>
<summary>Show the <number> cases</summary>

<setup that every case shares, as a list of at most 4 items>

### <Group of cases>

| Given | When | Then | Covers |
|---|---|---|---|
| <state> | <action> | <result> | R1 |
| <state> | <action that works today> | <the same result as today> | Unchanged |

</details>
