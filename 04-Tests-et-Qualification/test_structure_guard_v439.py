"""Functional PDF preservation tests, V43.9. Author: Abdelhalim Talbi."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
import fitz
from openpdf_structure_guard_v439 import validate_structure_preserved
from openpdf_compression_v327 import compress_with_profile

class InteractiveStructureTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.src = self.root / 'source.pdf'
        self.dst = self.root / 'candidate.pdf'

    def make(self, *, link=True, annotation=True, widget=False, outline=True,
             attachment=False, title='Original', signature=False):
        with fitz.open() as doc:
            page = doc.new_page(width=400, height=400)
            page.insert_text((40, 80), 'OpenPDF Studio')
            if link:
                page.insert_link({'kind': fitz.LINK_URI, 'from': fitz.Rect(35, 65, 170, 85),
                                  'uri': 'https://example.org'})
            if annotation:
                annot = page.add_text_annot((80, 100), 'Validation requise')
                annot.set_info(title='Réviseur', subject='Note')
                annot.update()
            if widget or signature:
                w = fitz.Widget()
                w.field_name = 'accept' if widget else 'signature'
                w.field_type = fitz.PDF_WIDGET_TYPE_TEXT if widget else fitz.PDF_WIDGET_TYPE_SIGNATURE
                w.rect = fitz.Rect(50, 160, 220, 185)
                w.field_value = 'OUI' if widget else ''
                page.add_widget(w)
            if outline:
                doc.set_toc([[1, 'Chapitre 1', 1]])
            if attachment:
                doc.embfile_add('audit.txt', b'preuve d audit', filename='audit.txt')
            doc.set_metadata({'title': title, 'author': 'Abdelhalim Talbi'})
            doc.save(self.src)

    def copy(self):
        with fitz.open(self.src) as doc:
            doc.save(self.dst, garbage=4, deflate=True)

    def test_preserves_link_annotation_outline_metadata(self):
        self.make(); self.copy()
        report = validate_structure_preserved(self.src, self.dst)
        self.assertEqual(report['links_verified'], 1)
        self.assertEqual(report['annotations_verified'], 1)
        self.assertEqual(report['bookmarks_verified'], 1)

    def test_rejects_lost_link(self):
        self.make(); self.copy()
        with fitz.open(self.dst) as doc:
            page = doc[0]
            page.delete_link(page.get_links()[0])
            doc.saveIncr()
        with self.assertRaisesRegex(RuntimeError, 'Liens/annotations'):
            validate_structure_preserved(self.src, self.dst)

    def test_rejects_changed_annotation(self):
        self.make(); self.copy()
        with fitz.open(self.dst) as doc:
            page = doc[0]
            annot = next(page.annots())
            annot.set_info(content='Texte altéré')
            annot.update()
            doc.saveIncr()
        with self.assertRaisesRegex(RuntimeError, 'Liens/annotations'):
            validate_structure_preserved(self.src, self.dst)

    def test_rejects_lost_bookmark(self):
        self.make(); self.copy()
        with fitz.open(self.dst) as doc:
            doc.set_toc([])
            doc.saveIncr()
        with self.assertRaisesRegex(RuntimeError, 'Signets'):
            validate_structure_preserved(self.src, self.dst)

    def test_rejects_metadata_change(self):
        self.make(); self.copy()
        with fitz.open(self.dst) as doc:
            doc.set_metadata({'title': 'Autre titre'})
            doc.saveIncr()
        with self.assertRaisesRegex(RuntimeError, 'Métadonnées'):
            validate_structure_preserved(self.src, self.dst)

    def test_preserves_widget(self):
        self.make(widget=True); self.copy()
        self.assertEqual(validate_structure_preserved(self.src, self.dst)['widgets_verified'], 1)

    def test_rejects_changed_widget_value(self):
        self.make(widget=True); self.copy()
        with fitz.open(self.dst) as doc:
            page = doc[0]
            widget = next(page.widgets())
            widget.field_value = 'NON'
            widget.update()
            doc.saveIncr()
        with self.assertRaisesRegex(RuntimeError, 'Liens/annotations'):
            validate_structure_preserved(self.src, self.dst)

    def test_preserves_attachment(self):
        self.make(attachment=True); self.copy()
        self.assertEqual(validate_structure_preserved(self.src, self.dst)['attachments_verified'], 1)

    def test_rejects_lost_attachment(self):
        self.make(attachment=True); self.copy()
        with fitz.open(self.dst) as doc:
            doc.embfile_del('audit.txt')
            doc.saveIncr()
        with self.assertRaisesRegex(RuntimeError, 'Pièces jointes'):
            validate_structure_preserved(self.src, self.dst)

    def test_rejects_signature_field(self):
        self.make(signature=True); self.copy()
        with self.assertRaisesRegex(RuntimeError, 'signature'):
            validate_structure_preserved(self.src, self.dst)

    def test_engine_does_not_publish_candidate_without_link(self):
        self.make(link=True, annotation=False, outline=False)
        output = self.root / 'output.pdf'
        def fake_engine(_source, tmp):
            with fitz.open(self.src) as doc:
                page = doc[0]
                page.delete_link(page.get_links()[0])
                doc.save(tmp, garbage=4, deflate=True)
        with patch('openpdf_compression_v327.compress_images', side_effect=fake_engine):
            with self.assertRaisesRegex(RuntimeError, 'Liens/annotations'):
                compress_with_profile(self.src, output, 'images_balanced')
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob('.openpdf-*.pdf')), [])

if __name__ == '__main__':
    unittest.main()
