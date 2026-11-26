# contacts

Cleans up the CRM contact dump before it goes to the mail-merge tool.

    python3 -m contacts in.csv out.csv

Reads `in.csv` (columns: name, email, phone, company), merges rows that are
the same contact, writes `out.csv` with the same columns.

- `contacts/merge.py`  - the merge rules
- `contacts/export.py` - CSV reading and writing

Tests: `python3 -m unittest`
