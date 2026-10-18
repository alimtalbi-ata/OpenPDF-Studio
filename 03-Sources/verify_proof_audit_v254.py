"""Independent SHA-256 audit chain verifier, V25.4. Usage: python verify_proof_audit_v254.py audit.json"""
import argparse
import hashlib
import json
from pathlib import Path

FIELDS=('sequence','document_side','page','region_index','pdf_bbox_pt','provenance','page_pair_status','region_cross_document_match')

def verify(payload):
    if payload.get('schema')!='openpdf-region-audit-sha256-v25.4' or payload.get('algorithm')!='SHA-256':return False,'Unsupported schema/algorithm'
    entries=payload.get('entries')
    if not isinstance(entries,list) or not entries or len(entries)>100 or payload.get('selection_count')!=len(entries):return False,'Invalid entry count'
    previous='0'*64
    if payload.get('chain_seed')!=previous:return False,'Invalid seed'
    last_sequence=0
    for i,e in enumerate(entries,1):
        if not isinstance(e,dict) or any(f not in e for f in FIELDS):return False,f'Entry {i}: missing fields'
        if e['document_side'] not in ('source','target') or e['provenance']!='raster-mapping-validated' or e['region_cross_document_match']!='not_asserted':return False,f'Entry {i}: invalid provenance'
        if type(e['sequence']) is not int or e['sequence']<=last_sequence:return False,f'Entry {i}: invalid sequence'
        last_sequence=e['sequence']
        if any(type(e[f]) is not int or e[f]<1 for f in ('page','region_index')):return False,f'Entry {i}: invalid page/region'
        b=e['pdf_bbox_pt']
        if not isinstance(b,list) or len(b)!=4 or any(type(v) not in (int,float) or not (-1e9<v<1e9) for v in b) or not (0<=b[0]<b[2] and 0<=b[1]<b[3]):return False,f'Entry {i}: invalid bbox'
        canonical=json.dumps([e[f] for f in FIELDS],ensure_ascii=False,separators=(',',':'))
        expected=hashlib.sha256((previous+'\n'+canonical).encode('utf-8')).hexdigest()
        if e.get('previous_sha256')!=previous or e.get('entry_sha256')!=expected:return False,f'Entry {i}: SHA-256 mismatch'
        previous=expected
    if payload.get('head_sha256')!=previous:return False,'Final head mismatch'
    return True,f'{len(entries)} entries verified (integrity only, not authenticity)'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('audit',type=Path);args=parser.parse_args()
    try: ok,message=verify(json.loads(args.audit.read_text(encoding='utf-8')))
    except (ValueError,OSError) as e:ok,message=False,str(e)
    print(('PASS: ' if ok else 'FAIL: ')+message);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
