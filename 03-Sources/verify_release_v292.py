"""Fail-closed source/build artifact checks; Windows runtime testing is separate."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def check_source(root=ROOT):
    if (root/'OpenPDF-Studio-V29.3.iss').exists():
        from verify_release_v293 import check_source as current_check
        return current_check(root)
    build=(root/'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')
    exe=(root/'BUILD-WINDOWS-EXE.cmd').read_text(encoding='utf-8')
    iss=(root/'OpenPDF-Studio-V29.2.iss').read_text(encoding='utf-8')
    required=['openpdf_windows_v292.py','OpenPDF-Studio-V29.2.iss','verify_release_v292.py --source','verify_release_v292.py --exe','verify_release_v292.py --installer','openpdf_functional_v282.py','smoke_windows_v292.py --static']
    assert all(x in build for x in required), 'Build chain incomplete'
    assert 'BUILD-WINDOWS-INSTALLER.cmd' in exe and '--exe-only' in exe
    assert 'OutputBaseFilename=OpenPDF-Studio-V29.2-Setup' in iss
    assert 'Source: "dist\\OpenPDF-Studio\\*"' in iss
    assert (root/'openpdf_windows_v292.py').is_file()
    assert 'if not exist ".venv\\Scripts\\python.exe" (' in build
    return True

def check_exe(root=ROOT):
    exe=root/'dist'/'OpenPDF-Studio'/'OpenPDF-Studio.exe'
    assert exe.is_file() and exe.stat().st_size > 100_000, 'Missing/empty Windows executable'
    assert (root/'dist'/'OpenPDF-Studio'/'_internal').is_dir(), 'Missing PyInstaller dependencies'
    return True

def check_installer(root=ROOT):
    check_exe(root)
    path=root/'installer'/'OpenPDF-Studio-V29.2-Setup.exe'
    assert path.is_file() and path.stat().st_size > 100_000, 'Missing/empty installer'
    with path.open('rb') as f: assert f.read(2)==b'MZ', 'Installer is not a PE executable'
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',action='store_true');p.add_argument('--exe',action='store_true');p.add_argument('--installer',action='store_true');a=p.parse_args()
    if a.source: check_source()
    if a.exe: check_exe()
    if a.installer: check_installer()
    print('PASS: requested static/artifact checks (not Windows runtime qualification)')
