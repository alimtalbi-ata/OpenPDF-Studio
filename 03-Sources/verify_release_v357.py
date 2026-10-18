"""V35.7 static build validation (no claim of Windows execution)."""
from pathlib import Path
import sys
p=Path(__file__).resolve().parent
b=(p.parent/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf8')
for token in ('openpdf_windows_v357.py','verify_release_v357.py','OpenPDF-Studio-V35.7.iss','test_openpdf_v357'):
 assert token in b,token
for file in ('openpdf_windows_v357.py','openpdf_corpus_v357.py','test_openpdf_v357.py','OpenPDF-Studio-V35.7.iss'):
 assert (p/file).is_file(),file
print('V35.7 STATIC SOURCE GATE PASS')
