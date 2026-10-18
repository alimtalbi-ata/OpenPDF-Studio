import unittest, tempfile, pathlib, fitz
from unittest.mock import patch
from openpdf_conversion_service_v351 import convert_office, SUPPORTED_FORMATS
from openpdf_ui_controller_v348 import OPERATIONS, run_operation
from openpdf_workspace_v349 import validate_request

class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name);self.source=self.root/'input.pdf'
        with fitz.open() as pdf:
            page=pdf.new_page();page.insert_text((72,72),'Exemple conversion Office');pdf.save(self.source)
    def test_registry(self):
        self.assertTrue(set(SUPPORTED_FORMATS).issubset(OPERATIONS))
    def test_invalid_extension(self):
        with self.assertRaises(ValueError):convert_office(self.source,self.root/'out.pdf',output_format='docx')
    def test_invalid_source(self):
        with self.assertRaises(ValueError):convert_office(self.root/'missing.pdf',self.root/'out.docx')
    def test_wrong_ui_extension(self):
        with self.assertRaises(ValueError):validate_request('docx',[str(self.source)],str(self.root/'out.pdf'))
    def test_multiple_sources_rejected(self):
        with self.assertRaises(ValueError):run_operation('docx',[self.source,self.source],str(self.root/'out.docx'))
    def test_docx_real_conversion(self):
        result=run_operation('docx',[self.source],str(self.root/'out.docx'))
        self.assertEqual(result.output_format,'docx');self.assertEqual(len(result.sha256),64)
        self.assertTrue((self.root/'out.docx').stat().st_size>0)
    def test_xlsx_real_conversion(self):
        result=run_operation('xlsx',[self.source],str(self.root/'out.xlsx'))
        self.assertEqual(result.output_format,'xlsx')
    def test_pptx_real_conversion(self):
        result=run_operation('pptx',[self.source],str(self.root/'out.pptx'))
        self.assertEqual(result.output_format,'pptx')
    def test_audit_failure_preserves_previous_artifact(self):
        old=self.root/'out.docx';old.write_bytes(b'previous file')
        with patch('openpdf_conversion_service_v351.audit_conversion',side_effect=ValueError('corrompu')):
            with self.assertRaises(ValueError):convert_office(self.source,old)
        self.assertEqual(old.read_bytes(),b'previous file')

if __name__=='__main__':unittest.main()
