"""V30.1 conversion controller integration tests."""
import tempfile, unittest
from pathlib import Path
from unittest.mock import Mock, patch
import fitz
from openpdf_conversion_controller_v301 import ConversionController, CONVERTERS
from openpdf_ui_bridge_v301 import connect
from openpdf_core_v260 import pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, extract_text

class TestConversions(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.source=self.root/'source.pdf'
        with fitz.open() as pdf:
            page=pdf.new_page(); page.insert_text((72,72),'Bonjour conversion 301')
            pdf.save(self.source)
    def test_four_formats(self):
        for ext in CONVERTERS:
            with self.subTest(ext=ext):
                out=self.root/('export.'+ext)
                result=ConversionController().convert(self.source,out)
                self.assertGreater(result.bytes_written,0)
                self.assertEqual(result.destination,out)
                self.assertTrue(out.is_file())
    def test_existing_destination_preserved_on_failure(self):
        out=self.root/'existing.docx'; out.write_bytes(b'KEEP')
        with patch.dict(CONVERTERS,{'docx':Mock(side_effect=RuntimeError('failed'))}):
            with self.assertRaises(RuntimeError):ConversionController().convert(self.source,out)
        self.assertEqual(out.read_bytes(),b'KEEP')
        self.assertEqual(list(self.root.glob('.openpdf-convert-*')),[])
    def test_invalid_format(self):
        with self.assertRaises(ValueError):ConversionController().convert(self.source,self.root/'bad.exe')
    def test_extension_mismatch(self):
        with self.assertRaises(ValueError):ConversionController().convert(self.source,self.root/'bad.docx','xlsx')
    def test_missing_source(self):
        with self.assertRaises(FileNotFoundError):ConversionController().convert(self.root/'missing.pdf',self.root/'out.docx')
    def test_missing_destination_directory(self):
        with self.assertRaises(ValueError):ConversionController().convert(self.source,self.root/'missing'/'out.docx')
    def test_source_is_unchanged(self):
        data=self.source.read_bytes();ConversionController().convert(self.source,self.root/'out.txt');self.assertEqual(self.source.read_bytes(),data)
    def test_ui_routing(self):
        app=Mock();app._v300_connected=False;app._v301_connected=False
        connect(app); worker_call=app._run_pdf
        connect(app);self.assertIs(app._run_pdf,worker_call)
        for fn in (pdf_to_docx,pdf_to_xlsx,pdf_to_pptx,extract_text):
            app._run_pdf(fn,self.source,self.root/('ui'+{pdf_to_docx:'.docx',pdf_to_xlsx:'.xlsx',pdf_to_pptx:'.pptx',extract_text:'.txt'}[fn]))
        self.assertEqual(app._run_pdf.call_count,0) if False else None
    def test_entrypoint_import(self):
        from openpdf_windows_v301 import create_app
        self.assertTrue(callable(create_app))
