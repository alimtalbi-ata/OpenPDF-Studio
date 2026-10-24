"""Bounded, independent PDF->XLSX corpus release gate.

No source text or case names are included in the machine-readable result.
The per-document oracle is openpdf_xlsx_ground_truth_v517.evaluate_ground_truth.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

SCHEMA = 'openpdf.xlsx.corpus.v1'
REPORT_SCHEMA = 'openpdf.xlsx.corpus.report.v1'
MAX_MANIFEST_BYTES = 256 * 1024
MAX_CASES = 64
ID_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]{0,63}$')
THRESHOLD_KEYS = frozenset({
    'min_nonempty_cell_accuracy', 'min_table_recall', 'min_merge_recall',
    'max_extra_nonempty_cells', 'min_human_reviewed',
})


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Cle JSON dupliquee')
        result[key] = value
    return result


def _json_file(path: Path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError('Manifeste absent, symbolique ou hors limite')
    raw = path.read_bytes()
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError('Manifeste trop volumineux')
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nombre non fini')))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Manifeste JSON invalide') from exc
    return data, hashlib.sha256(raw).hexdigest()


def _safe_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or '\\' in relative or '\x00' in relative:
        raise ValueError('Chemin de corpus invalide')
    path = Path(relative)
    if path.is_absolute() or any(part in ('.', '..') for part in relative.split('/')) or ':' in relative:
        raise ValueError('Chemin absolu ou traversal interdit')
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Lien symbolique interdit dans le corpus')
    if not current.is_file() or not current.resolve().is_relative_to(root.resolve()):
        raise ValueError('Fichier de corpus absent ou hors racine')
    return current


def _thresholds(value):
    if not isinstance(value, dict) or set(value) != THRESHOLD_KEYS:
        raise ValueError('Seuils de qualification incomplets')
    result = {}
    for name, number in value.items():
        if name.startswith('min_') and name != 'min_human_reviewed':
            if type(number) not in (int, float) or not math.isfinite(number) or not 0 <= number <= 1:
                raise ValueError('Seuil de fidelite invalide')
        elif type(number) is not int or not 0 <= number <= 100000:
            raise ValueError('Seuil entier invalide')
        result[name] = number
    return result


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 1.0


def evaluate_corpus(manifest, *, oracle=None):
    """Audit all cases; fail closed for invalid input, fail gate for measured drift."""
    manifest = Path(manifest)
    data, manifest_hash = _json_file(manifest)
    if not isinstance(data, dict) or set(data) != {'schema', 'cases', 'thresholds'} or data['schema'] != SCHEMA:
        raise ValueError('Schema de corpus invalide')
    cases = data['cases']
    if not isinstance(cases, list) or not 2 <= len(cases) <= MAX_CASES:
        raise ValueError('Le corpus doit contenir entre 2 et 64 cas')
    thresholds = _thresholds(data['thresholds'])
    if thresholds['min_human_reviewed'] > len(cases):
        raise ValueError('Nombre de validations humaines impossible')
    root = manifest.parent
    if oracle is None:
        from openpdf_xlsx_ground_truth_v517 import evaluate_ground_truth
        oracle = evaluate_ground_truth
    ids, triples = set(), set()
    hashes = []
    counts = {key: 0 for key in (
        'expected_tables', 'observed_tables', 'matched_tables',
        'annotated_cells', 'exact_cells', 'annotated_nonempty_cells',
        'exact_nonempty_cells', 'extra_nonempty_cells',
        'expected_merges', 'observed_merges', 'matched_merges',
    )}
    deviations = humans = 0
    for case in cases:
        if not isinstance(case, dict) or set(case) != {'id', 'pdf', 'xlsx', 'annotations'}:
            raise ValueError('Cas de corpus invalide')
        case_id = case['id']
        if not isinstance(case_id, str) or not ID_PATTERN.fullmatch(case_id) or case_id in ids:
            raise ValueError('Identifiant de cas invalide ou duplique')
        ids.add(case_id)
        files = tuple(_safe_file(root, case[key]) for key in ('pdf', 'xlsx', 'annotations'))
        if len(set(files)) != 3 or files in triples:
            raise ValueError('Fichiers ou cas de corpus reutilises')
        triples.add(files)
        result = oracle(*files)
        if result.get('schema') != 'openpdf.xlsx.ground_truth.report.v1' or result.get('status') not in ('PASS', 'DEVIATION'):
            raise ValueError('Rapport individuel non conforme')
        for key in counts:
            value = result.get(key)
            if type(value) is not int or value < 0:
                raise ValueError('Compteur individuel invalide')
            counts[key] += value
        for key in ('source_sha256', 'workbook_sha256', 'annotation_sha256'):
            value = result.get(key)
            if not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None:
                raise ValueError('Empreinte de preuve invalide')
            hashes.append(value)
        if result.get('annotation_origin') == 'human_reviewed':
            humans += 1
        elif result.get('annotation_origin') != 'synthetic_known_at_generation':
            raise ValueError('Origine annotation invalide')
        deviations += result['status'] != 'PASS'
    if counts['expected_tables'] == 0 or counts['annotated_nonempty_cells'] == 0:
        raise ValueError('Corpus sans tableaux ou cellules non vides annotes')
    measures = {
        'table_precision': _ratio(counts['matched_tables'], counts['observed_tables']),
        'table_recall': _ratio(counts['matched_tables'], counts['expected_tables']),
        'nonempty_cell_accuracy': _ratio(counts['exact_nonempty_cells'], counts['annotated_nonempty_cells']),
        'merge_precision': _ratio(counts['matched_merges'], counts['observed_merges']),
        'merge_recall': _ratio(counts['matched_merges'], counts['expected_merges']),
    }
    failed = []
    for key, numerator, denominator in (
        ('min_nonempty_cell_accuracy', counts['exact_nonempty_cells'], counts['annotated_nonempty_cells']),
        ('min_table_recall', counts['matched_tables'], counts['expected_tables']),
        ('min_merge_recall', counts['matched_merges'], counts['expected_merges']),
    ):
        # Compare unrounded fractions: a 0.9499996 result must not satisfy 0.95.
        if (numerator / denominator if denominator else 1.0) < thresholds[key]:
            failed.append(key)
    # V521: a corpus must never PASS when the converter invents empty table
    # worksheets or blank merged ranges. The v1 threshold schema has recall
    # but no minimum precision threshold; previously such phantom structures
    # escaped every release gate despite table/merge precision < 1.0.
    # Fail closed without changing the established manifest format.
    if counts['observed_tables'] != counts['matched_tables']:
        failed.append('unexpected_tables')
    if counts['observed_merges'] != counts['matched_merges']:
        failed.append('unexpected_merges')
    if counts['extra_nonempty_cells'] > thresholds['max_extra_nonempty_cells']:
        failed.append('max_extra_nonempty_cells')
    if humans < thresholds['min_human_reviewed']:
        failed.append('min_human_reviewed')
    # Exact deviations are visible even when permissive thresholds allow a pass.
    return {
        'schema': REPORT_SCHEMA,
        'status': 'FAIL' if failed else 'PASS',
        'coverage': 'independent_annotated_cells_not_visual_fidelity',
        'visual_fidelity': 'not_assessed',
        'manifest_sha256': manifest_hash,
        'evidence_set_sha256': hashlib.sha256('\n'.join(sorted(hashes)).encode('ascii')).hexdigest(),
        'cases': len(cases), 'human_reviewed_cases': humans,
        'synthetic_cases': len(cases) - humans, 'deviating_cases': deviations,
        **counts, **measures,
        'thresholds': thresholds, 'failed_thresholds': failed,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='Gate de corpus PDF vers Excel, sans contenu metier')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--report')
    args = parser.parse_args(argv)
    try:
        result = evaluate_corpus(args.manifest)
        if args.report:
            from openpdf_xlsx_fidelity_v515 import write_report_new
            write_report_new(args.report, result)
    except (ValueError, OSError, RuntimeError, FileExistsError) as exc:
        print(json.dumps({'status': 'ERROR', 'reason': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['status'] == 'PASS' else 3


if __name__ == '__main__':
    raise SystemExit(main())
