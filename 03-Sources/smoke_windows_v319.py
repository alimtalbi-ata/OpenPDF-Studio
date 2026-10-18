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

def verify_static(root=ROOT, exe_path=None):
    exe = Path(exe_path) if exe_path else executable(root)
    if not exe.is_file(): raise RuntimeError('Missing packaged executable')
    with exe.open('rb') as fh:
        if fh.read(2) != b'MZ': raise RuntimeError('Executable lacks Windows PE header')
    if not (exe.parent / '_internal').is_dir(): raise RuntimeError('Missing PyInstaller _internal directory')
    return {'exe': str(exe), 'bytes': exe.stat().st_size, 'pe_header': True}

def verify_launch(root=ROOT, timeout=12, screenshot=None, exe_path=None):
    if sys.platform != 'win32': raise RuntimeError('Windows runtime qualification requires Windows')
    exe = Path(exe_path) if exe_path else executable(root)
    verify_static(root, exe_path=exe_path)
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
                from windows_window_probe_v286 import window_rectangle
                rect = window_rectangle(found['hwnd'])
                if rect is None:
                    raise RuntimeError('Verified window has no usable screen rectangle')
                ImageGrab.grab(bbox=rect).save(target)
                result['window_rectangle'] = list(rect)
                result['screenshot'] = str(target)
                result['screenshot_type'] = 'real capture cropped to independently verified OpenPDF Studio window'
            except Exception as exc:
                raise RuntimeError(f'Window screenshot failed: {exc}') from exc
        return result
    finally:
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

def qualify(static=False, launch=False, screenshot=None, root=ROOT, timeout=12, exe_path=None):
    report = {'version':'29.7', 'timestamp_utc':datetime.now(timezone.utc).isoformat(), 'platform':sys.platform, 'status':'FAIL', 'checks':{}}
    try:
        report['checks']['static'] = verify_static(root, exe_path=exe_path)
        if launch: report['checks']['launch'] = verify_launch(root, timeout=timeout, screenshot=screenshot, exe_path=exe_path)
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
    ap.add_argument('--timeout',type=float,default=12)
    ap.add_argument('--exe-path')
    args=ap.parse_args(argv)
    report=qualify(static=args.static,launch=args.launch,screenshot=args.screenshot,timeout=args.timeout,exe_path=args.exe_path)
    if args.output:
        output=Path(args.output)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
