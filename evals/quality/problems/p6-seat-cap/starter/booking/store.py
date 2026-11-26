"""Event storage.

An event is a dict:
    {"capacity": 100,
     "reservations": [{"id": "ab12...", "user_id": "u1", "seats": 2}, ...]}

The service only ever calls get_event and save_event. Production swaps in
RedisStore (infra repo), which offers exactly these two methods.
"""
import copy


class MemoryStore:
    def __init__(self):
        self._events = {}

    def create_event(self, event_id, capacity):
        """Test/setup helper; not part of the interface the service uses."""
        self._events[event_id] = {"capacity": capacity, "reservations": []}

    def get_event(self, event_id):
        """Return a private copy of the event. KeyError if there is none."""
        return copy.deepcopy(self._events[event_id])

    def save_event(self, event_id, event):
        """Replace the stored event with this one."""
        self._events[event_id] = copy.deepcopy(event)
