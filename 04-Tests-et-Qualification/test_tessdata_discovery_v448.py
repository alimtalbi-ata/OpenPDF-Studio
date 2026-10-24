"""Find real Tesseract language data in installed and bundled locations."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_ocr_service_v347 import locate_tessdata

class TessdataDiscoveryTests(unittest.TestCase):
    def test_explicit_language_models(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'eng.traineddata').write_bytes(b'test')
            (root/'fra.traineddata').write_bytes(b'test')
            self.assertEqual(locate_tessdata('fra+eng',root),str(root))
            (root/'fra.traineddata').unlink()
            with self.assertRaisesRegex(ValueError,'fra.traineddata'):
                locate_tessdata('fra+eng',root)
    def test_environment_prefix_parent_or_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);data=root/'tessdata';data.mkdir()
            (data/'eng.traineddata').write_bytes(b'test')
            with patch.dict(os.environ,{'TESSDATA_PREFIX':str(root)}):
                self.assertEqual(locate_tessdata('eng'),str(data))
            with patch.dict(os.environ,{'TESSDATA_PREFIX':str(data)}):
                self.assertEqual(locate_tessdata('eng'),str(data))
if __name__=='__main__':unittest.main()
