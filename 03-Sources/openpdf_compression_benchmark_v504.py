"""Measured production PDF compression benchmark; never overwrites prior evidence.
RGB, page/pixel coverage and alpha checks are bounded-scale evidence, not archival/print/OCR certification.
Author: Abdelhalim Talbi — OpenPDF Studio V50.4.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
from openpdf_compression_quality_gate_v470 import CompressionQualityGate, validate_quality_gate
from openpdf_compression_service_v344 import CompressionRequest, execute_compression
from openpdf_compression_acceptance_v489 import AcceptancePolicy
from openpdf_compression_coverage_v507 import verify_render_coverage
from openpdf_compression_alpha_v508 import verify_alpha_fidelity

PROFILES = ('standard', 'smaller_only', 'images_balanced', 'images_adaptive')


@dataclass(frozen=True)
class BenchmarkPolicy:
    profiles: tuple[str, ...] = ('standard', 'smaller_only')
    render_scale: float = 0.5
    max_page_mae: float = 4.0
    max_page_changed_fraction: float = 0.02
    pixel_delta: int = 24
    min_saving_percent: float | None = None
    max_inputs: int = 12
    max_input_bytes: int = 50 * 1024 * 1024
    max_total_bytes: int = 200 * 1024 * 1024

    def __post_init__(self):
        if (not isinstance(self.profiles, tuple) or not self.profiles
                or len(set(self.profiles)) != len(self.profiles)
                or any(p not in PROFILES for p in self.profiles)):
            raise ValueError('Unsupported or duplicated compression profile')
        validate_quality_gate(CompressionQualityGate(self.max_page_mae,
            self.max_page_changed_fraction, self.render_scale, 1, self.pixel_delta))
        value = self.min_saving_percent
        if value is not None and (type(value) not in (int, float)
                                  or not math.isfinite(value) or not 0 <= value <= 100):
            raise ValueError('Invalid minimum saving percent')
        for name in ('max_inputs', 'max_input_bytes', 'max_total_bytes'):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError('Invalid benchmark budget: ' + name)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _sources(paths, policy):
    if not isinstance(paths, (tuple, list)) or not 1 <= len(paths) <= policy.max_inputs:
        raise ValueError('Invalid PDF corpus size')
    found, seen, total = [], set(), 0
    for value in paths:
        source = Path(value).expanduser()
        if source.is_symlink() or not source.is_file() or source.suffix.lower() != '.pdf':
            raise ValueError('Benchmark input must be a regular PDF (no symlinks)')
        source = source.resolve(strict=True)
        if source in seen:
            raise ValueError('Duplicate benchmark input')
        seen.add(source)
        size = source.stat().st_size
        total += size
        if not 0 < size <= policy.max_input_bytes or total > policy.max_total_bytes:
            raise ValueError('Benchmark input exceeds byte budget')
        found.append((source, size, _sha256(source)))
    return found


def _quality(audit, scale):
    if isinstance(audit, dict):
        sampled = audit.get('sampled_visual_audit', {})
        full = audit.get('full_pixel_acceptance', {})
        if not isinstance(sampled, dict) or not isinstance(full, dict) or full.get('accepted') is not True:
            raise RuntimeError('Missing full-pixel and saving evidence')
        quality = dict(pages=full['pages_compared'], pixels_compared=full['pixels_compared'],
            max_page_mae=full['max_page_mae'], max_page_changed_fraction=full['max_page_changed_fraction'],
            render_scale=full['policy']['render_scale'], pixel_step=1,
            text_identical=sampled.get('text_identical'),
            geometry_identical=sampled.get('geometry_identical'), evidence=full['evidence'])
    else:
        if audit is None:
            raise RuntimeError('Missing full-pixel quality evidence')
        quality = dict(pages=audit.pages_compared, pixels_compared=audit.pixels_sampled,
            max_page_mae=audit.max_page_mae, max_page_changed_fraction=audit.max_page_changed_fraction,
            render_scale=audit.render_scale, pixel_step=audit.sample_step,
            text_identical=audit.text_identical, geometry_identical=audit.geometry_identical,
            evidence=audit.evidence)
    if (quality['text_identical'] is not True or quality['geometry_identical'] is not True
            or quality['pixel_step'] != 1 or quality['render_scale'] < scale):
        raise RuntimeError('Missing full-pixel quality evidence')
    return quality


def benchmark_corpus(paths, output_dir, policy=BenchmarkPolicy()):
    """Execute real compression, enforce RGB and optional saving gates pre-publication."""
    if type(policy) is not BenchmarkPolicy:
        raise TypeError('Expected BenchmarkPolicy')
    sources = _sources(paths, policy)
    folder = Path(output_dir).expanduser()
    if folder.exists() or folder.is_symlink():
        raise FileExistsError('Benchmark output directory already exists')
    folder.mkdir(parents=False, exist_ok=False)
    gate = CompressionQualityGate(policy.max_page_mae, policy.max_page_changed_fraction,
                                  policy.render_scale, 1, policy.pixel_delta)
    # All profiles now require full-RGB, coverage and alpha checks, including
    # the default run without a minimum saving threshold.
    full_gate = AcceptancePolicy(min_saving_percent=policy.min_saving_percent or 0.0,
        max_page_mae=policy.max_page_mae,
        max_page_changed_fraction=policy.max_page_changed_fraction,
        render_scale=policy.render_scale, pixel_delta=policy.pixel_delta)
    import fitz
    report = dict(schema='openpdf.compression.benchmark.v50.4',
        created_utc=datetime.now(timezone.utc).isoformat(),
        environment=dict(python=platform.python_version(), platform=platform.platform(),
                         pymupdf=fitz.VersionBind), policy=asdict(policy),
        evidence_limit='bounded_scale_rgb_coverage_and_alpha_not_archival_print_ocr_certification',
        verification='v50.9-rgb-coverage-alpha-sha256',
        cases=[])
    for idx, (src, size, digest) in enumerate(sources, 1):
        for profile in policy.profiles:
            target = folder / f'case-{idx:03d}-{digest[:12]}-{profile}.pdf'
            start = time.perf_counter()
            cpu_start = time.process_time()
            case = dict(case=idx, source_name=src.name, profile=profile,
                        source_bytes=size, source_sha256=digest, output_file=target.name)
            try:
                receipt = execute_compression(CompressionRequest(str(src), str(target), profile,
                    quality_gate=gate, full_pixel_gate=full_gate))
                if receipt.published:
                    if target.is_symlink() or not target.is_file():
                        raise RuntimeError('Benchmark candidate is not a regular PDF')
                    if target.stat().st_size != receipt.size or _sha256(target) != receipt.sha256:
                        raise RuntimeError('Benchmark candidate differs from receipt')
                    quality = _quality(receipt.metrics.visual_audit, policy.render_scale)
                    full_audit = receipt.metrics.visual_audit['full_pixel_acceptance']
                    coverage = verify_render_coverage(src, target, full_audit, full_gate)
                    alpha = verify_alpha_fidelity(src, target, full_gate,
                        source_sha256=digest, candidate_sha256=receipt.sha256)
                    if (coverage['pixels_verified'] != alpha['pixels_verified']
                            or quality['pixels_compared'] != alpha['pixels_verified']):
                        raise RuntimeError('RGB/alpha coverage mismatch')
                    quality['coverage'] = coverage
                    quality['alpha'] = alpha
                    case.update(status='published', output_bytes=receipt.size,
                        output_sha256=receipt.sha256, saved_bytes=size - receipt.size,
                        saving_percent=round(100 * (size - receipt.size) / size, 4), quality=quality)
                else:
                    case.update(status='no_gain', output_bytes=0, saved_bytes=0,
                                saving_percent=0.0, quality=None)
            except Exception as exc:
                case.update(status='rejected', error_type=type(exc).__name__,
                            error=str(exc)[:240], quality=None)
                # Remove a rejected candidate, never leave a PDF marked accepted.
                if target.is_file() and not target.is_symlink():
                    target.unlink()
                if target.exists() or target.is_symlink():
                    case['unexpected_output_after_rejection'] = True
            finally:
                case['elapsed_ms'] = round((time.perf_counter() - start) * 1000, 2)
                case['process_cpu_ms'] = round((time.process_time() - cpu_start) * 1000, 2)
            if src.stat().st_size != size or _sha256(src) != digest:
                raise RuntimeError('Benchmark input changed during execution')
            report['cases'].append(case)
    report['counts'] = {status: sum(c['status'] == status for c in report['cases'])
                        for status in ('published', 'no_gain', 'rejected')}
    # Weighted gains include accepted outputs only; rejected/no-gain cases
    # are reported separately and cannot inflate the saving percentage.
    report['by_profile'] = {}
    for profile in policy.profiles:
        subset = [c for c in report['cases'] if c['profile'] == profile]
        accepted = [c for c in subset if c['status'] == 'published']
        before = sum(c['source_bytes'] for c in accepted)
        after = sum(c['output_bytes'] for c in accepted)
        report['by_profile'][profile] = {
            'attempted': len(subset), 'published': len(accepted),
            'no_gain': sum(c['status'] == 'no_gain' for c in subset),
            'rejected': sum(c['status'] == 'rejected' for c in subset),
            'accepted_source_bytes': before, 'accepted_output_bytes': after,
            'accepted_saved_bytes': before - after,
            'weighted_saving_percent': round(100 * (before - after) / before, 4) if before else None,
            'elapsed_ms': round(sum(c['elapsed_ms'] for c in subset), 2),
            'process_cpu_ms': round(sum(c['process_cpu_ms'] for c in subset), 2),
        }
    with (folder / 'compression-benchmark-v50.4.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write('\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Real PDF compression size/time/RGB benchmark')
    parser.add_argument('pdf', nargs='+')
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--profiles', default='standard,smaller_only')
    parser.add_argument('--max-mae', type=float, default=4.0)
    parser.add_argument('--max-changed', type=float, default=0.02)
    parser.add_argument('--min-saving-percent', type=float, default=None)
    parser.add_argument('--strict', action='store_true')
    args = parser.parse_args(argv)
    policy = BenchmarkPolicy(profiles=tuple(args.profiles.split(',')),
        max_page_mae=args.max_mae, max_page_changed_fraction=args.max_changed,
        min_saving_percent=args.min_saving_percent)
    report = benchmark_corpus(args.pdf, args.output_dir, policy)
    print(json.dumps(dict(counts=report['counts'],
        report=str(Path(args.output_dir) / 'compression-benchmark-v50.4.json')), ensure_ascii=False))
    return int(report['counts']['rejected'] > 0 or (args.strict and report['counts']['no_gain'] > 0))


if __name__ == '__main__':
    sys.exit(main())
