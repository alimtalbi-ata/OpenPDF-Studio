"""OpenPDF Studio V25.6: create/verify a self-contained, offline audit dossier.

python audit_dossier_v256.py create AUDIT.json SOURCE.pdf TARGET.pdf -o dossier.zip
python audit_dossier_v256.py verify dossier.zip --report rapport.txt
"""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from bind_pdf_audit_v255 import bind,verify_bound,canonical

NAMES=('audit-bound.json','source.pdf','target.pdf','manifest.json','verification.txt')
SCHEMA='openpdf-audit-dossier-v25.6'
def sha(data):return hashlib.sha256(data).hexdigest()
def describe(ok,message,manifest=None):
    lines=['OpenPDF Studio V25.6 — Rapport de vérification','Auteur : Abdelhalim Talbi','Résultat : '+('PASS' if ok else 'FAIL'),'Détail : '+message]
    if manifest:
        lines.extend(['Dossier : '+str(manifest.get('schema','inconnu')),'Empreinte source : '+str(manifest.get('files',{}).get('source.pdf','?')),'Empreinte cible : '+str(manifest.get('files',{}).get('target.pdf','?'))])
    lines.append('Limite : contrôle d’intégrité uniquement ; aucune signature ni identité certifiée.')
    return '\n'.join(lines)+'\n'
def create(audit_path,source_path,target_path,out):
    source=Path(source_path).read_bytes();target=Path(target_path).read_bytes()
    if not source.startswith(b'%PDF-') or not target.startswith(b'%PDF-'):raise ValueError('Les deux fichiers doivent avoir un en-tête PDF')
    audit=json.loads(Path(audit_path).read_text(encoding='utf-8'))
    bound=bind(audit,source_path,target_path)
    files={'audit-bound.json':json.dumps(bound,ensure_ascii=False,indent=2).encode('utf-8'),'source.pdf':source,'target.pdf':target}
    manifest={'schema':SCHEMA,'files':{name:sha(data) for name,data in files.items()}}
    files['manifest.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
    files['verification.txt']=describe(True,'Dossier créé ; revérifier avec la commande verify.',manifest).encode('utf-8')
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    return verify(out)
def verify(path):
    try:
        with zipfile.ZipFile(path) as z:
            if len(z.infolist())!=len(NAMES) or set(z.namelist())!=set(NAMES) or any(x.is_dir() for x in z.infolist()):return False,'Structure ZIP inattendue',None
            if any(x.file_size>100*1024*1024 for x in z.infolist()):return False,'Fichier trop volumineux',None
            files={name:z.read(name) for name in NAMES}
        manifest=json.loads(files['manifest.json']);bound=json.loads(files['audit-bound.json'])
        if not isinstance(manifest,dict) or manifest.get('schema')!=SCHEMA or set(manifest.get('files',{}))!=set(NAMES[:3]):return False,'Manifeste invalide',None
        for name in NAMES[:3]:
            if sha(files[name])!=manifest['files'][name]:return False,'Empreinte incorrecte : '+name,manifest
        if not files['source.pdf'].startswith(b'%PDF-') or not files['target.pdf'].startswith(b'%PDF-'):return False,'En-tête PDF invalide',manifest
        # Reuse the independently tested V25.5 byte-level verifier without writing user files.
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            s=Path(d)/'source.pdf';t=Path(d)/'target.pdf';s.write_bytes(files['source.pdf']);t.write_bytes(files['target.pdf'])
            ok,msg=verify_bound(bound,s,t)
        return ok,msg,manifest
    except (OSError,ValueError,TypeError,KeyError,zipfile.BadZipFile) as exc:return False,str(exc),None

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    c=sub.add_parser('create');c.add_argument('audit');c.add_argument('source');c.add_argument('target');c.add_argument('-o','--output',required=True)
    v=sub.add_parser('verify');v.add_argument('dossier');v.add_argument('--report')
    args=p.parse_args()
    try:
        if args.action=='create':ok,msg,manifest=create(args.audit,args.source,args.target,args.output)
        else:ok,msg,manifest=verify(args.dossier)
        report=describe(ok,msg,manifest)
        if args.action=='verify' and args.report:Path(args.report).write_text(report,encoding='utf-8')
        print(report,end='');return 0 if ok else 1
    except (OSError,ValueError,TypeError,KeyError) as exc:print(describe(False,str(exc)),end='');return 1
if __name__=='__main__':raise SystemExit(main())
