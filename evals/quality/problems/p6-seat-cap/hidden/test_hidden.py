# HIDDEN ACCEPTANCE TESTS - EVAL-CANARY-7f3a9c1e-quality
# Never show this file to the spec-writer, implementer, reader or judge.
import copy
import threading
import time
import unittest

import booking.service as service_module
from booking.service import BookingService, NotFound, SoldOut, User


class TwoMethodStore:
    """Offers only what RedisStore offers: get_event and save_event.
    The delay stands in for the network round trip to Redis."""

    def __init__(self, events, delay=0.0):
        self._events = copy.deepcopy(events)
        self._delay = delay

    def get_event(self, event_id):
        event = copy.deepcopy(self._events[event_id])
        time.sleep(self._delay)
        return event

    def save_event(self, event_id, event):
        time.sleep(self._delay)
        self._events[event_id] = copy.deepcopy(event)

    def seats_of(self, event_id, user_id=None):
        return sum(r["seats"] for r in self._events[event_id]["reservations"]
                   if user_id is None or r["user_id"] == user_id)


def empty(capacity):
    return {"capacity": capacity, "reservations": []}


def limit_error():
    return getattr(service_module, "LimitExceeded")


ANN, BOB, STAFF = User("ann"), User("bob"), User("staff", is_admin=True)


class CoreCap(unittest.TestCase):
    def setUp(self):
        self.store = TwoMethodStore({"gala": empty(100), "fair": empty(100)})
        self.service = BookingService(self.store)

    def test_limit_error_is_a_new_exception_next_to_sold_out(self):
        err = limit_error()
        self.assertTrue(issubclass(err, Exception))
        self.assertFalse(issubclass(err, SoldOut))
        self.assertFalse(issubclass(SoldOut, err))

    def test_two_then_two_is_fine_then_one_more_is_not(self):
        self.service.reserve("gala", ANN, 2)
        self.service.reserve("gala", ANN, 2)
        with self.assertRaises(limit_error()):
            self.service.reserve("gala", ANN, 1)
        self.assertEqual(self.store.seats_of("gala", "ann"), 4)

    def test_two_then_three_reserves_nothing_more(self):
        self.service.reserve("gala", ANN, 2)
        with self.assertRaises(limit_error()):
            self.service.reserve("gala", ANN, 3)
        self.assertEqual(self.store.seats_of("gala"), 2)
        self.service.reserve("gala", ANN, 2)

    def test_five_at_once_is_over(self):
        with self.assertRaises(limit_error()):
            self.service.reserve("gala", ANN, 5)
        self.assertEqual(self.service.seats_left("gala"), 100)

    def test_cap_is_per_user_and_per_event(self):
        self.service.reserve("gala", ANN, 4)
        self.service.reserve("gala", BOB, 4)
        self.service.reserve("fair", ANN, 4)
        self.assertEqual(self.store.seats_of("gala"), 8)
        with self.assertRaises(limit_error()):
            self.service.reserve("fair", ANN, 1)

    def test_cancel_frees_the_users_allowance(self):
        rid = self.service.reserve("gala", ANN, 4)
        self.service.cancel("gala", ANN, rid)
        self.service.reserve("gala", ANN, 3)
        self.assertEqual(self.store.seats_of("gala", "ann"), 3)
        with self.assertRaises(limit_error()):
            self.service.reserve("gala", ANN, 2)

    def test_admin_is_not_capped(self):
        self.service.reserve("gala", STAFF, 30)
        self.service.reserve("gala", STAFF, 12)
        self.assertEqual(self.store.seats_of("gala", "staff"), 42)
        with self.assertRaises(limit_error()):
            self.service.reserve("gala", BOB, 5)

    def test_max_per_user_constructor_argument(self):
        service = BookingService(self.store, max_per_user=2)
        service.reserve("gala", ANN, 2)
        with self.assertRaises(limit_error()):
            service.reserve("gala", ANN, 1)
        roomy = BookingService(self.store, max_per_user=6)
        roomy.reserve("fair", BOB, 6)


class EdgeConcurrency(unittest.TestCase):
    """20 requests in the same instant, as the brief describes."""

    def hammer(self, service, users, seats=1):
        barrier = threading.Barrier(len(users))
        results = [None] * len(users)

        def worker(i):
            barrier.wait(timeout=10)
            try:
                service.reserve("gala", users[i], seats)
                results[i] = "ok"
            except Exception as exc:  # noqa: BLE001 - recorded and asserted on
                results[i] = type(exc).__name__

        threads = [threading.Thread(target=worker, args=(i,), daemon=True)
                   for i in range(len(users))]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=20)
        self.assertFalse(any(t.is_alive() for t in threads), "reserve() hung")
        return results

    def test_cap_holds_under_parallel_requests(self):
        store = TwoMethodStore({"gala": empty(100)}, delay=0.01)
        results = self.hammer(BookingService(store), [ANN] * 20)
        self.assertEqual(store.seats_of("gala", "ann"), 4, results)
        self.assertEqual(results.count("ok"), 4, results)
        self.assertEqual(results.count("LimitExceeded"), 16, results)

    def test_capacity_holds_under_parallel_requests(self):
        store = TwoMethodStore({"gala": empty(5)}, delay=0.01)
        users = [User("u%d" % i) for i in range(20)]
        results = self.hammer(BookingService(store), users)
        self.assertEqual(store.seats_of("gala"), 5, results)
        self.assertEqual(results.count("ok"), 5, results)
        self.assertEqual(results.count("SoldOut"), 15, results)

    def test_parallel_cancel_and_reserve_lose_nothing(self):
        store = TwoMethodStore({"gala": empty(100)}, delay=0.01)
        service = BookingService(store)
        rids = [service.reserve("gala", User("c%d" % i), 1) for i in range(5)]
        threads = [threading.Thread(
            target=service.cancel, args=("gala", User("c%d" % i), rids[i]), daemon=True)
            for i in range(5)]
        threads += [threading.Thread(
            target=service.reserve, args=("gala", User("n%d" % i), 1), daemon=True)
            for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=20)
        self.assertEqual(store.seats_of("gala"), 5)
        self.assertEqual(sum(store.seats_of("gala", "c%d" % i) for i in range(5)), 0)


class EdgeRules(unittest.TestCase):
    def test_admin_is_still_bound_by_capacity(self):
        store = TwoMethodStore({"gala": empty(10)})
        service = BookingService(store)
        with self.assertRaises(SoldOut):
            service.reserve("gala", STAFF, 11)
        service.reserve("gala", STAFF, 10)

    def test_admin_cancelling_for_a_user_frees_that_users_allowance(self):
        store = TwoMethodStore({"gala": empty(10)})
        service = BookingService(store)
        rid = service.reserve("gala", ANN, 4)
        service.cancel("gala", STAFF, rid)
        service.reserve("gala", ANN, 4)

    def test_cap_survives_a_new_service_object(self):
        # the cap is counted from stored reservations, not from memory
        store = TwoMethodStore({"gala": empty(10)})
        BookingService(store).reserve("gala", ANN, 3)
        with self.assertRaises(limit_error()):
            BookingService(store).reserve("gala", ANN, 2)


class KeepExisting(unittest.TestCase):
    def setUp(self):
        self.store = TwoMethodStore({"gala": empty(10)})
        self.service = BookingService(self.store)

    def test_sold_out_still_raised_and_reserves_nothing(self):
        self.service.reserve("gala", STAFF, 8)
        with self.assertRaises(SoldOut):
            self.service.reserve("gala", BOB, 3)
        self.assertEqual(self.service.seats_left("gala"), 2)

    def test_cancel_permissions(self):
        rid = self.service.reserve("gala", ANN, 2)
        with self.assertRaises(PermissionError):
            self.service.cancel("gala", BOB, rid)
        self.service.cancel("gala", STAFF, rid)
        with self.assertRaises(NotFound):
            self.service.cancel("gala", ANN, rid)

    def test_zero_seats_is_a_value_error(self):
        with self.assertRaises(ValueError):
            self.service.reserve("gala", ANN, 0)

    def test_stored_reservation_shape_unchanged(self):
        rid = self.service.reserve("gala", ANN, 2)
        (stored,) = self.store._events["gala"]["reservations"]
        self.assertEqual((stored["id"], stored["user_id"], stored["seats"]), (rid, "ann", 2))


if __name__ == "__main__":
    unittest.main()
