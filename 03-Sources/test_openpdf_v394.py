import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from openpdf_release_gate import validate,NAMES
class ReleaseGateTests(unittest.TestCase):
 def setup_artifacts(self,d,mode='all'):
  for k,n in NAMES.items():
   (d/n).write_bytes(b'MZ'+b'fake-test-data')
   (d/f'windows-smoke-{k}.json').write_text(json.dumps({'version':'39.4','mode':k,'passed':True,'checks':[{'passed':True},{'passed':True}]}))
 def test_missing_binary_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(RuntimeError):validate(t)
 def test_missing_report_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.setup_artifacts(d);(d/'windows-smoke-installer.json').unlink()
   with patch('openpdf_release_gate.verify',return_value=True):
    with self.assertRaises(RuntimeError):validate(d)
 def test_stale_report_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.setup_artifacts(d);r=d/'windows-smoke-installer.json';v=json.loads(r.read_text());v['version']='39.3';r.write_text(json.dumps(v))
   with patch('openpdf_release_gate.verify',return_value=True):
    with self.assertRaises(RuntimeError):validate(d)
 def test_failed_check_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.setup_artifacts(d);r=d/'windows-smoke-installer.json';v=json.loads(r.read_text());v['checks'][1]['passed']=False;r.write_text(json.dumps(v))
   with patch('openpdf_release_gate.verify',return_value=True):
    with self.assertRaises(RuntimeError):validate(d)
 def test_full_success(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.setup_artifacts(d)
   with patch('openpdf_release_gate.verify',return_value=True):self.assertEqual(len(validate(d)['binaries']),2)
 def test_partial_requires_only_requested_edition(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.setup_artifacts(d);(d/NAMES['installer']).unlink()
   with patch('openpdf_release_gate.verify',return_value=True):self.assertEqual(len(validate(d,'portable')['binaries']),1)
if __name__=='__main__':unittest.main()
