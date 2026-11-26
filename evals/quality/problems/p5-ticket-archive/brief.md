(From the support-tools planning doc, section written by Renata, team lead)

## Auto-archive for closed tickets

The closed pile is at 40k tickets and search is useless because of it. We want closed tickets to get archived automatically once they've been closed for a while.

- New command, `archive`, runs nightly from cron the way `overdue` does (same flags). It prints how many tickets it archived, like `archived 12`.
- How long is "a while": legal owes us an answer. It's either 30 or 90 days and we'll know after the 12th. Don't wait for them. Make it a setting, `archive_after_days`, next to the others in the config.
- Archived tickets drop out of search. `search --include-archived` brings them back. `show` by id must still work for archived tickets, agents get linked to old tickets all the time.
- The clock runs from when the ticket was last closed. If a ticket gets reopened it's a live ticket again, obviously don't archive it just because it was closed once back in January.
- Tickets with legal_hold are never archived. That one is not negotiable.
- Sam thinks reopening an archived ticket should un-archive it. I think archived should mean read-only. We didn't settle it. Leave reopen alone for now and note it somewhere so we come back to it.
- Don't delete anything. Archive is a flag on the ticket, not a move to another file.
