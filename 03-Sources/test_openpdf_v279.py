import unittest
from openpdf_ui_lifecycle_v279 import RefreshScheduler

class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.pending = {}
        self.seq = 0
        def schedule(delay, fn):
            self.seq += 1
            self.pending[self.seq] = fn
            return self.seq
        self.scheduler = RefreshScheduler(schedule, self.pending.pop)
    def test_only_one_timer(self):
        self.assertTrue(self.scheduler.start(lambda: None))
        self.assertFalse(self.scheduler.start(lambda: None))
        self.assertEqual(len(self.pending), 1)
    def test_callback_rearms_once(self):
        calls=[]
        self.scheduler.start(lambda: calls.append(1))
        self.pending.pop(1)()
        self.assertEqual(calls,[1])
        self.assertEqual(len(self.pending),1)
    def test_close_cancels(self):
        self.scheduler.start(lambda: None)
        self.scheduler.close()
        self.assertEqual(self.pending,{})
    def test_closed_does_not_restart(self):
        self.scheduler.close()
        self.assertFalse(self.scheduler.start(lambda: None))
    def test_close_during_callback(self):
        self.scheduler.start(self.scheduler.close)
        self.pending.pop(1)()
        self.assertEqual(self.pending,{})

if __name__ == '__main__': unittest.main()
