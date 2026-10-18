"""Native Windows portable launch smoke test (must run on Windows)."""
import argparse,json,subprocess,sys,time
from pathlib import Path
from verify_release_v298 import check_portable

def check(root=Path(__file__).resolve().parent, seconds=20):
    report={'version':'29.7','platform':sys.platform,'status':'FAIL'}
    if sys.platform!='win32':
        report['reason']='Windows required';return report
    try:
        check_portable(root)
        exe=root/'portable'/'OpenPDF-Studio-Portable-V29.8.exe'
        proc=subprocess.Popen([str(exe)],cwd=str(root),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                if proc.poll() is not None:raise RuntimeError(f'Portable exited early: {proc.returncode}')
                time.sleep(.25)
            report['status']='PASS'
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
    except Exception as exc:report['reason']=str(exc)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='qualification-portable-v29.7.json');a=p.parse_args()
    r=check();Path(a.output).write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps(r));sys.exit(0 if r['status']=='PASS' else 1)
