"""OpenPDF Studio R22 Python adapter — Abdelhalim Talbi.
Runs the standalone Node diagnostic CLI; does not read PDF/Office files.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
from typing import Any

class DiagnosticBridgeError(RuntimeError):
    """A bounded diagnostic subprocess failed or returned an invalid response."""

HERE = Path(__file__).resolve().parent
MAX_REQUEST_BYTES = 20 * 1024 * 1024
MAX_RESPONSE_BYTES = 64 * 1024 * 1024

def run_diagnostic(source: list[dict[str, Any]], target: list[dict[str, Any]], *,
                   timeout: float = 30.0, node_executable: str = 'node',
                   bridge_path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Return validated diagnostic result, raising DiagnosticBridgeError on failure.

    No shell, no network, no fallback engine. Both documents must already be
    represented as arrays of JSON page objects.
    """
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 600:
        raise ValueError('timeout must be between 0 and 600 seconds')
    if not isinstance(node_executable, str) or not node_executable.strip():
        raise ValueError('node_executable must be a nonempty string')
    request = {'schema': 'openpdf.bridge.request.v1', 'source': source, 'target': target}
    try:
        payload = json.dumps(request, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise DiagnosticBridgeError(f'Invalid request data: {exc}') from exc
    if len(payload) > MAX_REQUEST_BYTES:
        raise DiagnosticBridgeError('Request exceeds 20 MiB')
    script = Path(bridge_path) if bridge_path is not None else HERE / 'bridge-cli.js'
    try:
        completed = subprocess.run([node_executable, str(script)], input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise DiagnosticBridgeError(f'Diagnostic timed out after {timeout} seconds') from exc
    except OSError as exc:
        raise DiagnosticBridgeError(f'Cannot launch diagnostic CLI: {exc}') from exc
    if len(completed.stdout) > MAX_RESPONSE_BYTES:
        raise DiagnosticBridgeError('Response exceeds 64 MiB')
    if completed.returncode != 0:
        error = completed.stderr[:2048].decode('utf-8', errors='replace').strip()
        raise DiagnosticBridgeError(f'Diagnostic CLI exited {completed.returncode}: {error}')
    try:
        response = json.loads(completed.stdout)
    except (ValueError, UnicodeDecodeError) as exc:
        raise DiagnosticBridgeError('Diagnostic CLI returned invalid JSON') from exc
    if not isinstance(response, dict) or response.get('schema') != 'openpdf.bridge.response.v1' or not isinstance(response.get('result'), dict):
        raise DiagnosticBridgeError('Diagnostic CLI returned an unsupported response schema')
    return response['result']
