import ast, unittest
from pathlib import Path
from unittest.mock import Mock,patch
from openpdf_windows_v336 import OpenPDFStudio
class TestV336(unittest.TestCase):
 def make_app(self, done=True, result=None):
  app=object.__new__(OpenPDFStudio)
  app._v273_handle=Mock()
  app._v273_handle.future.done.return_value=done
  app._v273_handle.future.result.return_value=result
  app._v273_handle.progress=.5
  app._v273_progress=Mock();app._v273_label=Mock();app._v273_cancel=Mock()
  app._v331_compression=None;app._task_state=Mock();app._task_state.finish.return_value='CANCELLED'
  app.after=Mock()
  return app
 def test_waiting_reschedules(self):
  app=self.make_app(False);app._poll_v274();app.after.assert_called_once();self.assertIsNotNone(app._v273_handle)
 def test_cancelled_cleans_handle(self):
  app=self.make_app();app._poll_v274();self.assertIsNone(app._v273_handle);app._v273_cancel.configure.assert_called_with(state='disabled')
 def test_exception_cleans_handle(self):
  app=self.make_app();app._v273_handle.future.result.side_effect=RuntimeError('test')
  with patch('openpdf_windows_v336.messagebox.showerror') as dialog:app._poll_v274();dialog.assert_called_once()
  self.assertIsNone(app._v273_handle)
 def test_stale_handle_is_not_completed(self):
  app=self.make_app();stale=app._v273_handle
  def switch(*args,**kwargs):app._v273_handle=Mock()
  app._v273_progress.configure.side_effect=switch
  app._poll_v274();self.assertIsNot(app._v273_handle,stale)
 def test_source_ast(self):
  ast.parse(Path(__file__).with_name('openpdf_windows_v336.py').read_text())
if __name__=='__main__':unittest.main()
