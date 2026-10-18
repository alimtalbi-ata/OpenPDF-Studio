"""Fail-closed source/build artifact checks; Windows runtime testing is separate."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def check_source(root=ROOT):
    # Compatibility adapter: historical release checks validate the current build.
    from verify_release_v292 import check_source as current_check
    return current_check(root)

def check_exe(root=ROOT):
    exe=root/'dist'/'OpenPDF-Studio'/'OpenPDF-Studio.exe'
    assert exe.is_file() and exe.stat().st_size > 100_000, 'Missing/empty Windows executable'
    assert (root/'dist'/'OpenPDF-Studio'/'_internal').is_dir(), 'Missing PyInstaller dependencies'
    return True

def check_installer(root=ROOT):
    check_exe(root)
    path=root/'installer'/'OpenPDF-Studio-V29.1-Setup.exe'
    assert path.is_file() and path.stat().st_size > 100_000, 'Missing/empty installer'
    with path.open('rb') as f: assert f.read(2)==b'MZ', 'Installer is not a PE executable'
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',action='store_true');p.add_argument('--exe',action='store_true');p.add_argument('--installer',action='store_true');a=p.parse_args()
    if a.source: check_source()
    if a.exe: check_exe()
    if a.installer: check_installer()
    print('PASS: requested static/artifact checks (not Windows runtime qualification)')
