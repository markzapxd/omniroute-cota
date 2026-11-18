import unittest
from omniquota.quota import normalize_usage, panel_percent

class QuotaTests(unittest.TestCase):
    def test_remaining_ratio(self):
        self.assertEqual(normalize_usage({'quotas': {'hour': {'remaining': 25, 'total': 100}}})[0]['remainingPercent'], 25)
    def test_multiple_windows(self):
        windows = normalize_usage({'quotas': {'a': {'remainingPercentage': 80}, 'b': {'remainingPercentage': 30}}})
        self.assertEqual(panel_percent(windows), 30)
    def test_missing_zero_and_invalid(self):
        for quota in ({}, {'total': 0, 'remaining': 0}, {'remainingPercentage': -1}, {'remainingPercentage': True}, {'remainingPercentage': float('nan')}, {'remainingPercentage': 101}, {'remainingPercentage': 100, 'fractionReported': False}, {'remainingPercentage': 100, 'unlimited': True}):
            with self.subTest(quota=quota):
                self.assertIsNone(normalize_usage({'quotas': {'a': quota}})[0]['remainingPercent'])
    def test_unknown_payload(self):
        self.assertEqual(normalize_usage({'message': 'Unavailable'}), [])
    def test_reset(self):
        self.assertEqual(normalize_usage({'quotas': {'weekly': {'remainingPercentage': 30, 'resetAt': 'tomorrow'}}})[0]['resetAt'], 'tomorrow')
