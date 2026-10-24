"""Audit must distinguish compression no-gain from published output.
Author: Abdelhalim Talbi.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_operations import run_operation
from openpdf_transaction_v338 import CompressionReceipt
from openpdf_audit_export_v416 import export_snapshot,verify_snapshot

class AuditOutcomeTests(unittest.TestCase):
    def test_no_gain_is_not_logged_as_success(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'OPENPDF_AUDIT':'1','OPENPDF_AUDIT_DIR':folder}):
            root=Path(folder)
            source=root/'source.pdf';source.write_bytes(b'input')
            destination=root/'output.pdf'
            receipt=CompressionReceipt(False,str(destination),'Aucun gain : sortie non créée')
            with patch('openpdf_operations._legacy_run_operation',return_value=receipt):
                result=run_operation('compression',[str(source)],str(destination))
            self.assertIs(result,receipt)
            self.assertFalse(destination.exists())
            lines=(root/'operations.jsonl').read_text(encoding='utf-8').splitlines()
            self.assertEqual(json.loads(lines[-1])['status'],'no_output')
            snapshot=root/'snapshot.json'
            export_snapshot(root/'operations.jsonl',snapshot)
            self.assertTrue(verify_snapshot(snapshot))
    def test_published_compression_is_success(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'OPENPDF_AUDIT':'1','OPENPDF_AUDIT_DIR':folder}):
            root=Path(folder);source=root/'source.pdf';source.write_bytes(b'input')
            receipt=CompressionReceipt(True,str(root/'out.pdf'),'OK')
            with patch('openpdf_operations._legacy_run_operation',return_value=receipt):
                run_operation('compression',[str(source)],str(root/'out.pdf'))
            record=json.loads((root/'operations.jsonl').read_text().splitlines()[-1])
            self.assertEqual(record['status'],'success')
if __name__=='__main__':unittest.main()
