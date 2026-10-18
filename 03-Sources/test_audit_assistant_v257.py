import tempfile
import unittest
from pathlib import Path
from audit_assistant_v257 import validate_create_paths, validate_verify_path
class TestAssistant(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        d=Path(self.tmp.name)
        for n in ('audit.json','source.pdf','target.pdf'):(d/n).write_bytes(b'test')
        self.d=d
    def paths(self):return [self.d/'audit.json',self.d/'source.pdf',self.d/'target.pdf',self.d/'out.zip']
    def test_valid(self):self.assertEqual(validate_create_paths(*self.paths())[-1],self.d/'out.zip')
    def test_missing(self):
        p=self.paths();p[1]=self.d/'missing.pdf'
        with self.assertRaises(ValueError):validate_create_paths(*p)
    def test_same_input(self):
        p=self.paths();p[2]=p[1]
        with self.assertRaises(ValueError):validate_create_paths(*p)
    def test_overwrite_input(self):
        p=self.paths();p[3]=p[1]
        with self.assertRaises(ValueError):validate_create_paths(*p)
    def test_extension(self):
        p=self.paths();p[3]=self.d/'out.txt'
        with self.assertRaises(ValueError):validate_create_paths(*p)
    def test_empty(self):
        p=self.paths();p[0]=''
        with self.assertRaises(ValueError):validate_create_paths(*p)
    def test_bad_parent(self):
        p=self.paths();p[3]=self.d/'missing'/'out.zip'
        with self.assertRaises(ValueError):validate_create_paths(*p)
    def test_verify_valid(self):
        p=self.d/'in.zip';p.write_bytes(b'zip')
        self.assertEqual(validate_verify_path(p),p)
    def test_verify_missing(self):
        with self.assertRaises(ValueError):validate_verify_path(self.d/'in.zip')
    def test_verify_wrong_extension(self):
        p=self.d/'in.txt';p.write_bytes(b'text')
        with self.assertRaises(ValueError):validate_verify_path(p)
if __name__=='__main__':unittest.main()
