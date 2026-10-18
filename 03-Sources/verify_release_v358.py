from pathlib import Path
p=Path(__file__).resolve().parent
b=(p.parent/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf8')
for token in ('openpdf_windows_v358.py','verify_release_v358.py','OpenPDF-Studio-V35.8.iss','test_openpdf_v358'):
 assert token in b,token
for name in ('openpdf_windows_v358.py','openpdf_batch_quality_v358.py','test_openpdf_v358.py','OpenPDF-Studio-V35.8.iss'):
 assert (p/name).is_file(),name
print('V35.8 STATIC SOURCE GATE PASS — Windows build not executed')
