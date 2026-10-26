"""V50.3 source reconciliation: provenance, syntax and fail-closed build gates.

These are static tests. Windows native binary qualification is a separate CI job.
Author: Abdelhalim Talbi.
"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "03-Sources"
CURRENT_VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8").strip()
MANIFEST = ROOT / f"07-Manifestes/V{CURRENT_VERSION}-REQUIRED-RUNTIME-MODULES.json"
HASHES = ROOT / "07-Manifestes/V50.3-RESTORED-SOURCE-HASHES.json"
V514_OVERRIDES = ROOT / "07-Manifestes/V51.4-SOURCE-HASH-OVERRIDES.json"


class SourceReconciliationV503Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.hashes = json.loads(HASHES.read_text(encoding="utf-8"))
        cls.overrides = json.loads(V514_OVERRIDES.read_text(encoding="utf-8"))["sha256"] if V514_OVERRIDES.exists() else {}

    def test_version_and_schema(self):
        self.assertIn(CURRENT_VERSION, ("50.3", "50.4", "50.5", "50.6", "50.7", "50.8", "50.9", "51.0", "51.1", "51.2", "51.3", "51.4"))
        self.assertEqual(self.manifest["version"], CURRENT_VERSION)
        self.assertEqual(self.manifest["schema"], "openpdf-runtime-module-set-v1")
        self.assertEqual(self.hashes["schema"], "openpdf-restored-source-hashes-v1")

    def test_43_restored_modules_pinned(self):
        self.assertEqual(len(self.hashes["sha256"]), 43)
        self.assertEqual(len(set(self.hashes["sha256"])), 43)

    def test_hashes_match_exact_source_bytes(self):
        for rel, expected in self.hashes["sha256"].items():
            with self.subTest(path=rel):
                path = ROOT / rel
                self.assertTrue(path.is_file() and not path.is_symlink())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.overrides.get(rel, expected))

    def test_git_checkout_preserves_pinned_source_bytes(self):
        attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("03-Sources/*.py -text", attrs)
        self.assertIn("03-Sources/*.iss -text", attrs)

    def test_required_runtime_set_complete(self):
        modules = self.manifest["modules"]
        self.assertGreaterEqual(len(modules), 97 if CURRENT_VERSION == "51.4" else 93 if CURRENT_VERSION == "51.3" else 92 if CURRENT_VERSION in ("51.1", "51.2") else 91 if CURRENT_VERSION == "51.0" else 90 if CURRENT_VERSION in ("50.8", "50.9") else 89 if CURRENT_VERSION == "50.7" else 88 if CURRENT_VERSION == "50.6" else 87 if CURRENT_VERSION == "50.5" else 86)
        if CURRENT_VERSION == "51.4":
            self.assertTrue({"openpdf_ocr_reference_corpus_v539", "openpdf_ocr_quality_ui_v541", "openpdf_office_reference_v542", "openpdf_office_quality_ui_v543"}.issubset(modules))
        self.assertEqual(len(modules), len(set(modules)))
        for module in modules:
            with self.subTest(module=module):
                path = SRC / (module + ".py")
                self.assertTrue(path.is_file() and not path.is_symlink())

    def test_required_runtime_syntax(self):
        for module in self.manifest["modules"]:
            with self.subTest(module=module):
                path = SRC / (module + ".py")
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=path.name)

    def test_actual_static_dependency_closure(self):
        spec = importlib.util.spec_from_file_location("closure_v502", SRC / "openpdf_source_closure_v502.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.audit_sources(ROOT, ["openpdf_studio", "openpdf_build_preflight",
                                                  "openpdf_inno_recipe_v491", "openpdf_release_gate",
                                                  "openpdf_bind_smoke", "openpdf_publish_binary",
                                                  "openpdf_binary_manifest"], MANIFEST)
        self.assertTrue(result["passed"], result.get("missing_modules"))
        self.assertEqual(result["missing_modules"], [])
        self.assertEqual(result["syntax_errors"], {})

    def test_single_windows_entrypoint_uses_versioned_manifest(self):
        script = (ROOT / "02-Compilation/BUILD-WINDOWS-INSTALLER.cmd").read_text(encoding="utf-8")
        self.assertIn("V%VERSION%-REQUIRED-RUNTIME-MODULES.json", script)
        self.assertIn("openpdf_source_closure_v502.py", script)
        self.assertIn("--portable-only", script)
        self.assertIn("|| goto fail", script)

    def test_six_historical_modules_reconciled(self):
        optional = json.loads((ROOT / "07-Manifestes/V50.3-OPTIONAL-SOURCE-HASHES.json").read_text(encoding="utf-8"))
        self.assertEqual(len(optional["sha256"]), 6)
        for rel, expected in optional["sha256"].items():
            with self.subTest(path=rel):
                path = ROOT / rel
                self.assertTrue(path.is_file() and not path.is_symlink())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
                ast.parse(path.read_text(encoding="utf-8-sig"))

    def test_sixteen_runtime_interfaces_match_candidate(self):
        runtime = json.loads((ROOT / ("07-Manifestes/V51.3-RUNTIME-INTERFACE-HASHES.json" if CURRENT_VERSION in ("51.3", "51.4") else "07-Manifestes/V51.2-RUNTIME-INTERFACE-HASHES.json" if CURRENT_VERSION == "51.2" else "07-Manifestes/V51.0-RUNTIME-INTERFACE-HASHES.json" if CURRENT_VERSION in ("51.0", "51.1") else "07-Manifestes/V50.5-RUNTIME-INTERFACE-HASHES.json" if CURRENT_VERSION in ("50.5", "50.6", "50.7", "50.8", "50.9") else "07-Manifestes/V50.3-RUNTIME-INTERFACE-HASHES.json")).read_text(encoding="utf-8"))
        self.assertEqual(len(runtime["sha256"]), 16)
        for rel, expected in runtime["sha256"].items():
            with self.subTest(path=rel):
                path = ROOT / rel
                self.assertTrue(path.is_file() and not path.is_symlink())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.overrides.get(rel, expected))
                ast.parse(path.read_text(encoding="utf-8-sig"))

    def test_build_preflight_accepts_dynamic_version_recipe(self):
        spec = importlib.util.spec_from_file_location("preflight_v503", SRC / "openpdf_build_preflight.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.inspect_release(ROOT)
        self.assertTrue(report["passed"], report["checks"])
        self.assertTrue(report["checks"]["build_references_inno"])

    def test_v547_cumulative_zip_uses_only_qualified_windows_artifacts(self):
        workflow = (ROOT / ".github/workflows/source-closure-v502.yml").read_text(encoding="utf-8")
        self.assertIn("windows-cumulative-package:", workflow)
        self.assertIn("needs: [closure-unit-tests, source-readiness, windows-portable-build, windows-installer-build]", workflow)
        for contract in (
            "v514-windows-portable-build-evidence",
            "v514-windows-installer-build-evidence",
            "package_cumulative_v434.py --verify",
            "Get-FileHash -LiteralPath $zip -Algorithm SHA256",
            "OpenPDF-Studio-V",
            "Pillow>=10,<13",
            "actions/upload-artifact@v4",
            "write_v549_ci_qualification.py --root .",
            "generate_docs_v549.py",
            "write_v551_ci_qualification.py --root .",
            "generate_docs_v551.py",
            "test_atomic_output_v551.py",
            "openpdf_windows_handle_publish_v551.py",
            "V551-Cumulative-Windows",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, workflow)

    def test_ci_has_native_windows_job_and_preserves_evidence(self):
        workflow = (ROOT / ".github/workflows/source-closure-v502.yml").read_text(encoding="utf-8")
        self.assertIn("windows-portable-build:", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("BUILD-WINDOWS-INSTALLER.cmd --portable-only", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn(f"V{CURRENT_VERSION}-REQUIRED-RUNTIME-MODULES.json", workflow)
        self.assertIn(f"windows-installation-v{CURRENT_VERSION}.json", workflow)
        self.assertIn(f"$report.version -ne '{CURRENT_VERSION}'", workflow)


if __name__ == "__main__":
    unittest.main()
