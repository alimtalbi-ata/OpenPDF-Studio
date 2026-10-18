import unittest
from pathlib import Path
from openpdf_release_gate import VERSION
ROOT=Path(__file__).resolve().parents[1]
class WindowsBuildIntegrityTests(unittest.TestCase):
    def test_current_inno_script_exists(self):
        self.assertTrue((ROOT/f'03-Sources/OpenPDF-Studio-V{VERSION}.iss').is_file())
    def test_build_invokes_matching_inno(self):
        cmd=(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertIn(f'"OpenPDF-Studio-V{VERSION}.iss"',cmd)
        self.assertIn('openpdf_release_gate.py "%STAGE%"',cmd)
    def test_staging_paths_match(self):
        iss=(ROOT/f'03-Sources/OpenPDF-Studio-V{VERSION}.iss').read_text()
        self.assertIn(f'binary\\.staging-v{VERSION}',iss)
        self.assertIn(f'OutputBaseFilename=OpenPDF-Studio-V{VERSION}-Setup',iss)
    def test_ci_runner_and_upload(self):
        ci=(ROOT/'.github/workflows/windows-release.yml').read_text()
        self.assertIn('windows-2022',ci)
        self.assertIn('upload-artifact@v4',ci)
        self.assertIn('BUILD-WINDOWS-INSTALLER.cmd',ci)
if __name__=='__main__': unittest.main()
