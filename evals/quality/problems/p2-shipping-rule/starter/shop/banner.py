"""Cart page strip: 'Add $X more for free shipping'."""
from .pricing import FREE_SHIPPING_MIN_CENTS, needs_shipping, subtotal_of


def free_shipping_gap(items, country, coupon=None):
    """Cents still missing for free shipping. 0 means shipping is free.

    country and coupon are passed by the cart page for every call.
    """
    if not needs_shipping(items):
        return 0
    return max(0, FREE_SHIPPING_MIN_CENTS - subtotal_of(items))


def banner_text(items, country, coupon=None):
    gap = free_shipping_gap(items, country, coupon)
    if gap == 0:
        return "You've got free shipping!"
    return "Add $%d.%02d more for free shipping" % (gap // 100, gap % 100)
