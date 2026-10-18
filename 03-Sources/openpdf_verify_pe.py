"""Lightweight structural PE verification, not a substitute for Authenticode or execution."""
import sys,struct
from pathlib import Path
def verify(path):
    p=Path(path)
    if not p.is_file() or p.stat().st_size < 256:return False
    with p.open('rb') as f:
        if f.read(2)!=b'MZ':return False
        f.seek(0x3c); offset=struct.unpack('<I',f.read(4))[0]
        if offset < 64 or offset > p.stat().st_size-24:return False
        f.seek(offset);return f.read(4)==b'PE\0\0'
if __name__=='__main__':
    ok=len(sys.argv)==2 and verify(sys.argv[1]);print('PE_OK' if ok else 'PE_INVALID');sys.exit(0 if ok else 1)
