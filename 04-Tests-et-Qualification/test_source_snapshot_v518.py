"""Regression: cumulative source snapshot must include the one-command Windows launcher.
Author: Abdelhalim Talbi. Static contract, not a native Windows qualification.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SourceSnapshotV518Tests(unittest.TestCase):
    def test_required_paths_in_source_artifact(self):
        workflow = (ROOT / '.github/workflows/source-closure-v502.yml').read_text(encoding='utf-8')
        artifact = workflow.split('name: v514-reconciled-source-snapshot', 1)[1]
        for required in (
            'BUILD-OPENPDF-WINDOWS.cmd',
            'VERSION.txt',
            '02-Compilation/**',
            '03-Sources/**',
            '04-Tests-et-Qualification/*.py',
            '05-Documentation/*.md',
            '07-Manifestes/*.json',
        ):
            with self.subTest(path=required):
                self.assertIn(required, artifact)
        self.assertTrue((ROOT / 'BUILD-OPENPDF-WINDOWS.cmd').is_file())

    def test_single_entrypoint_delegates_to_build_pipeline(self):
        launcher = (ROOT / 'BUILD-OPENPDF-WINDOWS.cmd').read_text(encoding='utf-8')
        self.assertIn('BUILD-WINDOWS-INSTALLER.cmd', launcher)
        self.assertIn('%*', launcher)


if __name__ == '__main__':
    unittest.main()
