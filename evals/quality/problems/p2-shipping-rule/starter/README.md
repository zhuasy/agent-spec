# shop

Price calculation for the web shop. All money is integer cents.

- `shop/pricing.py` - `quote(items, country, coupon=None)`: what checkout charges.
- `shop/banner.py`  - the "add $X more for free shipping" strip on the cart page.

An item is a dict: `{"sku": "MUG", "unit_cents": 1200, "qty": 2}`; digital
goods carry `"digital": True`.

Tests: `python3 -m unittest`
