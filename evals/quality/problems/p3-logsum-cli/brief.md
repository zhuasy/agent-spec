(Ticket OPS-2291, written by Kofi, on-call engineer)

Need a quick log summariser for the edge boxes. Single file, `logsum.py` at the top of the ops-scripts repo like the other scripts, stdlib only, I scp these around.

Usage I want:

    python3 logsum.py access.log
    python3 logsum.py access.log --top 5
    zcat old.log.gz | python3 logsum.py -

Lines look like this (sample/access.log has real ones):

    2026-03-01T12:00:01Z GET /api/users?id=7 200 123ms

Output is JSON on stdout so I can jq it:

    {"requests": 1234, "errors": 17, "skipped": 2, "by_path": [{"path": "/api/users", "count": 800, "p95_ms": 310}, ...]}

- errors = 5xx only. 4xx is the client's problem.
- by_path sorted busiest first, --top N limits how many paths it shows (default 10). Ties: alphabetical is fine. requests/errors are for the whole file, not just the top ones.
- strip the query string. /api/users?id=7 and /api/users?id=8 are the same path.
- p95 the same way the dashboards do it: nearest rank (sort the durations, take the one at position ceil(0.95 * n), counting from 1). No interpolation, I want numbers that match grafana.
- the logs have garbage in them sometimes (truncated lines when a box falls over mid-write). Don't die, skip the line and count it in skipped. Skipped lines aren't requests.
- file not there -> a message on stderr and exit 2, not a traceback.

Nothing fancy otherwise. No time filtering for now, I'll ask if I need it.
