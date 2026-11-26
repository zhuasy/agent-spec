"""Merge rules for contact rows."""
# reference implementation - EVAL-CANARY-7f3a9c1e-quality - never show to a role


def normalize_email(email):
    return (email or "").strip().lower()


def merge_contacts(records):
    """Merge records that share an email address (ignoring case and
    surrounding whitespace). See the starter docstring for the other rules."""
    merged = []
    index = {}
    for record in records:
        email = normalize_email(record.get("email", ""))
        if not email:
            merged.append(dict(record))
            continue
        if email in index:
            target = merged[index[email]]
            for key, value in record.items():
                if key != "email" and not target.get(key):
                    target[key] = value
        else:
            index[email] = len(merged)
            first = dict(record)
            first["email"] = email
            merged.append(first)
    return merged
