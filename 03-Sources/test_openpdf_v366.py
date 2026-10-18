import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_operations import run_operation

class TransactionalGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.d=Path(self.temp.name);self.source=self.d/'input.pdf'
        with fitz.open() as pdf:
            pdf.new_page().insert_text((40,60),'Original page')
            pdf.save(self.source)
    def test_existing_target_preserved(self):
        target=self.d/'out.pdf';target.write_bytes(b'DO NOT TOUCH')
        with self.assertRaises(FileExistsError):run_operation('fusion',[self.source],target)
        self.assertEqual(target.read_bytes(),b'DO NOT TOUCH')
    def test_source_not_overwritten(self):
        before=self.source.read_bytes()
        with self.assertRaises(ValueError):run_operation('extraction',[self.source],self.source,first=1,last=1)
        self.assertEqual(self.source.read_bytes(),before)
    def test_missing_directory(self):
        with self.assertRaises(ValueError):run_operation('fusion',[self.source],self.d/'absent'/'out.pdf')
    def test_unknown_operation(self):
        with self.assertRaises(ValueError):run_operation('unknown',[self.source],self.d/'out.pdf')
    def test_successful_publish(self):
        target=self.d/'out.pdf';run_operation('extraction',[self.source],target,first=1,last=1)
        with fitz.open(target) as pdf:self.assertEqual(pdf[0].get_text().strip(),'Original page')
    def test_split_collision_preserves_existing(self):
        existing=self.d/'input_pages_0001-0001.pdf';existing.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):run_operation('decoupage',[self.source],self.d,chunk=1)
        self.assertEqual(existing.read_bytes(),b'KEEP')
    def test_invalid_pdf_preserves_target_absence(self):
        bad=self.d/'bad.pdf';bad.write_bytes(b'bad pdf')
        target=self.d/'out.pdf'
        with self.assertRaises(Exception):run_operation('fusion',[bad],target)
        self.assertFalse(target.exists())
if __name__=='__main__':unittest.main()
