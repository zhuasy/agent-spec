"""Command line for the todo list."""
# reference implementation - EVAL-CANARY-7f3a9c1e-quality - never show to a role
import argparse
import os
import sys

from .store import Store


def format_task(task):
    mark = "x" if task["done"] else " "
    line = "[%s] %d %s" % (mark, task["id"], task["title"])
    for tag in sorted(task.get("tags", [])):
        line += " #" + tag
    return line


def build_parser():
    parser = argparse.ArgumentParser(prog="todo")
    parser.add_argument("--file", default=os.environ.get("TODO_FILE", "todo.json"))
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("title")
    p_add.add_argument("--tag", action="append", default=[])

    p_list = sub.add_parser("list")
    p_list.add_argument("--all", action="store_true")
    p_list.add_argument("--tag", action="append", default=[])

    p_done = sub.add_parser("done")
    p_done.add_argument("id", type=int)

    sub.add_parser("tags")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    store = Store(args.file)
    try:
        if args.command == "add":
            print("added %d" % store.add(args.title, tags=args.tag))
        elif args.command == "list":
            for task in store.list(include_done=args.all, tags=args.tag):
                print(format_task(task))
        elif args.command == "done":
            store.done(args.id)
            print("done %d" % args.id)
        elif args.command == "tags":
            for tag, count in store.tag_counts():
                print("%s %d" % (tag, count))
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    except KeyError as exc:
        print("error: no task %s" % exc, file=sys.stderr)
        return 1
    return 0
