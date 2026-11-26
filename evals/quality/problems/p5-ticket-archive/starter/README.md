# helpdesk

Ticket store and the small jobs that run against it.

    python3 -m helpdesk --data tickets.json search [--status open|closed] [--text WORD]
    python3 -m helpdesk --data tickets.json show ID
    python3 -m helpdesk --data tickets.json close ID
    python3 -m helpdesk --data tickets.json reopen ID
    python3 -m helpdesk --data tickets.json --config config.json overdue

Global flags (before the command):

- `--data PATH`   the tickets file (required)
- `--config PATH` settings file, optional; see `helpdesk/config.py`
- `--now ISO`     pretend it is this time, e.g. `2026-06-01T00:00:00Z`
                  (cron leaves it out; tests and backfills set it)

`overdue` runs nightly from cron and prints the ids of open tickets older
than `sla_hours`.

Tests: `python3 -m unittest`
