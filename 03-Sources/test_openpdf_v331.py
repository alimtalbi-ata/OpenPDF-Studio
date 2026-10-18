import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
from openpdf_windows_v331 import OpenPDFStudio
from openpdf_task_state_v274 import Phase

class TestV331(unittest.TestCase):
    def test_compression_operation_names(self):
        from openpdf_windows_v331 import COMPRESSION_OPERATIONS
        self.assertIn('compress_with_profile', COMPRESSION_OPERATIONS)
        self.assertNotIn('merge_pdfs', COMPRESSION_OPERATIONS)

    def test_success_shows_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'a.pdf';dst=Path(tmp)/'b.pdf'
            src.write_bytes(b'X'*100);dst.write_bytes(b'Y'*50)
            app=MagicMock();app._v331_compression=(str(src),str(dst))
            app._v273_handle=MagicMock();app._v273_handle.future.done.return_value=True
            app._v273_handle.future.result.return_value=MagicMock(value=str(dst))
            app._task_state.finish.return_value=Phase.SUCCEEDED
            with patch('openpdf_windows_v331.show_summary_dialog') as show,patch('openpdf_windows_v331.messagebox.showinfo') as info:
                OpenPDFStudio._poll_v274(app)
                show.assert_called_once();info.assert_not_called()
                self.assertEqual(app._v331_compression,None)

    def test_failure_never_shows_summary(self):
        app=MagicMock();app._v331_compression=('a','b')
        app._v273_handle.future.done.return_value=True
        app._v273_handle.future.result.return_value=MagicMock(error=RuntimeError('failure'))
        app._task_state.finish.return_value=Phase.FAILED
        with patch('openpdf_windows_v331.show_summary_dialog') as show,patch('openpdf_windows_v331.messagebox.showerror') as err:
            OpenPDFStudio._poll_v274(app)
            show.assert_not_called();err.assert_called_once()

    def test_no_output_no_false_summary(self):
        app=MagicMock();app._v331_compression=('notfound-a','notfound-b')
        app._v273_handle.future.done.return_value=True
        app._v273_handle.future.result.return_value=MagicMock(value='Aucun gain')
        app._task_state.finish.return_value=Phase.SUCCEEDED
        with patch('openpdf_windows_v331.show_summary_dialog') as show,patch('openpdf_windows_v331.messagebox.showinfo') as info:
            OpenPDFStudio._poll_v274(app)
            show.assert_not_called();info.assert_called_once()
