"""Transactional split must reject source changes before publishing. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
import openpdf_split_transaction as tx

class SplitSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.src=self.root/'source.pdf';self.dest=self.root/'output';self.dest.mkdir()
        with fitz.open() as doc:
            doc.new_page();doc.new_page();doc.save(self.src)
    def test_split_stable(self):
        receipt=tx.split_transaction(self.src,self.dest,1)
        self.assertEqual(receipt.page_counts,(1,1))
        self.assertEqual(len(list(self.dest.glob('*.pdf'))),2)
    def test_source_change_rejects_all_outputs(self):
        original=tx.legacy_split
        def mutate(source,folder,chunk_size):
            receipt=original(source,folder,chunk_size)
            with open(self.src,'ab') as stream:stream.write(b'\n% external edit')
            return receipt
        with patch.object(tx,'legacy_split',side_effect=mutate):
            with self.assertRaisesRegex(RuntimeError,'Source modifiée'):
                tx.split_transaction(self.src,self.dest,1)
        self.assertFalse(list(self.dest.glob('*.pdf')))
        self.assertFalse(list(self.dest.glob('.openpdf-stage-*')))
if __name__=='__main__':unittest.main()
