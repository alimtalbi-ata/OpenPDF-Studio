"""Privacy-preserving opt-in operation audit. Abdelhalim Talbi.
Never records filenames, source paths, destination paths, or document contents.
"""
import json
import os
import time
from pathlib import Path

def write_event(operation, status, duration_ms, *, directory=None, max_bytes=1048576):
    """Append one compact JSONL event only when explicitly enabled.

    OPENPDF_AUDIT=1 enables; OPENPDF_AUDIT_DIR selects an existing private folder.
    Audit failure must never change the result of the document operation.
    """
    if os.environ.get('OPENPDF_AUDIT') != '1':
        return False
    if operation not in {'compression','fusion','extraction','decoupage','reorganisation','ocr','docx','xlsx','pptx'}:
        return False
    if status not in {'success','failure','no_output'}:
        return False
    try:
        folder=Path(directory or os.environ.get('OPENPDF_AUDIT_DIR') or Path.home()/'.openpdf-studio').expanduser()
        folder.mkdir(parents=True,exist_ok=True)
        log=folder/'operations.jsonl'
        if log.is_symlink():
            return False
        if log.exists() and log.stat().st_size>=max_bytes:
            rotated=folder/'operations.previous.jsonl'
            if rotated.is_symlink(): return False
            log.replace(rotated)
        record={'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'operation':operation,'status':status,'duration_ms':max(0,int(duration_ms))}
        flags=os.O_WRONLY|os.O_CREAT|os.O_APPEND
        if hasattr(os,'O_NOFOLLOW'):flags|=os.O_NOFOLLOW
        fd=os.open(log,flags,0o600)
        with os.fdopen(fd,'a',encoding='utf-8') as stream:
            stream.write(json.dumps(record,ensure_ascii=True,separators=(',',':'))+'\n')
        return True
    except (OSError,ValueError,TypeError):
        return False
