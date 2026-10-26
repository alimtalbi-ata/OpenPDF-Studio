"""Bind Windows native handle-publication qualification to one exact CI SHA.
Synthetic parser fixtures are tests only, never release evidence.
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
import write_v550_ci_qualification as v550

SCHEMA = "openpdf.v551.ci-qualification.v1"
TEST_FILE = "04-Tests-et-Qualification/test_atomic_output_v551.py"
TEST_CLASS = "AtomicOutputV551Tests"
WINDOWS_ONLY_TESTS = frozenset({
    "test_windows_publishes_by_handle_and_preserves_staging_name",
    "test_windows_existing_destination_is_never_replaced",
    "test_windows_junction_ancestor_is_rejected",
    "test_windows_dotdot_does_not_hide_junction",
    "test_windows_parent_swap_is_detected_without_redirect",
    "test_windows_staging_cannot_be_renamed_while_pinned",
})


def expected_test_names(root):
    source = Path(root) / TEST_FILE
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        raise v550.v549.QualificationError(
            "V551 test source invalid: " + type(exc).__name__
        ) from None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == TEST_CLASS:
            names = sorted(
                item.name for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name.startswith("test_")
            )
            if names and len(names) == len(set(names)):
                return names
    raise v550.v549.QualificationError("V551 test class/methods not found")


def analyze_test_log(log_text, expected_names):
    class_name = re.escape("test_atomic_output_v551.AtomicOutputV551Tests")
    pattern = re.compile(
        r"\b(test_[A-Za-z0-9_]+) \(" + class_name
        + r"\.\1\) \.\.\. (ok|skipped|FAIL|ERROR)(?:\s|$)"
    )
    results = {}
    for line in log_text.splitlines():
        match = pattern.search(line)
        if match:
            name, outcome = match.groups()
            if name in results:
                raise v550.v549.QualificationError("Duplicate V551 test result")
            results[name] = outcome
    if set(results) != set(expected_names):
        raise v550.v549.QualificationError(
            "V551 results differ from test source; expected=" + str(len(expected_names))
            + ", found=" + str(len(results))
        )
    failed = sorted(
        name for name, outcome in results.items() if outcome in ("FAIL", "ERROR")
    )
    if failed:
        raise v550.v549.QualificationError("V551 functional tests failed: " + ",".join(failed))
    return {
        "expected": len(expected_names),
        "passed": sum(outcome == "ok" for outcome in results.values()),
        "skipped": sum(outcome == "skipped" for outcome in results.values()),
        "failed": 0,
        "skipped_names": sorted(
            name for name, outcome in results.items() if outcome == "skipped"
        ),
    }


def validate_platform_results(platform, result, expected_names):
    if result["expected"] != len(expected_names):
        raise v550.v549.QualificationError("V551 test inventory changed during parsing")
    if platform == "ubuntu":
        if set(result["skipped_names"]) != WINDOWS_ONLY_TESTS:
            raise v550.v549.QualificationError(
                "Ubuntu V551 skips differ from the six documented Windows-only tests"
            )
        if result["passed"] != result["expected"] - len(WINDOWS_ONLY_TESTS) or result["failed"]:
            raise v550.v549.QualificationError("Ubuntu V551 functional results did not reconcile")
    elif platform == "windows":
        if result["skipped"] or result["failed"] or result["passed"] != result["expected"]:
            raise v550.v549.QualificationError(
                "Windows V551 requires every handle-publication test to pass without skips"
            )
    else:
        raise v550.v549.QualificationError("Unknown V551 platform")
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
        raise v550.v549.QualificationError("Required ephemeral V551 GitHub Actions context is missing")

    package_run = v550.v549._request_json(repo, token, "/actions/runs/" + run_id)
    if package_run.get("head_sha") != head_sha:
        raise v550.v549.QualificationError("V551 packaging commit SHA mismatch")
    page_run = v550.v549._candidate_page_order_run(repo, token, head_sha)
    jobs = v550.v549._jobs(repo, token, page_run["id"])
    _, by_name = v550.v549._successful_job_map(jobs, v550.v549.PAGE_JOB_NAMES)
    names = expected_test_names(root)
    platform_results = {}
    for platform, job_name in v550.PAGE_JOB_NAMES.items():
        job = by_name[job_name]
        parsed = analyze_test_log(
            v550.v549._download_job_log(repo, token, job["id"]), names
        )
        validate_platform_results(platform, parsed, names)
        platform_results[platform] = {
            **parsed, "job_id": job["id"], "job_url": job.get("html_url"),
            "conclusion": job.get("conclusion"),
        }

    parent_path = root / "04-Tests-et-Qualification" / "V550-CI-QUALIFICATION.json"
    try:
        parent = json.loads(parent_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise v550.v549.QualificationError("Exact-commit V550 parent receipt missing") from None
    if (
        not isinstance(parent, dict) or parent.get("qualified") is not True
        or parent.get("commit_sha") != head_sha
        or parent.get("schema") != "openpdf.v550.ci-qualification.v1"
    ):
        raise v550.v549.QualificationError("V550 parent receipt is stale or unqualified")

    report = {
        "schema": SCHEMA,
        "version": "51.4",
        "milestone": "V551",
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
        "parent_v550": {
            "qualified": True,
            "commit_sha": parent["commit_sha"],
            "page_order_run_id": parent.get("page_order", {}).get("run_id"),
        },
        "capabilities": {
            "windows_native_handle_relative_publication": (
                platform_results["windows"]["passed"] == len(names)
            ),
            "windows_handle_relative_exclusive_link": True,
            "windows_path_based_fallback": False,
            "windows_full_toctou_elimination": False,
        },
        "limits": {
            "unc_paths_supported": False,
            "mapped_network_drives_supported": False,
            "network_shares_qualified": False,
            "full_windows_toctou_elimination": False,
            "human_windows_gui_qualified": False,
            "ocr_accuracy_certified": False,
            "authenticode_signed": False,
        },
    }
    out = root / "04-Tests-et-Qualification" / "V551-CI-QUALIFICATION.json"
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
    except (OSError, ValueError, v550.v549.QualificationError) as exc:
        print("V551 qualification rejected: " + str(exc))
        return 2
    print(json.dumps({
        "qualified": report["qualified"],
        "commit_sha": report["commit_sha"],
        "page_order_run_id": report["page_order"]["run_id"],
        "tests": {
            key: {name: value[name] for name in ("expected", "passed", "skipped", "failed")}
            for key, value in report["page_order"]["tests"].items()
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
