import unittest
from audit_assistant_v257 import readable_result

class TestReadableResult(unittest.TestCase):
    def test_success(self):
        self.assertTrue(readable_result(True, 'contrôle terminé').startswith('SUCCÈS'))
    def test_failure(self):
        self.assertTrue(readable_result(False, 'empreinte incorrecte').startswith('ÉCHEC'))
    def test_reason_visible(self):
        self.assertIn('empreinte incorrecte', readable_result(False, 'empreinte incorrecte'))

if __name__ == '__main__': unittest.main()
