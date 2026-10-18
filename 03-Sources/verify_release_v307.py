"""Fail-closed source/build artifact checks; Windows runtime testing is separate."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def check_source(root=ROOT):
    from verify_release_v308 import check_source as latest
    return latest(root)

def check_exe(root=ROOT):
    exe=root/'dist'/'OpenPDF-Studio'/'OpenPDF-Studio.exe'
    assert exe.is_file() and exe.stat().st_size > 100_000, 'Missing/empty Windows executable'
    assert (root/'dist'/'OpenPDF-Studio'/'_internal').is_dir(), 'Missing PyInstaller dependencies'
    return True

def check_portable(root=ROOT):
    path=root/'portable'/'OpenPDF-Studio-Portable-V30.7.exe'
    assert path.is_file() and path.stat().st_size > 100_000, 'Portable EXE absent ou vide'
    with path.open('rb') as f:
        assert f.read(2)==b'MZ', 'Signature MZ manquante'
        f.seek(0x3c); offset=int.from_bytes(f.read(4),'little')
        assert 64 <= offset < path.stat().st_size-4, 'Offset PE invalide'
        f.seek(offset); assert f.read(4)==b'PE\\0\\0'.replace(b'\\0',b'\0'), 'Signature PE manquante'
    return True

def check_installer(root=ROOT):
    check_exe(root)
    path=root/'installer'/'OpenPDF-Studio-V30.7-Setup.exe'
    assert path.is_file() and path.stat().st_size > 100_000, 'Missing/empty installer'
    with path.open('rb') as f: assert f.read(2)==b'MZ', 'Installer is not a PE executable'
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',action='store_true');p.add_argument('--exe',action='store_true');p.add_argument('--installer',action='store_true');p.add_argument('--portable',action='store_true');a=p.parse_args()
    if a.source: check_source()
    if a.exe: check_exe()
    if a.installer: check_installer()
    if a.portable: check_portable()
    print('PASS: requested static/artifact checks (not Windows runtime qualification)')
