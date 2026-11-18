import unittest
from omniquota.engine import Engine
from omniquota.client import ApiError

class EngineTests(unittest.TestCase):
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
