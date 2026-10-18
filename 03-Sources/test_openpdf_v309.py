import tempfile, unittest
from pathlib import Path
from unittest.mock import Mock, patch
from openpdf_conversion_controller_v309 import ConversionController, ConversionCancelled, ConversionError
from openpdf_ui_bridge_v309 import connect
from openpdf_core_v260 import pdf_to_docx

class ConversionV309(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        self.src=self.root/'input.pdf';self.src.write_bytes(b'%PDF-test')
        self.dst=self.root/'out.docx';self.dst.write_bytes(b'original')
    def test_success_phase_and_progress(self):
        phases=[];progress=[]
        with patch('openpdf_conversion_controller_v308.CONVERTERS',{'docx':lambda s,d:Path(d).write_bytes(b'new')}):
            result=ConversionController().convert(self.src,self.dst,'docx',phase=phases.append,progress=lambda a,b:progress.append((a,b)))
        self.assertEqual(self.dst.read_bytes(),b'new');self.assertEqual(result.bytes_written,3)
        self.assertEqual(phases,['validation','conversion','termine']);self.assertEqual(progress,[(1,1)])
    def test_failure_preserves_destination(self):
        phases=[]
        with patch('openpdf_conversion_controller_v308.CONVERTERS',{'docx':lambda s,d:(_ for _ in ()).throw(OSError('disk'))}):
            with self.assertRaisesRegex(ConversionError,'DOCX impossible'):
                ConversionController().convert(self.src,self.dst,'docx',phase=phases.append)
        self.assertEqual(self.dst.read_bytes(),b'original');self.assertIn('erreur',phases)
        self.assertFalse(list(self.root.glob('.openpdf-convert-*')))
    def test_cancel_before_conversion(self):
        phases=[]
        with self.assertRaises(ConversionCancelled):ConversionController().convert(self.src,self.dst,'docx',cancelled=lambda:True,phase=phases.append)
        self.assertIn('annulation',phases);self.assertEqual(self.dst.read_bytes(),b'original')
    def test_observer_error_does_not_corrupt_conversion(self):
        with patch('openpdf_conversion_controller_v308.CONVERTERS',{'docx':lambda s,d:Path(d).write_bytes(b'new')}):
            ConversionController().convert(self.src,self.dst,'docx',phase=lambda x:1/0,progress=lambda a,b:1/0)
        self.assertEqual(self.dst.read_bytes(),b'new')
    def test_invalid_source(self):
        with self.assertRaisesRegex(ValueError,'source existant'):ConversionController().convert(self.root/'absent.pdf',self.dst,'docx')
    def test_ui_routing_and_phase(self):
        app=type('App',(),{})();app._run_pdf=Mock(return_value='queued');events=[];app._conversion_phase_observer=events.append
        original=app._run_pdf;connect(app)
        self.assertEqual(app._run_pdf(pdf_to_docx,self.src,self.dst),'queued')
        worker=original.call_args.args[0]
        with patch('openpdf_conversion_controller_v308.CONVERTERS',{'docx':lambda s,d:Path(d).write_bytes(b'new')}):worker()
        self.assertIn('termine',events)
    def test_passthrough_and_idempotence(self):
        app=type('App',(),{})();app._run_pdf=Mock();original=app._run_pdf
        connect(app);routed=app._run_pdf;connect(app);self.assertIs(routed,app._run_pdf)
        app._run_pdf('other',1);original.assert_called_once_with('other',1)
