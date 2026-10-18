"""Publish staged Windows binaries with rollback on failure.
Not an atomic multi-file transaction; readers can see intermediate versions.
"""
import os,sys,shutil,uuid
from pathlib import Path
VERSION='40.0'
NAMES={'installer':f'OpenPDF-Studio-V{VERSION}-Setup.exe','portable':f'OpenPDF-Studio-Portable-V{VERSION}.exe'}
def publish(stage,binary,mode='all',validator=None):
    stage,binary=Path(stage),Path(binary)
    if mode not in ('all','installer','portable'):raise ValueError('invalid mode')
    editions=('installer','portable') if mode=='all' else (mode,)
    names=[NAMES[k] for k in editions]
    names += [f'windows-smoke-{k}.json' for k in editions]
    if 'installer' in editions:names.append(f'windows-installation-v{VERSION}.json')
    for name in names:
        p=stage/name
        if not p.is_file() or p.stat().st_size==0:raise FileNotFoundError(str(p))
        if validator and name.lower().endswith('.exe') and not validator(p):raise ValueError('invalid binary: '+name)
    binary.mkdir(parents=True,exist_ok=True)
    backups={}; promoted=[]; txn=uuid.uuid4().hex
    try:
        for name in names:
            target=binary/name
            if target.exists():
                backup=binary/(name+'.backup-'+txn)
                os.replace(target,backup)
                backups[name]=backup
            # same-filesystem staged copy enables atomic replacement per file
            temp=binary/(name+'.incoming-'+txn)
            try:
                shutil.copy2(stage/name,temp)
                with temp.open('rb') as f:os.fsync(f.fileno())
                os.replace(temp,target)
            finally:
                temp.unlink(missing_ok=True)
            promoted.append(name)
    except BaseException:
        for name in reversed(names):
            target=binary/name
            if name in promoted:target.unlink(missing_ok=True)
            if name in backups:os.replace(backups[name],target)
        raise
    for backup in backups.values():backup.unlink(missing_ok=True)
    return names
if __name__=='__main__':
    from openpdf_verify_pe import verify
    if len(sys.argv)!=4:raise SystemExit('usage: publish.py STAGE BINARY all|installer|portable')
    publish(sys.argv[1],sys.argv[2],sys.argv[3],validator=verify)
    print('PUBLICATION_OK')
