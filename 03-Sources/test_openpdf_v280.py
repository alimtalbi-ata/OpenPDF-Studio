"""V28.0 UI controller regression tests. Abdelhalim Talbi."""
import unittest
from openpdf_ui_controller_v280 import UIController

class TestUIController(unittest.TestCase):
    def setUp(self):
        self.jobs = {}
        self.cancelled = []
        self.counter = 0
        def schedule(delay, fn):
            self.counter += 1
            self.jobs[self.counter] = fn
            return self.counter
        def cancel(token):
            self.cancelled.append(token)
            self.jobs.pop(token, None)
        self.controller = UIController(schedule, cancel)

    def test_schedule_and_fire(self):
        called=[]
        self.controller.schedule(10,lambda:called.append(1))
        self.assertEqual(self.controller.pending,1)
        self.jobs.pop(1)()
        self.assertEqual(called,[1]);self.assertEqual(self.controller.pending,0)

    def test_close_cancels_pending(self):
        self.controller.schedule(10,lambda:None)
        self.controller.schedule(20,lambda:None)
        self.controller.close()
        self.assertEqual(self.cancelled,[1,2]);self.assertEqual(self.controller.pending,0)

    def test_close_idempotent(self):
        self.controller.schedule(10,lambda:None)
        self.controller.close();self.controller.close()
        self.assertEqual(self.cancelled,[1])

    def test_no_new_jobs_after_close(self):
        self.controller.close()
        self.assertIsNone(self.controller.schedule(10,lambda:None))
        self.assertEqual(self.jobs,{})

    def test_cancelled_callback_noop(self):
        called=[]
        self.controller.schedule(10,lambda:called.append(1))
        stale=self.jobs[1]
        self.controller.close();stale()
        self.assertEqual(called,[])

if __name__ == '__main__': unittest.main()
