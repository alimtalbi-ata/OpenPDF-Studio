from pathlib import Path
root=Path(__file__).resolve().parent
for f in ("openpdf_studio.py","openpdf_desktop.py","openpdf_operations.py","openpdf_navigation.py","openpdf_jobs.py","openpdf_dependency_audit.py","test_openpdf_v364.py"):
 assert (root/f).is_file(),f
assert (root.parent/"02-Compilation"/"BUILD-WINDOWS-INSTALLER.cmd").is_file()
assert (root/"OpenPDF-Studio-V36.4.iss").is_file()
print("PASS: V36.4 static release files")
