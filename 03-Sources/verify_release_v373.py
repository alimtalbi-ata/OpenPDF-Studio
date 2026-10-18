from pathlib import Path
p=Path(__file__).resolve().parent
for f in ("openpdf_studio.py","openpdf_reservation.py","test_openpdf_v373.py","OpenPDF-Studio-V37.3.iss"):
 assert (p/f).is_file(),f
b=(p.parent/"02-Compilation"/"BUILD-WINDOWS-INSTALLER.cmd").read_text()
assert "OpenPDF-Studio-V37.3.iss" in b
print("V37.3 static build configuration: PASS")
