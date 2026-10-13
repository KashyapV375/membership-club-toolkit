"""Checks that the right email journey is picked.  Run:  python -m unittest discover tests"""
import os
import sys
import unittest

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_journeys import pick_journey

TODAY = pd.Timestamp("2026-09-30")


def member(status, signup, cancel=None):
    return {"status": status, "signup_date": pd.Timestamp(signup),
            "cancel_date": pd.Timestamp(cancel) if cancel else pd.NaT}


class TestJourneys(unittest.TestCase):
    def test_new_member_gets_welcome(self):
        self.assertEqual(pick_journey(member("active", "2026-09-27"), TODAY)[0], "welcome")

    def test_anniversary_next_week(self):
        journey, extra = pick_journey(member("active", "2024-10-03"), TODAY)
        self.assertEqual(journey, "anniversary")
        self.assertEqual(extra["years"], 2)

    def test_recently_cancelled_gets_win_back(self):
        self.assertEqual(pick_journey(member("cancelled", "2025-01-10", "2026-08-01"), TODAY)[0], "win_back")

    def test_cancelled_last_week_gets_nothing_yet(self):
        self.assertIsNone(pick_journey(member("cancelled", "2025-01-10", "2026-09-25"), TODAY)[0])

    def test_regular_member_gets_nothing(self):
        self.assertIsNone(pick_journey(member("active", "2025-03-15"), TODAY)[0])


if __name__ == "__main__":
    unittest.main()
