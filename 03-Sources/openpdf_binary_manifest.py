"""Generate a transparent inventory of genuine PE binaries after a Windows build."""
import hashlib,json,sys,datetime
from pathlib import Path
VERSION='39.8'
def inspect(binary):
    binary=Path(binary)
    items=[]
    for name in (f'OpenPDF-Studio-V{VERSION}-Setup.exe',f'OpenPDF-Studio-Portable-V{VERSION}.exe'):
        p=binary/name
        exists=p.is_file()
        size=p.stat().st_size if exists else 0
        mz=__import__('openpdf_verify_pe').verify(p) if exists else False
        items.append({'filename':name,'present':exists,'size_bytes':size,'pe_mz_header':mz,'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if mz else None})
    return {'version':VERSION,'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'binaries':items,'note':'PE header alone does not prove Windows execution; see separate smoke reports.'}
if __name__=='__main__':
    d=Path(sys.argv[1])
    r=inspect(d)
    (d/'binary-manifest-v39.8.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps(r,indent=2))
    if any(x['present'] and not x['pe_mz_header'] for x in r['binaries']):sys.exit(1)
