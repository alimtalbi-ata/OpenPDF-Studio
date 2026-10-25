"""Recovery must reject unexpected journal states without touching files."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_split_transaction import recover_transactions

class RecoveryJournalStateTests(unittest.TestCase):
    def test_invalid_state_preserves_stage_and_output(self):
        with tempfile.TemporaryDirectory() as root:
            dest=Path(root)
            stage=dest/'.openpdf-stage-example'
            stage.mkdir()
            staged=stage/'document_pages_0001-0001.pdf'
            staged.write_bytes(b'staged')
            target=dest/staged.name
            target.hardlink_to(staged)
            (stage/'transaction.json').write_text(json.dumps({'schema':1,'state':'unexpected','names':[staged.name]}),encoding='utf-8')
            report=recover_transactions(dest)
            self.assertEqual(report[0]['status'],'manual_review_invalid_journal')
            self.assertTrue(stage.exists())
            self.assertEqual(target.read_bytes(),b'staged')
    def test_prepared_state_recovers_hardlinked_output(self):
        with tempfile.TemporaryDirectory() as root:
            dest=Path(root)
            stage=dest/'.openpdf-stage-example'
            stage.mkdir()
            staged=stage/'document_pages_0001-0001.pdf'
            staged.write_bytes(b'staged')
            target=dest/staged.name
            target.hardlink_to(staged)
            (stage/'transaction.json').write_text(json.dumps({'schema':1,'state':'prepared','names':[staged.name]}),encoding='utf-8')
            report=recover_transactions(dest)
            self.assertEqual(report[0]['status'],'recovered')
            self.assertFalse(stage.exists())
            self.assertFalse(target.exists())
if __name__=='__main__':unittest.main()
