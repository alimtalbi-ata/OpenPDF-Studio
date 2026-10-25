"""Office conversion refuses publication when its source changes mid-flight."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
import openpdf_conversion_service_v351 as service

class OfficeSourceMutationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.src=self.root/'input.pdf';self.dest=self.root/'output.docx'
        with fitz.open() as doc:
            doc.new_page();doc.save(self.src)
    def test_source_mutation_rejects_publication(self):
        class Audit:
            warnings=()
            sha256=''
        def converter(source,destination):
            destination.write_bytes(b'office result')
            with self.src.open('ab') as stream:stream.write(b'\n%changed')
        import hashlib
        Audit.sha256=hashlib.sha256(b'office result').hexdigest()
        with patch('openpdf_conversion_controller_v301.CONVERTERS',{'docx':converter}),patch.object(service,'audit_conversion',return_value=Audit()):
            with self.assertRaisesRegex(RuntimeError,'Source PDF modifiee'):
                service.convert_office(self.src,self.dest)
        self.assertFalse(self.dest.exists())
        self.assertFalse(list(self.root.glob('.openpdf-office-*')))
    def test_stable_source_publishes(self):
        class Audit:
            warnings=()
            sha256=''
        def converter(source,destination):
            destination.write_bytes(b'office result')
        import hashlib
        Audit.sha256=hashlib.sha256(b'office result').hexdigest()
        with patch('openpdf_conversion_controller_v301.CONVERTERS',{'docx':converter}),patch.object(service,'audit_conversion',return_value=Audit()):
            receipt=service.convert_office(self.src,self.dest)
        self.assertEqual(self.dest.read_bytes(),b'office result')
        self.assertEqual(receipt.bytes_written,len(b'office result'))
if __name__=='__main__':unittest.main()
