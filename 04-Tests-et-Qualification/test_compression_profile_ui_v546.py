"""V546 controlled compression profile and dispatcher regressions.
Author: Abdelhalim Talbi.
"""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03-Sources"))

from openpdf_desktop import (
    COMPRESSION_PROFILE_CHOICES,
    LOSSY_COMPRESSION_PROFILES,
    authorize_compression_profile,
    compression_profile_id,
    compression_profile_option_names,
)
from openpdf_operations import run_operation


class CompressionProfileUiV546(unittest.TestCase):
    def test_visible_choices_are_unique_and_cover_supported_profiles(self):
        labels = [label for label, _ in COMPRESSION_PROFILE_CHOICES]
        ids = [profile for _, profile in COMPRESSION_PROFILE_CHOICES]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {
            "smaller_only", "standard", "images_balanced",
            "images_adaptive", "auto_quality",
        })
        self.assertEqual(LOSSY_COMPRESSION_PROFILES, {
            "images_balanced", "images_adaptive", "auto_quality",
        })

    def test_labels_and_legacy_ids_resolve_to_stable_engine_ids(self):
        for label, profile in COMPRESSION_PROFILE_CHOICES:
            with self.subTest(label=label):
                self.assertEqual(compression_profile_id(label), profile)
                self.assertEqual(compression_profile_id(profile), profile)

    def test_unknown_or_non_string_profile_fails_closed(self):
        for value in ("auto", "Auto", "", None, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                compression_profile_id(value)

    def test_auto_mode_hides_legacy_quality_controls_it_does_not_use(self):
        self.assertEqual(compression_profile_option_names("auto_quality"), ("Profil",))
        self.assertEqual(
            compression_profile_option_names("Automatique contrôlé — comparer et vérifier"),
            ("Profil",),
        )
        self.assertEqual(
            compression_profile_option_names("smaller_only"),
            ("Profil", "Contrôle qualité", "Audit RGB intégral"),
        )
        self.assertEqual(
            compression_profile_option_names("Images adaptatif — perte possible"),
            ("Profil", "Contrôle qualité", "Audit RGB intégral"),
        )

    def test_lossless_profile_does_not_prompt_for_loss_or_preview(self):
        self.assertTrue(authorize_compression_profile(
            "smaller_only",
            ask_lossy=lambda: self.fail("lossless selection must not prompt"),
            preview=lambda: self.fail("lossless selection must not force preview"),
        ))

    def test_each_lossy_profile_requires_consent_and_preview(self):
        for profile in LOSSY_COMPRESSION_PROFILES:
            calls = []
            with self.subTest(profile=profile):
                accepted = authorize_compression_profile(
                    profile,
                    ask_lossy=lambda: calls.append("consent") or True,
                    preview=lambda: calls.append("preview") or True,
                )
                self.assertTrue(accepted)
                self.assertEqual(calls, ["consent", "preview"])

    def test_declined_consent_never_opens_preview(self):
        calls = []
        accepted = authorize_compression_profile(
            "auto_quality",
            ask_lossy=lambda: calls.append("consent") or False,
            preview=lambda: calls.append("preview") or True,
        )
        self.assertFalse(accepted)
        self.assertEqual(calls, ["consent"])

    def test_declined_preview_blocks_publication_path(self):
        calls = []
        accepted = authorize_compression_profile(
            "images_adaptive",
            ask_lossy=lambda: calls.append("consent") or True,
            preview=lambda: calls.append("preview") or False,
        )
        self.assertFalse(accepted)
        self.assertEqual(calls, ["consent", "preview"])

    def _source_pdf(self, folder):
        source = Path(folder) / "source.pdf"
        with fitz.open() as document:
            page = document.new_page(width=400, height=500)
            for index in range(18):
                page.insert_text((30, 35 + index * 20),
                    f"OpenPDF Studio V546 controlled compression line {index:02d}")
            document.save(source, deflate=False, garbage=0)
        # Trailing bytes make the fixture reliably benefit from a safe rewrite.
        with source.open("ab") as stream:
            stream.write(b" " * 4096)
        return source

    def test_auto_quality_dispatch_reports_actual_size_and_bounded_quality(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self._source_pdf(folder)
            destination = Path(folder) / "compressed.pdf"
            before = sha256(source.read_bytes()).hexdigest()
            result = run_operation("compression", [str(source)], str(destination),
                                   profile="auto_quality")
            self.assertIsInstance(result, str)
            self.assertTrue(destination.is_file())
            self.assertIn("Taille mesurée", result)
            self.assertIn("octets", result)
            self.assertIn("gain", result)
            self.assertIn("Profil retenu", result)
            self.assertIn("Contrôle RGB", result)
            self.assertIn("Contrôle structurel", result)
            self.assertIn("pas une certification PDF/A", result)
            self.assertEqual(sha256(source.read_bytes()).hexdigest(), before)
            self.assertLess(destination.stat().st_size, source.stat().st_size)

    def test_auto_quality_no_gain_is_recorded_as_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self._source_pdf(folder)
            destination = Path(folder) / "no-output.pdf"
            no_gain = "Aucun gain conforme aux seuils de qualité. Aucun fichier de sortie modifié."
            with patch("openpdf_auto_compression_v505.auto_compress_gui",
                       return_value=no_gain) as auto, \
                 patch("openpdf_operations.write_event") as event:
                result = run_operation("compression", [str(source)], str(destination),
                                       profile="auto_quality")
            self.assertEqual(result, no_gain)
            auto.assert_called_once()
            self.assertFalse(destination.exists())
            self.assertEqual(event.call_args.args[0], "compression")
            self.assertEqual(event.call_args.args[1], "no_output")


if __name__ == "__main__":
    unittest.main()
