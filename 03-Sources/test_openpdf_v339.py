import unittest
from unittest.mock import Mock, patch
from openpdf_windows_v339 import OpenPDFStudio, resolve_operation
from openpdf_transaction_v338 import compress_with_receipt
from openpdf_compression_v327 import compress_with_profile

class OperationTests(unittest.TestCase):
    def test_resolve_legacy(self):
        self.assertEqual(resolve_operation(compress_with_profile),(compress_with_receipt,True))
    def test_resolve_receipt(self):
        self.assertEqual(resolve_operation(compress_with_receipt),(compress_with_receipt,True))
    def test_other_unchanged(self):
        fn=lambda: None
        self.assertEqual(resolve_operation(fn),(fn,False))
    def _app(self,busy=False):
        app=object.__new__(OpenPDFStudio)
        app._task_state=Mock(busy=busy)
        app._v331_compression=None
        return app
    def test_register_after_dispatch(self):
        app=self._app()
        with patch('openpdf_windows_v339.Previous._run_pdf',return_value='submitted') as dispatch:
            self.assertEqual(app._run_pdf(compress_with_profile,'source.pdf','out.pdf'),'submitted')
        dispatch.assert_called_once()
        self.assertEqual(app._v331_compression,('source.pdf','out.pdf'))
    def test_busy_does_not_overwrite(self):
        app=self._app(True)
        app._v331_compression=('old','oldout')
        with patch('openpdf_windows_v339.Previous._run_pdf'):
            app._run_pdf(compress_with_profile,'new','newout')
        self.assertEqual(app._v331_compression,('old','oldout'))
    def test_other_does_not_register(self):
        app=self._app()
        with patch('openpdf_windows_v339.Previous._run_pdf'):
            app._run_pdf(lambda:None,'a','b')
        self.assertIsNone(app._v331_compression)
    def test_failure_does_not_register(self):
        app=self._app()
        with patch('openpdf_windows_v339.Previous._run_pdf',side_effect=RuntimeError('fail')):
            with self.assertRaises(RuntimeError):app._run_pdf(compress_with_profile,'a','b')
        self.assertIsNone(app._v331_compression)

if __name__=='__main__': unittest.main()
