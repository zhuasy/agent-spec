import unittest

from shop.banner import banner_text, free_shipping_gap
from shop.pricing import quote


def item(cents, qty=1, digital=False):
    return {"sku": "X", "unit_cents": cents, "qty": qty, "digital": digital}


class QuoteTest(unittest.TestCase):
    def test_small_us_cart_pays_shipping(self):
        self.assertEqual(
            quote([item(1200, 2)], "US"),
            {"subtotal": 2400, "discount": 0, "shipping": 499, "tax": 0, "total": 2899},
        )

    def test_big_us_cart_ships_free(self):
        self.assertEqual(quote([item(5000)], "US")["shipping"], 0)

    def test_coupon_and_tax(self):
        q = quote([item(1999)], "DE", coupon="WELCOME10")
        self.assertEqual(q["discount"], 200)
        self.assertEqual(q["tax"], 342)
        self.assertEqual(q["total"], 1999 - 200 + 499 + 342)

    def test_unknown_coupon(self):
        with self.assertRaises(ValueError):
            quote([item(1000)], "US", coupon="NOPE")

    def test_digital_only_ships_free(self):
        self.assertEqual(quote([item(900, digital=True)], "US")["shipping"], 0)


class BannerTest(unittest.TestCase):
    def test_gap(self):
        self.assertEqual(free_shipping_gap([item(4000)], "US"), 1000)
        self.assertEqual(banner_text([item(4000)], "US"), "Add $10.00 more for free shipping")

    def test_free(self):
        self.assertEqual(banner_text([item(5000)], "US"), "You've got free shipping!")


if __name__ == "__main__":
    unittest.main()
