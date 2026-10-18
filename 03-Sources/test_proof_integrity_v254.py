import copy
import hashlib
import json
import unittest
from verify_proof_audit_v254 import verify,FIELDS

class ProofIntegrityV254(unittest.TestCase):
 def setUp(self):
  e=dict(sequence=1,document_side='source',page=1,region_index=1,pdf_bbox_pt=[40,60,140,110],provenance='raster-mapping-validated',page_pair_status='unmatched-source',region_cross_document_match='not_asserted')
  seed='0'*64
  digest=hashlib.sha256((seed+'\n'+json.dumps([e[f] for f in FIELDS],separators=(',',':'))).encode()).hexdigest()
  e.update(previous_sha256=seed,entry_sha256=digest)
  self.payload=dict(schema='openpdf-region-audit-sha256-v25.4',algorithm='SHA-256',chain_seed=seed,selection_count=1,head_sha256=digest,entries=[e])
 def test_valid(self):self.assertTrue(verify(self.payload)[0])
 def test_tamper(self):
  p=copy.deepcopy(self.payload);p['entries'][0]['pdf_bbox_pt'][0]+=1;self.assertFalse(verify(p)[0])
 def test_head(self):
  p=copy.deepcopy(self.payload);p['head_sha256']='0'*64;self.assertFalse(verify(p)[0])
 def test_provenance(self):
  p=copy.deepcopy(self.payload);p['entries'][0]['provenance']='unverified';self.assertFalse(verify(p)[0])
 def test_empty(self):
  p=copy.deepcopy(self.payload);p['entries']=[];p['selection_count']=0;self.assertFalse(verify(p)[0])
if __name__=='__main__':unittest.main()
