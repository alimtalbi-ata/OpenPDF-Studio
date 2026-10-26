"""Pure parser/document freshness tests for V551; fixtures are not CI evidence."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))
import write_v551_ci_qualification as qualification
import generate_docs_v551 as docs


def log_line(name, result="ok"):
    tail = "skipped 'platform-only'" if result == "skipped" else result
    return f"{name} (test_atomic_output_v551.AtomicOutputV551Tests.{name}) ... {tail}"


class V551QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names = qualification.expected_test_names(ROOT)

    def test_page_order_job_map_comes_from_canonical_v549_helper(self):
        # V550 re-exports the V549 helper module as `v549`; it does not define
        # PAGE_JOB_NAMES itself. Keep receipt generation aligned with that API.
        names = qualification.v550.v549.PAGE_JOB_NAMES
        self.assertEqual(set(names), {"ubuntu", "windows"})
        source = (ROOT / "02-Compilation" / "write_v551_ci_qualification.py").read_text(encoding="utf-8")
        self.assertIn("for platform, job_name in v550.v549.PAGE_JOB_NAMES.items():", source)
    def test_inventory_has_eight_tests(self):
        self.assertEqual(len(self.names), 8)

    def test_ubuntu_platform_skips_only_six_native_windows_tests(self):
        rows = [
            log_line(name, "skipped") if name in qualification.WINDOWS_ONLY_TESTS
            else log_line(name)
            for name in self.names
        ]
        parsed = qualification.analyze_test_log("\n".join(rows), self.names)
        self.assertEqual(parsed["expected"], 8)
        self.assertEqual(parsed["passed"], 2)
        self.assertEqual(parsed["skipped"], 6)
        self.assertEqual(set(parsed["skipped_names"]), qualification.WINDOWS_ONLY_TESTS)
        self.assertTrue(qualification.validate_platform_results("ubuntu", parsed, self.names))

    def test_windows_requires_all_eight_native_and_static_tests_to_pass(self):
        parsed = qualification.analyze_test_log(
            "\n".join(log_line(name) for name in self.names), self.names
        )
        self.assertEqual((parsed["expected"], parsed["passed"], parsed["skipped"], parsed["failed"]),
                         (8, 8, 0, 0))
        self.assertTrue(qualification.validate_platform_results("windows", parsed, self.names))

    def test_unexpected_skip_failure_duplicate_and_missing_result_are_rejected(self):
        rows = [log_line(name) for name in self.names]
        rows[0] = log_line(self.names[0], "skipped")
        parsed = qualification.analyze_test_log("\n".join(rows), self.names)
        with self.assertRaises(qualification.v550.v549.QualificationError):
            qualification.validate_platform_results("windows", parsed, self.names)
        rows = [log_line(name) for name in self.names]
        rows[0] = log_line(self.names[0], "FAIL")
        with self.assertRaises(qualification.v550.v549.QualificationError):
            qualification.analyze_test_log("\n".join(rows), self.names)
        with self.assertRaises(qualification.v550.v549.QualificationError):
            qualification.analyze_test_log("\n".join(rows[:-1]), self.names)
        duplicate = "\n".join(log_line(name) for name in self.names) + "\n" + log_line(self.names[0])
        with self.assertRaises(qualification.v550.v549.QualificationError):
            qualification.analyze_test_log(duplicate, self.names)

    def receipt(self, sha):
        tests = {
            "ubuntu": {
                "expected": 8, "passed": 2, "skipped": 6, "failed": 0,
                "skipped_names": sorted(qualification.WINDOWS_ONLY_TESTS),
                "job_url": "https://github.com/example/job", "conclusion": "success",
            },
            "windows": {
                "expected": 8, "passed": 8, "skipped": 0, "failed": 0,
                "skipped_names": [],
                "job_url": "https://github.com/example/job", "conclusion": "success",
            },
        }
        return {
            "schema": qualification.SCHEMA, "version": "51.4", "milestone": "V551",
            "qualified": True, "commit_sha": sha,
            "page_order": {
                "head_sha": sha, "status": "completed", "conclusion": "success",
                "url": "https://github.com/example/actions/runs/123",
                "tests": tests,
            },
            "parent_v550": {"qualified": True, "commit_sha": sha},
            "capabilities": {"windows_native_handle_relative_publication": True, "windows_path_based_fallback": False},
            "limits": {"full_windows_toctou_elimination": False},
        }

    def test_document_rejects_stale_or_incomplete_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "04-Tests-et-Qualification" / "V551-CI-QUALIFICATION.json"
            target.parent.mkdir()
            good_sha = "a" * 40
            target.write_text(json.dumps(self.receipt(good_sha)), encoding="utf-8")
            self.assertIsNotNone(docs.load_current_report(root, expected_head_sha=good_sha))
            self.assertIsNone(docs.load_current_report(root, expected_head_sha="b" * 40))
            invalid = self.receipt(good_sha)
            invalid["page_order"]["tests"]["windows"]["skipped"] = 1
            target.write_text(json.dumps(invalid), encoding="utf-8")
            self.assertIsNone(docs.load_current_report(root, expected_head_sha=good_sha))


if __name__ == "__main__":
    unittest.main(verbosity=2)
