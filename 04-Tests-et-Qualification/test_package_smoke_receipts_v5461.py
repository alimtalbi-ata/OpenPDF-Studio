"""V546.1: cumulative release packaging binds all native Windows smoke checks.
Author: Abdelhalim Talbi.
"""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))
from package_cumulative_v434 import SMOKE_ARGUMENTS, validate_smoke_receipt


class PackageSmokeReceiptsV5461(unittest.TestCase):
    def setUp(self):
        self.filename = "OpenPDF-Studio-Portable-V51.4.exe"
        self.digest = "a" * 64
        self.receipt = {
            "version": "51.4",
            "mode": "portable",
            "passed": True,
            "artifact_name": self.filename,
            "artifact_sha256": self.digest,
            "checks": [
                {"argument": arg, "exit_code": 0, "passed": True,
                 "timed_out": False, "stdout": "OK", "stderr": ""}
                for arg in SMOKE_ARGUMENTS
            ],
        }

    def validate(self, receipt=None):
        return validate_smoke_receipt(
            self.receipt if receipt is None else receipt,
            version="51.4", mode="portable",
            filename=self.filename, sha256=self.digest,
        )

    def test_accepts_complete_startup_functional_and_ocr_runtime_receipt(self):
        self.assertTrue(self.validate())
        self.assertEqual(set(x["argument"] for x in self.receipt["checks"]),
                         set(SMOKE_ARGUMENTS))
        self.assertEqual(len(SMOKE_ARGUMENTS), 3)

    def test_rejects_stale_two_check_receipt_without_ocr(self):
        stale = dict(self.receipt)
        stale["checks"] = self.receipt["checks"][:2]
        with self.assertRaisesRegex(ValueError, "Incomplete Windows smoke checks"):
            self.validate(stale)

    def test_rejects_missing_functional_check(self):
        incomplete = dict(self.receipt)
        incomplete["checks"] = [x for x in self.receipt["checks"]
                                if x["argument"] != "--functional-self-test"]
        with self.assertRaises(ValueError):
            self.validate(incomplete)

    def test_rejects_duplicate_check_even_when_count_is_three(self):
        duplicate = dict(self.receipt)
        duplicate["checks"] = [
            self.receipt["checks"][0], self.receipt["checks"][0],
            self.receipt["checks"][2],
        ]
        with self.assertRaisesRegex(ValueError, "duplicated"):
            self.validate(duplicate)

    def test_rejects_nonzero_exit_even_if_pass_flag_is_true(self):
        failed = dict(self.receipt)
        failed["checks"] = [dict(x) for x in self.receipt["checks"]]
        failed["checks"][1]["exit_code"] = 1
        with self.assertRaisesRegex(ValueError, "Failed Windows smoke check"):
            self.validate(failed)

    def test_rejects_timeout_even_with_zero_exit(self):
        timed_out = dict(self.receipt)
        timed_out["checks"] = [dict(x) for x in self.receipt["checks"]]
        timed_out["checks"][2]["timed_out"] = True
        with self.assertRaisesRegex(ValueError, "Failed Windows smoke check"):
            self.validate(timed_out)

    def test_rejects_unknown_argument(self):
        unknown = dict(self.receipt)
        unknown["checks"] = [dict(x) for x in self.receipt["checks"]]
        unknown["checks"][0]["argument"] = "--invented-check"
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            self.validate(unknown)

    def test_rejects_mismatched_artifact_digest(self):
        mismatch = dict(self.receipt)
        mismatch["artifact_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "Unbound Windows smoke"):
            self.validate(mismatch)

    def test_rejects_non_text_output_fields(self):
        malformed = dict(self.receipt)
        malformed["checks"] = [dict(x) for x in self.receipt["checks"]]
        malformed["checks"][0]["stdout"] = None
        with self.assertRaisesRegex(ValueError, "Failed Windows smoke check"):
            self.validate(malformed)

    def test_rejects_false_top_level_pass_flag(self):
        failed = dict(self.receipt)
        failed["passed"] = False
        with self.assertRaisesRegex(ValueError, "Unbound Windows smoke"):
            self.validate(failed)


if __name__ == "__main__":
    unittest.main()
