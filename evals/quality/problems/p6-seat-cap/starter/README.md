# booking

Seat reservations for events. Called from the web handlers.

- `booking/service.py` - `BookingService`: reserve, cancel, seats_left
- `booking/store.py`   - `MemoryStore`, used in tests and local runs.
  Production uses `RedisStore` from the infra repo, which has the same
  `get_event` / `save_event` methods.

Tests: `python3 -m unittest`
