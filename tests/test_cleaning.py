"""Small checks for the cleaning helpers.  Run:  python -m unittest discover tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clean_customers import clean_email, clean_phone, split_pos_name, yes_no


class TestCleaning(unittest.TestCase):
    def test_email_is_lowercased_and_trimmed(self):
        self.assertEqual(clean_email("  Maya.Reyes@Example.COM "), "maya.reyes@example.com")

    def test_bad_email_becomes_none(self):
        self.assertIsNone(clean_email("not an email"))
        self.assertIsNone(clean_email(None))

    def test_phone_formats_all_match(self):
        for phone in ["(210) 555-1234", "210-555-1234", "210.555.1234", "+1 210 555 1234"]:
            self.assertEqual(clean_phone(phone), "2105551234")

    def test_short_phone_becomes_none(self):
        self.assertIsNone(clean_phone("555-1234"))

    def test_register_name_is_split(self):
        self.assertEqual(split_pos_name("REYES, Maya"), ("Maya", "Reyes"))

    def test_yes_no(self):
        self.assertTrue(yes_no("Y"))
        self.assertTrue(yes_no("Yes"))
        self.assertFalse(yes_no("no"))


if __name__ == "__main__":
    unittest.main()
