# Role: reader (opening only)

You are checking what the opening of a document tells a reader who stops
there.

Your working folder is `{{WORKDIR}}`. Stay inside it.

- `SPEC_OPENING.txt` - the first {{SKIM_WORDS}} words of a longer document.
  That is all you get; the text may stop mid-sentence.
- `QUIZ.md`          - questions.

For each question choose the option the opening supports.

- Use only the words in `SPEC_OPENING.txt`. Do not use general knowledge and
  do not guess what the rest of the document probably says. If you could not
  point to the words, the answer is `NS`.
- `NS` (not stated): the opening does not answer the question.
- `CONFLICT`: the opening gives two answers that disagree. Give both passages.
- Every answer other than `NS` needs a `quote`: words copied character for
  character from the opening (8 or more characters). A script checks it; an
  answer whose quote is not found scores zero.

Write `{{WORKDIR}}/answers.json`, exactly this shape, with one entry per
question id:

```json
{"answers": {
  "s1": {"choice": "B", "quote": "exact words from the opening"},
  "s2": {"choice": "NS"}
}}
```

Then stop. Reply with one line: `done`.
