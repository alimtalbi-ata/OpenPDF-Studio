"""Audit export integrity and privacy regression tests. Abdelhalim Talbi."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_audit_v415 import write_event
from openpdf_audit_export_v416 import export_snapshot,verify_snapshot

class ExportTests(unittest.TestCase):
    def test_export_verify_and_detect_tampering(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'OPENPDF_AUDIT':'1'}):
            root=Path(d)
            self.assertTrue(write_event('fusion','success',18,directory=root))
            export=root/'export.json'
            digest=export_snapshot(root/'operations.jsonl',export)
            self.assertEqual(len(digest),64)
            self.assertTrue(verify_snapshot(export))
            payload=json.loads(export.read_text())
            self.assertNotIn('source',str(payload))
            payload['records'][0]['duration_ms']=999
            export.write_text(json.dumps(payload))
            self.assertFalse(verify_snapshot(export))
    def test_export_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'OPENPDF_AUDIT':'1'}):
            root=Path(d)
            write_event('ocr','failure',4,directory=root)
            export=root/'export.json'
            export.write_text('existing')
            with self.assertRaises(FileExistsError):
                export_snapshot(root/'operations.jsonl',export)
            self.assertEqual(export.read_text(),'existing')
    def test_reject_sensitive_fields(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'operations.jsonl'
            src.write_text(json.dumps({'operation':'fusion','status':'success','duration_ms':1,'timestamp_utc':'2026-10-19T12:00:00Z','filename':'secret.pdf'})+'\n')
            with self.assertRaisesRegex(ValueError,'Schéma'):
                export_snapshot(src,root/'out.json')
if __name__=='__main__':unittest.main()
