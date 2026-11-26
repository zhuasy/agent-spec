"""Merge rules for contact rows."""


def merge_contacts(records):
    """Merge records that share an email address.

    - The first record with an address wins; later records with the same
      address only fill in fields the first one left blank.
    - Records without an email are never merged with anything.
    - Output keeps the order in which contacts first appear.
    - The input list and its dicts are not modified.
    """
    merged = []
    index = {}
    for record in records:
        email = record.get("email", "")
        if not email:
            merged.append(dict(record))
            continue
        if email in index:
            target = merged[index[email]]
            for key, value in record.items():
                if not target.get(key):
                    target[key] = value
        else:
            index[email] = len(merged)
            merged.append(dict(record))
    return merged
