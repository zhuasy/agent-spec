"""CSV in and out."""
import csv

COLUMNS = ["name", "email", "phone", "company"]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{c: (row.get(c) or "") for c in COLUMNS} for row in csv.DictReader(f)]


def export_csv(records, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)
