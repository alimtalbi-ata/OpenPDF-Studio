import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from openpdf_operations import run_operation

class SplitTransactionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
  self.base=Path(self.tmp.name); self.source=self.base/'source.pdf'
  d=fitz.open()
  for i in range(3): d.new_page().insert_text((72,72),f"page {i}")
  d.save(self.source);d.close()
 def test_split_success(self):
  receipt=run_operation('decoupage',[self.source],self.base,chunk=1)
  self.assertEqual(len(receipt.outputs),3)
  self.assertTrue(all(Path(p).exists() for p in receipt.outputs))
  self.assertFalse(list(self.base.glob('.openpdf-stage-*')))
 def test_collision_keeps_existing(self):
  existing=self.base/'source_pages_0001-0001.pdf'; existing.write_bytes(b'untouched')
  with self.assertRaises(FileExistsError): run_operation('decoupage',[self.source],self.base,chunk=1)
  self.assertEqual(existing.read_bytes(),b'untouched')
  self.assertFalse((self.base/'source_pages_0002-0002.pdf').exists())
 def test_publication_failure_rolls_back(self):
  import openpdf_split_transaction as mod
  original=mod.os.link; calls=[0]
  def fail_second(a,b):
   calls[0]+=1
   if calls[0]==2: raise OSError('simulated publication error')
   return original(a,b)
  with patch.object(mod.os,'link',side_effect=fail_second):
   with self.assertRaises(OSError):run_operation('decoupage',[self.source],self.base,chunk=1)
  self.assertFalse(list(self.base.glob('source_pages_*.pdf')))
  self.assertFalse(list(self.base.glob('.openpdf-stage-*')))
 def test_invalid_chunk(self):
  with self.assertRaises(ValueError):run_operation('decoupage',[self.source],self.base,chunk=0)
 def test_source_unchanged(self):
  before=self.source.read_bytes();run_operation('decoupage',[self.source],self.base,chunk=2)
  self.assertEqual(before,self.source.read_bytes())

if __name__=='__main__':unittest.main()
