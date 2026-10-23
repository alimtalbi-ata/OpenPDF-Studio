"""Fail-closed, dependency-free audit of OpenPDF Studio's local Python imports.

This gate prevents Windows packaging when required OpenPDF modules are absent.
It performs *static* source inspection; it does not prove runtime or Windows
binary qualification. Author: Abdelhalim Talbi. OpenPDF Studio V50.2.
"""
from __future__ import annotations

import argparse
import ast
from collections import deque
import json
from pathlib import Path
import re

MODULE_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z", re.ASCII)
DEFAULT_ENTRIES = ("openpdf_studio",)


def _module_name(value: str) -> str:
    if not isinstance(value, str) or not MODULE_NAME.fullmatch(value):
        raise ValueError(f"Invalid module name: {value!r}")
    return value


def _imports(tree: ast.AST, available: set[str]) -> set[str]:
    """Collect static local imports, including literal dynamic imports.

    Imports under functions/conditionals are intentionally included because
    PyInstaller must ship their targets even when smoke tests don't visit them.
    External packages are not asserted here (pip handles those separately).
    """
    required = set()
    for node in ast.walk(tree):
        candidates = []
        if isinstance(node, ast.Import):
            candidates.extend(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                candidates.append(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call) and node.args:
            target = node.func
            dynamic = (isinstance(target, ast.Name) and target.id == "__import__") or (
                isinstance(target, ast.Attribute) and target.attr == "import_module"
                and isinstance(target.value, ast.Name) and target.value.id == "importlib"
            )
            if dynamic and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                candidates.append(node.args[0].value.split(".", 1)[0])
        for name in candidates:
            if name in available or name.startswith("openpdf_"):
                if MODULE_NAME.fullmatch(name):
                    required.add(name)
    return required


def audit_sources(root: str | Path, entries=DEFAULT_ENTRIES, required_manifest=None) -> dict:
    """Return a stable report, never importing or executing untrusted sources."""
    root = Path(root)
    source = root / "03-Sources"
    if not source.is_dir() or source.is_symlink():
        raise ValueError("03-Sources must be a real directory")
    entry_names = sorted({_module_name(x) for x in entries})
    if not entry_names:
        raise ValueError("At least one entrypoint is required")
    available = {p.stem for p in source.glob("*.py") if p.is_file() and not p.is_symlink()}
    version_file = root / "VERSION.txt"
    version = version_file.read_text(encoding="utf-8-sig").strip() if version_file.is_file() else None
    required = []
    expected_version = None
    if required_manifest is not None:
        manifest = json.loads(Path(required_manifest).read_text(encoding="utf-8-sig"))
        if not isinstance(manifest, dict) or manifest.get("schema") != "openpdf-runtime-module-set-v1":
            raise ValueError("Invalid required runtime manifest schema")
        modules = manifest.get("modules")
        if not isinstance(modules, list) or not modules or any(not isinstance(x, str) for x in modules):
            raise ValueError("Invalid required runtime modules")
        required = [_module_name(x) for x in modules]
        if len(required) != len(set(required)):
            raise ValueError("Duplicate required runtime module")
        expected_version = manifest.get("version")
        if not isinstance(expected_version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+", expected_version):
            raise ValueError("Invalid required runtime version")
    seen = set()
    pending = deque(entry_names + sorted(required))
    missing = set()
    errors = {}
    edges = {}
    while pending:
        module = pending.popleft()
        if module in seen:
            continue
        seen.add(module)
        path = source / (module + ".py")
        if module not in available or path.is_symlink():
            missing.add(module)
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=path.name)
        except (SyntaxError, UnicodeError, OSError) as exc:
            errors[module] = f"{type(exc).__name__}: {exc}"
            continue
        dependencies = sorted(_imports(tree, available))
        edges[module] = dependencies
        pending.extend(dependencies)
    return {
        "schema": "openpdf-source-closure-v1",
        "version": version,
        "required_manifest_version": expected_version,
        "version_matches_manifest": expected_version is None or version == expected_version,
        "required_modules": sorted(required),
        "entrypoints": entry_names,
        "scanned_modules": sorted(edges),
        "missing_modules": sorted(missing),
        "syntax_errors": dict(sorted(errors.items())),
        "imports": dict(sorted(edges.items())),
        "passed": not missing and not errors and (expected_version is None or version == expected_version),
        "qualification": "static_source_only_not_windows_binary",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="OpenPDF Studio static source closure gate")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--entry", action="append", dest="entries", default=None,
                        help="Root module without .py; may be specified repeatedly")
    parser.add_argument("--report", type=Path, help="Write JSON report to this path")
    parser.add_argument("--required-manifest", type=Path,
                        help="Pin the complete V50.2 runtime module set and version")
    args = parser.parse_args(argv)
    try:
        report = audit_sources(args.root, args.entries or DEFAULT_ENTRIES, args.required_manifest)
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        report = {"schema": "openpdf-source-closure-v1", "passed": False,
                  "error": f"{type(exc).__name__}: {exc}",
                  "qualification": "static_source_only_not_windows_binary"}
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
