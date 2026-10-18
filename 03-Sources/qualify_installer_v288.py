"""Isolated Windows installer smoke test; writes evidence even on failure."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from smoke_windows_v288 import verify_launch

ROOT=Path(__file__).resolve().parent

def command(executable, *args, timeout=180):
    p=subprocess.run([str(executable), *map(str,args)],capture_output=True,text=True,timeout=timeout)
    if p.returncode: raise RuntimeError(f"Exit {p.returncode}: {p.stderr[-600:]} {p.stdout[-600:]}")
    return p.returncode

def qualify(installer=None, root=ROOT, timeout=25):
    report={'version':'28.8','platform':sys.platform,'utc':datetime.now(timezone.utc).isoformat(), 'status':'FAIL','checks':{}}
    install_root=None
    try:
        if sys.platform!='win32': raise RuntimeError('Windows required for installation qualification')
        setup=Path(installer) if installer else root/'installer'/'OpenPDF-Studio-V28.8-Setup.exe'
        if not setup.is_file() or setup.read_bytes()[:2]!=b'MZ': raise RuntimeError('Installer missing or not Windows PE')
        install_root=Path(tempfile.mkdtemp(prefix='openpdf-v288-'))/'Application'
        # Inno Setup silent install; unique destination protects existing installations.
        command(setup, '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/DIR={install_root}', '/LOG='+str(install_root.parent/'setup.log'))
        exe=install_root/'OpenPDF-Studio.exe'
        uninstall=install_root/'unins000.exe'
        if not exe.is_file() or not uninstall.is_file(): raise RuntimeError('Missing installed exe or uninstaller')
        report['checks']['installed_files']=True
        report['checks']['launch']=verify_launch(root, timeout=timeout, exe_path=exe)
        report['checks']['uninstaller_found']=True
        command(uninstall,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',timeout=180)
        if exe.exists(): raise RuntimeError('Executable remains after uninstall')
        report['checks']['uninstalled']=True
        report['status']='PASS'
    except Exception as exc:
        report['error']=f'{type(exc).__name__}: {exc}'
    finally:
        if install_root is not None and (install_root/'unins000.exe').is_file():
            try:
                command(install_root/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',timeout=180)
                report['checks']['cleanup_uninstaller_attempted']=True
            except Exception as exc: report['cleanup_error']=str(exc)
    return report

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--installer')
    parser.add_argument('--output',default='qualification-install-v28.8.json')
    parser.add_argument('--timeout',type=float,default=25)
    args=parser.parse_args(argv)
    result=qualify(installer=args.installer,timeout=args.timeout)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
