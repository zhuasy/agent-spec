(Thread in the events-eng channel, started by Dmitri)

We need a per-person cap on seats. Scalpers grabbed 60 seats for the March gala under one account.

- Max 4 seats per user per event, total across all their reservations for that event. So 2 then 2 is fine, 2 then 3 is not.
- Over the cap -> raise a new error, `LimitExceeded`, next to `SoldOut`. All-or-nothing like SoldOut, no partial fills.
- If they cancel, those seats stop counting against them.
- Box office staff (is_admin) book for groups, the cap doesn't apply to them. Capacity still does, obviously.
- Make the 4 a constructor arg (`max_per_user`, default 4). The charity events want 2.

Context you need: the handlers run in a thread pool (16 threads, one process) and sales open at noon sharp, so everyone hits reserve() in the same second. The cap has to hold under that. The scalper scripts fire 20 requests in parallel. And yes, we know we've had the odd oversell at openings, probably for the same reason. Capacity has to hold too.

Don't change the store interface (get_event / save_event). Prod uses RedisStore from the infra repo with those same two methods, and I can't get a change into that repo this quarter.
