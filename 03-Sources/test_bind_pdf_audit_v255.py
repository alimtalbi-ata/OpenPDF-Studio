import copy
import tempfile
import unittest
from pathlib import Path
from bind_pdf_audit_v255 import bind,verify_bound
from verify_proof_audit_v254 import FIELDS
import hashlib,json
class BoundAuditTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=Path(self.tmp.name)/'source.pdf';self.t=Path(self.tmp.name)/'target.pdf'
  self.s.write_bytes(b'%PDF-1.4 source');self.t.write_bytes(b'%PDF-1.4 target')
  e=dict(sequence=1,document_side='source',page=1,region_index=1,pdf_bbox_pt=[1,2,10,20],provenance='raster-mapping-validated',page_pair_status='exact-text',region_cross_document_match='not_asserted')
  canonical=json.dumps([e[f] for f in FIELDS],ensure_ascii=False,separators=(',',':'))
  e['previous_sha256']='0'*64;e['entry_sha256']=hashlib.sha256((e['previous_sha256']+'\n'+canonical).encode()).hexdigest()
  self.audit=dict(schema='openpdf-region-audit-sha256-v25.4',algorithm='SHA-256',chain_seed='0'*64,selection_count=1,head_sha256=e['entry_sha256'],entries=[e])
 def test_valid(self):self.assertTrue(verify_bound(bind(self.audit,self.s,self.t),self.s,self.t)[0])
 def test_changed_source(self):
  obj=bind(self.audit,self.s,self.t);self.s.write_bytes(b'%PDF-1.4 changed');self.assertFalse(verify_bound(obj,self.s,self.t)[0])
 def test_changed_target(self):
  obj=bind(self.audit,self.s,self.t);self.t.write_bytes(b'%PDF-1.4 changed');self.assertFalse(verify_bound(obj,self.s,self.t)[0])
 def test_tampered_envelope(self):
  obj=bind(self.audit,self.s,self.t);obj['pdfs']['source']['sha256']='0'*64;self.assertFalse(verify_bound(obj,self.s,self.t)[0])
 def test_tampered_audit_with_recomputed_envelope(self):
  obj=bind(self.audit,self.s,self.t);obj['audit']['entries'][0]['page']=2
  body={k:obj[k] for k in ('schema','pdfs','audit')}
  obj['envelope_sha256']=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  self.assertFalse(verify_bound(obj,self.s,self.t)[0])
 def test_wrong_pdf_order(self):
  obj=bind(self.audit,self.s,self.t);self.assertFalse(verify_bound(obj,self.t,self.s)[0])
 def test_invalid_inner_audit(self):
  a=copy.deepcopy(self.audit);a['head_sha256']='0'*64
  with self.assertRaises(ValueError):bind(a,self.s,self.t)
if __name__=='__main__':unittest.main()
