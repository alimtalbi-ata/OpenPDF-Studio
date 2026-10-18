import unittest
from openpdf_task_state_v274 import TaskState,Phase
from openpdf_tasks_v273 import TaskResult
class Handle:
    def __init__(self):self.flag=False
    def cancel(self):self.flag=True
    def cancelled(self):return self.flag
class LifecycleTests(unittest.TestCase):
    def test_success(self):
        s=TaskState();s.start(Handle());self.assertEqual(s.finish(TaskResult(value='ok')),Phase.SUCCEEDED)
    def test_failure(self):
        s=TaskState();s.start(Handle());self.assertEqual(s.finish(TaskResult(error=ValueError('bad'))),Phase.FAILED)
    def test_cancel(self):
        s=TaskState();h=Handle();s.start(h);self.assertTrue(s.cancel());self.assertTrue(h.flag);self.assertEqual(s.finish(TaskResult(error=RuntimeError('cancelled'))),Phase.CANCELLED)
    def test_no_double_start(self):
        s=TaskState();s.start(Handle());self.assertRaises(RuntimeError,s.start,Handle())
    def test_no_finish_idle(self):self.assertRaises(RuntimeError,TaskState().finish,TaskResult())
    def test_reuse_after_finish(self):
        s=TaskState();s.start(Handle());s.finish(TaskResult());s.start(Handle());self.assertTrue(s.busy)
if __name__=='__main__':unittest.main()
