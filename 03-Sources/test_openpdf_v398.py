import unittest,tempfile,json,hashlib,sys
from pathlib import Path
from unittest.mock import patch
import openpdf_release_gate as gate
import openpdf_publish_binary as pub
class ReleaseEvidenceTests(unittest.TestCase):
 def test_missing_installer_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(RuntimeError):gate.validate(d,'installer')
 def test_missing_portable_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(RuntimeError):gate.validate(d,'portable')
 def test_publish_requires_installation_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); stage=root/'stage';stage.mkdir()
   (stage/pub.NAMES['installer']).write_bytes(b'MZdummy')
   (stage/'windows-smoke-installer.json').write_text('{}')
   with self.assertRaises(FileNotFoundError):pub.publish(stage,root/'binary','installer')
 def test_release_gate_checks_installation_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/gate.NAMES['installer'];p.write_bytes(b'MZdummy')
   report={'version':gate.VERSION,'mode':'installer','passed':True,'artifact_name':p.name,'artifact_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':[{'passed':True},{'passed':True}]}
   (root/'windows-smoke-installer.json').write_text(json.dumps(report))
   with patch.object(gate,'verify',return_value=True):
    with self.assertRaisesRegex(RuntimeError,'Missing installation evidence'):gate.validate(root,'installer')
 def test_installation_evidence_wrong_hash_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/gate.NAMES['installer'];p.write_bytes(b'MZdummy')
   digest=hashlib.sha256(p.read_bytes()).hexdigest()
   (root/'windows-smoke-installer.json').write_text(json.dumps({'version':gate.VERSION,'mode':'installer','passed':True,'artifact_name':p.name,'artifact_sha256':digest,'checks':[{'passed':True},{'passed':True}]}))
   (root/f'windows-installation-v{gate.VERSION}.json').write_text(json.dumps({'version':gate.VERSION,'passed':True,'artifact_name':p.name,'artifact_sha256':'wrong','steps':['silent_install_pass','installed_launch_pass','silent_uninstall_pass']}))
   with patch.object(gate,'verify',return_value=True):
    with self.assertRaisesRegex(RuntimeError,'Invalid installation evidence'):gate.validate(root,'installer')
if __name__=='__main__':unittest.main()
