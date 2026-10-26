"""Bind V550 anchored-publication qualification to the exact GitHub commit.
Fixtures belong only to unit tests and are never release evidence.
Author: Abdelhalim Talbi.
"""
import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import write_v549_ci_qualification as v549

SCHEMA = "openpdf.v550.ci-qualification.v1"
TEST_FILE = "04-Tests-et-Qualification/test_atomic_output_v550.py"
TEST_CLASS = "AtomicOutputV550Tests"
ALLOWED_WINDOWS_SKIPS = frozenset({
    "test_final_symlink_staging_entry_is_rejected",
    "test_link_in_parent_chain_is_rejected_before_publication",
    "test_dotdot_does_not_hide_a_symlink_component",
    "test_parent_replacement_during_link_does_not_redirect_write",
    "test_temporary_entry_swap_cannot_change_inode_published_on_linux",
})


def expected_test_names(root):
    source = Path(root) / TEST_FILE
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        raise v549.QualificationError("V550 test source invalid: " + type(exc).__name__) from None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == TEST_CLASS:
            names = sorted(item.name for item in node.body
                           if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                           and item.name.startswith("test_"))
            if names and len(names) == len(set(names)):
                return names
    raise v549.QualificationError("V550 test class/methods not found")


def analyze_test_log(log_text, expected_names):
    pattern = re.compile(
        r"\b(test_[A-Za-z0-9_]+) \(test_atomic_output_v550\.AtomicOutputV550Tests\.\1\) "
        r"\.\.\. (ok|skipped|FAIL|ERROR)(?:\s|$)"
    )
    results = {}
    for line in log_text.splitlines():
        match = pattern.search(line)
        if match:
            name, outcome = match.groups()
            if name in results:
                raise v549.QualificationError("Duplicate V550 test outcome")
            results[name] = outcome
    if set(results) != set(expected_names):
        raise v549.QualificationError(
            "V550 outcomes do not match source; expected=" + str(len(expected_names))
            + ", found=" + str(len(results))
        )
    failed = sorted(name for name, outcome in results.items() if outcome in ("FAIL", "ERROR"))
    if failed:
        raise v549.QualificationError("V550 tests failed: " + ",".join(failed))
    return {
        "expected": len(expected_names),
        "passed": sum(v == "ok" for v in results.values()),
        "skipped": sum(v == "skipped" for v in results.values()),
        "failed": 0,
        "skipped_names": sorted(name for name, v in results.items() if v == "skipped"),
    }


def validate_platform_results(platform, result):
    if platform == "ubuntu":
        if result["passed"] != result["expected"] or result["skipped"] or result["failed"]:
            raise v549.QualificationError("V550 POSIX tests must all pass without skips")
    elif platform == "windows":
        if set(result["skipped_names"]) != ALLOWED_WINDOWS_SKIPS:
            raise v549.QualificationError("V550 Windows skips differ from the documented platform-only set")
        if result["passed"] != result["expected"] - len(ALLOWED_WINDOWS_SKIPS) or result["failed"]:
            raise v549.QualificationError("V550 Windows functional outcomes did not reconcile")
    else:
        raise v549.QualificationError("Unknown V550 platform")
    return True


def generate(root):
    root = Path(root).resolve()
    repo = os.environ.get("OPENPDF_REPOSITORY", "").strip()
    head_sha = os.environ.get("OPENPDF_HEAD_SHA", "").strip()
    branch = os.environ.get("OPENPDF_HEAD_BRANCH", "").strip()
    token = os.environ.get("OPENPDF_GITHUB_TOKEN", "").strip()
    run_id = os.environ.get("OPENPDF_RUN_ID", "").strip()
    pr_number = os.environ.get("OPENPDF_PULL_REQUEST_NUMBER", "").strip() or None
    if not repo or not head_sha or not branch or not token or not run_id:
        raise v549.QualificationError("Required ephemeral V550 GitHub Actions context is missing")

    package_run = v549._request_json(repo, token, "/actions/runs/" + run_id)
    if package_run.get("head_sha") != head_sha:
        raise v549.QualificationError("V550 packaging commit SHA mismatch")
    page_run = v549._candidate_page_order_run(repo, token, head_sha)
    jobs = v549._jobs(repo, token, page_run["id"])
    _, by_name = v549._successful_job_map(jobs, v549.PAGE_JOB_NAMES)
    names = expected_test_names(root)
    platform_results = {}
    for platform, job_name in v549.PAGE_JOB_NAMES.items():
        job = by_name[job_name]
        parsed = analyze_test_log(v549._download_job_log(repo, token, job["id"]), names)
        validate_platform_results(platform, parsed)
        platform_results[platform] = {
            **parsed, "job_id": job["id"], "job_url": job.get("html_url"),
            "conclusion": job.get("conclusion"),
        }

    parent_path = root / "04-Tests-et-Qualification" / "V549-CI-QUALIFICATION.json"
    try:
        parent = json.loads(parent_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise v549.QualificationError("Exact-commit V549 qualification receipt missing") from None
    if parent.get("qualified") is not True or parent.get("commit_sha") != head_sha:
        raise v549.QualificationError("V549 parent qualification is stale or unqualified")

    report = {
        "schema": SCHEMA,
        "version": "51.4",
        "milestone": "V550",
        "qualified": True,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repository": repo,
        "branch": branch,
        "pull_request": int(pr_number) if pr_number and pr_number.isdigit() else None,
        "commit_sha": head_sha,
        "page_order": {
            "workflow": page_run.get("name"), "run_id": page_run.get("id"),
            "url": page_run.get("html_url"), "head_sha": page_run.get("head_sha"),
            "status": page_run.get("status"), "conclusion": page_run.get("conclusion"),
            "tests": platform_results,
        },
        "parent_v549": {
            "qualified": True, "commit_sha": parent["commit_sha"],
            "source_closure_run_id": parent.get("source_closure", {}).get("run_id"),
            "native_windows": parent.get("source_closure", {}).get("native_windows"),
        },
        "capabilities": {
            "posix_directory_handle_anchoring": True,
            "linux_open_inode_publication": platform_results["ubuntu"]["passed"] == len(names),
            "windows_fully_toctou_hardened": False,
        },
        "limits": {
            "windows_handle_relative_publication": False,
            "full_windows_toctou_elimination": False,
            "human_windows_gui_qualified": False,
            "ocr_accuracy_certified": False,
            "authenticode_signed": False,
        },
    }
    out = root / "04-Tests-et-Qualification" / "V550-CI-QUALIFICATION.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, out)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        report = generate(args.root)
    except (OSError, ValueError, v549.QualificationError) as exc:
        print("V550 qualification rejected: " + str(exc))
        return 2
    print(json.dumps({
        "qualified": report["qualified"], "commit_sha": report["commit_sha"],
        "page_order_run_id": report["page_order"]["run_id"],
        "tests": {k: {"expected": v["expected"], "passed": v["passed"],
                      "skipped": v["skipped"], "failed": v["failed"]}
                  for k, v in report["page_order"]["tests"].items()},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
