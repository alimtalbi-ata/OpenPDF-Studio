"""Real generated PDF integration tests; no mocks of the PDF engine.
Author: Abdelhalim Talbi.
"""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'03-Sources'))
from openpdf_page_service_v345 import merge,extract,reorder
from openpdf_operations import run_operation

def create_pdf(path,labels):
    with fitz.open() as doc:
        for label in labels:
            page=doc.new_page(width=595,height=842)
            page.insert_text((72,100),label,fontsize=18)
        doc.save(path)

def labels(path):
    with fitz.open(path) as doc:
        return [page.get_text().strip() for page in doc]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class RealPDFIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.a=self.root/'alpha.pdf';self.b=self.root/'beta.pdf'
        create_pdf(self.a,['ALPHA-ONE','ALPHA-TWO','ALPHA-THREE'])
        create_pdf(self.b,['BETA-ONE','BETA-TWO'])
    def test_merge_preserves_page_order_and_digest(self):
        output=self.root/'merged.pdf'
        receipt=run_operation('fusion',[str(self.a),str(self.b)],str(output))
        self.assertEqual(labels(output),['ALPHA-ONE','ALPHA-TWO','ALPHA-THREE','BETA-ONE','BETA-TWO'])
        self.assertEqual(receipt.page_counts,(5,))
        self.assertEqual(receipt.sha256,(sha(output),))
    def test_extract_preserves_requested_pages(self):
        output=self.root/'extract.pdf'
        receipt=run_operation('extraction',[str(self.a)],str(output),first=2,last=3)
        self.assertEqual(labels(output),['ALPHA-TWO','ALPHA-THREE'])
        self.assertEqual(receipt.page_counts,(2,))
    def test_reorder_supports_repeated_pages(self):
        output=self.root/'reordered.pdf'
        receipt=run_operation('reorganisation',[str(self.a)],str(output),order='3,1,3')
        self.assertEqual(labels(output),['ALPHA-THREE','ALPHA-ONE','ALPHA-THREE'])
        self.assertEqual(receipt.page_counts,(3,))
    def test_out_of_range_does_not_publish(self):
        output=self.root/'invalid.pdf'
        with self.assertRaises(ValueError):
            run_operation('extraction',[str(self.a)],str(output),first=2,last=10)
        self.assertFalse(output.exists())
    def test_existing_output_unchanged(self):
        output=self.root/'occupied.pdf'
        output.write_bytes(b'keep-original')
        with self.assertRaises(FileExistsError):
            run_operation('fusion',[str(self.a),str(self.b)],str(output))
        self.assertEqual(output.read_bytes(),b'keep-original')
    def test_input_files_unchanged(self):
        before=(sha(self.a),sha(self.b))
        run_operation('fusion',[str(self.a),str(self.b)],str(self.root/'merged.pdf'))
        self.assertEqual((sha(self.a),sha(self.b)),before)
if __name__=='__main__':unittest.main()
