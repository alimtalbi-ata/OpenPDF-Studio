"""Windows post-build smoke verification; never claim a GUI pass without a real Windows run."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent

def verify_static():
    exe=ROOT/'dist'/'OpenPDF-Studio'/'OpenPDF-Studio.exe'
    if not exe.is_file(): raise RuntimeError('Missing packaged executable')
    if exe.read_bytes()[:2] != b'MZ': raise RuntimeError('Executable lacks Windows PE header')
    if not (exe.parent/'_internal').is_dir(): raise RuntimeError('Missing PyInstaller _internal directory')
    return {'exe':str(exe),'bytes':exe.stat().st_size,'pe_header':True}

def verify_launch(timeout=12):
    if sys.platform!='win32': raise RuntimeError('Windows runtime qualification requires Windows')
    exe=ROOT/'dist'/'OpenPDF-Studio'/'OpenPDF-Studio.exe'
    proc=subprocess.Popen([str(exe)],cwd=str(exe.parent),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        time.sleep(min(timeout, 5))
        if proc.poll() is not None:
            raise RuntimeError('Application exited during startup (exit code %s): %s' % (proc.returncode,proc.stderr.read().decode(errors='replace')[-2000:]))
        return {'started':True,'pid':proc.pid,'startup_seconds':min(timeout,5)}
    finally:
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill();proc.wait()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--static',action='store_true');ap.add_argument('--launch',action='store_true');ap.add_argument('--output');args=ap.parse_args()
    results={'platform':sys.platform,'static':verify_static()}
    if args.launch:results['launch']=verify_launch()
    if args.output:Path(args.output).write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
