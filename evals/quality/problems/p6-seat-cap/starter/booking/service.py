"""Reservations."""
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    is_admin: bool = False


class SoldOut(Exception):
    """Not enough seats left for this request. Nothing was reserved."""


class NotFound(Exception):
    """No such reservation."""


class BookingService:
    def __init__(self, store):
        self.store = store

    def seats_left(self, event_id):
        event = self.store.get_event(event_id)
        return event["capacity"] - sum(r["seats"] for r in event["reservations"])

    def reserve(self, event_id, user, seats):
        """Reserve seats for user. Returns the reservation id."""
        if seats < 1:
            raise ValueError("seats must be at least 1")
        event = self.store.get_event(event_id)
        taken = sum(r["seats"] for r in event["reservations"])
        if taken + seats > event["capacity"]:
            raise SoldOut("only %d seats left" % (event["capacity"] - taken))
        reservation_id = uuid.uuid4().hex
        event["reservations"].append(
            {"id": reservation_id, "user_id": user.id, "seats": seats}
        )
        self.store.save_event(event_id, event)
        return reservation_id

    def cancel(self, event_id, user, reservation_id):
        """Cancel a reservation. Only its owner or an admin may do that."""
        event = self.store.get_event(event_id)
        for reservation in event["reservations"]:
            if reservation["id"] == reservation_id:
                if reservation["user_id"] != user.id and not user.is_admin:
                    raise PermissionError("not your reservation")
                event["reservations"].remove(reservation)
                self.store.save_event(event_id, event)
                return
        raise NotFound(reservation_id)
