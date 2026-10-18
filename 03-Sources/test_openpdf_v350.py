import unittest
from openpdf_job_controller_v350 import JobState
class JobTests(unittest.TestCase):
    def test_success(self):
        s=JobState();j=s.start('fusion');self.assertTrue(s.finish(j,'success'));self.assertEqual(s.last_result,'success')
    def test_failure(self):
        s=JobState();j=s.start('ocr');self.assertTrue(s.finish(j,'error'));self.assertEqual(s.last_result,'error')
    def test_busy(self):
        s=JobState();s.start('fusion');self.assertRaises(RuntimeError,s.start,'ocr')
    def test_stale(self):
        s=JobState();j=s.start('fusion');self.assertFalse(s.finish('stale','success'));self.assertEqual(s.active_id,j)
    def test_unknown_outcome(self):
        s=JobState();j=s.start('fusion');self.assertRaises(ValueError,s.finish,j,'cancelled');self.assertEqual(s.active_id,j)
    def test_restart(self):
        s=JobState();j=s.start('fusion');s.finish(j,'success');self.assertNotEqual(j,s.start('ocr'))
    def test_missing_operation(self):
        self.assertRaises(ValueError,JobState().start,'')
