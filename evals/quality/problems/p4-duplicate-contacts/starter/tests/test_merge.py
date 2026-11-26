import unittest

from contacts.merge import merge_contacts


def rec(name, email, phone="", company=""):
    return {"name": name, "email": email, "phone": phone, "company": company}


class MergeTest(unittest.TestCase):
    def test_same_email_is_merged_first_wins_blanks_filled(self):
        out = merge_contacts([
            rec("Ana Ruiz", "ana@acme.example", "", "Acme"),
            rec("A. Ruiz", "ana@acme.example", "555-0101", "Acme Corp"),
        ])
        self.assertEqual(out, [rec("Ana Ruiz", "ana@acme.example", "555-0101", "Acme")])

    def test_no_email_rows_are_kept_apart(self):
        out = merge_contacts([rec("Unknown", ""), rec("Unknown", "")])
        self.assertEqual(len(out), 2)

    def test_order_is_first_appearance(self):
        out = merge_contacts([
            rec("B", "b@x.example"), rec("A", "a@x.example"), rec("B2", "b@x.example"),
        ])
        self.assertEqual([r["name"] for r in out], ["B", "A"])


if __name__ == "__main__":
    unittest.main()
