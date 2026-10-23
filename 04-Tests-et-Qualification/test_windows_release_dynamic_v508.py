"""Static tag-release workflow regression; not a native Windows execution test.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/windows-release.yml'


class DynamicWindowsReleaseV508(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding='utf-8')

    def test_tag_release_uses_current_version_file(self):
        self.assertIn('Get-Content -LiteralPath VERSION.txt -Raw', self.text)
        self.assertIn('OPENPDF_VERSION=$version', self.text)

    def test_tag_mismatch_fails_closed(self):
        self.assertIn('GITHUB_REF_TYPE', self.text)
        self.assertIn('GITHUB_REF_NAME -ne "v$version"', self.text)
        self.assertIn('throw "Tag', self.text)

    def test_no_hardcoded_legacy_release(self):
        self.assertNotIn('V40.2', self.text)
        self.assertNotIn('v40.2', self.text)

    def test_uses_one_command_build(self):
        self.assertIn('call 02-Compilation\\BUILD-WINDOWS-INSTALLER.cmd', self.text)

    def test_validates_both_current_version_binaries(self):
        self.assertIn('OpenPDF-Studio-V{0}-Setup.exe', self.text)
        self.assertIn('OpenPDF-Studio-Portable-V{0}.exe', self.text)
        self.assertIn('binary-manifest-v{0}.json', self.text)
        self.assertIn('windows-installation-v{0}.json', self.text)

    def test_versioned_artifact_names(self):
        self.assertEqual(self.text.count('$' + '{{ env.OPENPDF_VERSION }}'), 2)

    def test_never_uploads_unqualified_binary(self):
        self.assertRegex(self.text, r'(?s)Upload qualified binaries.*?if: success\(\)')
        self.assertIn('if-no-files-found: error', self.text)


if __name__ == '__main__':
    unittest.main()
