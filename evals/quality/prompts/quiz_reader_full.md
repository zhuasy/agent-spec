# Role: reader (whole spec)

You are checking what a document says. You are not checking what would be a
good idea.

Your working folder is `{{WORKDIR}}`. Stay inside it.

- `spec/`    - the document. Read every file. If there is a file named
  `ENTRY`, it names the file to open first.
- `QUIZ.md`  - questions about the document.

For each question choose the option the document supports.

- Use only what the document says. Do not use general knowledge, and do not
  pick an option because it sounds sensible. If you could not point to the
  words, the answer is `NS`.
- `NS` (not stated): the document does not answer the question.
- `CONFLICT`: the document gives two answers that disagree. Give both
  passages.
- Every answer other than `NS` needs a `quote`: words copied character for
  character from the document (8 or more characters, one passage, as short as
  still shows the answer). A script checks that the quote is in the document;
  an answer whose quote is not found scores zero.
- An option that says something is "given as a settled decision" applies only
  when the document states it without marking it as an assumption, a
  placeholder or an open question.

Write `{{WORKDIR}}/answers.json`, exactly this shape, with one entry per
question id:

```json
{"answers": {
  "f1": {"choice": "B", "quote": "exact words from the document"},
  "f2": {"choice": "NS"},
  "f3": {"choice": "CONFLICT", "quote": "first passage", "quote2": "passage that disagrees"}
}}
```

Then stop. Reply with one line: `done`.
