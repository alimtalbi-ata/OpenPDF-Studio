import unittest
from openpdf_operations_v342 import *

class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.r=OperationRegistry()
        self.r.register("pdf.compress",lambda:None)
        self.c=OperationController(self.r)
    def test_registered(self):self.assertEqual(self.r.available(),("pdf.compress",))
    def test_unknown(self):
        with self.assertRaises(KeyError):self.r.register("pdf.unknown",lambda:None)
    def test_duplicate(self):
        with self.assertRaises(ValueError):self.r.register("pdf.compress",lambda:None)
    def test_not_callable(self):
        with self.assertRaises(TypeError):self.r.register("pdf.merge",None)
    def test_missing_paths(self):self.assertFalse(self.c.validate("pdf.compress").accepted)
    def test_same_paths(self):self.assertFalse(self.c.validate("pdf.compress","/tmp/a.pdf","/tmp/./a.pdf").accepted)
    def test_distinct_paths(self):self.assertTrue(self.c.validate("pdf.compress","/tmp/a.pdf","/tmp/b.pdf").accepted)
    def test_busy(self):
        self.assertTrue(self.c.begin("pdf.compress","/tmp/a.pdf","/tmp/b.pdf").accepted)
        self.assertFalse(self.c.begin("pdf.compress","/tmp/a.pdf","/tmp/b.pdf").accepted)
        self.c.finish();self.assertFalse(self.c.busy)
    def test_unregistered(self):self.assertFalse(self.c.validate("pdf.merge").accepted)
    def test_resolve(self):self.assertIsNone(self.r.resolve("pdf.compress")())

if __name__=="__main__":unittest.main()
