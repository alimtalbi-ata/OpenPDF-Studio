"""Opt-in privacy audit tests. Abdelhalim Talbi."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_audit_v415 import write_event

class AuditTests(unittest.TestCase):
    def test_default_disabled_and_no_file(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'OPENPDF_AUDIT':'0'}):
            self.assertFalse(write_event('fusion','success',12,directory=d))
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_no_sensitive_paths_and_rotation(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'OPENPDF_AUDIT':'1'}):
            self.assertTrue(write_event('fusion','success',12,directory=d,max_bytes=1))
            self.assertTrue(write_event('ocr','failure',25,directory=d,max_bytes=1))
            current=json.loads((Path(d)/'operations.jsonl').read_text())
            previous=json.loads((Path(d)/'operations.previous.jsonl').read_text())
            self.assertEqual(set(current),{'timestamp_utc','operation','status','duration_ms'})
            self.assertEqual(previous['operation'],'fusion')
            self.assertEqual(current['operation'],'ocr')
    def test_invalid_event_ignored(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'OPENPDF_AUDIT':'1'}):
            self.assertFalse(write_event('/private/file.pdf','success',1,directory=d))
if __name__=='__main__':unittest.main()
