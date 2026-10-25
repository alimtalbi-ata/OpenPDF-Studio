"""V50.5: choose the smallest verified PDF from explicit compression profiles.
All profiles run on private candidates; RGB and alpha are checked before publication.
Lossy profiles require explicit opt-in. Author: Abdelhalim Talbi.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

from openpdf_atomic_output import publish_exclusive
from openpdf_compression_evidence_v506 import verified_evidence
from openpdf_compression_coverage_v507 import verify_render_coverage
from openpdf_compression_alpha_v508 import verify_alpha_fidelity
from openpdf_compression_acceptance_v489 import AcceptancePolicy
from openpdf_compression_service_v344 import CompressionRequest, execute_compression
from openpdf_source_integrity_v430 import fingerprint_source, verify_source_unchanged

_ALLOWED = ('smaller_only', 'standard', 'images_balanced', 'images_adaptive')


@dataclass(frozen=True)
class AutoCompressionPolicy:
    profiles: tuple[str, ...] = ('smaller_only',)
    min_saving_percent: float = 0.0
    max_page_mae: float = 4.0
    max_page_changed_fraction: float = 0.02
    render_scale: float = 0.5
    pixel_delta: int = 24
    max_input_bytes: int = 50 * 1024 * 1024

    def __post_init__(self):
        if (type(self.profiles) is not tuple or not self.profiles
                or len(self.profiles) > len(_ALLOWED)
                or len(set(self.profiles)) != len(self.profiles)
                or any(p not in _ALLOWED for p in self.profiles)):
            raise ValueError('Invalid or duplicated compression profiles')
        if type(self.max_input_bytes) is not int or not 1 <= self.max_input_bytes <= 500 * 1024 * 1024:
            raise ValueError('Invalid PDF byte budget')
        AcceptancePolicy(min_saving_percent=self.min_saving_percent,
            max_page_mae=self.max_page_mae,
            max_page_changed_fraction=self.max_page_changed_fraction,
            render_scale=self.render_scale, pixel_delta=self.pixel_delta)


def _hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _paths(source, destination, policy):
    src, dst = Path(source).expanduser(), Path(destination).expanduser()
    if src.is_symlink() or not src.is_file() or src.suffix.lower() != '.pdf':
        raise ValueError('Source must be a regular PDF, without symlinks')
    src = src.resolve(strict=True)
    if not 0 < src.stat().st_size <= policy.max_input_bytes:
        raise ValueError('PDF exceeds input byte budget')
    if dst.suffix.lower() != '.pdf' or not dst.parent.is_dir():
        raise ValueError('Destination must be a PDF in an existing directory')
    if dst.exists() or dst.is_symlink():
        raise FileExistsError('Destination already exists')
    if src == dst.resolve(strict=False):
        raise ValueError('Source and destination must differ')
    return src, dst


def auto_compress(source, destination, policy=AutoCompressionPolicy()):
    """Pick the smallest verified candidate; never overwrite an existing PDF."""
    if type(policy) is not AutoCompressionPolicy:
        raise TypeError('Expected AutoCompressionPolicy')
    src, dst = _paths(source, destination, policy)
    original = fingerprint_source(src)
    quality = AcceptancePolicy(min_saving_percent=policy.min_saving_percent,
        max_page_mae=policy.max_page_mae,
        max_page_changed_fraction=policy.max_page_changed_fraction,
        render_scale=policy.render_scale, pixel_delta=policy.pixel_delta)
    report = dict(schema='openpdf.auto-compression.v50.6',
        source_bytes=original.size, source_sha256=original.sha256,
        destination=dst.name, policy=asdict(policy), cases=[],
        status='no_compliant_gain', selected_profile=None,
        coverage_verification='v50.7-exact-pages-and-pixels',
        alpha_verification='v50.8-exact-alpha-at-bounded-scale',
        evidence_limit='full_rgb_at_bounded_scale_not_print_ocr_or_archival_certification')
    with tempfile.TemporaryDirectory(prefix='.openpdf-auto-', dir=dst.parent) as work:
        folder = Path(work)
        winners = []
        for index, profile in enumerate(policy.profiles):
            candidate = folder / f'candidate-{index}.pdf'
            started = time.perf_counter()
            case = dict(profile=profile)
            try:
                receipt = execute_compression(CompressionRequest(str(src), str(candidate), profile,
                    full_pixel_gate=quality))
                if not receipt.published:
                    case['status'] = 'no_gain'
                else:
                    size, digest = candidate.stat().st_size, _hash(candidate)
                    if size != receipt.size or digest != receipt.sha256 or size >= original.size:
                        raise RuntimeError('Candidate receipt or saving inconsistent')
                    evidence = verified_evidence(receipt, source_sha256=original.sha256,
                        source_bytes=original.size, candidate_sha256=digest,
                        candidate_bytes=size, profile=profile, policy=quality)
                    coverage = verify_render_coverage(src, candidate,
                        receipt.metrics.visual_audit, quality)
                    evidence['coverage'] = coverage
                    evidence['alpha'] = verify_alpha_fidelity(src, candidate, quality,
                        source_sha256=original.sha256, candidate_sha256=digest)
                    case.update(status='accepted', bytes=size, sha256=digest,
                        saving_percent=round(100 * (original.size - size) / original.size, 4),
                        quality=evidence)
                    winners.append((size, index, candidate, digest, profile))
            except Exception as exc:
                case.update(status='rejected', error_type=type(exc).__name__,
                            error=str(exc)[:180])
            finally:
                case['elapsed_ms'] = round((time.perf_counter() - started) * 1000, 2)
            verify_source_unchanged(src, original)
            report['cases'].append(case)
        if not winners:
            return report
        size, index, winner, digest, profile = min(winners)
        fd, temp_name = tempfile.mkstemp(prefix='.openpdf-auto-publish-', suffix='.pdf', dir=dst.parent)
        try:
            with os.fdopen(fd, 'wb') as target, winner.open('rb') as candidate:
                shutil.copyfileobj(candidate, target, 1024 * 1024)
                target.flush()
                os.fsync(target.fileno())
            if os.path.getsize(temp_name) != size or _hash(temp_name) != digest:
                raise RuntimeError('Selected candidate changed during copy')
            verify_source_unchanged(src, original)
            publish_exclusive(temp_name, dst)
            if dst.stat().st_size != size or _hash(dst) != digest:
                raise RuntimeError('Published candidate differs from verified receipt')
            report.update(status='published', selected_profile=profile,
                selected_quality=report['cases'][index]['quality'],
                output_bytes=size, output_sha256=digest,
                saving_percent=round(100 * (original.size - size) / original.size, 4))
            return report
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


def auto_compress_gui(source, destination):
    """GUI worker: report exact bytes and bounded RGB/alpha/structure evidence."""
    report = auto_compress(source, destination, AutoCompressionPolicy(
        profiles=('smaller_only', 'images_balanced', 'images_adaptive')))
    if report['status'] != 'published':
        return 'Aucun gain conforme aux seuils de qualité. Aucun fichier de sortie modifié.'

    def size_text(value):
        return f"{value:,}".replace(",", " ") + " octets"

    quality = report.get('selected_quality') or {}
    structure = quality.get('structure') or {}
    return (
        f"Compression automatique publiée : {Path(destination).name}\n"
        f"Taille mesurée : {size_text(report['source_bytes'])} → "
        f"{size_text(report['output_bytes'])} ; gain : "
        f"{size_text(report['source_bytes'] - report['output_bytes'])} "
        f"({report['saving_percent']:.2f} %).\n"
        f"Profil retenu : {report['selected_profile']}. "
        f"Contrôle RGB : {quality.get('pages_compared', 0)} page(s), "
        f"{quality.get('pixels_compared', 0):,} pixels à l’échelle "
        f"{quality.get('render_scale', 0.5)} ; MAE max "
        f"{quality.get('max_page_mae', 0):.3f}/255 ; pixels modifiés "
        f"{quality.get('max_page_changed_fraction', 0):.2%}. "
        f"Contrôle structurel : {structure.get('links_verified', 0)} lien(s), "
        f"{structure.get('bookmarks_verified', 0)} signet(s), "
        f"{structure.get('annotations_verified', 0)} annotation(s), "
        f"{structure.get('attachments_verified', 0)} pièce(s) jointe(s). "
        "Couverture de transparence contrôlée. Mesure raster à échelle bornée ; "
        "ce n’est pas une certification PDF/A, impression, OCR ou accessibilité."
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description='Select smallest quality-verified PDF')
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('--profiles', default='smaller_only', help='Comma-separated; lossy profiles are opt-in')
    parser.add_argument('--min-saving-percent', type=float, default=0.0)
    parser.add_argument('--max-mae', type=float, default=4.0)
    parser.add_argument('--max-changed', type=float, default=0.02)
    args = parser.parse_args(argv)
    policy = AutoCompressionPolicy(profiles=tuple(args.profiles.split(',')),
        min_saving_percent=args.min_saving_percent,
        max_page_mae=args.max_mae, max_page_changed_fraction=args.max_changed)
    result = auto_compress(args.source, args.destination, policy)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result['status'] == 'published' else 2


if __name__ == '__main__':
    sys.exit(main())
