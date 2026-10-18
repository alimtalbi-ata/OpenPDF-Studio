import unittest
from openpdf_orchestrator_v343 import JobOrchestrator,JobPhase

def noop(*args):pass
class OrchestratorTests(unittest.TestCase):
 def setUp(self):
  self.o=JobOrchestrator();self.o.registry.register('pdf.compress',noop)
 def test_submit_complete(self):
  decision,job=self.o.submit('pdf.compress','a.pdf','b.pdf');self.assertTrue(decision.accepted)
  self.assertEqual(self.o.complete(job.job_id,JobPhase.SUCCEEDED).phase,JobPhase.SUCCEEDED)
  self.assertFalse(self.o.controller.busy)
 def test_busy_rejected(self):
  _,job=self.o.submit('pdf.compress','a','b');decision,_=self.o.submit('pdf.compress','c','d')
  self.assertFalse(decision.accepted);self.o.abort_submission(job.job_id)
 def test_same_path_rejected(self):
  decision,job=self.o.submit('pdf.compress','a','a');self.assertFalse(decision.accepted);self.assertIsNone(job)
 def test_stale_completion_rejected(self):
  _,job=self.o.submit('pdf.compress','a','b');self.assertIsNone(self.o.complete('stale',JobPhase.SUCCEEDED))
  self.assertTrue(self.o.controller.busy);self.o.abort_submission(job.job_id)
 def test_cancel_lifecycle(self):
  _,job=self.o.submit('pdf.compress','a','b');self.assertTrue(self.o.cancelling(job.job_id))
  self.assertFalse(self.o.cancelling(job.job_id));self.assertEqual(self.o.complete(job.job_id,'cancelled').phase,JobPhase.CANCELLED)
 def test_terminal_phase_validation(self):
  _,job=self.o.submit('pdf.compress','a','b')
  with self.assertRaises(ValueError):self.o.complete(job.job_id,'running')
  self.assertTrue(self.o.controller.busy);self.o.abort_submission(job.job_id)
 def test_failed_submission_cleanup(self):
  _,job=self.o.submit('pdf.compress','a','b');self.o.abort_submission(job.job_id,'error')
  self.assertEqual(self.o.last.error,'error');self.assertIsNone(self.o.active)
if __name__=='__main__':unittest.main()
