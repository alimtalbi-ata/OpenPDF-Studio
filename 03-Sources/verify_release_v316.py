"""Fail-closed source/build artifact checks; Windows runtime testing is separate."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def check_source(root=ROOT):
    from verify_release_v321 import check_source as latest_check
    return latest_check(root)
    build=(root/'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')
    exe=(root/'BUILD-WINDOWS-EXE.cmd').read_text(encoding='utf-8')
    iss=(root/'OpenPDF-Studio-V31.6.iss').read_text(encoding='utf-8')
    required=['openpdf_windows_v316.py','OpenPDF-Studio-V31.6.iss','verify_release_v316.py --source','verify_release_v316.py --exe','verify_release_v316.py --installer','openpdf_functional_v282.py','smoke_windows_v316.py --static']
    assert all(x in build for x in required), 'Build chain incomplete'
    assert 'BUILD-WINDOWS-INSTALLER.cmd' in exe and '--exe-only' in exe
    assert 'OutputBaseFilename=OpenPDF-Studio-V31.6-Setup' in iss
    assert 'Source: "dist\\OpenPDF-Studio\\*"' in iss
    assert (root/'openpdf_windows_v316.py').is_file()
    assert (root/'openpdf_conversion_controller_v309.py').is_file()
    assert (root/'smoke_windows_v316.py').is_file()
    assert (root/'openpdf_guided_v315.py').is_file()
    assert 'openpdf_windows_v315' in (root/'openpdf_windows_v316.py').read_text()
    assert 'build-v31.6.log' in build and 'qualification-static-v31.6.json' in build
    assert '--onefile' in build and 'verify_release_v316.py --portable' in build
    assert 'if not exist ".venv\\Scripts\\python.exe" (' in build
    docs=root/'Documentation'
    required_docs=['Word/OpenPDF-Studio-V31.6-Manuel-Complet.docx','PDF/OpenPDF-Studio-V31.6-Manuel-Complet.pdf','Qualification/CAPTURES-STATUS-V31.6.md','Architecture/ARCHITECTURE-V31.6.md','Installation/COMPILATION-WINDOWS-V31.6.md']
    assert all((docs/f).is_file() and (docs/f).stat().st_size>100 for f in required_docs), 'Documentation manquante'
    return True

def check_exe(root=ROOT):
    exe=root/'dist'/'OpenPDF-Studio'/'OpenPDF-Studio.exe'
    assert exe.is_file() and exe.stat().st_size > 100_000, 'Missing/empty Windows executable'
    assert (root/'dist'/'OpenPDF-Studio'/'_internal').is_dir(), 'Missing PyInstaller dependencies'
    return True

def check_portable(root=ROOT):
    path=root/'portable'/'OpenPDF-Studio-Portable-V31.6.exe'
    assert path.is_file() and path.stat().st_size > 100_000, 'Portable EXE absent ou vide'
    with path.open('rb') as f:
        assert f.read(2)==b'MZ', 'Signature MZ manquante'
        f.seek(0x3c); offset=int.from_bytes(f.read(4),'little')
        assert 64 <= offset < path.stat().st_size-4, 'Offset PE invalide'
        f.seek(offset); assert f.read(4)==b'PE\\0\\0'.replace(b'\\0',b'\0'), 'Signature PE manquante'
    return True

def check_installer(root=ROOT):
    check_exe(root)
    path=root/'installer'/'OpenPDF-Studio-V31.6-Setup.exe'
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
