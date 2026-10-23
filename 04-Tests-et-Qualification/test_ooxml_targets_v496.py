"""V49.6 real DOCX package-relationship containment regression tests."""
from io import BytesIO
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '02-Compilation'))
from openpdf_docx_safety_v495 import validate_release_docx

REL = 'http://schemas.openxmlformats.org/package/2006/relationships'


def package(target, *, part='word/_rels/document.xml.rels', member='word/media/picture.png'):
    rels = (f'<Relationships xmlns="{REL}"><Relationship Id="rId1" '
            f'Type="image" Target="{target}"/></Relationships>').encode()
    with BytesIO() as buffer:
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('word/document.xml', '<document/>')
            archive.writestr(part, rels)
            archive.writestr(member, b'fake-png')
        return buffer.getvalue()


class OoxmlTargetTests(unittest.TestCase):
    def test_present_relative_target(self):
        self.assertEqual(validate_release_docx(package('media/picture.png'))['relationships_checked'], 1)

    def test_parent_within_package(self):
        self.assertEqual(validate_release_docx(package('../media/picture.png',
            part='word/charts/_rels/chart1.xml.rels'))['relationships_checked'], 1)

    def test_missing_target_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            validate_release_docx(package('media/missing.png'))

    def test_traversal_escape_rejected(self):
        with self.assertRaisesRegex(ValueError, 'escapes'):
            validate_release_docx(package('../../outside.png'))

    def test_encoded_dot_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            validate_release_docx(package('%2e%2e/%2e%2e/outside.png'))

    def test_encoded_slash_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            validate_release_docx(package('media%2fpicture.png'))

    def test_fragment_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            validate_release_docx(package('media/picture.png#frag'))

    def test_query_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            validate_release_docx(package('media/picture.png?download=1'))

    def test_root_relationship_valid(self):
        self.assertEqual(validate_release_docx(package('word/document.xml',
            part='_rels/.rels', member='word/media/picture.png'))['relationships_checked'], 1)

    def test_bad_relationship_location_rejected(self):
        with self.assertRaisesRegex(ValueError, 'location'):
            validate_release_docx(package('media/picture.png', part='word/document.xml.rels'))

    def test_existing_release_document(self):
        root = Path(__file__).resolve().parents[1]
        p = root / '05-Documentation' / 'OpenPDF-Studio-V49.5-Guide.docx'
        if p.is_file():
            self.assertGreater(validate_release_docx(p.read_bytes())['parts'], 10)


if __name__ == '__main__':
    unittest.main()
