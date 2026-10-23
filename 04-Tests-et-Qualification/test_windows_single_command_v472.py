"""V47.2 build orchestration contract tests (static, NOT native Windows execution).

Author: Abdelhalim Talbi.
"""
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / '03-Sources'
sys.path.insert(0, str(SOURCES))
from openpdf_build_preflight import inspect_release


class WindowsSingleCommandV472(unittest.TestCase):
    def setUp(self):
        self.build = (ROOT / '02-Compilation' / 'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')
        self.launch = (ROOT / 'BUILD-OPENPDF-WINDOWS.cmd').read_text(encoding='utf-8')
        self.compat = (SOURCES / 'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')

    def test_preflight_current_release(self):
        report = inspect_release(ROOT)
        self.assertTrue(report['passed'], report['checks'])
        self.assertEqual(report['version'], (ROOT / 'VERSION.txt').read_text().strip())

    def test_one_command_calls_qualified_pipeline(self):
        self.assertIn('BUILD-AND-PACKAGE-WINDOWS.cmd', self.launch)
        self.assertIn('exit /b %errorlevel%', self.launch)
        pipeline = (ROOT / '02-Compilation' / 'BUILD-AND-PACKAGE-WINDOWS.cmd').read_text(encoding='utf-8')
        commands = ('BUILD-WINDOWS-INSTALLER.cmd', 'VERIFY-WINDOWS-RELEASE.ps1',
                    'generate_release_docs.py', 'package_cumulative_v434.py')
        self.assertEqual(len(commands), sum(name in pipeline for name in commands))
        self.assertEqual(sorted(pipeline.index(x) for x in commands), [pipeline.index(x) for x in commands])

    def test_legacy_entrypoint_only_delegates(self):
        self.assertIn('02-Compilation\\BUILD-WINDOWS-INSTALLER.cmd', self.compat)
        self.assertIn('%*', self.compat)
        self.assertIn('exit /b %errorlevel%', self.compat)
        for forbidden in ('PyInstaller', 'winget', 'v39.9', 'OpenPDF-Studio-V39.9.iss'):
            self.assertNotIn(forbidden, self.compat)

    def test_python_executable_quoted_for_spaces(self):
        self.assertIn('"%PY_EXE%" %PY_ARGS% -m venv .venv', self.build)
        self.assertIn('set "PY_EXE=py"', self.build)
        self.assertIn('set "PY_ARGS=-3.12"', self.build)
        self.assertIn('"%ProgramFiles%\\Python312\\python.exe"', self.build)
        self.assertNotIn('%PY% -m venv', self.build)
        self.assertNotIn('set "PY=py -3.12"', self.build)

    def test_versioned_inno_recipe_matches(self):
        version = (ROOT / 'VERSION.txt').read_text().strip()
        recipe = (SOURCES / f'OpenPDF-Studio-V{version}.iss').read_text()
        self.assertIn(f'#define AppVersion "{version}"', recipe)
        self.assertIn(f'OutputBaseFilename=OpenPDF-Studio-V{version}-Setup', recipe)
        self.assertIn('OpenPDF-Studio-V%VERSION%.iss', self.build)

    def test_native_evidence_required_before_cumulative_package(self):
        pipeline = (ROOT / '02-Compilation' / 'BUILD-AND-PACKAGE-WINDOWS.cmd').read_text()
        self.assertLess(pipeline.index('VERIFY-WINDOWS-RELEASE.ps1'), pipeline.index('package_cumulative_v434.py'))
        package = (ROOT / '02-Compilation' / 'package_cumulative_v434.py').read_text()
        self.assertIn("'BUILD-OPENPDF-WINDOWS.cmd'", package)
        for marker in ('windows-installation-v', 'windows-smoke-installer.json', 'artifact_sha256', 'Missing qualified Windows artifact'):
            self.assertIn(marker, package)

    def test_preflight_fails_closed_when_launcher_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            tmp = Path(folder)
            for name in ('01-Application', '02-Compilation', '03-Sources'):
                (tmp / name).mkdir()
            (tmp / 'VERSION.txt').write_text('47.2')
            # Even if a source entrypoint exists, no complete build is claimed.
            report = inspect_release(tmp)
            self.assertFalse(report['passed'])
            self.assertFalse(report['checks']['single_command_entrypoint'])


if __name__ == '__main__':
    unittest.main()
