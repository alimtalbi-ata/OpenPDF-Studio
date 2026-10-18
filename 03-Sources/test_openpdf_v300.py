"""V30.0: source/destination collision prevention and task routing."""
import tempfile, unittest
from pathlib import Path
from unittest.mock import Mock
from openpdf_output_policy_v300 import validate_output, OutputConflictError
from openpdf_ui_bridge_v300 import connect, dispatch
from openpdf_engine_v273 import merge_pdfs, extract_pages, compress_pdf

class TestOutputSafety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.src=self.root/'a.pdf'; self.src.write_bytes(b'input')
    def test_identical_destination(self):
        with self.assertRaises(OutputConflictError): validate_output([self.src],self.src)
        self.assertEqual(self.src.read_bytes(),b'input')
    def test_relative_alias(self):
        with self.assertRaises(OutputConflictError): validate_output([self.src],self.root/'sub'/'..'/'a.pdf')
    def test_symlink_alias(self):
        link=self.root/'alias.pdf';link.symlink_to(self.src)
        with self.assertRaises(OutputConflictError): validate_output([self.src],link)
    def test_valid_destination(self):
        self.assertEqual(validate_output([self.src],self.root/'new.pdf'),self.root/'new.pdf')
    def test_missing_directory(self):
        with self.assertRaises(OutputConflictError):validate_output([self.src],self.root/'missing'/'new.pdf')
    def test_all_operations_reject_same_file(self):
        for operation,args in [(merge_pdfs,([self.src],self.src)),(extract_pages,(self.src,self.src,1,1)),(compress_pdf,(self.src,self.src))]:
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(OutputConflictError): dispatch(Mock(),operation,args)
        self.assertEqual(self.src.read_bytes(),b'input')
    def test_generator_merge_materialized_once(self):
        commands=Mock(); commands.merge.return_value=Mock(destination=self.root/'out.pdf')
        out=dispatch(commands,merge_pdfs,(iter([self.src]),self.root/'out.pdf'))
        self.assertEqual(out,str(self.root/'out.pdf'))
        self.assertEqual(commands.merge.call_args.args[0],[self.src])
    def test_unknown_function_fails_closed(self):
        with self.assertRaises(ValueError):dispatch(Mock(),lambda:None,())
    def test_connect_idempotent(self):
        app=Mock(); app._v300_connected=False
        connect(app); fn=app._run_pdf
        self.assertIs(connect(app)._run_pdf,fn)
    def test_entry_import(self):
        from openpdf_windows_v300 import create_app
        self.assertTrue(callable(create_app))
