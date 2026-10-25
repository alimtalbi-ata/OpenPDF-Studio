"""Privacy-preserving OCR reference qualification UI adapter (V541).

Author: Abdelhalim Talbi. No PDF text, filenames or paths in receipts.
"""
from __future__ import annotations
import json
import math

REPORT_SCHEMA = 'openpdf.ocr.reference.report.v1'
COUNTS = ('cases', 'pages', 'human_reviewed_cases', 'synthetic_cases',
          'cases_below_quality_floors', 'pages_below_quality_floors',
          'reference_characters', 'reference_words', 'character_errors', 'word_errors')
RATES = ('cer', 'wer', 'worst_case_cer', 'worst_case_wer',
         'worst_page_cer', 'worst_page_wer')
HASHES = ('manifest_sha256', 'evidence_set_sha256')


def safe_receipt(report):
    """Allowlist a V539/V540 result for GUI display/export; never echo unknown fields."""
    if not isinstance(report, dict) or report.get('schema') != REPORT_SCHEMA:
        raise ValueError('Invalid OCR qualification receipt')
    if report.get('status') not in ('PASS', 'FAIL'):
        raise ValueError('Invalid OCR qualification status')
    result = {'schema': REPORT_SCHEMA, 'status': report['status']}
    for key in COUNTS:
        value = report.get(key)
        if type(value) is not int or value < 0:
            raise ValueError('Invalid OCR qualification count')
        result[key] = value
    for key in RATES:
        value = report.get(key)
        if value is None and key.startswith('worst_page_'):
            result[key] = None
        elif type(value) in (float, int) and math.isfinite(value) and value >= 0:
            result[key] = value
        else:
            raise ValueError('Invalid OCR qualification rate')
    for key in HASHES:
        value = report.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Invalid OCR evidence digest')
        result[key] = value
    failed = report.get('failed_thresholds')
    allowed = {'max_cer', 'max_wer', 'case_quality_floors', 'page_quality_floors', 'min_human_reviewed'}
    if not isinstance(failed, list) or any(type(x) is not str or x not in allowed for x in failed):
        raise ValueError('Invalid OCR threshold failure list')
    result['failed_thresholds'] = list(failed)
    if type(report.get('page_quality_floors_enabled')) is not bool:
        raise ValueError('Invalid OCR page gate status')
    result['page_quality_floors_enabled'] = report['page_quality_floors_enabled']
    result['visual_fidelity'] = 'not_assessed'
    result['annotation_provenance'] = 'declared_not_independently_attested'
    return result


def format_ocr_quality_summary(report):
    """Human-readable, bounded summary with explicit non-certification warning."""
    receipt = safe_receipt(report)
    lines = [f"Qualification OCR : {receipt['status']}",
             f"Documents : {receipt['cases']} ; pages : {receipt['pages']}",
             f"CER : {receipt['cer']:.4%} ; WER : {receipt['wer']:.4%}",
             f"Pages sous seuil : {receipt['pages_below_quality_floors']}",
             f"Documents sous seuil : {receipt['cases_below_quality_floors']}",
             f"Références déclarées humaines : {receipt['human_reviewed_cases']}",
             'Contrôle : couche texte PDF uniquement ; aucune fidélité visuelle ou Office certifiée.',
             'Provenance humaine déclarative, non authentifiée.']
    if not receipt['page_quality_floors_enabled']:
        lines.append('Attention : seuils OCR par page désactivés.')
    if receipt['failed_thresholds']:
        lines.append('Seuils échoués : ' + ', '.join(receipt['failed_thresholds']))
    return '\n'.join(lines)


def serialize_ocr_quality_receipt(report):
    """JSON safe to save locally, excluding original text, paths and unknown metadata."""
    return json.dumps(safe_receipt(report), ensure_ascii=False, sort_keys=True, indent=2) + '\n'
