"""V548 qualification report and guide freshness tests.

All report fixtures are synthetic test inputs; they are never release evidence.
No GitHub API or credential is used by this suite.
Author: Abdelhalim Talbi.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))

import write_v548_ci_qualification as qualification


def outcome_line(name, outcome="ok"):
    cls = "test_source_path_chain_guard_v548.SourcePathChainGuardV548Tests"
    suffix = "skipped 'fixture skip'" if outcome == "skipped" else outcome
    return f"{name} ({cls}.{name}) ... {suffix}"


class V548QualificationLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = qualification.expected_test_names(ROOT)

    def test_expected_names_and_full_pass_log_reconcile(self):
        log = "\n".join(outcome_line(name) for name in self.expected)
        report = qualification.analyze_test_log(log, self.expected)
        self.assertEqual(report["expected"], len(self.expected))
        self.assertEqual(report["passed"], len(self.expected))
        self.assertEqual(report["skipped"], 0)
        self.assertEqual(report["failed"], 0)

    def test_missing_test_result_is_rejected(self):
        log = "\n".join(outcome_line(name) for name in self.expected[:-1])
        with self.assertRaisesRegex(qualification.QualificationError, "did not reconcile"):
            qualification.analyze_test_log(log, self.expected)

    def test_duplicate_test_result_is_rejected(self):
        log = "\n".join(outcome_line(name) for name in self.expected)
        log += "\n" + outcome_line(self.expected[0])
        with self.assertRaisesRegex(qualification.QualificationError, "Duplicate"):
            qualification.analyze_test_log(log, self.expected)

    def test_failed_test_result_is_rejected(self):
        lines = [outcome_line(name) for name in self.expected]
        lines[0] = outcome_line(self.expected[0], "FAIL")
        with self.assertRaisesRegex(qualification.QualificationError, "functional test failed"):
            qualification.analyze_test_log("\n".join(lines), self.expected)

    def test_skip_is_explicit_and_counted_not_silently_passed(self):
        lines = [outcome_line(name) for name in self.expected]
        lines[0] = outcome_line(self.expected[0], "skipped")
        report = qualification.analyze_test_log("\n".join(lines), self.expected)
        self.assertEqual(report["passed"], len(self.expected) - 1)
        self.assertEqual(report["skipped"], 1)
        self.assertEqual(report["skipped_names"], [self.expected[0]])

    def test_log_lines_from_another_class_are_not_counted(self):
        unrelated = [
            f"{name} (different.TestCase.{name}) ... ok"
            for name in self.expected
        ]
        with self.assertRaisesRegex(qualification.QualificationError, "did not reconcile"):
            qualification.analyze_test_log("\n".join(unrelated), self.expected)

    def test_old_green_page_order_run_on_another_sha_is_not_reused(self):
        stale = {
            "workflow_runs": [{
                "name": qualification.PAGE_ORDER_WORKFLOW,
                "head_sha": "b" * 40,
                "status": "completed",
                "conclusion": "success",
                "id": 123,
            }]
        }
        with mock.patch.object(qualification, "_request_json", return_value=stale):
            with self.assertRaisesRegex(qualification.QualificationError, "exact source revision"):
                qualification._candidate_page_order_run(
                    "alimtalbi-ata/OpenPDF-Studio", "test-token", self.head
                )

    def test_current_page_order_run_is_selected_by_exact_sha(self):
        current = {
            "workflow_runs": [{
                "name": qualification.PAGE_ORDER_WORKFLOW,
                "head_sha": self.head,
                "status": "completed",
                "conclusion": "success",
                "id": 456,
                "created_at": "2026-10-26T00:00:00Z",
            }]
        }
        with unittest.mock.patch.object(qualification, "_request_json", return_value=current):
            run = qualification._candidate_page_order_run(
                "alimtalbi-ata/OpenPDF-Studio", "test-token", self.head
            )
        self.assertEqual(run["id"], 456)



class V548GuideFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "generate_docs_v514_tested", ROOT / "02-Compilation" / "generate_docs_v514.py"
        )
        cls.docs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.docs)
        cls.manifest = json.loads(
            (ROOT / "07-Manifestes" / "V51.4-REQUIRED-RUNTIME-MODULES.json").read_text(encoding="utf-8")
        )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        manifest_path = self.root / "07-Manifestes" / "V51.4-REQUIRED-RUNTIME-MODULES.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.head = "a" * 40

    def valid_report(self):
        count = len(self.manifest["modules"])
        tests = {
            platform: {
                "expected": 7, "passed": 7, "skipped": 0, "failed": 0,
                "conclusion": "success", "job_id": 101 if platform == "ubuntu" else 102,
                "job_url": "https://github.com/alimtalbi-ata/OpenPDF-Studio/actions/runs/1/job/101",
            }
            for platform in ("ubuntu", "windows")
        }
        return {
            "schema": "openpdf.v548.ci-qualification.v1",
            "version": "51.4",
            "qualified": True,
            "repository": "alimtalbi-ata/OpenPDF-Studio",
            "branch": "feature/v51.4-source-path-chain-guard-v548-20261026",
            "commit_sha": self.head,
            "module_count": count,
            "page_order": {
                "head_sha": self.head, "status": "completed", "conclusion": "success",
                "tests": tests,
                "jobs": {
                    "ubuntu": {"name": "page-order-functional (ubuntu-latest)", "status": "completed", "conclusion": "success"},
                    "windows": {"name": "page-order-functional (windows-latest)", "status": "completed", "conclusion": "success"},
                },
            },
            "source_closure": {
                "prerequisite_jobs": {
                    "source_closure": {"status": "completed", "conclusion": "success"}
                },
                "native_windows": {
                    "portable": {"smoke_passed": True},
                    "installer": {"smoke_passed": True},
                    "installation": {"passed": True},
                },
            },
            "limits": {
                "windows_gui_human_qualified": False,
                "ocr_accuracy_certified": False,
                "authenticode_signed": False,
            },
        }

    def write_report(self, report):
        path = self.root / "04-Tests-et-Qualification" / "V548-CI-QUALIFICATION.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report), encoding="utf-8")
        return path

    def test_unqualified_guide_says_ci_is_unverified_and_has_no_stale_counts(self):
        sections = dict(self.docs.build_sections(self.root, None))
        text = "\n".join(sections.values())
        self.assertIn("NON VÉRIFIÉE", text)
        self.assertIn(f"{len(self.manifest['modules'])} modules distincts", text)
        for obsolete in ("1 176 tests", "94 modules", "40051065571", "24 octobre 2026"):
            self.assertNotIn(obsolete, text)

    def test_current_report_is_accepted_only_for_same_commit(self):
        self.write_report(self.valid_report())
        self.assertIsNotNone(self.docs.load_current_ci_report(self.root, expected_head_sha=self.head))
        self.assertIsNone(self.docs.load_current_ci_report(self.root, expected_head_sha="b" * 40))

    def test_old_report_schema_is_ignored(self):
        report = self.valid_report()
        report["schema"] = "openpdf.v547.qualification.v1"
        self.write_report(report)
        self.assertIsNone(self.docs.load_current_ci_report(self.root, expected_head_sha=self.head))

    def test_failed_or_skipped_test_cannot_be_called_fully_qualified(self):
        report = self.valid_report()
        report["page_order"]["tests"]["windows"]["passed"] = 6
        report["page_order"]["tests"]["windows"]["failed"] = 1
        self.write_report(report)
        self.assertIsNone(self.docs.load_current_ci_report(self.root, expected_head_sha=self.head))

    def test_stale_runtime_module_count_is_rejected(self):
        report = self.valid_report()
        report["module_count"] -= 1
        self.write_report(report)
        self.assertIsNone(self.docs.load_current_ci_report(self.root, expected_head_sha=self.head))

    def test_missing_native_install_receipt_is_rejected(self):
        report = self.valid_report()
        del report["source_closure"]["native_windows"]["installation"]
        self.write_report(report)
        self.assertIsNone(self.docs.load_current_ci_report(self.root, expected_head_sha=self.head))


if __name__ == "__main__":
    unittest.main()
