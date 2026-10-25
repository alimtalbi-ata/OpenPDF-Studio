"""V539 bounded, SHA-bound OCR reference corpus gate. Author: Abdelhalim Talbi.
Compares serialized OCR PDF text with independent references, without leaking text.
The annotation origin is declared provenance, not attested human review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from openpdf_ocr_quality_v487 import _edit_distance

SCHEMA = 'openpdf.ocr.reference.corpus.v1'
ANNOTATION_SCHEMA = 'openpdf.ocr.reference.v1'
REPORT_SCHEMA = 'openpdf.ocr.reference.report.v1'
MAX_CASES = 32
MAX_PAGES_PER_CASE = 16
MAX_TOTAL_PAGES = 64
MAX_FILE_BYTES = (32 * 1024 * 1024, 32 * 1024 * 1024, 256 * 1024)
MAX_MANIFEST_BYTES = 128 * 1024
MAX_PAGE_CHARS = 5000
MAX_PAGE_WORDS = 1000
MAX_EDIT_WORK_PER_PAGE = 12_000_000
MAX_EDIT_WORK_TOTAL = 60_000_000
ID_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{0,63}$')

def _pairs(items):
    obj = {}
    for key, value in items:
        if key in obj:
            raise ValueError('Duplicate JSON key')
        obj[key] = value
    return obj

def _digest(path: Path, limit: int):
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= limit:
            raise ValueError('Missing, empty or oversized evidence')
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(os.dup(fd), 'rb') as stream:
            while block := stream.read(1024 * 1024):
                size += len(block)
                if size > limit:
                    raise ValueError('Evidence exceeds size budget')
                digest.update(block)
        after = os.fstat(fd)
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError('Evidence modified during read')
        return digest.hexdigest()
    finally:
        os.close(fd)

def _json(path: Path, limit: int):
    if path.is_symlink():
        raise ValueError('Symlink evidence refused')
    _digest(path, limit)
    raw = path.read_bytes()
    if not 0 < len(raw) <= limit:
        raise ValueError('JSON exceeds size budget')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid UTF-8 JSON') from exc

def _file(root: Path, name: str):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name or ':' in name:
        raise ValueError('Invalid relative evidence path')
    relative = Path(name)
    if relative.is_absolute() or any(part in ('', '.', '..') for part in name.split('/')):
        raise ValueError('Path traversal refused')
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Symlink evidence refused')
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Evidence missing or outside corpus')
    return path

def _thresholds(value):
    required = {'max_cer', 'max_wer', 'max_case_cer', 'max_case_wer', 'min_human_reviewed'}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError('Incomplete OCR thresholds')
    for name in required - {'min_human_reviewed'}:
        number = value[name]
        if type(number) not in (int, float) or not 0 <= number <= 1:
            raise ValueError('Invalid OCR error threshold')
    humans = value['min_human_reviewed']
    if type(humans) is not int or not 0 <= humans <= MAX_CASES:
        raise ValueError('Invalid human-reviewed threshold')
    return value

def _normalize(value: str):
    return ' '.join(value.split())

def _page_distance(reference: str, recognized: str):
    if type(reference) is not str or type(recognized) is not str:
        raise ValueError('OCR reference and result must be text')
    ref, got = _normalize(reference), _normalize(recognized)
    if max(len(ref), len(got)) > MAX_PAGE_CHARS:
        raise ValueError('OCR page exceeds character budget')
    ref_words, got_words = ref.split(), got.split()
    if max(len(ref_words), len(got_words)) > MAX_PAGE_WORDS:
        raise ValueError('OCR page exceeds word budget')
    work = len(ref) * len(got)
    if work > MAX_EDIT_WORK_PER_PAGE:
        raise ValueError('OCR page exceeds edit-distance budget')
    return (len(ref), len(ref_words), _edit_distance(ref, got),
            _edit_distance(ref_words, got_words), work)

def evaluate_ocr_reference_corpus(manifest):
    """Compare actual OCR PDF text to independently authored references."""
    import fitz
    manifest = Path(manifest)
    data = _json(manifest, MAX_MANIFEST_BYTES)
    if not isinstance(data, dict) or set(data) != {'schema', 'cases', 'thresholds'} or data['schema'] != SCHEMA:
        raise ValueError('Invalid OCR corpus manifest')
    cases = data['cases']
    if not isinstance(cases, list) or not 2 <= len(cases) <= MAX_CASES:
        raise ValueError('OCR corpus requires 2 to 32 cases')
    thresholds = _thresholds(data['thresholds'])
    if thresholds['min_human_reviewed'] > len(cases):
        raise ValueError('Impossible human-reviewed threshold')
    root = manifest.parent
    ids, seen_sources, seen_outputs = set(), set(), set()
    chars = words = char_errors = word_errors = pages = humans = work_total = 0
    case_failures = 0
    worst_cer = worst_wer = 0.0
    bound_hashes = []
    manifest_hash = _digest(manifest, MAX_MANIFEST_BYTES)
    for case in cases:
        if not isinstance(case, dict) or set(case) != {'id', 'source_pdf', 'ocr_pdf', 'annotations'}:
            raise ValueError('Invalid OCR corpus case')
        identifier = case['id']
        if type(identifier) is not str or not ID_RE.fullmatch(identifier) or identifier in ids:
            raise ValueError('Invalid or duplicate case ID')
        ids.add(identifier)
        files = tuple(_file(root, case[k]) for k in ('source_pdf', 'ocr_pdf', 'annotations'))
        if len(set(files)) != 3:
            raise ValueError('Source, OCR and annotation must be distinct')
        hashes = tuple(_digest(path, limit) for path, limit in zip(files, MAX_FILE_BYTES))
        if hashes[0] == hashes[1]:
            raise ValueError('OCR output is byte-identical to source')
        if hashes[0] in seen_sources or hashes[1] in seen_outputs:
            raise ValueError('Duplicate source or OCR output in corpus')
        seen_sources.add(hashes[0]); seen_outputs.add(hashes[1])
        annotation = _json(files[2], MAX_FILE_BYTES[2])
        if (not isinstance(annotation, dict) or
                set(annotation) != {'schema', 'source_sha256', 'origin', 'pages'} or
                annotation['schema'] != ANNOTATION_SCHEMA or annotation['source_sha256'] != hashes[0] or
                annotation['origin'] not in ('human_reviewed', 'synthetic_known_at_generation')):
            raise ValueError('Invalid or unbound OCR annotation')
        if annotation['origin'] == 'human_reviewed':
            humans += 1
        refs = annotation['pages']
        if not isinstance(refs, list) or not 1 <= len(refs) <= MAX_PAGES_PER_CASE:
            raise ValueError('Invalid annotated page count')
        with fitz.open(files[0]) as source, fitz.open(files[1]) as output:
            if (source.needs_pass or output.needs_pass or source.page_count != output.page_count
                    or output.page_count != len(refs)):
                raise ValueError('Encrypted or misaligned OCR PDF')
            pages += len(refs)
            if pages > MAX_TOTAL_PAGES:
                raise ValueError('Corpus exceeds page budget')
            case_chars = case_words = case_char_errors = case_word_errors = 0
            for index, item in enumerate(refs):
                if (not isinstance(item, dict) or set(item) != {'page', 'text'} or
                        type(item['page']) is not int or item['page'] != index + 1):
                    raise ValueError('OCR page reference missing or reordered')
                recognized = output[index].get_text('text', sort=True)
                c, w, ce, we, work = _page_distance(item['text'], recognized)
                work_total += work
                if work_total > MAX_EDIT_WORK_TOTAL:
                    raise ValueError('Corpus exceeds edit-distance work budget')
                case_chars += c; case_words += w
                case_char_errors += ce; case_word_errors += we
        if not case_chars or not case_words:
            raise ValueError('OCR case has no measurable reference text')
        cer, wer = case_char_errors / case_chars, case_word_errors / case_words
        worst_cer = max(worst_cer, cer); worst_wer = max(worst_wer, wer)
        case_failures += cer > thresholds['max_case_cer'] or wer > thresholds['max_case_wer']
        chars += case_chars; words += case_words
        char_errors += case_char_errors; word_errors += case_word_errors
        if hashes != tuple(_digest(path, limit) for path, limit in zip(files, MAX_FILE_BYTES)):
            raise ValueError('OCR evidence modified during evaluation')
        bound_hashes.extend(hashes)
    if _digest(manifest, MAX_MANIFEST_BYTES) != manifest_hash:
        raise ValueError('OCR manifest modified during evaluation')
    cer, wer = char_errors / chars, word_errors / words
    failed = []
    if cer > thresholds['max_cer']:
        failed.append('max_cer')
    if wer > thresholds['max_wer']:
        failed.append('max_wer')
    if case_failures:
        failed.append('case_quality_floors')
    if humans < thresholds['min_human_reviewed']:
        failed.append('min_human_reviewed')
    return {
        'schema': REPORT_SCHEMA, 'status': 'FAIL' if failed else 'PASS',
        'scope': 'serialized_pdf_extractable_text_against_independent_reference',
        'visual_fidelity': 'not_assessed', 'annotation_provenance': 'declared_not_independently_attested',
        'manifest_sha256': manifest_hash,
        'evidence_set_sha256': hashlib.sha256('\n'.join(sorted(bound_hashes)).encode('ascii')).hexdigest(),
        'cases': len(cases), 'pages': pages, 'human_reviewed_cases': humans,
        'synthetic_cases': len(cases) - humans, 'cases_below_quality_floors': case_failures,
        'reference_characters': chars, 'reference_words': words,
        'character_errors': char_errors, 'word_errors': word_errors,
        'cer': round(cer, 6), 'wer': round(wer, 6),
        'worst_case_cer': round(worst_cer, 6), 'worst_case_wer': round(worst_wer, 6),
        'thresholds': thresholds, 'failed_thresholds': failed,
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description='Independent OCR PDF reference corpus gate (no text in reports)')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--report')
    args = parser.parse_args(argv)
    try:
        result = evaluate_ocr_reference_corpus(args.manifest)
        if args.report:
            path = Path(args.report)
            if path.is_symlink() or path.exists():
                raise FileExistsError('OCR report already exists')
            with path.open('x', encoding='utf-8') as stream:
                json.dump(result, stream, ensure_ascii=False, sort_keys=True, indent=2)
                stream.write('\n')
    except (ValueError, OSError, RuntimeError, TypeError) as exc:
        print(json.dumps({'status': 'ERROR', 'reason': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['status'] == 'PASS' else 3

if __name__ == '__main__':
    raise SystemExit(main())
