import unittest
from omniquota.engine import Engine
from omniquota.client import ApiError

class EngineTests(unittest.TestCase):
    def test_reset_credits(self):
        for value in (0, 2, 3.0):
            e = Engine(); e.success(e.begin(), {'bankedResetCredits': value})
            self.assertEqual(e.state['bankedResetCredits'], value)
    def test_invalid_or_missing_reset_credits(self):
        for value in (None, -1, True, '2', 1.5, float('nan'), float('inf')):
            e = Engine(); e.success(e.begin(), {'bankedResetCredits': value})
            self.assertIsNone(e.state['bankedResetCredits'])
    def test_reset_credits_removed_when_missing(self):
        e = Engine(); e.success(e.begin(), {'bankedResetCredits': 2})
        e.success(e.begin(), {})
        self.assertIsNone(e.state['bankedResetCredits'])
        e.reset()
        self.assertIsNone(e.state['bankedResetCredits'])
    def test_no_overlapping_requests(self):
        e = Engine()
        self.assertIsNotNone(e.begin())
        self.assertIsNone(e.begin())
    def test_discard_old_generation(self):
        e = Engine(); ticket = e.begin(); e.reset()
        e.success(ticket, {'quotas':{'x':{'remainingPercentage':20}}})
        self.assertEqual(e.state['status'],'signed-out')
    def test_error_keeps_stale_data(self):
        e = Engine(); ticket = e.begin()
        e.success(ticket, {'quotas':{'x':{'remainingPercentage':20}}})
        e.failure(e.begin(), ApiError('offline'))
        self.assertEqual(e.state['remainingPercent'],20)
        self.assertTrue(e.state['stale'])
        self.assertEqual(e.delay,120)
    def test_retry_after(self):
        e = Engine(); e.failure(e.begin(),ApiError('wait',429,1800))
        self.assertEqual(e.delay,1800)
    def test_provider_stale(self):
        e = Engine(); e.success(e.begin(),{'_stale':True,'quotas':{'x':{'remainingPercentage':10}}})
        self.assertTrue(e.state['stale'])
    def test_logout_clears_state(self):
        e = Engine(); e.success(e.begin(),{'quotas':{'x':{'remainingPercentage':10}}}); e.reset()
        self.assertIsNone(e.state['remainingPercent'])
