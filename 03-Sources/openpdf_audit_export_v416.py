"""Verifiable local audit snapshot (not a cryptographic signature).
Author: Abdelhalim Talbi.
"""
import hashlib
import json
import os
from pathlib import Path

FIELDS={'timestamp_utc','operation','status','duration_ms'}
OPERATIONS={'compression','fusion','extraction','decoupage','reorganisation','ocr','docx','xlsx','pptx'}

def _validate(lines):
    records=[]
    for line in lines:
        if not line.strip(): continue
        record=json.loads(line)
        if not isinstance(record,dict) or set(record)!=FIELDS:
            raise ValueError('Schéma audit invalide')
        if record['operation'] not in OPERATIONS or record['status'] not in ('success','failure'):
            raise ValueError('Événement audit invalide')
        if type(record['duration_ms']) is not int or record['duration_ms']<0:
            raise ValueError('Durée audit invalide')
        if not isinstance(record['timestamp_utc'],str) or len(record['timestamp_utc'])!=20:
            raise ValueError('Horodatage audit invalide')
        records.append(record)
    return records

def export_snapshot(log_path, output_path):
    """Snapshot JSON with SHA256 over canonical event payload. Refuses overwrite."""
    source=Path(log_path)
    destination=Path(output_path)
    if source.resolve()==destination.resolve():
        raise ValueError('Source et export identiques')
    if source.stat().st_size>16*1024*1024:
        raise ValueError('Journal trop volumineux')
    records=_validate(source.read_text(encoding='utf-8').splitlines())
    canonical=json.dumps(records,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode('ascii')
    payload={'format':'openpdf-audit-v1','records':records,'sha256':hashlib.sha256(canonical).hexdigest()}
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    fd=os.open(destination,flags,0o600)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(payload,stream,ensure_ascii=True,indent=2)
            stream.write('\n')
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return payload['sha256']

def verify_snapshot(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(payload,dict) or set(payload)!={'format','records','sha256'} or payload['format']!='openpdf-audit-v1':
        raise ValueError('Format export invalide')
    if not isinstance(payload['records'],list):
        raise ValueError('Enregistrements invalides')
    records=_validate(json.dumps(r,ensure_ascii=True) for r in payload['records'])
    canonical=json.dumps(records,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode('ascii')
    digest=hashlib.sha256(canonical).hexdigest()
    return digest==payload['sha256']
