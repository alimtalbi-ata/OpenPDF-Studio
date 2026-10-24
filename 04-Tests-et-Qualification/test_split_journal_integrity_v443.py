"""Reject linked journals and empty recovery manifests without touching staged files."""
import json,os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_split_transaction import recover_transactions

class RecoveryJournalIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.dest=Path(self.tmp.name);self.stage=self.dest/'.openpdf-stage-test';self.stage.mkdir()
    def test_empty_names_preserves_stage(self):
        (self.stage/'transaction.json').write_text(json.dumps({'schema':1,'state':'prepared','names':[]}),encoding='utf-8')
        report=recover_transactions(self.dest)
        self.assertEqual(report[0]['status'],'manual_review_invalid_journal')
        self.assertTrue(self.stage.exists())
    def test_symlink_journal_preserves_stage_and_output(self):
        external=self.dest/'external.json'
        external.write_text(json.dumps({'schema':1,'state':'prepared','names':['part.pdf']}),encoding='utf-8')
        staged=self.stage/'part.pdf';staged.write_bytes(b'payload')
        published=self.dest/'part.pdf';published.hardlink_to(staged)
        try:
            (self.stage/'transaction.json').symlink_to(external)
        except (OSError,NotImplementedError) as exc:
            self.skipTest(f'Symlink privilege unavailable: {exc}')
        report=recover_transactions(self.dest)
        self.assertEqual(report[0]['status'],'manual_review_invalid_journal')
        self.assertEqual(published.read_bytes(),b'payload')
        self.assertTrue(self.stage.exists())
if __name__=='__main__':unittest.main()
