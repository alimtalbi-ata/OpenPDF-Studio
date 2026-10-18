"""Bind each Windows smoke report to the final staged artifact by SHA-256."""
import sys,json,hashlib
from pathlib import Path
from openpdf_verify_pe import verify
VERSION=(Path(__file__).resolve().parents[1]/'VERSION.txt').read_text().strip()
def bind(stage,mode):
    stage=Path(stage)
    editions=('installer','portable') if mode=='all' else (mode,)
    for edition in editions:
        name=f'OpenPDF-Studio-V{VERSION}-Setup.exe' if edition=='installer' else f'OpenPDF-Studio-Portable-V{VERSION}.exe'
        exe=stage/name; report=stage/f'windows-smoke-{edition}.json'
        if not verify(exe):raise RuntimeError('Invalid staged executable: '+name)
        data=json.loads(report.read_text(encoding='utf-8-sig'))
        if data.get('passed') is not True or data.get('mode')!=edition or str(data.get('version'))!=VERSION:raise RuntimeError('Invalid smoke report')
        if len(data.get('checks',[]))!=2 or not all(x.get('passed') is True for x in data['checks']):raise RuntimeError('Incomplete checks')
        data['artifact_name']=name
        data['artifact_sha256']=hashlib.sha256(exe.read_bytes()).hexdigest()
        report.write_text(json.dumps(data,indent=2),encoding='utf-8')
        if edition=='installer':
            install=stage/f'windows-installation-v{VERSION}.json'
            evidence=json.loads(install.read_text(encoding='utf-8-sig'))
            if evidence.get('passed') is not True or str(evidence.get('version'))!=VERSION:raise RuntimeError('Invalid installation report')
            evidence['artifact_name']=name
            evidence['artifact_sha256']=data['artifact_sha256']
            install.write_text(json.dumps(evidence,indent=2),encoding='utf-8')
if __name__=='__main__':bind(sys.argv[1],sys.argv[2])
