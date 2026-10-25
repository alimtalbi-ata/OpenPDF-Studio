"""Recover only complete staged transactions; preserve outputs on missing stage files."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_split_transaction import recover_transactions

class RecoveryCompletenessTests(unittest.TestCase):
    def test_missing_staged_file_preserves_all_published_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            dest=Path(root);stage=dest/'.openpdf-stage-example';stage.mkdir()
            names=['part1.pdf','part2.pdf']
            staged=stage/names[0];staged.write_bytes(b'part one')
            target=dest/names[0];target.hardlink_to(staged)
            (stage/'transaction.json').write_text(json.dumps({'schema':1,'state':'prepared','names':names}),encoding='utf-8')
            report=recover_transactions(dest)
            self.assertEqual(report[0]['status'],'manual_review_missing_staged_output')
            self.assertTrue(stage.exists())
            self.assertEqual(target.read_bytes(),b'part one')
    def test_complete_staged_transaction_is_recovered(self):
        with tempfile.TemporaryDirectory() as root:
            dest=Path(root);stage=dest/'.openpdf-stage-example';stage.mkdir()
            names=['part1.pdf','part2.pdf']
            for name in names:
                staged=stage/name;staged.write_bytes(name.encode())
                (dest/name).hardlink_to(staged)
            (stage/'transaction.json').write_text(json.dumps({'schema':1,'state':'prepared','names':names}),encoding='utf-8')
            report=recover_transactions(dest)
            self.assertEqual(report[0]['status'],'recovered')
            self.assertFalse(stage.exists())
            self.assertFalse(any((dest/name).exists() for name in names))
if __name__=='__main__':unittest.main()
