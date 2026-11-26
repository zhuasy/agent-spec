import unittest

from booking.service import BookingService, NotFound, SoldOut, User
from booking.store import MemoryStore


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.store.create_event("gala", 10)
        self.service = BookingService(self.store)
        self.ann, self.bob, self.staff = User("ann"), User("bob"), User("staff", is_admin=True)

    def test_reserve_and_seats_left(self):
        self.service.reserve("gala", self.ann, 3)
        self.assertEqual(self.service.seats_left("gala"), 7)

    def test_sold_out_reserves_nothing(self):
        self.service.reserve("gala", self.staff, 8)
        with self.assertRaises(SoldOut):
            self.service.reserve("gala", self.bob, 3)
        self.assertEqual(self.service.seats_left("gala"), 2)

    def test_cancel_rules(self):
        rid = self.service.reserve("gala", self.ann, 2)
        with self.assertRaises(PermissionError):
            self.service.cancel("gala", self.bob, rid)
        self.service.cancel("gala", self.staff, rid)
        self.assertEqual(self.service.seats_left("gala"), 10)
        with self.assertRaises(NotFound):
            self.service.cancel("gala", self.ann, rid)

    def test_zero_seats(self):
        with self.assertRaises(ValueError):
            self.service.reserve("gala", self.ann, 0)


if __name__ == "__main__":
    unittest.main()
