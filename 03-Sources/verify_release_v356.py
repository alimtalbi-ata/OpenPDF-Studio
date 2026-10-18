"""Release checks V35.6. No Windows runtime claims. Author: Abdelhalim Talbi."""
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def verify(mode):
    build=(ROOT/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
    assert 'openpdf_windows_v356.py' in build
    assert 'test_openpdf_v356' in build
    assert 'verify_release_v356.py --source' in build
    iss=(ROOT/'OpenPDF-Studio-V35.6.iss').read_text()
    assert 'OpenPDF-Studio-V35.6-Setup' in iss
    for name in ('openpdf_windows_v356.py','openpdf_roundtrip_v356.py','openpdf_quality_metrics_v356.py','test_openpdf_v356.py'):
        assert (ROOT/name).is_file(),name
    if mode=='exe':assert (ROOT/'dist/OpenPDF-Studio/OpenPDF-Studio.exe').is_file()
    if mode=='portable':assert (ROOT/'portable/OpenPDF-Studio-Portable-V35.6.exe').is_file()
    if mode=='installer':assert (ROOT/'installer/OpenPDF-Studio-V35.6-Setup.exe').is_file()
    return True
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',action='store_true');parser.add_argument('--exe',action='store_true');parser.add_argument('--portable',action='store_true');parser.add_argument('--installer',action='store_true')
    args=parser.parse_args();mode='installer' if args.installer else 'portable' if args.portable else 'exe' if args.exe else 'source'
    verify(mode);print('PASS',mode)
