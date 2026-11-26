# todo

A tiny command-line todo list. Standard library only.

    python3 -m todo add "buy milk"
    python3 -m todo list            # open tasks
    python3 -m todo list --all      # open and done
    python3 -m todo done 3

Tasks live in one JSON file: `--file PATH`, or the `TODO_FILE` environment
variable, or `todo.json` in the current directory.

Tests: `python3 -m unittest`
