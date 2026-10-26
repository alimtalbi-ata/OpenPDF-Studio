"""Reconcile V549's current GitHub Actions receipts before generating release docs.

The report contains only bounded statuses, counts, hashes and public run links.
No job logs, document text, local paths or credentials are copied into it.
Author: Abdelhalim Talbi.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
import zipfile


SCHEMA = "openpdf.v549.ci-qualification.v1"
PAGE_ORDER_WORKFLOW = "PDF page reorganisation V49.7"
PAGE_JOB_NAMES = {
    "ubuntu": "page-order-functional (ubuntu-latest)",
    "windows": "page-order-functional (windows-latest)",
}
CLOSURE_JOB_NAMES = {
    "source_reconciliation_ubuntu": "Source reconciliation and regression (ubuntu-latest)",
    "source_reconciliation_windows": "Source reconciliation and regression (windows-latest)",
    "source_closure": "Full application source closure (release-blocking)",
    "portable_windows": "Native Windows portable build and smoke",
    "installer_windows": "Native Windows installer, install and uninstall",
}
TEST_FILE = "04-Tests-et-Qualification/test_destination_path_chain_guard_v549.py"
MAX_LOG_BYTES = 16 * 1024 * 1024


class QualificationError(RuntimeError):
    """A current CI receipt could not be reconciled with its source."""


def _request_json(repo, token, path):
    url = "https://api.github.com/repos/" + repo + path
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "User-Agent": "OpenPDF-Studio-V549-Qualification",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read(8 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as exc:
        raise QualificationError("GitHub API request failed with HTTP " + str(exc.code)) from None
    except (OSError, TimeoutError) as exc:
        raise QualificationError("GitHub API request failed: " + type(exc).__name__) from None
    if len(payload) > 8 * 1024 * 1024:
        raise QualificationError("GitHub API response exceeded the size budget")
    try:
        return json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise QualificationError("GitHub API returned invalid JSON") from None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Keep the GitHub bearer token away from the signed log-download host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _download_job_log(repo, token, job_id):
    url = "https://api.github.com/repos/" + repo + "/actions/jobs/" + str(job_id) + "/logs"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "User-Agent": "OpenPDF-Studio-V549-Qualification",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        try:
            response = opener.open(request, timeout=30)
        except urllib.error.HTTPError as exc:
            if exc.code not in (301, 302, 303, 307, 308):
                raise QualificationError("GitHub job log download failed with HTTP " + str(exc.code)) from None
            target = exc.headers.get("Location")
            exc.close()
            parsed = urllib.parse.urlsplit(target or "")
            if parsed.scheme != "https" or not parsed.netloc:
                raise QualificationError("GitHub returned an invalid signed log URL")
            # Deliberately no Authorization header on the redirected request.
            response = urllib.request.urlopen(
                urllib.request.Request(target, headers={"User-Agent": "OpenPDF-Studio-V549-Qualification"}),
                timeout=45,
            )
        with response:
            raw = response.read(MAX_LOG_BYTES + 1)
    except QualificationError:
        raise
    except urllib.error.HTTPError as exc:
        raise QualificationError("Signed job log download failed with HTTP " + str(exc.code)) from None
    except (OSError, TimeoutError) as exc:
        raise QualificationError("Job log download failed: " + type(exc).__name__) from None
    if len(raw) > MAX_LOG_BYTES:
        raise QualificationError("Job log exceeded the size budget")
    if raw.startswith(b"PK"):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                if archive.testzip() is not None:
                    raise QualificationError("GitHub job log archive failed CRC validation")
                parts = []
                for name in archive.namelist():
                    if name.lower().endswith(".txt"):
                        parts.append(archive.read(name).decode("utf-8", "replace"))
                if not parts:
                    raise QualificationError("GitHub job log archive contained no text")
                return "\n".join(parts)
        except zipfile.BadZipFile:
            raise QualificationError("GitHub job log archive was invalid") from None
    return raw.decode("utf-8", "replace")


def expected_test_names(root):
    source = Path(root) / TEST_FILE
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        raise QualificationError("V549 test source could not be parsed: " + type(exc).__name__) from None
    for item in tree.body:
        if isinstance(item, ast.ClassDef) and item.name == "DestinationPathChainGuardV549Tests":
            names = sorted(
                node.name for node in item.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
            )
            if not names or len(names) != len(set(names)):
                break
            return names
    raise QualificationError("V549 test class or methods were not found")


def analyze_test_log(log_text, expected_names):
    """Parse only unittest's bounded test outcome lines, not user/document text."""
    escaped_class = re.escape("test_destination_path_chain_guard_v549.DestinationPathChainGuardV549Tests")
    results = {}
    pattern = re.compile(
        r"\b(test_[A-Za-z0-9_]+) \(" + escaped_class + r"\.\1\) \.\.\. (ok|skipped|FAIL|ERROR)(?:\s|$)"
    )
    for line in log_text.splitlines():
        match = pattern.search(line)
        if match:
            name, outcome = match.groups()
            if name in results:
                raise QualificationError("Duplicate unittest result line detected")
            results[name] = outcome
    if set(results) != set(expected_names):
        missing = sorted(set(expected_names) - set(results))
        unexpected = sorted(set(results) - set(expected_names))
        raise QualificationError(
            "V549 test results did not reconcile; expected=" + str(len(expected_names))
            + ", found=" + str(len(results))
            + ", missing=" + ",".join(missing)
            + ", unexpected=" + ",".join(unexpected)
        )
    failed = sorted(name for name, outcome in results.items() if outcome in ("FAIL", "ERROR"))
    if failed:
        raise QualificationError("V549 functional test failed: " + ",".join(failed))
    return {
        "expected": len(expected_names),
        "passed": sum(outcome == "ok" for outcome in results.values()),
        "skipped": sum(outcome == "skipped" for outcome in results.values()),
        "failed": 0,
        "skipped_names": sorted(name for name, outcome in results.items() if outcome == "skipped"),
    }


def _jobs(repo, token, run_id):
    data = _request_json(repo, token, "/actions/runs/" + str(run_id) + "/jobs?per_page=100")
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise QualificationError("GitHub workflow jobs payload was invalid")
    return jobs


def _successful_job_map(jobs, required_names):
    by_name = {job.get("name"): job for job in jobs if isinstance(job, dict)}
    missing = [job_name for job_name in required_names.values() if job_name not in by_name]
    if missing:
        raise QualificationError("Required CI jobs were missing: " + ", ".join(missing))
    result = {}
    for key, name in required_names.items():
        job = by_name[name]
        if job.get("status") != "completed" or job.get("conclusion") != "success":
            raise QualificationError("Required CI job did not pass: " + name)
        result[key] = {
            "name": name,
            "status": job.get("status"),
            "conclusion": job.get("conclusion"),
            "job_url": job.get("html_url"),
        }
    return result, by_name


def _candidate_page_order_run(repo, token, head_sha):
    # Never borrow a green run from an older commit on the same PR. The path
    # filters explicitly include this qualification pipeline, so each PR update
    # produces a current page-order run for the checked-out SHA.
    query = urllib.parse.urlencode({"head_sha": head_sha, "per_page": 100})
    data = _request_json(repo, token, "/actions/runs?" + query)
    candidates = [
        run for run in data.get("workflow_runs", [])
        if isinstance(run, dict)
        and run.get("name") == PAGE_ORDER_WORKFLOW
        and run.get("head_sha") == head_sha
    ]
    if not candidates:
        raise QualificationError("No page-order workflow run exists for this exact source revision")
    run = max(candidates, key=lambda item: item.get("created_at", ""))
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise QualificationError("The V549 page-order workflow has not passed for this exact revision")
    return run


def _verify_windows_binary_receipts(root, version):
    binary = Path(root) / "01-Application" / "binary"
    manifest_path = binary / ("binary-manifest-v" + version + ".json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise QualificationError("Native Windows binary manifest is missing or invalid") from None
    if not isinstance(manifest, dict):
        raise QualificationError("Native Windows binary manifest schema mismatch")
    if str(manifest.get("version")) != version or not isinstance(manifest.get("binaries"), list):
        raise QualificationError("Native Windows binary manifest version/schema mismatch")
    required = {
        "OpenPDF-Studio-Portable-V" + version + ".exe": "portable",
        "OpenPDF-Studio-V" + version + "-Setup.exe": "installer",
    }
    observed = {}
    for filename, mode in required.items():
        path = binary / filename
        if not path.is_file() or path.is_symlink():
            raise QualificationError("Native Windows binary missing or linked: " + filename)
        data_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        size = path.stat().st_size
        entries = [item for item in manifest["binaries"] if isinstance(item, dict) and item.get("filename") == filename]
        if len(entries) != 1:
            raise QualificationError("Native Windows binary manifest entry mismatch: " + filename)
        entry = entries[0]
        if entry.get("sha256") != data_hash or entry.get("size_bytes") != size or entry.get("pe_mz_header") is not True:
            raise QualificationError("Native Windows binary hash/size/PE receipt mismatch: " + filename)
        receipt_path = binary / ("windows-smoke-" + mode + ".json")
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            raise QualificationError("Native Windows smoke receipt missing or invalid: " + mode) from None
        if not isinstance(receipt, dict):
            raise QualificationError("Native Windows smoke receipt schema mismatch: " + mode)
        checks = receipt.get("checks")
        if (str(receipt.get("version")) != version or receipt.get("mode") != mode
                or receipt.get("passed") is not True or receipt.get("artifact_sha256") != data_hash
                or not isinstance(checks, list) or not checks
                or any(not isinstance(check, dict) or check.get("passed") is not True for check in checks)):
            raise QualificationError("Native Windows smoke receipt did not match: " + mode)
        observed[mode] = {
            "filename": filename,
            "bytes": size,
            "sha256": data_hash,
            "checks_passed": len(checks),
            "smoke_passed": True,
        }
    install_path = binary / ("windows-installation-v" + version + ".json")
    try:
        install = json.loads(install_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise QualificationError("Native Windows install receipt missing or invalid") from None
    if not isinstance(install, dict):
        raise QualificationError("Native Windows install receipt schema mismatch")
    installer_hash = observed["installer"]["sha256"]
    required_steps = {"silent_install_pass", "installed_launch_pass", "installed_ocr_pass", "silent_uninstall_pass"}
    install_steps = install.get("steps")
    if (str(install.get("version")) != version or install.get("passed") is not True
            or install.get("artifact_sha256") != installer_hash
            or not isinstance(install_steps, list)
            or any(not isinstance(step, str) for step in install_steps)
            or not required_steps.issubset(set(install_steps))):
        raise QualificationError("Native Windows install/uninstall receipt did not match")
    observed["installation"] = {
        "passed": True,
        "steps_passed": sorted(required_steps),
        "utc": install.get("utc"),
    }
    return observed


def generate(root):
    root = Path(root).resolve()
    repo = os.environ.get("OPENPDF_REPOSITORY", "").strip()
    head_sha = os.environ.get("OPENPDF_HEAD_SHA", "").strip()
    branch = os.environ.get("OPENPDF_HEAD_BRANCH", "").strip()
    token = os.environ.get("OPENPDF_GITHUB_TOKEN", "").strip()
    run_id = os.environ.get("OPENPDF_RUN_ID", "").strip()
    pr_number = os.environ.get("OPENPDF_PULL_REQUEST_NUMBER", "").strip() or None
    version = (root / "VERSION.txt").read_text(encoding="utf-8-sig").strip()
    if version != "51.4":
        raise QualificationError("V549 qualification script is scoped to version 51.4")
    if not repo or not head_sha or not branch or not token or not run_id:
        raise QualificationError("Required ephemeral GitHub Actions context is missing")

    source_run = _request_json(repo, token, "/actions/runs/" + run_id)
    if source_run.get("head_sha") != head_sha:
        raise QualificationError("The packaging run SHA does not match the checked-out SHA")
    source_jobs = _jobs(repo, token, run_id)
    source_names, source_by_name = _successful_job_map(source_jobs, CLOSURE_JOB_NAMES)
    page_run = _candidate_page_order_run(repo, token, head_sha)
    if page_run.get("head_sha") != head_sha:
        raise QualificationError("The page-order run SHA does not match the checked-out SHA")
    page_jobs = _jobs(repo, token, page_run["id"])
    page_names, page_by_name = _successful_job_map(page_jobs, PAGE_JOB_NAMES)

    expected_names = expected_test_names(root)
    os_results = {}
    for os_key in ("ubuntu", "windows"):
        job = page_by_name[PAGE_JOB_NAMES[os_key]]
        log = _download_job_log(repo, token, job["id"])
        result = analyze_test_log(log, expected_names)
        if result["skipped"] != 0:
            raise QualificationError("V549 functional suite contains skipped tests on " + os_key)
        os_results[os_key] = {
            **result,
            "job_id": job["id"],
            "job_url": job.get("html_url"),
            "conclusion": job.get("conclusion"),
        }

    module_manifest_path = root / "07-Manifestes" / "V51.4-REQUIRED-RUNTIME-MODULES.json"
    try:
        module_manifest = json.loads(module_manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise QualificationError("Required runtime module manifest missing or invalid") from None
    modules = module_manifest.get("modules")
    if not isinstance(modules, list) or not modules or len(modules) != len(set(modules)):
        raise QualificationError("Runtime module manifest contains duplicates or no modules")
    if ("openpdf_source_path_guard_v548" not in modules
            or "openpdf_destination_path_guard_v549" not in modules):
        raise QualificationError("Runtime manifest is missing a required source or destination path guard")

    binaries = _verify_windows_binary_receipts(root, version)
    report = {
        "schema": SCHEMA,
        "version": version,
        "qualified": True,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repository": repo,
        "branch": branch,
        "commit_sha": head_sha,
        "pull_request_head_sha": os.environ.get("OPENPDF_PR_HEAD_SHA", "").strip() or None,
        "pull_request": int(pr_number) if pr_number and pr_number.isdigit() else None,
        "module_count": len(modules),
        "page_order": {
            "workflow": page_run.get("name"),
            "run_id": page_run.get("id"),
            "url": page_run.get("html_url"),
            "head_sha": page_run.get("head_sha"),
            "status": page_run.get("status"),
            "conclusion": page_run.get("conclusion"),
            "jobs": page_names,
            "tests": os_results,
        },
        "source_closure": {
            "workflow": source_run.get("name"),
            "run_id": source_run.get("id"),
            "url": source_run.get("html_url"),
            "head_branch": source_run.get("head_branch"),
            "prerequisite_jobs": source_names,
            "native_windows": binaries,
        },
        "limits": {
            "windows_gui_human_qualified": False,
            "ocr_accuracy_certified": False,
            "authenticode_signed": False,
            "toctou_race_eliminated": False,
            "hard_links_distinguished": False,
        },
        "note": "The cumulative ZIP inventory/CRC/SHA-256 receipt is generated and checked by the subsequent packaging step; this file does not self-certify that outer step.",
    }
    out = root / "04-Tests-et-Qualification" / "V549-CI-QUALIFICATION.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(out.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, out)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        report = generate(args.root)
    except (OSError, ValueError, QualificationError) as exc:
        print("V549 qualification evidence rejected: " + str(exc))
        return 2
    print(json.dumps({
        "schema": report["schema"],
        "qualified": report["qualified"],
        "commit_sha": report["commit_sha"],
        "page_order_run_id": report["page_order"]["run_id"],
        "page_order_tests": {key: {"expected": value["expected"], "passed": value["passed"], "skipped": value["skipped"], "failed": value["failed"]} for key, value in report["page_order"]["tests"].items()},
        "source_closure_run_id": report["source_closure"]["run_id"],
        "module_count": report["module_count"],
        "windows_native": report["source_closure"]["native_windows"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
