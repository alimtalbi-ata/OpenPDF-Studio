"""Regression: Windows fsync requires writable file descriptor. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
import openpdf_split_transaction as tx

class SplitFsyncTests(unittest.TestCase):
    def test_fsync_uses_writable_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input.pdf';output=root/'out';output.mkdir()
            with fitz.open() as pdf:
                pdf.new_page();pdf.save(source)
            original=tx.os.fsync
            modes=[]
            def check(fd):
                import os
                if os.name=='posix':
                    import fcntl
                    access=fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE
                    self.assertNotEqual(access,os.O_RDONLY)
                modes.append(fd)
                return original(fd)
            with patch.object(tx.os,'fsync',side_effect=check):
                receipt=tx.split_transaction(source,output)
            self.assertEqual(receipt.page_counts,(1,))
            self.assertTrue(modes)
if __name__=='__main__':unittest.main()
