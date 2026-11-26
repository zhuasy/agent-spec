# HIDDEN ACCEPTANCE TESTS - EVAL-CANARY-7f3a9c1e-quality
# Never show this file to the spec-writer, implementer, reader or judge.
import unittest

from shop.banner import banner_text, free_shipping_gap
from shop.pricing import quote


def item(cents, qty=1, digital=False):
    return {"sku": "X", "unit_cents": cents, "qty": qty, "digital": digital}


class CoreThresholdAfterCoupon(unittest.TestCase):
    def test_example_from_the_request(self):
        q = quote([item(5200)], "US", coupon="VIP25")
        self.assertEqual(q["discount"], 1300)
        self.assertEqual(q["shipping"], 499)
        self.assertEqual(q["total"], 5200 - 1300 + 499)

    def test_one_cent_under_after_coupon_pays(self):
        q = quote([item(5554)], "US", coupon="WELCOME10")
        self.assertEqual(q["subtotal"] - q["discount"], 4999)
        self.assertEqual(q["shipping"], 499)


class EdgeBoundary(unittest.TestCase):
    def test_exactly_fifty_after_coupon_is_free(self):
        q = quote([item(5556)], "US", coupon="WELCOME10")
        self.assertEqual(q["subtotal"] - q["discount"], 5000)
        self.assertEqual(q["shipping"], 0)


class CoreInternationalThreshold(unittest.TestCase):
    def test_sixty_dollars_abroad_now_pays(self):
        for country in ("DE", "FR", "GB", "CA"):
            self.assertEqual(quote([item(6000)], country)["shipping"], 499, country)

    def test_seventy_five_abroad_is_free(self):
        self.assertEqual(quote([item(7500)], "DE")["shipping"], 0)
        self.assertEqual(quote([item(7499)], "DE")["shipping"], 499)

    def test_abroad_with_coupon_uses_discounted_amount(self):
        self.assertEqual(quote([item(8400)], "FR", coupon="WELCOME10")["shipping"], 0)
        self.assertEqual(quote([item(8000)], "FR", coupon="WELCOME10")["shipping"], 499)


class EdgeBannerTellsTheTruth(unittest.TestCase):
    CASES = [
        ([item(5200)], "US", "VIP25"),
        ([item(6000)], "US", "WELCOME10"),
        ([item(5556)], "US", "WELCOME10"),
        ([item(5554)], "US", "WELCOME10"),
        ([item(6000)], "DE", None),
        ([item(7500)], "GB", None),
        ([item(8000)], "FR", "WELCOME10"),
        ([item(8400)], "FR", "WELCOME10"),
        ([item(4000)], "US", None),
        ([item(900, digital=True)], "DE", None),
    ]

    def test_banner_agrees_with_checkout(self):
        for items, country, coupon in self.CASES:
            charged = quote(items, country, coupon)["shipping"] > 0
            gap = free_shipping_gap(items, country, coupon)
            self.assertEqual(gap > 0, charged, (items, country, coupon, gap))
            free_text = banner_text(items, country, coupon) == "You've got free shipping!"
            self.assertEqual(free_text, not charged, (items, country, coupon))

    def test_gap_abroad_without_coupon(self):
        self.assertEqual(free_shipping_gap([item(6000)], "DE"), 1500)
        self.assertEqual(banner_text([item(6000)], "DE"), "Add $15.00 more for free shipping")


class KeepEverythingElse(unittest.TestCase):
    def test_us_threshold_unchanged(self):
        self.assertEqual(quote([item(5000)], "US")["shipping"], 0)
        self.assertEqual(quote([item(4999)], "US")["shipping"], 499)

    def test_still_free_when_discounted_amount_is_over(self):
        self.assertEqual(quote([item(6000)], "US", coupon="WELCOME10")["shipping"], 0)

    def test_quote_fields(self):
        q = quote([item(1200, 2)], "US")
        self.assertEqual(q, {"subtotal": 2400, "discount": 0, "shipping": 499,
                             "tax": 0, "total": 2899})

    def test_tax_and_discount_rounding(self):
        q = quote([item(1999)], "DE", coupon="WELCOME10")
        self.assertEqual((q["discount"], q["tax"]), (200, 342))
        q = quote([item(1005)], "FR", coupon="VIP25")
        self.assertEqual((q["discount"], q["tax"]), (251, 151))
        self.assertEqual(q["total"], 1005 - 251 + 499 + 151)

    def test_tax_ignores_shipping(self):
        q = quote([item(6000)], "DE")
        self.assertEqual(q["tax"], 1140)
        self.assertEqual(q["total"], 6000 + 499 + 1140)

    def test_flat_rate_is_the_same_abroad(self):
        self.assertEqual(quote([item(1000)], "GB")["shipping"], 499)

    def test_digital_only_ships_free_everywhere(self):
        self.assertEqual(quote([item(900, digital=True)], "DE")["shipping"], 0)
        self.assertEqual(quote([item(900, digital=True)], "US", coupon="VIP25")["shipping"], 0)

    def test_errors(self):
        with self.assertRaises(ValueError):
            quote([item(1000)], "US", coupon="NOPE")
        with self.assertRaises(ValueError):
            quote([item(1000)], "ZZ")

    def test_us_banner_without_coupon_unchanged(self):
        self.assertEqual(free_shipping_gap([item(4000)], "US"), 1000)
        self.assertEqual(banner_text([item(4000)], "US"), "Add $10.00 more for free shipping")
        self.assertEqual(banner_text([item(5000)], "US"), "You've got free shipping!")


if __name__ == "__main__":
    unittest.main()
