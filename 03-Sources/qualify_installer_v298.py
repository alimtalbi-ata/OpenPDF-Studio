"""Isolated Windows installer smoke test; writes evidence even on failure."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from smoke_windows_v298 import verify_launch
from openpdf_functional_v282 import run as run_pdf_functional

ROOT=Path(__file__).resolve().parent

def command(executable, *args, timeout=180):
    p=subprocess.run([str(executable), *map(str,args)],capture_output=True,text=True,timeout=timeout)
    if p.returncode: raise RuntimeError(f"Exit {p.returncode}: {p.stderr[-600:]} {p.stdout[-600:]}")
    return p.returncode

def is_windows_pe(path):
    """Verify both DOS and PE signatures with bounded reads."""
    path=Path(path)
    if not path.is_file() or path.stat().st_size < 256:
        return False
    with path.open('rb') as f:
        head=f.read(64)
        if head[:2] != b'MZ':
            return False
        offset=int.from_bytes(head[0x3c:0x40], 'little')
        if not 64 <= offset <= min(path.stat().st_size-4, 1048576):
            return False
        f.seek(offset)
        return f.read(4)==b'PE\x00\x00'


def existing_installations(app_id='{A94653C4-3C6E-4B8D-BF1C-728A7EDB1C2A}'):
    """Check both machine and user registry views before any installer is launched."""
    if sys.platform != 'win32':
        return []
    import winreg
    found=[]
    for hive_name, hive in [('HKCU',winreg.HKEY_CURRENT_USER),('HKLM',winreg.HKEY_LOCAL_MACHINE)]:
        for view in [winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY]:
            key_path='Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\'+app_id+'_is1'
            try:
                with winreg.OpenKey(hive,key_path,0,winreg.KEY_READ|view) as key:
                    try: location=winreg.QueryValueEx(key,'InstallLocation')[0]
                    except OSError: location='unknown'
                    found.append({'hive':hive_name,'view':view,'location':location})
            except FileNotFoundError: pass
    return found

def qualify(installer=None, root=ROOT, timeout=25, allow_install_test=False):
    report={'version':'29.7','platform':sys.platform,'utc':datetime.now(timezone.utc).isoformat(), 'status':'FAIL','checks':{}}
    install_root=None
    try:
        report['checks']['pdf_engine_functional'] = run_pdf_functional()
        if not allow_install_test: raise RuntimeError('Installation test disabled by default: pass --allow-install-test on a disposable Windows VM')
        if sys.platform!='win32': raise RuntimeError('Windows required for installation qualification')
        found=existing_installations()
        if found: raise RuntimeError('Existing OpenPDF Studio installation detected; refusing shared AppId installer test: '+json.dumps(found))
        setup=Path(installer) if installer else root/'installer'/'OpenPDF-Studio-V29.8-Setup.exe'
        if not is_windows_pe(setup): raise RuntimeError('Installer missing or not Windows PE')
        install_root=Path(tempfile.mkdtemp(prefix='openpdf-v298-'))/'Application'
        # Inno Setup silent install; unique destination protects existing installations.
        command(setup, '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/DIR={install_root}', '/LOG='+str(install_root.parent/'setup.log'))
        exe=install_root/'OpenPDF-Studio.exe'
        uninstall=install_root/'unins000.exe'
        if not is_windows_pe(exe) or not is_windows_pe(uninstall): raise RuntimeError('Missing installed exe or uninstaller')
        report['checks']['installed_files']=True
        report['checks']['installed_pe_signatures']=True
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
            except Exception as exc:
                report['cleanup_error']=str(exc)
                report['status']='FAIL'
        if install_root is not None and (install_root/'OpenPDF-Studio.exe').exists():
            report['checks']['leftover_executable']=True
            report['status']='FAIL'
            report.setdefault('error','Executable remains after attempted cleanup')
    return report

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--installer')
    parser.add_argument('--allow-install-test',action='store_true',help='Explicitly permit install/uninstall on a disposable Windows VM')
    parser.add_argument('--output',default='qualification-install-v29.7.json')
    parser.add_argument('--timeout',type=float,default=25)
    args=parser.parse_args(argv)
    result=qualify(installer=args.installer,timeout=args.timeout,allow_install_test=args.allow_install_test)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
