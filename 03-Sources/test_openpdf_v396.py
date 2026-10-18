"""Regression: the Windows build must gate staged artifacts before publication."""
import unittest,tempfile,json,hashlib,sys
from pathlib import Path
from unittest.mock import patch
from openpdf_release_gate import validate

class ReleaseGatePrepublication(unittest.TestCase):
 def test_order(self):
  text=(Path(__file__).resolve().parents[1]/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
  self.assertLess(text.index('openpdf_release_gate.py "%STAGE%"'),text.index('openpdf_publish_binary.py'))
 def test_missing_stage_binary(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(RuntimeError):validate(d,'portable')
 def test_missing_report(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'OpenPDF-Studio-Portable-V39.8.exe';p.write_bytes(b'MZ')
   with patch('openpdf_release_gate.verify',return_value=True):
    with self.assertRaisesRegex(RuntimeError,'Missing Windows smoke report'):validate(d,'portable')
 def test_wrong_digest(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);name='OpenPDF-Studio-Portable-V39.8.exe';(root/name).write_bytes(b'MZmock')
   (root/'windows-smoke-portable.json').write_text(json.dumps({'version':'39.8','mode':'portable','passed':True,'artifact_name':name,'artifact_sha256':'0'*64,'checks':[{'passed':True},{'passed':True}]}))
   with patch('openpdf_release_gate.verify',return_value=True):
    with self.assertRaisesRegex(RuntimeError,'not bound'):validate(d,'portable')
 def test_valid_staged_artifact(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);name='OpenPDF-Studio-Portable-V39.8.exe';data=b'MZmock';(root/name).write_bytes(data)
   (root/'windows-smoke-portable.json').write_text(json.dumps({'version':'39.8','mode':'portable','passed':True,'artifact_name':name,'artifact_sha256':hashlib.sha256(data).hexdigest(),'checks':[{'passed':True},{'passed':True}]}))
   with patch('openpdf_release_gate.verify',return_value=True):self.assertTrue(validate(d,'portable')['qualified'])
if __name__=='__main__':unittest.main()
