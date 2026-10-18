import unittest
from openpdf_controller_v340 import OperationKind,OperationRequest,classify_operation,validate_request

class TestController(unittest.TestCase):
    def test_compression(self):
        def compress_with_profile(): pass
        self.assertEqual(classify_operation(compress_with_profile),OperationKind.COMPRESS)
    def test_merge(self):
        def merge_pdf(): pass
        self.assertEqual(classify_operation(merge_pdf),OperationKind.MERGE)
    def test_unknown(self):
        self.assertEqual(classify_operation(lambda:None),OperationKind.OTHER)
    def test_busy(self):
        self.assertFalse(validate_request(OperationRequest(OperationKind.OTHER,'','',''),True).accepted)
    def test_same_file(self):
        self.assertFalse(validate_request(OperationRequest(OperationKind.COMPRESS,'a.pdf','./a.pdf','')).accepted)
    def test_missing_paths(self):
        self.assertFalse(validate_request(OperationRequest(OperationKind.COMPRESS,'','b.pdf','')).accepted)
    def test_valid(self):
        self.assertTrue(validate_request(OperationRequest(OperationKind.COMPRESS,'a.pdf','b.pdf','')).accepted)
if __name__=='__main__':unittest.main()
