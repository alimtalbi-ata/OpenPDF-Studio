"""V49.5 regression tests for active OOXML content preflight."""
from io import BytesIO
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '02-Compilation'))
from openpdf_docx_safety_v495 import validate_release_docx

REL = 'http://schemas.openxmlformats.org/package/2006/relationships'


def docx(parts):
    out = BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('word/document.xml', b'<w:document/>')
        for name, payload in parts.items():
            z.writestr(name, payload)
    return out.getvalue()


def rel(target, mode='Internal'):
    return (f'<Relationships xmlns="{REL}"><Relationship Id="r1" '
            f'Type="image" Target="{target}" TargetMode="{mode}"/></Relationships>').encode()


class ReleaseDocxSafetyTests(unittest.TestCase):
    def test_safe_internal_image(self):
        result = validate_release_docx(docx({'word/_rels/document.xml.rels': rel('media/image1.png'),
                                             'word/media/image1.png': b'PNG'}))
        self.assertEqual(result['relationships_checked'], 1)

    def test_external_https_link_rejected(self):
        with self.assertRaisesRegex(ValueError, 'External'):
            validate_release_docx(docx({'word/_rels/document.xml.rels': rel('https://example.invalid', 'External')}))

    def test_external_file_link_rejected(self):
        with self.assertRaisesRegex(ValueError, 'External'):
            validate_release_docx(docx({'word/_rels/document.xml.rels': rel('file:///C:/secrets', 'External')}))

    def test_implicit_url_rejected(self):
        with self.assertRaisesRegex(ValueError, 'External'):
            validate_release_docx(docx({'word/_rels/document.xml.rels': rel('https://example.invalid')}))

    def test_vba_project_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Active'):
            validate_release_docx(docx({'word/vbaProject.bin': b'fixture'}))

    def test_embedded_object_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Active'):
            validate_release_docx(docx({'word/embeddings/oleObject1.bin': b'fixture'}))

    def test_macro_content_type_rejected(self):
        xml = b'<Types><Override ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/></Types>'
        with self.assertRaisesRegex(ValueError, 'Macro'):
            validate_release_docx(docx({'[Content_Types].xml': xml}))

    def test_dtd_rejected(self):
        xml = b'<!DOCTYPE x [<!ENTITY test "boom">]><Relationships/>'
        with self.assertRaisesRegex(ValueError, 'DTD'):
            validate_release_docx(docx({'_rels/.rels': xml}))

    def test_bad_xml_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Malformed'):
            validate_release_docx(docx({'_rels/.rels': b'<Relationships'}))

    def test_oversized_relationship_rejected(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            validate_release_docx(docx({'_rels/.rels': b' ' * (1024 * 1024 + 1)}))

    def test_windows_absolute_relationship_rejected(self):
        with self.assertRaisesRegex(ValueError, 'External'):
            validate_release_docx(docx({'_rels/.rels': rel('C:/windows/system32')}))

    def test_release_docx_fixture(self):
        root = Path(__file__).resolve().parents[1]
        p = root / '05-Documentation' / 'OpenPDF-Studio-V49.4-Guide.docx'
        if p.is_file():
            self.assertGreater(validate_release_docx(p.read_bytes())['parts'], 10)


if __name__ == '__main__':
    unittest.main()
