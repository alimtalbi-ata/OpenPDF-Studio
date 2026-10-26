"""Pure tests for V550 qualification parsing; synthetic fixtures are not evidence."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))
import write_v550_ci_qualification as qualification
import generate_docs_v550 as docs


def line(name, result="ok"):
    suffix = "skipped 'platform-only'" if result == "skipped" else result
    return f"{name} (test_atomic_output_v550.AtomicOutputV550Tests.{name}) ... {suffix}"


class V550QualificationParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names = qualification.expected_test_names(ROOT)

    def test_source_inventory_contains_eleven_tests(self):
        self.assertEqual(len(self.names), 11)

    def test_all_functional_results_are_parsed(self):
        report = qualification.analyze_test_log("\n".join(line(n) for n in self.names), self.names)
        self.assertEqual((report["expected"], report["passed"], report["skipped"], report["failed"]), (11,11,0,0))
        self.assertTrue(qualification.validate_platform_results("ubuntu", report))

    def test_only_documented_windows_platform_skips_are_accepted(self):
        rows = [line(n, "skipped") if n in qualification.ALLOWED_WINDOWS_SKIPS else line(n) for n in self.names]
        report = qualification.analyze_test_log("\n".join(rows), self.names)
        self.assertEqual(report["skipped_names"], sorted(qualification.ALLOWED_WINDOWS_SKIPS))
        self.assertEqual(report["passed"], 6)
        self.assertTrue(qualification.validate_platform_results("windows", report))

    def test_unexpected_windows_skip_is_not_qualified(self):
        rows = [line(n, "skipped") if n == self.names[0] else line(n) for n in self.names]
        report = qualification.analyze_test_log("\n".join(rows), self.names)
        with self.assertRaises(qualification.v549.QualificationError):
            qualification.validate_platform_results("windows", report)

    def test_missing_duplicate_and_failure_outcomes_are_rejected(self):
        with self.assertRaises(qualification.v549.QualificationError):
            qualification.analyze_test_log("\n".join(line(n) for n in self.names[:-1]), self.names)
        dup = "\n".join(line(n) for n in self.names) + "\n" + line(self.names[0])
        with self.assertRaises(qualification.v549.QualificationError):
            qualification.analyze_test_log(dup, self.names)
        rows = [line(n) for n in self.names]
        rows[0] = line(self.names[0], "FAIL")
        with self.assertRaises(qualification.v549.QualificationError):
            qualification.analyze_test_log("\n".join(rows), self.names)

    def valid_receipt(self, sha):
        tests = {
            "ubuntu": {"expected":11,"passed":11,"skipped":0,"failed":0,"skipped_names":[]},
            "windows": {"expected":11,"passed":6,"skipped":5,"failed":0,
                        "skipped_names":sorted(qualification.ALLOWED_WINDOWS_SKIPS)},
        }
        for item in tests.values():
            item.update({"job_url":"https://github.com/example/job","conclusion":"success"})
        return {"schema":qualification.SCHEMA,"version":"51.4","milestone":"V550",
                "qualified":True,"commit_sha":sha,
                "page_order":{"head_sha":sha,"status":"completed","conclusion":"success","tests":tests},
                "parent_v549":{"qualified":True,"commit_sha":sha,
                    "native_windows":{"portable":{"smoke_passed":True},"installer":{"smoke_passed":True},
                                     "installation":{"passed":True}}}}

    def test_documentation_accepts_only_exact_commit_and_complete_results(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "04-Tests-et-Qualification" / "V550-CI-QUALIFICATION.json"
            target.parent.mkdir()
            target.write_text(json.dumps(self.valid_receipt("a"*40)), encoding="utf-8")
            self.assertIsNotNone(docs.load_current_report(root, expected_head_sha="a"*40))
            self.assertIsNone(docs.load_current_report(root, expected_head_sha="b"*40))
            bad = self.valid_receipt("a"*40)
            bad["page_order"]["tests"]["windows"]["skipped_names"] = ["test_unrelated"]
            target.write_text(json.dumps(bad), encoding="utf-8")
            self.assertIsNone(docs.load_current_report(root, expected_head_sha="a"*40))


if __name__ == "__main__":
    unittest.main(verbosity=2)
