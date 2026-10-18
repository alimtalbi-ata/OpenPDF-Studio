from pathlib import Path
r=Path(__file__).resolve().parent
for name in ('openpdf_studio.py','openpdf_desktop.py','openpdf_operations.py','openpdf_reservation.py','test_openpdf_v368.py','OpenPDF-Studio-V36.8.iss'):
    assert (r/name).is_file(),name
s=(r.parent/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
assert 'openpdf_studio.py' in s and 'OpenPDF-Studio-V36.8.iss' in s
print('PASS: V36.8 static release')
