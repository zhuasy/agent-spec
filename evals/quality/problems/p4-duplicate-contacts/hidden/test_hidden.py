# HIDDEN ACCEPTANCE TESTS - EVAL-CANARY-7f3a9c1e-quality
# Never show this file to the spec-writer, implementer, reader or judge.
import csv
import os
import subprocess
import sys
import tempfile
import unittest

from contacts.merge import merge_contacts

COLUMNS = ["name", "email", "phone", "company"]


def rec(name, email, phone="", company=""):
    return {"name": name, "email": email, "phone": phone, "company": company}


def key(record):
    return record["email"].strip().lower()


JANE = "jane.okafor@northwind.example"


class CliMixin:
    def run_cli(self, rows):
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "in.csv"), os.path.join(d, "out.csv")
            with open(src, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNS)
                w.writeheader()
                w.writerows(rows)
            p = subprocess.run([sys.executable, "-m", "contacts", src, dst],
                               capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(dst, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return reader.fieldnames, list(reader)


class CoreDuplicates(CliMixin, unittest.TestCase):
    ROWS = [
        rec("Jane Okafor", JANE, "", "Northwind"),
        rec("Jane Okafor", "Jane.Okafor@Northwind.example", "555-0199", ""),
        rec("Jane Okafor", " " + JANE, "", ""),
    ]

    def test_case_and_space_variants_merge_in_merge_contacts(self):
        out = merge_contacts(self.ROWS)
        self.assertEqual(len(out), 1)
        self.assertEqual(key(out[0]), JANE)

    def test_export_has_one_row_with_clean_lowercase_address(self):
        _, rows = self.run_cli(self.ROWS)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["email"], JANE)

    def test_trailing_space_and_all_caps(self):
        out = merge_contacts([rec("A", "a@x.example  "), rec("A", "A@X.EXAMPLE")])
        self.assertEqual(len(out), 1)


class EdgeNormalising(CliMixin, unittest.TestCase):
    def test_first_row_wins_even_when_it_is_the_messy_one(self):
        out = merge_contacts([
            rec("Jane O.", "  Jane.Okafor@Northwind.example", "", ""),
            rec("Jane Okafor", JANE, "555-0199", "Northwind"),
        ])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["name"], "Jane O.")
        self.assertEqual(out[0]["phone"], "555-0199")
        self.assertEqual(out[0]["company"], "Northwind")

    def test_unduplicated_messy_address_is_cleaned_in_export(self):
        _, rows = self.run_cli([rec("Bob", " Bob@X.example ")])
        self.assertEqual(rows[0]["email"], "bob@x.example")

    def test_whitespace_only_email_counts_as_no_email(self):
        out = merge_contacts([rec("Junk 1", "  "), rec("Junk 2", "  "), rec("Junk 3", "")])
        self.assertEqual([r["name"] for r in out], ["Junk 1", "Junk 2", "Junk 3"])

    def test_input_is_not_modified(self):
        rows = [rec("A", " A@x.example"), rec("A2", "a@x.example", "555")]
        snapshot = [dict(r) for r in rows]
        merge_contacts(rows)
        self.assertEqual(rows, snapshot)


class KeepMergeRules(CliMixin, unittest.TestCase):
    def test_same_name_different_people_stay_apart(self):
        out = merge_contacts([
            rec("John Smith", "john.smith@acme.example", company="Acme"),
            rec("John Smith", "jsmith@globex.example", company="Globex"),
        ])
        self.assertEqual(len(out), 2)

    def test_plus_addresses_are_separate_inboxes(self):
        out = merge_contacts([
            rec("Jane Okafor", JANE),
            rec("Northwind Billing", "billing+jane@northwind.example"),
            rec("Jane Okafor", "jane.okafor+news@northwind.example"),
            rec("J Okafor", "janeokafor@northwind.example"),
        ])
        self.assertEqual(len(out), 4)

    def test_no_email_rows_are_kept_apart_and_in_place(self):
        out = merge_contacts([
            rec("Unknown", ""), rec("A", "a@x.example"), rec("Unknown", ""),
            rec("A again", "A@x.example"),
        ])
        self.assertEqual([r["name"] for r in out], ["Unknown", "A", "Unknown"])

    def test_first_wins_and_blanks_filled(self):
        out = merge_contacts([
            rec("Ana Ruiz", "ana@acme.example", "", "Acme"),
            rec("A. Ruiz", "ana@acme.example", "555-0101", "Acme Corp"),
        ])
        self.assertEqual(out, [rec("Ana Ruiz", "ana@acme.example", "555-0101", "Acme")])

    def test_order_is_first_appearance(self):
        out = merge_contacts([
            rec("B", "b@x.example"), rec("A", "a@x.example"), rec("B2", "B@x.example"),
        ])
        self.assertEqual([r["name"] for r in out], ["B", "A"])

    def test_csv_columns_unchanged(self):
        header, rows = self.run_cli([rec("A", "a@x.example", "1", "X"), rec("N", "", "2", "Y")])
        self.assertEqual(header, COLUMNS)
        self.assertEqual(rows, [rec("A", "a@x.example", "1", "X"), rec("N", "", "2", "Y")])


if __name__ == "__main__":
    unittest.main()
