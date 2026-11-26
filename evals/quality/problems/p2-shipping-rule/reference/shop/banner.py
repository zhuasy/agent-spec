"""Cart page strip: 'Add $X more for free shipping'."""
# reference implementation - EVAL-CANARY-7f3a9c1e-quality - never show to a role
from .pricing import discount_of, free_shipping_min, needs_shipping, subtotal_of


def free_shipping_gap(items, country, coupon=None):
    """Cents of paid-for goods still missing for free shipping. 0 = free."""
    threshold = free_shipping_min(country)
    if not needs_shipping(items):
        return 0
    subtotal = subtotal_of(items)
    return max(0, threshold - (subtotal - discount_of(subtotal, coupon)))


def banner_text(items, country, coupon=None):
    gap = free_shipping_gap(items, country, coupon)
    if gap == 0:
        return "You've got free shipping!"
    return "Add $%d.%02d more for free shipping" % (gap // 100, gap % 100)
