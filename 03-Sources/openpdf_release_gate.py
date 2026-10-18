"""Fail closed if requested Windows deliverables are missing or unqualified."""
import json,sys,hashlib
from pathlib import Path
from openpdf_verify_pe import verify
VERSION=(Path(__file__).resolve().parents[1]/'VERSION.txt').read_text().strip()
NAMES={'installer':f'OpenPDF-Studio-V{VERSION}-Setup.exe','portable':f'OpenPDF-Studio-Portable-V{VERSION}.exe'}

def validate(directory,mode='all'):
    if mode not in ('all','installer','portable'):raise ValueError('unsupported build mode')
    root=Path(directory)
    requested=('installer','portable') if mode=='all' else (mode,)
    findings=[]
    for edition in requested:
        name=NAMES[edition]; p=root/name
        if not p.is_file() or not verify(p):raise RuntimeError(f'Unverified PE binary: {p}')
        report=root/f'windows-smoke-{edition}.json'
        if not report.is_file():raise RuntimeError(f'Missing Windows smoke report: {report}')
        data=json.loads(report.read_text(encoding='utf-8-sig'))
        if str(data.get('version'))!=VERSION or data.get('mode')!=edition or data.get('passed') is not True:
            raise RuntimeError(f'Failed or stale Windows smoke report: {report}')
        if data.get('artifact_name')!=name or data.get('artifact_sha256')!=hashlib.sha256(p.read_bytes()).hexdigest():
            raise RuntimeError(f'Smoke report not bound to executable: {report}')
        checks=data.get('checks')
        if not isinstance(checks,list) or len(checks)!=2 or any(c.get('passed') is not True for c in checks):
            raise RuntimeError(f'Incomplete smoke checks: {report}')
        if edition=='installer':
            installation=root/f'windows-installation-v{VERSION}.json'
            if not installation.is_file():raise RuntimeError(f'Missing installation evidence: {installation}')
            evidence=json.loads(installation.read_text(encoding='utf-8-sig'))
            required={'silent_install_pass','installed_launch_pass','silent_uninstall_pass'}
            if (evidence.get('passed') is not True or str(evidence.get('version'))!=VERSION
                or evidence.get('artifact_name')!=name
                or evidence.get('artifact_sha256')!=hashlib.sha256(p.read_bytes()).hexdigest()
                or not required.issubset(set(evidence.get('steps',[])))):
                raise RuntimeError(f'Invalid installation evidence: {installation}')
        with p.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        findings.append({'edition':edition,'name':name,'bytes':p.stat().st_size,'sha256':digest})
    return {'version':VERSION,'mode':mode,'qualified':True,'binaries':findings}

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: openpdf_release_gate.py BINARY_DIR all|installer|portable')
    result=validate(sys.argv[1],sys.argv[2]);print(json.dumps(result,indent=2))
