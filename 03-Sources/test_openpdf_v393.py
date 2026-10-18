import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from openpdf_publish_binary import publish,NAMES,VERSION
class PublicationTests(unittest.TestCase):
 def evidence(self,s):
  for name in ('windows-smoke-installer.json','windows-smoke-portable.json',f'windows-installation-v{VERSION}.json'):(s/name).write_text('{}')
 def test_both(self):
  with tempfile.TemporaryDirectory() as t:
   s=Path(t)/'stage'; b=Path(t)/'binary';s.mkdir();b.mkdir();self.evidence(s)
   for name in NAMES.values():(s/name).write_bytes(b'new');(b/name).write_bytes(b'old')
   self.assertEqual(len(publish(s,b,'all')),5)
   self.assertTrue(all((b/n).read_bytes()==b'new' for n in NAMES.values()))
 def test_missing_stage_preserves_previous(self):
  with tempfile.TemporaryDirectory() as t:
   s=Path(t)/'stage';b=Path(t)/'binary';s.mkdir();b.mkdir();self.evidence(s)
   for n in NAMES.values():(b/n).write_bytes(b'old')
   with self.assertRaises(FileNotFoundError):publish(s,b)
   self.assertTrue(all((b/n).read_bytes()==b'old' for n in NAMES.values()))
 def test_validation_failure_preserves_previous(self):
  with tempfile.TemporaryDirectory() as t:
   s=Path(t)/'stage';b=Path(t)/'binary';s.mkdir();b.mkdir();self.evidence(s)
   for n in NAMES.values():(s/n).write_bytes(b'new');(b/n).write_bytes(b'old')
   with self.assertRaises(ValueError):publish(s,b,validator=lambda p:False)
   self.assertTrue(all((b/n).read_bytes()==b'old' for n in NAMES.values()))
 def test_partial_copy_failure_restores_both(self):
  with tempfile.TemporaryDirectory() as t:
   s=Path(t)/'stage';b=Path(t)/'binary';s.mkdir();b.mkdir();self.evidence(s)
   for n in NAMES.values():(s/n).write_bytes(b'new');(b/n).write_bytes(b'old')
   import openpdf_publish_binary as mod
   orig=mod.shutil.copy2;count=[0]
   def broken(*a,**kw):
    count[0]+=1
    if count[0]==2:raise OSError('disk full')
    return orig(*a,**kw)
   with patch.object(mod.shutil,'copy2',side_effect=broken):
    with self.assertRaises(OSError):publish(s,b)
   self.assertTrue(all((b/n).read_bytes()==b'old' for n in NAMES.values()))
 def test_single_edition(self):
  with tempfile.TemporaryDirectory() as t:
   s=Path(t)/'stage';b=Path(t)/'binary';s.mkdir();b.mkdir();self.evidence(s)
   for n in NAMES.values():(s/n).write_bytes(b'new');(b/n).write_bytes(b'old')
   publish(s,b,'portable')
   self.assertEqual((b/NAMES['installer']).read_bytes(),b'old')
   self.assertEqual((b/NAMES['portable']).read_bytes(),b'new')
if __name__=='__main__':unittest.main()
