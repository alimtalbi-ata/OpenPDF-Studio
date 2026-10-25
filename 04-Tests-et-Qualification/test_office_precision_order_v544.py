"""V544 precision, extra-token and extraction-order regression tests.
All conversion fixtures are synthetic and known at generation time.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from pathlib import Path
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03-Sources"))
sys.path.insert(0, str(ROOT / "04-Tests-et-Qualification"))

from openpdf_precision_order_v544 import measure_precision_order
from openpdf_office_reference_v542 import evaluate_office_reference_corpus, REPORT_SCHEMA_V2
from openpdf_office_precision_order_ui_v544 import (
    safe_office_receipt, format_office_quality_summary, serialize_office_quality_receipt)
import test_office_reference_v542 as office_fixtures


def extended(thresholds):
    return {
        **thresholds,
        "min_token_precision": 0.90,
        "min_case_token_precision": 0.80,
        "min_case_ordered_token_recall": 0.80,
    }


class OfficePrecisionOrderV544Tests(unittest.TestCase):
    def fixture(self):
        value = office_fixtures.OfficeReferenceV542Tests()
        value.setUp()
        self.addCleanup(value.doCleanups)
        return value

    def test_multiset_precision_detects_unexpected_tokens(self):
        metric = measure_precision_order(["alpha", "beta"], ["alpha", "beta", "extra"])
        self.assertEqual(metric["matched_tokens"], 2)
        self.assertEqual(metric["unexpected_tokens"], 1)
        self.assertAlmostEqual(metric["token_precision"], 2 / 3)
        self.assertEqual(metric["token_recall"], 1.0)

    def test_order_gate_detects_reordering_without_false_precision_failure(self):
        metric = measure_precision_order(["alpha", "beta", "gamma"], ["gamma", "beta", "alpha"])
        self.assertEqual(metric["token_precision"], 1.0)
        self.assertEqual(metric["token_recall"], 1.0)
        self.assertAlmostEqual(metric["ordered_token_recall"], 1 / 3)

    def test_repeated_tokens_are_matched_only_as_many_times_as_expected(self):
        metric = measure_precision_order(["alpha", "alpha", "beta"], ["alpha", "beta", "extra"])
        self.assertEqual(metric["matched_tokens"], 2)
        self.assertAlmostEqual(metric["token_recall"], 2 / 3)
        self.assertEqual(metric["unexpected_tokens"], 1)

    def test_empty_actual_has_zero_scores_not_division_errors(self):
        metric = measure_precision_order(["expected"], [])
        self.assertEqual(metric["token_precision"], 0.0)
        self.assertEqual(metric["token_recall"], 0.0)
        self.assertEqual(metric["token_f1"], 0.0)
        self.assertEqual(metric["ordered_token_recall"], 0.0)

    def test_exact_sequence_passes_with_all_extended_thresholds(self):
        fixture = self.fixture()
        fixture.case("docx", "Contrat alpha 123")
        fixture.case("xlsx", "Budget beta 456")
        fixture.thresholds = extended(fixture.thresholds)
        report = evaluate_office_reference_corpus(fixture.manifest())
        self.assertEqual(report["schema"], REPORT_SCHEMA_V2)
        self.assertEqual(report["status"], "PASS")
        metric = report["precision_order"]
        self.assertEqual(metric["actual_tokens"], metric["matched_tokens"])
        self.assertEqual(metric["unexpected_tokens"], 0)
        self.assertEqual(metric["token_precision"], 1.0)
        self.assertEqual(metric["token_f1"], 1.0)
        self.assertEqual(metric["worst_case_ordered_token_recall"], 1.0)
        self.assertEqual(safe_office_receipt(report)["status"], "PASS")

    def test_legacy_recall_can_pass_while_extended_gate_rejects_extras_and_order(self):
        fixture = self.fixture()
        fixture.case("docx", "Alpha Beta Gamma", actual="Extra Alpha Gamma Beta")
        fixture.case("xlsx", "Budget annual 2026")
        legacy = evaluate_office_reference_corpus(fixture.manifest())
        self.assertEqual(legacy["status"], "PASS")
        fixture.thresholds = extended(fixture.thresholds)
        report = evaluate_office_reference_corpus(fixture.manifest())
        self.assertEqual(report["schema"], REPORT_SCHEMA_V2)
        self.assertEqual(report["token_recall"], 1.0)
        self.assertAlmostEqual(report["precision_order"]["token_precision"], 6 / 7, places=6)
        self.assertEqual(report["precision_order"]["unexpected_tokens"], 1)
        self.assertAlmostEqual(report["precision_order"]["worst_case_token_precision"], 0.75, places=6)
        self.assertAlmostEqual(report["precision_order"]["worst_case_ordered_token_recall"], 2 / 3, places=6)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(set(report["failed_thresholds"]),
                         {"min_token_precision", "min_case_token_precision",
                          "min_case_ordered_token_recall"})
        safe = safe_office_receipt(report)
        self.assertEqual(safe["status"], "FAIL")
        self.assertEqual(set(safe["failed_thresholds"]), set(report["failed_thresholds"]))

    def test_receipt_validation_strips_paths_and_document_text(self):
        fixture = self.fixture()
        fixture.case("docx", "Client secret 123")
        fixture.case("xlsx", "Budget secret 456")
        fixture.thresholds = extended(fixture.thresholds)
        report = evaluate_office_reference_corpus(fixture.manifest())
        report["source_path"] = "C:/Private/secret.pdf"
        report["text"] = "SENSITIVE-CUSTOMER-DATA"
        serialized = serialize_office_quality_receipt(report)
        summary = format_office_quality_summary(report)
        for value in ("Private", "SENSITIVE", "Client secret", str(fixture.root)):
            self.assertNotIn(value, serialized)
            self.assertNotIn(value, summary)
        self.assertIn("Précision", summary)
        self.assertIn("ordre d’extraction", summary)

    def test_extended_thresholds_are_all_or_none_and_bounded(self):
        fixture = self.fixture()
        fixture.case("docx", "Alpha beta")
        fixture.case("xlsx", "Gamma delta")
        partial = {**fixture.thresholds, "min_token_precision": 0.8}
        nan_thresholds = extended(fixture.thresholds)
        nan_thresholds["min_token_precision"] = float("nan")
        bool_thresholds = extended(fixture.thresholds)
        bool_thresholds["min_case_token_precision"] = True
        for thresholds in (partial, nan_thresholds, bool_thresholds):
            fixture.thresholds = thresholds
            with self.subTest(keys=tuple(sorted(thresholds)), values=str(thresholds)), self.assertRaises(ValueError):
                evaluate_office_reference_corpus(fixture.manifest())

    def test_metrics_match_cross_format_aggregates(self):
        fixture = self.fixture()
        fixture.case("docx", "Alpha beta", actual="Alpha beta extra")
        fixture.case("pptx", "Gamma delta")
        fixture.thresholds = {**fixture.thresholds, "min_token_precision": 0.0,
                              "min_case_token_precision": 0.0,
                              "min_case_ordered_token_recall": 0.0}
        report = evaluate_office_reference_corpus(fixture.manifest())
        metric = report["precision_order"]
        self.assertEqual(sum(v["actual_tokens"] for v in metric["by_format"].values()),
                         metric["actual_tokens"])
        self.assertEqual(sum(v["matched_tokens"] for v in metric["by_format"].values()),
                         metric["matched_tokens"])
        self.assertEqual(sum(v["cases"] for v in metric["by_format"].values()), report["cases"])
        self.assertEqual(metric["unexpected_tokens"], 1)


@unittest.skipUnless(os.environ.get("OPENPDF_RUN_GUI_TEST") == "1",
                     "Explicit GUI qualification not requested")
class OfficePrecisionOrderV544LiveGuiTests(unittest.TestCase):
    def test_live_dialog_displays_v2_metrics_and_exports_private_receipt(self):
        import tkinter as tk
        from tkinter import ttk
        from openpdf_desktop import OpenPDFStudio

        fixture = office_fixtures.OfficeReferenceV542Tests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.case("docx", "Alpha Beta Gamma", actual="Extra Alpha Gamma Beta")
        fixture.case("xlsx", "Budget annual 2026")
        fixture.thresholds = extended(fixture.thresholds)
        real_report = evaluate_office_reference_corpus(fixture.manifest())
        self.assertEqual(real_report["schema"], REPORT_SCHEMA_V2)
        self.assertEqual(real_report["status"], "FAIL")

        root = OpenPDFStudio()
        root.withdraw()
        self.addCleanup(lambda: root.destroy() if root.winfo_exists() else None)

        def widgets(widget):
            yield widget
            for child in widget.winfo_children():
                yield from widgets(child)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "receipt.json"
            with mock.patch("openpdf_office_reference_v542.evaluate_office_reference_corpus",
                            return_value=real_report), \
                 mock.patch("openpdf_desktop.filedialog.askopenfilename",
                            return_value="synthetic.json"), \
                 mock.patch("openpdf_desktop.filedialog.asksaveasfilename",
                            return_value=str(target)), \
                 mock.patch("openpdf_desktop.messagebox.showinfo"), \
                 mock.patch("openpdf_desktop.messagebox.showerror") as show_error:
                root._office_quality_dialog()
                root.update()
                window = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))

                def button(label):
                    return next(w for w in widgets(window)
                                if isinstance(w, ttk.Button) and w.cget("text") == label)

                button("Manifeste…").invoke()
                button("Analyser").invoke()
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    root.update()
                    if str(button("Exporter le reçu").cget("state")) == "normal":
                        break
                    time.sleep(.04)
                self.assertEqual(str(button("Exporter le reçu").cget("state")), "normal")
                summary = "\n".join(w.get("1.0", "end") for w in widgets(window)
                                    if isinstance(w, tk.Text))
                self.assertIn("FAIL", summary)
                self.assertIn("Précision", summary)
                self.assertIn("ordre d’extraction", summary)
                self.assertNotIn("Alpha Beta Gamma", summary)
                self.assertNotIn(str(fixture.root), summary)
                button("Exporter le reçu").invoke()
                receipt = json.loads(target.read_text(encoding="utf-8"))
                self.assertEqual(receipt["schema"], REPORT_SCHEMA_V2)
                self.assertEqual(receipt["status"], "FAIL")
                self.assertIn("precision_order", receipt)
                self.assertNotIn(str(fixture.root), target.read_text(encoding="utf-8"))
                button("Exporter le reçu").invoke()
                show_error.assert_called_once()
                window.destroy()


if __name__ == "__main__":
    unittest.main()
