"""Deterministic, bounded JSON export for validated diagnostic findings.
Author: Abdelhalim Talbi. No semantic certainty is inferred.
"""
import hashlib
import json
from diagnostic_pipeline import prepare_spatial_diagnostic

SCHEMA='openpdf.spatial-diagnostic.v1'

def export_diagnostic(report, *, limit=200):
    """Return a portable evidence summary, not a certification of PDF fidelity."""
    spatial=prepare_spatial_diagnostic(report,limit=limit)
    regions=[{'side':r['side'],'page':r['page'],'bbox':list(r['bbox'])} for r in spatial['mapped_regions']]
    correlations=[dict(c) for c in spatial['correlations']]
    result={'schema':SCHEMA,'version':'21.7','author':'Abdelhalim Talbi',
            'status':'candidate_spatial_overlap_only','requires_human_review':True,
            'mapped_regions':regions,'correlations':correlations,
            'rejections':spatial['rejections'],
            'limitations':['Browser-only pixel regions are not imported',
                           'Overlap is not semantic classification',
                           'Rotated or cropped pages require independent validation']}
    payload=json.dumps(result,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    result['sha256_payload']=hashlib.sha256(payload).hexdigest()
    return result

def verify_export(value):
    if not isinstance(value,dict) or value.get('schema')!=SCHEMA:return False
    checksum=value.get('sha256_payload')
    if not isinstance(checksum,str) or len(checksum)!=64:return False
    data={k:v for k,v in value.items() if k!='sha256_payload'}
    try:payload=json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    except (TypeError,ValueError):return False
    return hashlib.sha256(payload).hexdigest()==checksum
