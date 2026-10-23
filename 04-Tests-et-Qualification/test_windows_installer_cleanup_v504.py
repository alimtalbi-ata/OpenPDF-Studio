"""Windows installer qualification must not run the uninstaller twice on success.
Author: Abdelhalim Talbi — V50.4.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WindowsInstallerCleanupV504(unittest.TestCase):
    def test_cleanup_only_runs_after_failed_installation(self):
        script = (ROOT / '02-Compilation/TEST-WINDOWS-INSTALLATION.ps1').read_text(encoding='utf-8-sig')
        self.assertIn("$report.steps+='silent_uninstall_pass'", script)
        self.assertIn('if (-not $report.passed -and (Test-Path -LiteralPath $folder))', script)
        self.assertIn('if (Test-Path -LiteralPath $exe -PathType Leaf)', script)
        self.assertIn('$report.passed=$true', script)

    def test_ci_checks_no_cleanup_error_and_actual_version(self):
        workflow = (ROOT / '.github/workflows/source-closure-v502.yml').read_text(encoding='utf-8')
        version = (ROOT / 'VERSION.txt').read_text().strip()
        self.assertIn(f"windows-installation-v{version}.json", workflow)
        self.assertIn("if ($report.cleanup_error) { throw 'Unexpected installer cleanup error' }", workflow)
        self.assertIn('test_windows_installer_cleanup_v504.py', workflow)


if __name__ == '__main__':
    unittest.main()
