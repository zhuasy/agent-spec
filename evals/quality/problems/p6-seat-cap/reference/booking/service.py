"""Reservations."""
# reference implementation - EVAL-CANARY-7f3a9c1e-quality - never show to a role
import threading
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    is_admin: bool = False


class SoldOut(Exception):
    """Not enough seats left for this request. Nothing was reserved."""


class LimitExceeded(Exception):
    """The request would take the user over the per-event seat cap."""


class NotFound(Exception):
    """No such reservation."""


class BookingService:
    def __init__(self, store, max_per_user=4):
        self.store = store
        self.max_per_user = max_per_user
        # One process, many handler threads: every read-modify-write of an
        # event happens under this lock.
        self._lock = threading.Lock()

    def seats_left(self, event_id):
        event = self.store.get_event(event_id)
        return event["capacity"] - sum(r["seats"] for r in event["reservations"])

    def reserve(self, event_id, user, seats):
        """Reserve seats for user. Returns the reservation id."""
        if seats < 1:
            raise ValueError("seats must be at least 1")
        with self._lock:
            event = self.store.get_event(event_id)
            taken = sum(r["seats"] for r in event["reservations"])
            if taken + seats > event["capacity"]:
                raise SoldOut("only %d seats left" % (event["capacity"] - taken))
            if not user.is_admin:
                held = sum(r["seats"] for r in event["reservations"]
                           if r["user_id"] == user.id)
                if held + seats > self.max_per_user:
                    raise LimitExceeded(
                        "limit is %d seats per person" % self.max_per_user)
            reservation_id = uuid.uuid4().hex
            event["reservations"].append(
                {"id": reservation_id, "user_id": user.id, "seats": seats}
            )
            self.store.save_event(event_id, event)
            return reservation_id

    def cancel(self, event_id, user, reservation_id):
        """Cancel a reservation. Only its owner or an admin may do that."""
        with self._lock:
            event = self.store.get_event(event_id)
            for reservation in event["reservations"]:
                if reservation["id"] == reservation_id:
                    if reservation["user_id"] != user.id and not user.is_admin:
                        raise PermissionError("not your reservation")
                    event["reservations"].remove(reservation)
                    self.store.save_event(event_id, event)
                    return
            raise NotFound(reservation_id)
