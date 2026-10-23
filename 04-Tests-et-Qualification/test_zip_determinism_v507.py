"""V50.7: generated ZIP inventory/qualification metadata must be reproducible.
Author: Abdelhalim Talbi.
"""
from io import BytesIO
from pathlib import Path
import hashlib
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '02-Compilation'))
from package_cumulative_v434 import write_fixed_member, INVENTORY


class ZipDeterminismV507(unittest.TestCase):
    def _archive(self):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            write_fixed_member(z, '07-Manifestes/RELEASE-QUALIFICATION-LIMITS.txt', b'qualified')
            write_fixed_member(z, INVENTORY, b'[]')
        return buffer.getvalue()

    def test_generated_metadata_is_byte_identical(self):
        self.assertEqual(hashlib.sha256(self._archive()).hexdigest(),
                         hashlib.sha256(self._archive()).hexdigest())

    def test_generated_metadata_has_fixed_timestamp_and_permissions(self):
        with zipfile.ZipFile(BytesIO(self._archive())) as z:
            for info in z.infolist():
                self.assertEqual(info.date_time, (2020, 1, 1, 0, 0, 0))
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o644)
                self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)


if __name__ == '__main__':
    unittest.main()
