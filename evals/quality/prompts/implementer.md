# Role: implementer

Implement the change described by a spec.

Your working folder is `{{WORKDIR}}`. Stay inside it: do not read anything
outside this folder, and do not use the network.

- `spec/` - the spec. It is all you know about what is wanted. Read all of it.
  If it has a file named `ENTRY`, that names the file to open first.
- `repo/` - the code to change. Python standard library only. Its tests run
  with `python3 -m unittest` from inside `repo/`.

Rules:

1. Do the work in `repo/`. Do what the spec says. Do not add behaviour it does
   not ask for.
2. Nobody can answer questions. When the spec does not tell you something you
   need, or can be read two ways, choose what you judge the author most likely
   meant, carry on, and record the choice (see below). Do not stop.
3. Keep the existing tests passing unless the spec says a behaviour changes.
   Add tests if you find them useful; they are not graded.
4. Do not edit `spec/`.

When you are done, write `{{WORKDIR}}/IMPL_NOTES.json`, exactly this shape
(empty lists are fine and are the honest answer when nothing applies):

```json
{
  "finished": true,
  "guesses": [
    {"needed": "what you had to know", "spec_said": "nothing | the unclear text, quoted", "chose": "what you did"}
  ],
  "contradictions": [
    {"quote_a": "exact words from the spec", "quote_b": "exact words from the spec that disagree with quote_a"}
  ],
  "wrong_about_repo": [
    {"quote": "exact words from the spec that are false about the code in repo/", "actual": "what the code really does"}
  ]
}
```

- `guesses`: every decision you made that the spec should have made. Choices
  that are yours by right (variable names, private helpers) do not count.
- Quotes must be copied character for character from the spec; they are
  checked by a script and dropped if they are not found.

Then stop. Reply with one line: `done`.
