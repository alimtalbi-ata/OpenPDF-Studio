import unittest, tempfile, json, os, subprocess, sys
from pathlib import Path
from unittest.mock import patch
from openpdf_split_transaction import recover_transactions, split_transaction, _safe_names, _journal
from openpdf_reservation import reserve

class RecoveryTests(unittest.TestCase):
    def test_names(self):
        self.assertFalse(_safe_names(["../bad"]))
        self.assertFalse(_safe_names(["a","a"]))
        self.assertTrue(_safe_names(["one.pdf"]))
    def test_no_journal_manual_review(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/".openpdf-stage-abc").mkdir()
            self.assertEqual(recover_transactions(d)[0]["status"],"manual_review_missing_journal")
    def test_crash_recovery_hardlink(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d); stage=dest/".openpdf-stage-test";stage.mkdir()
            (stage/"one.pdf").write_bytes(b"test")
            _journal(stage,["one.pdf"])
            os.link(stage/"one.pdf",dest/"one.pdf")
            result=recover_transactions(dest)
            self.assertEqual(result[0]["status"],"recovered")
            self.assertFalse((dest/"one.pdf").exists())
            self.assertFalse(stage.exists())
    def test_foreign_file_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d);stage=dest/".openpdf-stage-test";stage.mkdir()
            (stage/"one.pdf").write_bytes(b"ours")
            _journal(stage,["one.pdf"])
            (dest/"one.pdf").write_bytes(b"foreign")
            self.assertEqual(recover_transactions(dest)[0]["status"],"manual_review_foreign_target")
            self.assertEqual((dest/"one.pdf").read_bytes(),b"foreign")
    def test_invalid_journal(self):
        with tempfile.TemporaryDirectory() as d:
            stage=Path(d)/".openpdf-stage-test";stage.mkdir()
            (stage/"transaction.json").write_text('{bad')
            self.assertEqual(recover_transactions(d)[0]["status"],"manual_review_invalid_journal")
    def test_clean_split(self):
        import fitz
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d);pdf=dest/"input.pdf";doc=fitz.open();doc.new_page();doc.new_page();doc.save(pdf);doc.close()
            result=split_transaction(pdf,dest,1)
            self.assertEqual(len(result.outputs),2)
            self.assertFalse(list(dest.glob(".openpdf-stage-*")))
    def test_reservation_recovery_api(self):
        from openpdf_operations import recover_split
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(recover_split(d),[])
    def test_crash_subprocess(self):
        with tempfile.TemporaryDirectory() as d:
            script="from pathlib import Path; import os; from openpdf_split_transaction import _journal; p=Path("+repr(d)+");s=p/'.openpdf-stage-crashed';s.mkdir();(s/'one.pdf').write_bytes(b'crash');_journal(s,['one.pdf']);os.link(s/'one.pdf',p/'one.pdf');os._exit(71)"
            run=subprocess.run([sys.executable,"-c",script],cwd=str(Path(__file__).parent),capture_output=True)
            self.assertEqual(run.returncode,71)
            self.assertTrue((Path(d)/"one.pdf").exists())
            self.assertEqual(recover_transactions(d)[0]["status"],"recovered")

if __name__=="__main__":unittest.main()
