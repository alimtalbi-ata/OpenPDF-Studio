"""Cross-platform source-level packaging preflight (not a Windows binary test)."""
from pathlib import Path
import ast
import json

VERSION = (Path(__file__).resolve().parent.parent / "VERSION.txt").read_text().strip()

def inspect_release(root):
    root=Path(root)
    sources=root/"03-Sources"
    build=root/"02-Compilation"/"BUILD-WINDOWS-INSTALLER.cmd"
    script=build.read_text(encoding="utf-8") if build.is_file() else ""
    iss=sources/f"OpenPDF-Studio-V{VERSION}.iss"
    checks={
      "entrypoint_exists": (sources/"openpdf_studio.py").is_file(),
      "desktop_exists": (sources/"openpdf_desktop.py").is_file(),
      "inno_exists": iss.is_file(),
      "build_references_inno": "OpenPDF-Studio-V%VERSION%.iss" in script,
      "smoke_script_exists": (root/"02-Compilation"/"TEST-WINDOWS-BINARIES.ps1").is_file(),
      "smoke_both_modes": "-Mode installer" in script and "-Mode portable" in script,
      "build_portable": "--onefile" in script,
      "build_installer": "--onedir" in script,
      "build_uses_stable_entry": "openpdf_studio.py" in script,
      "requirements_exist": (sources/"requirements-windows-v260.txt").is_file(),
      "build_has_no_legacy_verifier": "verify_release_v373.py" not in script,
      "python_executable_quoted": '"%PY_EXE%" %PY_ARGS% -m venv .venv' in script,
      "python_path_and_arguments_separated": 'set "PY_EXE="' in script and 'set "PY_ARGS="' in script,
      "single_command_entrypoint": (root / "BUILD-OPENPDF-WINDOWS.cmd").is_file() and
        "BUILD-AND-PACKAGE-WINDOWS.cmd" in (root / "BUILD-OPENPDF-WINDOWS.cmd").read_text(encoding="utf-8"),
      "legacy_entrypoint_delegates": (sources / "BUILD-WINDOWS-INSTALLER.cmd").is_file() and
        "02-Compilation\\BUILD-WINDOWS-INSTALLER.cmd" in (sources / "BUILD-WINDOWS-INSTALLER.cmd").read_text(encoding="utf-8") and
        "v39.9" not in (sources / "BUILD-WINDOWS-INSTALLER.cmd").read_text(encoding="utf-8"),
    }
    if iss.exists():
        txt=iss.read_text(encoding="utf-8")
        checks["inno_version_correct"]=f'#define AppVersion "{VERSION}"' in txt
        checks["inno_installer_filename_correct"]=f"OpenPDF-Studio-V{VERSION}-Setup" in txt
    for f in [sources/"openpdf_studio.py", sources/"openpdf_desktop.py"]:
        if f.exists():
            try: ast.parse(f.read_text(encoding="utf-8")); checks[f"syntax_{f.stem}"]=True
            except SyntaxError: checks[f"syntax_{f.stem}"]=False
    return {"version":VERSION,"passed":all(checks.values()),"checks":checks}

if __name__=="__main__":
    import sys
    result=inspect_release(Path(__file__).resolve().parent.parent)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result["passed"] else 1)
