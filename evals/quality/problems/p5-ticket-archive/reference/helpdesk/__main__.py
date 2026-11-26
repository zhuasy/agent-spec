# reference implementation - EVAL-CANARY-7f3a9c1e-quality - never show to a role
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from .config import load_config
from .repo import TicketRepo, parse_time


def build_parser():
    parser = argparse.ArgumentParser(prog="helpdesk")
    parser.add_argument("--data", required=True)
    parser.add_argument("--config")
    parser.add_argument("--now")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search")
    p_search.add_argument("--status", choices=["open", "closed"])
    p_search.add_argument("--text")
    p_search.add_argument("--include-archived", action="store_true")

    for name in ("show", "close", "reopen"):
        p = sub.add_parser(name)
        p.add_argument("id", type=int)

    sub.add_parser("overdue")
    sub.add_parser("archive")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    repo = TicketRepo(args.data)

    try:
        if args.command == "search":
            for t in repo.search(status=args.status, text=args.text,
                                 include_archived=args.include_archived):
                print("%d\t%s\t%s" % (t["id"], t["status"], t["title"]))
        elif args.command == "show":
            print(json.dumps(repo.get(args.id), indent=2))
        elif args.command == "close":
            repo.close(args.id, now)
            repo.save()
        elif args.command == "reopen":
            repo.reopen(args.id)
            repo.save()
        elif args.command == "overdue":
            limit = now - timedelta(hours=config["sla_hours"])
            for t in repo.search(status="open"):
                if parse_time(t["created_at"]) < limit:
                    print(t["id"])
        elif args.command == "archive":
            count = repo.archive_old(now, config["archive_after_days"])
            repo.save()
            print("archived %d" % count)
    except KeyError as exc:
        print("error: no ticket %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
