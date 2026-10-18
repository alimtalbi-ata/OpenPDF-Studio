"""Bind a V25.4 integrity audit to exact PDF bytes, independently verifiable.

Usage: python bind_pdf_audit_v255.py bind AUDIT SOURCE TARGET -o BOUND.json
       python bind_pdf_audit_v255.py verify BOUND.json SOURCE TARGET
"""
import argparse
import hashlib
import json
from pathlib import Path
from verify_proof_audit_v254 import verify as verify_chain

SCHEMA='openpdf-bound-pdf-audit-v25.5'
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def bind(audit,source,target):
    ok,msg=verify_chain(audit)
    if not ok:raise ValueError('Invalid inner audit: '+msg)
    pdfs={'source':{'sha256':digest(source),'size_bytes':Path(source).stat().st_size},'target':{'sha256':digest(target),'size_bytes':Path(target).stat().st_size}}
    body={'schema':SCHEMA,'pdfs':pdfs,'audit':audit}
    return {**body,'envelope_sha256':hashlib.sha256(canonical(body)).hexdigest()}
def verify_bound(envelope,source,target):
    if not isinstance(envelope,dict) or set(envelope)!={'schema','pdfs','audit','envelope_sha256'} or envelope['schema']!=SCHEMA:return False,'Invalid envelope schema'
    body={k:envelope[k] for k in ('schema','pdfs','audit')}
    if hashlib.sha256(canonical(body)).hexdigest()!=envelope['envelope_sha256']:return False,'Envelope checksum mismatch'
    ok,msg=verify_chain(envelope['audit'])
    if not ok:return False,'Inner audit invalid: '+msg
    for side,path in [('source',source),('target',target)]:
        entry=envelope['pdfs'].get(side)
        if not isinstance(entry,dict) or set(entry)!={'sha256','size_bytes'}:return False,side+' metadata invalid'
        if digest(path)!=entry['sha256'] or Path(path).stat().st_size!=entry['size_bytes']:return False,side+' PDF bytes mismatch'
    return True,'PDFs and audit integrity verified; no author authentication'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['bind','verify']);p.add_argument('audit');p.add_argument('source');p.add_argument('target');p.add_argument('-o','--output');a=p.parse_args()
    try:
        if a.action=='bind':
            if not a.output:p.error('bind requires -o OUTPUT')
            obj=bind(json.loads(Path(a.audit).read_text(encoding='utf-8')),a.source,a.target)
            Path(a.output).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8');print('BOUND:',a.output)
        else:
            ok,msg=verify_bound(json.loads(Path(a.audit).read_text(encoding='utf-8')),a.source,a.target)
            print(('PASS: ' if ok else 'FAIL: ')+msg);return 0 if ok else 1
    except (ValueError,OSError,KeyError,TypeError) as e:print('FAIL:',e);return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
