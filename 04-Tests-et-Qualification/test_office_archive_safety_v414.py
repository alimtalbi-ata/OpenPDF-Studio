"""Office archive resource-limit security regression tests. Abdelhalim Talbi."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_conversion_audit_v346 import audit_conversion

class OfficeArchiveSafety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.pdf=self.root/'input.pdf'
        doc=fitz.open();doc.new_page().insert_text((40,70),'sample');doc.save(self.pdf);doc.close()
        self.out=self.root/'output.docx'
    def test_reject_oversized_office_entry_before_decompression(self):
        with zipfile.ZipFile(self.out,'w') as z:
            z.writestr('word/document.xml','ok')
        with patch('zipfile.ZipFile.infolist') as mocked:
            item=zipfile.ZipInfo('word/document.xml')
            item.file_size=129*1024*1024
            mocked.return_value=[item]
            with self.assertRaisesRegex(ValueError,'anormalement volumineuse'):
                audit_conversion(self.pdf,self.out)
    def test_reject_excessive_office_entries(self):
        with zipfile.ZipFile(self.out,'w') as z:
            z.writestr('word/document.xml','ok')
        with patch('zipfile.ZipFile.infolist') as mocked:
            mocked.return_value=[zipfile.ZipInfo('x')]*10001
            with self.assertRaisesRegex(ValueError,'anormalement volumineuse'):
                audit_conversion(self.pdf,self.out)
if __name__=='__main__':unittest.main()
