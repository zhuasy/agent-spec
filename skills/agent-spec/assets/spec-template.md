# Spec: <what changes, in a few words>

**Status:** Draft · **Decider:** <the one person who answers a blocking question> · **Links:** <ticket, incident, design file>

<!-- The first three sections are for a person who skims. The last three are for the build. -->

## Why

<!-- At most 80 words. What happens today, with a number. What is true after the change.
     End with one sentence that gives the scope. -->

## Example

<!-- One real input and its real output, at the entry point that a client uses. One line of introduction. -->

```
<request or call, and its response or result>
```

## Check

<!-- The steps that a person or an agent runs, and the result that proves the change works. -->

1. <step>
2. <result that proves the change>

## Requirements

<!-- One behaviour for each row. One sentence, one EARS pattern, one of MUST / SHOULD / MAY:
     When <trigger>, the <system> MUST <response>.
     While <state>, the <system> MUST <response>.
     If <condition>, then the <system> MUST <response>.
     The <system> MUST <response>. -->

| ID | Requirement |
|---|---|
| R1 | When <trigger>, the <system> MUST <response>. |

## Design

<!-- Optional. Only what the agent cannot find in the code or decide alone:
     a schema or interface that other code depends on, a decision and its reason,
     an approach that the agent must not use, a deploy or rollback step.
     One fact for each bullet, with a bold label that names the topic. Do not repeat a requirement.
     Delete the section if it is empty. -->

- **<Topic>.** <decision, and the reason if the agent cannot infer it>

## Cases

<!-- Real values. Every requirement ID appears in Covers.
     Add a row with "Unchanged" in Covers for each behaviour that works today and that the change must keep.
     Include the case that is easiest to get wrong: empty, duplicate, no permission,
     two at the same time, too large, old data.
     At most 8 rows in one table. Group the cases under ### sub-headings. -->

<setup that every case shares, as a short list>

### <Group of cases>

| Given | When | Then | Covers |
|---|---|---|---|
| <state> | <action> | <result> | R1 |
| <state> | <action that works today> | <the same result as today> | Unchanged |
