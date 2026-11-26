"""Checkout quote. All amounts are integer cents."""

SHIPPING_FLAT_CENTS = 499
FREE_SHIPPING_MIN_CENTS = 5000

TAX_PERCENT = {"US": 0, "CA": 5, "DE": 19, "FR": 20, "GB": 20}
COUPONS = {"WELCOME10": 10, "VIP25": 25}


def percent_of(cents, percent):
    """percent of cents, rounded half up to a whole cent."""
    return (cents * percent + 50) // 100


def subtotal_of(items):
    return sum(item["unit_cents"] * item["qty"] for item in items)


def needs_shipping(items):
    return any(not item.get("digital") for item in items)


def quote(items, country, coupon=None):
    if country not in TAX_PERCENT:
        raise ValueError("unsupported country: %r" % (country,))
    subtotal = subtotal_of(items)

    discount = 0
    if coupon is not None:
        if coupon not in COUPONS:
            raise ValueError("unknown coupon: %r" % (coupon,))
        discount = percent_of(subtotal, COUPONS[coupon])

    if not needs_shipping(items):
        shipping = 0
    elif subtotal >= FREE_SHIPPING_MIN_CENTS:
        shipping = 0
    else:
        shipping = SHIPPING_FLAT_CENTS

    tax = percent_of(subtotal - discount, TAX_PERCENT[country])
    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": subtotal - discount + shipping + tax,
    }
