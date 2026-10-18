"""V30.8 tests for cooperative cancellation and UI dispatch."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from openpdf_conversion_controller_v308 import ConversionController,ConversionCancelled
from openpdf_ui_bridge_v308 import connect
from openpdf_core_v260 import pdf_to_docx

class ConversionSafety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.src=self.root/'a.pdf';self.src.write_bytes(b'%PDF-synthetic')
        self.out=self.root/'out.docx';self.out.write_bytes(b'original')
    def test_cancel_before_work(self):
        with self.assertRaises(ConversionCancelled):ConversionController().convert(self.src,self.out,'docx',cancelled=lambda:True)
        self.assertEqual(self.out.read_bytes(),b'original')
    def test_cancel_after_work_preserves_destination(self):
        count=[0]
        def cancel():count[0]+=1;return count[0]>=3
        def fake(src,dst):Path(dst).write_bytes(b'converted')
        with patch('openpdf_conversion_controller_v308.CONVERTERS',{'docx':fake}):
            with self.assertRaises(ConversionCancelled):ConversionController().convert(self.src,self.out,'docx',cancelled=cancel)
        self.assertEqual(self.out.read_bytes(),b'original')
        self.assertEqual(list(self.root.glob('.openpdf-convert-*')),[])
    def test_success_progress_and_commit(self):
        progress=[]
        with patch('openpdf_conversion_controller_v308.CONVERTERS',{'docx':lambda s,d:Path(d).write_bytes(b'converted')}):
            result=ConversionController().convert(self.src,self.out,'docx',progress=lambda a,b:progress.append((a,b)))
        self.assertEqual(result.bytes_written,9);self.assertEqual(progress,[(1,1)])
        self.assertEqual(self.out.read_bytes(),b'converted')
    def test_converter_failure_keeps_output(self):
        with patch('openpdf_conversion_controller_v308.CONVERTERS',{'docx':lambda s,d:(_ for _ in ()).throw(OSError('failed'))}):
            with self.assertRaises(OSError):ConversionController().convert(self.src,self.out,'docx')
        self.assertEqual(self.out.read_bytes(),b'original')
    def test_missing_source_message(self):
        with self.assertRaisesRegex(ValueError,'source existant'):ConversionController().convert(self.root/'missing.pdf',self.out,'docx')
    def test_ui_forwards_cancel_callback(self):
        app=type('App',(),{})();app._run_pdf=Mock(return_value='scheduled');original=app._run_pdf
        connect(app);app._run_pdf(pdf_to_docx,self.src,self.out)
        worker=original.call_args.args[0]
        with self.assertRaises(ConversionCancelled):worker(cancelled=lambda:True)
        self.assertEqual(self.out.read_bytes(),b'original')
    def test_connect_idempotent(self):
        app=type('App',(),{})();app._run_pdf=Mock();connect(app);method=app._run_pdf;connect(app);self.assertIs(method,app._run_pdf)
    def test_non_conversion_passthrough(self):
        app=type('App',(),{})();app._run_pdf=Mock();original=app._run_pdf;connect(app);app._run_pdf('other',1,2);original.assert_called_once_with('other',1,2)
