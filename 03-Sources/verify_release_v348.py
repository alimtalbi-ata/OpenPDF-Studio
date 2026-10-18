"""V34.8 fail-closed release gate, no claim of Windows runtime qualification."""
from pathlib import Path
import argparse,ast,re
ROOT=Path(__file__).resolve().parent
VERSION="34.8"
def check_source(root=ROOT):
    build=(root/'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')
    iss=(root/'OpenPDF-Studio-V34.8.iss').read_text(encoding='utf-8')
    assert 'openpdf_windows_v348.py' in build and 'openpdf_windows_v339.py' not in build
    assert 'verify_release_v348.py --source' in build
    assert 'AppVersion "34.8"' in iss
    assert 'OutputBaseFilename=OpenPDF-Studio-V34.8-Setup' in iss
    for f in ('openpdf_windows_v348.py','openpdf_compression_service_v344.py','openpdf_page_service_v345.py','test_openpdf_v345.py','test_openpdf_v348.py','openpdf_conversion_audit_v346.py','openpdf_windows_v348.py','openpdf_ui_controller_v348.py','test_openpdf_v348.py','openpdf_windows_v340.py','openpdf_controller_v340.py','openpdf_operations_v342.py','openpdf_orchestrator_v343.py','test_openpdf_v343.py'):
        ast.parse((root/f).read_text(encoding='utf-8'))
    docs=root.parent/'05-Documentation'
    for ext,folder in (('docx','Word'),('pdf','PDF')):
        assert (docs/folder/f'OpenPDF-Studio-V34.8-Manuel-Complet.{ext}').stat().st_size>1000
    return True
def check_exe(root=ROOT):
    f=root/'dist'/'OpenPDF-Studio'/'OpenPDF-Studio.exe'
    assert f.is_file() and f.stat().st_size>100000
    return True
def check_portable(root=ROOT):
    f=root/'portable'/'OpenPDF-Studio-Portable-V34.8.exe'
    assert f.is_file() and f.stat().st_size>100000 and f.read_bytes()[:2]==b'MZ'
    return True
def check_installer(root=ROOT):
    f=root/'installer'/'OpenPDF-Studio-V34.8-Setup.exe'
    assert f.is_file() and f.stat().st_size>100000 and f.read_bytes()[:2]==b'MZ'
    return True
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('source','exe','portable','installer'):p.add_argument('--'+arg,action='store_true')
    a=p.parse_args()
    for arg in ('source','exe','portable','installer'):
        if getattr(a,arg):globals()['check_'+arg]()
    print('PASS: V34.8 static/artifact checks only')
