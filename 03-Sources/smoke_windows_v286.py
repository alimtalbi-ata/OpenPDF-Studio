"""Windows GUI launch qualification with failure-safe JSON report and optional real screenshot."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from windows_window_probe_v286 import matching_window

ROOT = Path(__file__).resolve().parent

def executable(root=ROOT):
    return root / 'dist' / 'OpenPDF-Studio' / 'OpenPDF-Studio.exe'

def verify_static(root=ROOT):
    exe = executable(root)
    if not exe.is_file(): raise RuntimeError('Missing packaged executable')
    with exe.open('rb') as fh:
        if fh.read(2) != b'MZ': raise RuntimeError('Executable lacks Windows PE header')
    if not (exe.parent / '_internal').is_dir(): raise RuntimeError('Missing PyInstaller _internal directory')
    return {'exe': str(exe), 'bytes': exe.stat().st_size, 'pe_header': True}

def verify_launch(root=ROOT, timeout=12, screenshot=None):
    if sys.platform != 'win32': raise RuntimeError('Windows runtime qualification requires Windows')
    exe = executable(root)
    verify_static(root)
    proc = subprocess.Popen([str(exe)], cwd=str(exe.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + timeout
        found = None
        while time.monotonic() < deadline:
            if proc.poll() is not None: raise RuntimeError(f'Application exited during startup: {proc.returncode}')
            found = matching_window(proc.pid)
            if found: break
            time.sleep(0.25)
        if not found: raise RuntimeError(f'No visible OpenPDF Studio window after {timeout}s')
        result = {'started': True, 'pid': proc.pid, 'window': found, 'visible_window_verified': True}
        if screenshot:
            try:
                from PIL import ImageGrab
                target = Path(screenshot).resolve()
                target.parent.mkdir(parents=True, exist_ok=True)
                ImageGrab.grab().save(target)
                result['screenshot'] = str(target)
                result['screenshot_type'] = 'real Windows desktop capture; window title independently verified'
            except Exception as exc:
                result['screenshot_error'] = str(exc)
        return result
    finally:
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

def qualify(static=False, launch=False, screenshot=None, root=ROOT, timeout=6):
    report = {'version':'28.6', 'timestamp_utc':datetime.now(timezone.utc).isoformat(), 'platform':sys.platform, 'status':'FAIL', 'checks':{}}
    try:
        report['checks']['static'] = verify_static(root)
        if launch: report['checks']['launch'] = verify_launch(root, timeout=timeout, screenshot=screenshot)
        report['status'] = 'PASS'
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    return report

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--static',action='store_true')
    ap.add_argument('--launch',action='store_true')
    ap.add_argument('--screenshot')
    ap.add_argument('--output')
    ap.add_argument('--timeout',type=float,default=6)
    args=ap.parse_args(argv)
    report=qualify(static=args.static,launch=args.launch,screenshot=args.screenshot,timeout=args.timeout)
    if args.output:
        output=Path(args.output)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
