(Chat message from a teammate, Ines, in the team channel)

hey, can we get tags in the todo tool? I keep one file for home + work and it's a mess.

what I'm picturing:

    todo add "buy milk" --tag home --tag errands
    todo list --tag home

list should show them after the title, like

    [ ] 3 buy milk #errands #home

if I pass --tag twice on list I want the things that have both, not either. --all should still work together with it.

tags shouldn't care about case, Home and home are the same thing, just store them lowercase.

keep tags simple: letters, digits, dash. If someone types `--tag "to do"` or something with a # in it, that's an error (same style as the other errors, exit 1) and the task doesn't get saved.

also a `todo tags` command would be nice: each tag and how many open tasks have it, biggest first

    home 4
    work 2

Dana and a few others have todo.json files from the current version, those have to keep working as they are, no migration step please.

not needed now: renaming tags, removing a tag from a task. maybe later.
