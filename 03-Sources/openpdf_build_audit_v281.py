"""Version-aware Windows packaging audit. Author: Abdelhalim Talbi."""
from pathlib import Path
import re

def audit(root):
    root=Path(root)
    script=(root/'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')
    wrapper=(root/'BUILD-WINDOWS-EXE.cmd').read_text(encoding='utf-8')
    match=re.search(r'openpdf_windows_v(\d+)\.py',script)
    version=match.group(1) if match else ''
    dotted=f'{version[:-1]}.{version[-1:]}' if version else ''
    iss_path=root/f'OpenPDF-Studio-V{dotted}.iss'
    iss=iss_path.read_text(encoding='utf-8') if iss_path.exists() else ''
    return {'entrypoint':bool(version) and (root/f'openpdf_windows_v{version}.py').exists(),
            'test_gate':'unittest' in script and '|| goto fail' in script,
            'exe_gate':r'dist\OpenPDF-Studio\OpenPDF-Studio.exe' in script,
            'installer_gate':f'OpenPDF-Studio-V{dotted}-Setup.exe' in script,
            'installer_definition':iss_path.name in script,
            'shared_build':'BUILD-WINDOWS-INSTALLER.cmd' in wrapper and '--exe-only' in wrapper,
            'iss_payload':'recursesubdirs' in iss and r'dist\OpenPDF-Studio' in iss,
            'iss_version':bool(dotted) and dotted in iss}
