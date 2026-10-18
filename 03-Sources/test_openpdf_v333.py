import unittest
from types import SimpleNamespace
from openpdf_task_presenter_v333 import completion_view
class TestPresenter(unittest.TestCase):
    def test_cancel(self): self.assertEqual(completion_view('CANCELLED', None).kind,'cancelled')
    def test_failure(self): self.assertEqual(completion_view('FAILED',SimpleNamespace(error='échec')).message,'échec')
    def test_success(self): self.assertEqual(completion_view('SUCCEEDED',SimpleNamespace(value='ok')).kind,'success')
    def test_compression(self): self.assertEqual(completion_view('SUCCEEDED',None,('a.pdf','b.pdf')).kind,'compression')
    def test_invalid_compression(self): self.assertEqual(completion_view('SUCCEEDED',None,('a.pdf',)).kind,'warning')
    def test_unknown(self): self.assertEqual(completion_view('PENDING',None).kind,'warning')
if __name__=='__main__': unittest.main()
