"""V543 editable-Office reference gate: strict, private GUI receipts.

This is a qualification tool, not a claim of visual fidelity or human review.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations
import json
import math

SCHEMA = 'openpdf.office.reference.report.v1'
FORMATS = ('docx', 'pptx', 'xlsx')
COUNTS = ('cases', 'human_reviewed_cases', 'synthetic_cases',
          'editable_elements', 'cases_below_recall_floor',
          'cases_below_editable_floor', 'reference_tokens', 'matched_tokens')
THRESHOLDS = ('min_token_recall', 'min_case_token_recall',
              'min_human_reviewed', 'min_editable_elements_per_case')
FAILURES = frozenset(THRESHOLDS)
SHA = ('manifest_sha256', 'evidence_set_sha256')


def _count(value, label):
    if type(value) is not int or not 0 <= value <= 100_000_000:
        raise ValueError(f'Invalid Office {label} count')
    return value


def _rate(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'Invalid Office {label} rate')
    return value


def safe_office_receipt(report):
    """Reject malformed reports and strip any unexpected text, path or metadata.

    A report may originate from a future version or an untrusted manifest. Never
    serialize or display fields outside this explicit, versioned allowlist.
    """
    if not isinstance(report, dict) or report.get('schema') != SCHEMA:
        raise ValueError('Invalid Office qualification schema')
    if report.get('status') not in ('PASS', 'FAIL'):
        raise ValueError('Invalid Office qualification status')
    result = {'schema': SCHEMA, 'status': report['status']}
    for key in COUNTS:
        result[key] = _count(report.get(key), key)
    if not 2 <= result['cases'] <= 32 or result['human_reviewed_cases'] + result['synthetic_cases'] != result['cases']:
        raise ValueError('Inconsistent Office corpus size')
    if (result['matched_tokens'] > result['reference_tokens'] or
            result['reference_tokens'] < result['cases'] or
            result['cases_below_recall_floor'] > result['cases'] or
            result['cases_below_editable_floor'] > result['cases']):
        raise ValueError('Inconsistent Office token counts')
    for key in ('token_recall', 'worst_case_token_recall'):
        result[key] = _rate(report.get(key), key)
    if abs(result['token_recall'] - result['matched_tokens'] / result['reference_tokens']) > 0.00000051:
        raise ValueError('Inconsistent Office recall')
    for key in SHA:
        value = report.get(key)
        if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Invalid Office evidence digest')
        result[key] = value
    threshold_data = report.get('thresholds')
    if not isinstance(threshold_data, dict) or set(threshold_data) != set(THRESHOLDS):
        raise ValueError('Invalid Office thresholds')
    result['thresholds'] = {}
    for key in THRESHOLDS:
        value = threshold_data[key]
        result['thresholds'][key] = (_rate(value, key) if 'recall' in key else _count(value, key))
    failed = report.get('failed_thresholds')
    if not isinstance(failed, list) or len(failed) > len(FAILURES) or any(type(v) is not str or v not in FAILURES for v in failed) or len(set(failed)) != len(failed):
        raise ValueError('Invalid Office failure reasons')
    if (report['status'] == 'PASS') != (len(failed) == 0):
        raise ValueError('Inconsistent Office qualification status')
    result['failed_thresholds'] = list(failed)
    formats = report.get('by_format')
    if not isinstance(formats, dict) or set(formats) != set(FORMATS):
        raise ValueError('Invalid Office format breakdown')
    result['by_format'] = {}
    for name in FORMATS:
        entry = formats[name]
        if not isinstance(entry, dict) or set(entry) != {'cases', 'reference_tokens', 'matched_tokens', 'token_recall'}:
            raise ValueError('Invalid Office format entry')
        values = {key: _count(entry.get(key), key) for key in ('cases', 'reference_tokens', 'matched_tokens')}
        if values['matched_tokens'] > values['reference_tokens']:
            raise ValueError('Inconsistent Office format counts')
        rate = entry.get('token_recall')
        if values['reference_tokens'] == 0:
            if values['cases'] or rate is not None:
                raise ValueError('Invalid empty Office format')
        else:
            if not values['cases'] or abs(_rate(rate, 'format recall') - values['matched_tokens'] / values['reference_tokens']) > 0.00000051:
                raise ValueError('Inconsistent Office format recall')
        result['by_format'][name] = {**values, 'token_recall': rate}
    if (sum(v['cases'] for v in result['by_format'].values()) != result['cases'] or
            sum(v['reference_tokens'] for v in result['by_format'].values()) != result['reference_tokens'] or
            sum(v['matched_tokens'] for v in result['by_format'].values()) != result['matched_tokens']):
        raise ValueError('Inconsistent Office format totals')
    # Claims are intentionally hardcoded, not copied from untrusted input.
    result.update(scope='editable_ooxml_text_token_multiset_recall_against_separate_reference',
                  visual_fidelity='not_assessed', reading_order='not_assessed',
                  token_precision='not_assessed',
                  annotation_provenance='declared_not_independently_attested')
    return result


def format_office_quality_summary(report):
    receipt = safe_office_receipt(report)
    lines = [f"Qualification Office éditable : {receipt['status']}",
             f"Documents : {receipt['cases']} ; objets éditables : {receipt['editable_elements']}",
             f"Rappel de mots : {receipt['token_recall']:.2%} ; pire document : {receipt['worst_case_token_recall']:.2%}",
             f"Documents sous seuil : {receipt['cases_below_recall_floor']} ; sans objets suffisants : {receipt['cases_below_editable_floor']}",
             f"Références déclarées humaines : {receipt['human_reviewed_cases']}"]
    for fmt in FORMATS:
        slot = receipt['by_format'][fmt]
        if slot['cases']:
            lines.append(f"{fmt.upper()} : {slot['cases']} document(s), rappel {slot['token_recall']:.2%}")
    if receipt['failed_thresholds']:
        lines.append('Seuils échoués : ' + ', '.join(receipt['failed_thresholds']))
    lines.extend(('Mesure : mots dans des objets Office éditables, pas dans les images.',
                  'Non évalués : précision, mise en page, tableaux, styles, ordre et fidélité visuelle.',
                  'Provenance des annotations déclarative, non attestée.'))
    return '\n'.join(lines)


def serialize_office_quality_receipt(report):
    return json.dumps(safe_office_receipt(report), sort_keys=True, ensure_ascii=False, indent=2) + '\n'
