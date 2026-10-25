"""V538: real PDF semantic regression for quality-gated compression.

A raster/text-only acceptance must reject invisible losses of PDF navigation,
review annotations and descriptive metadata. All files are local fixtures.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import sys
import tempfile
import unittest

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_compression_acceptance_v489 import (
    AcceptancePolicy, CompressionRejected, audit_compression_candidate)


class CompressionSemanticV538(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.source = self.root / 'original.pdf'
        self.candidate = self.root / 'candidate.pdf'

    def fixture(self, *, link=False, bookmark=False, annotation=False, metadata=False):
        with fitz.open() as doc:
            page = doc.new_page(width=400, height=300)
            page.insert_text((40, 70), 'Quality-gated PDF semantic regression')
            if link:
                page.insert_link({'kind': fitz.LINK_URI, 'from': fitz.Rect(40, 90, 200, 110),
                                  'uri': 'https://example.org/reference'})
            if annotation:
                note = page.add_text_annot((220, 110), 'Reviewer note')
                note.update()
            if bookmark:
                doc.set_toc([[1, 'Chapter one', 1]])
            if metadata:
                doc.set_metadata({'title': 'User title', 'author': 'Abdelhalim Talbi'})
            doc.save(self.source)
        # Harmless trailing whitespace is ignored by PDF readers. It makes
        # the tampered candidate genuinely smaller, so size gates cannot mask
        # the missing semantic comparison.
        with self.source.open('ab') as stream:
            stream.write(b'\n' + b' ' * 10000)

    def candidate_copy(self, mutate=None):
        with fitz.open(self.source) as doc:
            if mutate:
                mutate(doc)
            doc.save(self.candidate, garbage=4, deflate=True)
        self.assertLess(self.candidate.stat().st_size, self.source.stat().st_size)

    def assert_semantic_rejected(self, keyword):
        with self.assertRaisesRegex(CompressionRejected, keyword):
            audit_compression_candidate(self.source, self.candidate,
                                        AcceptancePolicy(max_page_mae=0,
                                                         max_page_changed_fraction=0))

    def test_preserved_link_and_bookmark_pass(self):
        self.fixture(link=True, bookmark=True, metadata=True)
        self.candidate_copy()
        result = audit_compression_candidate(self.source, self.candidate)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['structure']['links_verified'], 1)
        self.assertEqual(result['structure']['bookmarks_verified'], 1)

    def test_invisible_link_loss_rejected(self):
        self.fixture(link=True)
        self.candidate_copy(lambda doc: doc[0].delete_link(doc[0].get_links()[0]))
        self.assert_semantic_rejected('Liens|structure|semanti')

    def test_invisible_bookmark_loss_rejected(self):
        self.fixture(bookmark=True)
        self.candidate_copy(lambda doc: doc.set_toc([]))
        self.assert_semantic_rejected('Signets|structure|semanti')

    def test_invisible_metadata_loss_rejected(self):
        self.fixture(metadata=True)
        self.candidate_copy(lambda doc: doc.set_metadata({}))
        self.assert_semantic_rejected('M.tadonn.es|structure|semanti')

    def test_invisible_annotation_loss_rejected(self):
        self.fixture(annotation=True)
        def remove(doc):
            page = doc[0]
            page.delete_annot(next(page.annots()))
        self.candidate_copy(remove)
        # The visible annotation icon is small and may change rendered pixels,
        # so use permissive RGB policy to isolate the semantic invariant.
        with self.assertRaisesRegex(CompressionRejected, 'annotations|structure|semanti'):
            audit_compression_candidate(self.source, self.candidate,
                AcceptancePolicy(max_page_mae=255, max_page_changed_fraction=1))

    def test_real_auto_compression_reports_semantic_evidence(self):
        self.fixture(link=True, bookmark=True, metadata=True)
        from openpdf_auto_compression_v505 import auto_compress
        report = auto_compress(self.source, self.candidate)
        self.assertEqual(report['status'], 'published', report)
        semantic = report['selected_quality']['structure']
        self.assertEqual(semantic['pages_verified'], 1)
        self.assertEqual(semantic['links_verified'], 1)
        self.assertEqual(semantic['bookmarks_verified'], 1)
        self.assertTrue(self.candidate.is_file())

    def test_semantic_receipt_is_bound_to_auto_quality(self):
        self.fixture(link=True, bookmark=True)
        self.candidate_copy()
        from types import SimpleNamespace
        from openpdf_compression_evidence_v506 import verified_evidence
        audit = audit_compression_candidate(self.source, self.candidate)
        src_size = self.source.stat().st_size
        dst_size = self.candidate.stat().st_size
        policy = AcceptancePolicy()
        from dataclasses import asdict
        metrics = SimpleNamespace(visual_audit=audit, published=True, profile='smaller_only',
                                  source_sha256=audit['source_sha256'], source_bytes=src_size,
                                  output_bytes=dst_size)
        receipt = SimpleNamespace(published=True, metrics=metrics, visual_audit=audit,
                                  sha256=audit['candidate_sha256'], size=dst_size)
        result = verified_evidence(receipt, source_sha256=audit['source_sha256'],
            source_bytes=src_size, candidate_sha256=audit['candidate_sha256'],
            candidate_bytes=dst_size, profile='smaller_only', policy=policy)
        self.assertEqual(result['structure']['links_verified'], 1)
        bad = dict(audit)
        bad['structure'] = {'pages_verified': 1}
        metrics.visual_audit = bad
        receipt.visual_audit = bad
        with self.assertRaises(RuntimeError):
            verified_evidence(receipt, source_sha256=audit['source_sha256'],
                source_bytes=src_size, candidate_sha256=audit['candidate_sha256'],
                candidate_bytes=dst_size, profile='smaller_only', policy=policy)


if __name__ == '__main__':
    unittest.main()
