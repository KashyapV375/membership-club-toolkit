"""Checks for reading messy survey answers.  Run:  python -m unittest discover tests"""
import os
import sys
import unittest

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from link_surveys import net_promoter_score, parse_score


class TestSurveys(unittest.TestCase):
    def test_plain_number(self):
        self.assertEqual(parse_score("4", 1, 5), 4)

    def test_number_with_extra_text(self):
        self.assertEqual(parse_score(" 4/5 ", 1, 5), 4)
        self.assertEqual(parse_score("9 - definitely", 0, 10), 9)
        self.assertEqual(parse_score("10 - definitely", 0, 10), 10)

    def test_number_written_as_a_word(self):
        self.assertEqual(parse_score("Four", 1, 5), 4)

    def test_out_of_range_or_blank_is_none(self):
        self.assertIsNone(parse_score("7", 1, 5))
        self.assertIsNone(parse_score("", 1, 5))
        self.assertIsNone(parse_score(None, 1, 5))

    def test_net_promoter_score(self):
        # 2 promoters, 1 passive, 1 detractor out of 4 -> 50% - 25% = 25
        self.assertEqual(net_promoter_score(pd.Series([10, 9, 8, 3])), 25)


if __name__ == "__main__":
    unittest.main()
