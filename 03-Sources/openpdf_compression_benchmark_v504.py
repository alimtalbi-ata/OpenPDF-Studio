"""Measured production PDF compression benchmark; never overwrites prior evidence.
RGB checks are bounded-scale evidence, not archival/print/OCR certification.
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
    full_gate = None
    if policy.min_saving_percent is not None:
        from openpdf_compression_acceptance_v489 import AcceptancePolicy
        full_gate = AcceptancePolicy(min_saving_percent=policy.min_saving_percent,
            max_page_mae=policy.max_page_mae,
            max_page_changed_fraction=policy.max_page_changed_fraction,
            render_scale=policy.render_scale, pixel_delta=policy.pixel_delta)
    import fitz
    report = dict(schema='openpdf.compression.benchmark.v50.4',
        created_utc=datetime.now(timezone.utc).isoformat(),
        environment=dict(python=platform.python_version(), platform=platform.platform(),
                         pymupdf=fitz.VersionBind), policy=asdict(policy),
        evidence_limit='bounded_scale_full_rgb_pixel_comparison_not_archival_print_or_ocr_certification',
        cases=[])
    for idx, (src, size, digest) in enumerate(sources, 1):
        for profile in policy.profiles:
            target = folder / f'case-{idx:03d}-{digest[:12]}-{profile}.pdf'
            start = time.perf_counter()
            case = dict(case=idx, source_name=src.name, profile=profile,
                        source_bytes=size, source_sha256=digest, output_file=target.name)
            try:
                receipt = execute_compression(CompressionRequest(str(src), str(target), profile,
                    quality_gate=gate, full_pixel_gate=full_gate))
                if receipt.published:
                    quality = _quality(receipt.metrics.visual_audit, policy.render_scale)
                    case.update(status='published', output_bytes=receipt.size,
                        output_sha256=receipt.sha256, saved_bytes=size - receipt.size,
                        saving_percent=round(100 * (size - receipt.size) / size, 4), quality=quality)
                else:
                    case.update(status='no_gain', output_bytes=0, saved_bytes=0,
                                saving_percent=0.0, quality=None)
            except Exception as exc:
                case.update(status='rejected', error_type=type(exc).__name__,
                            error=str(exc)[:240], quality=None)
                if target.exists():
                    case['unexpected_output_after_rejection'] = True
            finally:
                case['elapsed_ms'] = round((time.perf_counter() - start) * 1000, 2)
            if src.stat().st_size != size or _sha256(src) != digest:
                raise RuntimeError('Benchmark input changed during execution')
            report['cases'].append(case)
    report['counts'] = {status: sum(c['status'] == status for c in report['cases'])
                        for status in ('published', 'no_gain', 'rejected')}
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
