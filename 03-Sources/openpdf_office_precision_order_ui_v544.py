"""V544 privacy-safe GUI adapter for precision and extracted-object sequence metrics.
Legacy V1 reports continue to use the strict V543 adapter.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import json
import math

from openpdf_office_quality_ui_v543 import (
    safe_office_receipt as _safe_v1,
    format_office_quality_summary as _format_v1,
)

SCHEMA_V1 = "openpdf.office.reference.report.v1"
SCHEMA_V2 = "openpdf.office.reference.report.v2"
BASE_THRESHOLDS = ("min_token_recall", "min_case_token_recall",
                   "min_human_reviewed", "min_editable_elements_per_case")
EXTRA_THRESHOLDS = ("min_token_precision", "min_case_token_precision",
                    "min_case_ordered_token_recall")
BASE_FAILURES = frozenset(BASE_THRESHOLDS)
EXTRA_FAILURES = frozenset(EXTRA_THRESHOLDS)
PO_FIELDS = frozenset({
    "actual_tokens", "matched_tokens", "unexpected_tokens", "token_precision",
    "token_f1", "worst_case_token_precision", "worst_case_ordered_token_recall",
    "cases_below_precision_floor", "cases_below_order_floor", "thresholds", "by_format",
})
PO_FORMAT_FIELDS = frozenset({
    "cases", "actual_tokens", "matched_tokens", "unexpected_tokens",
    "cases_below_precision_floor", "cases_below_order_floor",
    "token_precision", "token_f1", "worst_case_token_precision",
    "worst_case_ordered_token_recall",
})


def _count(value, label):
    if type(value) is not int or not 0 <= value <= 100_000_000:
        raise ValueError(f"Invalid V544 {label} count")
    return value


def _rate(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"Invalid V544 {label} rate")
    return float(value)


def safe_office_receipt(report):
    """Whitelist either legacy V1 or extended V2 metrics; reject contradictory receipts."""
    if not isinstance(report, dict):
        raise ValueError("Invalid Office report")
    if report.get("schema") == SCHEMA_V1:
        return _safe_v1(report)
    if report.get("schema") != SCHEMA_V2:
        raise ValueError("Invalid V544 Office report schema")

    failed = report.get("failed_thresholds")
    allowed = BASE_FAILURES | EXTRA_FAILURES
    if (not isinstance(failed, list) or len(failed) > len(allowed) or
            any(type(item) is not str or item not in allowed for item in failed) or
            len(set(failed)) != len(failed)):
        raise ValueError("Invalid V544 failure list")
    old_failed = [item for item in failed if item in BASE_FAILURES]
    extra_failed = {item for item in failed if item in EXTRA_FAILURES}
    thresholds = report.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != set(BASE_THRESHOLDS):
        raise ValueError("Invalid V544 base thresholds")
    legacy = dict(report)
    legacy["schema"] = SCHEMA_V1
    legacy["status"] = "FAIL" if old_failed else "PASS"
    legacy["failed_thresholds"] = old_failed
    legacy["thresholds"] = dict(thresholds)
    legacy["token_precision"] = "not_assessed"
    legacy.pop("precision_order", None)
    safe = _safe_v1(legacy)

    base_thresholds = safe["thresholds"]
    expected_base_failures = set()
    if safe["token_recall"] < base_thresholds["min_token_recall"]:
        expected_base_failures.add("min_token_recall")
    if safe["cases_below_recall_floor"]:
        expected_base_failures.add("min_case_token_recall")
    if safe["cases_below_editable_floor"]:
        expected_base_failures.add("min_editable_elements_per_case")
    if safe["human_reviewed_cases"] < base_thresholds["min_human_reviewed"]:
        expected_base_failures.add("min_human_reviewed")
    if expected_base_failures != set(old_failed):
        raise ValueError("V544 legacy thresholds do not match the report")

    metric = report.get("precision_order")
    if not isinstance(metric, dict) or set(metric) != set(PO_FIELDS):
        raise ValueError("Invalid V544 precision/order block")
    actual = _count(metric.get("actual_tokens"), "actual tokens")
    matched = _count(metric.get("matched_tokens"), "matched tokens")
    unexpected = _count(metric.get("unexpected_tokens"), "unexpected tokens")
    cases_below_precision = _count(metric.get("cases_below_precision_floor"), "precision failures")
    cases_below_order = _count(metric.get("cases_below_order_floor"), "order failures")
    if matched != safe["matched_tokens"] or actual < matched or unexpected != actual - matched:
        raise ValueError("Contradictory V544 aggregate token counts")
    if cases_below_precision > safe["cases"] or cases_below_order > safe["cases"]:
        raise ValueError("Contradictory V544 case counts")

    precision = _rate(metric.get("token_precision"), "token precision")
    f1 = _rate(metric.get("token_f1"), "token F1")
    worst_precision = _rate(metric.get("worst_case_token_precision"), "worst precision")
    worst_order = _rate(metric.get("worst_case_ordered_token_recall"), "worst ordered recall")
    expected_precision = matched / actual if actual else 0.0
    recall = safe["token_recall"]
    expected_f1 = (2 * expected_precision * recall / (expected_precision + recall)
                   if expected_precision + recall else 0.0)
    if abs(precision - expected_precision) > 0.0000021 or abs(f1 - expected_f1) > 0.0000021:
        raise ValueError("V544 precision/F1 is not reconciled")

    metric_thresholds = metric.get("thresholds")
    if not isinstance(metric_thresholds, dict) or set(metric_thresholds) != set(EXTRA_THRESHOLDS):
        raise ValueError("Invalid V544 precision/order thresholds")
    metric_thresholds = {key: _rate(metric_thresholds[key], key) for key in EXTRA_THRESHOLDS}
    expected_extra_failures = set()
    if precision < metric_thresholds["min_token_precision"]:
        expected_extra_failures.add("min_token_precision")
    if cases_below_precision:
        expected_extra_failures.add("min_case_token_precision")
    if cases_below_order:
        expected_extra_failures.add("min_case_ordered_token_recall")
    if expected_extra_failures != extra_failed:
        raise ValueError("V544 precision/order failures do not match metrics")
    all_failures = set(old_failed) | expected_extra_failures
    expected_status = "FAIL" if all_failures else "PASS"
    if report.get("status") != expected_status:
        raise ValueError("V544 status does not match its thresholds")

    by_format = metric.get("by_format")
    if not isinstance(by_format, dict) or set(by_format) != {"docx", "pptx", "xlsx"}:
        raise ValueError("Invalid V544 format breakdown")
    safe_by_format = {}
    sums = {key: 0 for key in (
        "cases", "actual_tokens", "matched_tokens", "unexpected_tokens",
        "cases_below_precision_floor", "cases_below_order_floor")}
    worst_p = []
    worst_o = []
    for name in ("docx", "pptx", "xlsx"):
        entry = by_format[name]
        if not isinstance(entry, dict) or set(entry) != PO_FORMAT_FIELDS:
            raise ValueError("Invalid V544 format metric")
        values = {key: _count(entry.get(key), key) for key in (
            "cases", "actual_tokens", "matched_tokens", "unexpected_tokens",
            "cases_below_precision_floor", "cases_below_order_floor")}
        if (values["cases"] != safe["by_format"][name]["cases"] or
                values["matched_tokens"] != safe["by_format"][name]["matched_tokens"] or
                values["matched_tokens"] > values["actual_tokens"] or
                values["unexpected_tokens"] != values["actual_tokens"] - values["matched_tokens"] or
                values["cases_below_precision_floor"] > values["cases"] or
                values["cases_below_order_floor"] > values["cases"]):
            raise ValueError("Inconsistent V544 format counts")
        for key, value in values.items():
            sums[key] += value
        if values["cases"]:
            p = _rate(entry.get("token_precision"), "format precision")
            f = _rate(entry.get("token_f1"), "format F1")
            wp = _rate(entry.get("worst_case_token_precision"), "format worst precision")
            wo = _rate(entry.get("worst_case_ordered_token_recall"), "format worst order")
            expected_p = values["matched_tokens"] / values["actual_tokens"] if values["actual_tokens"] else 0.0
            format_recall = safe["by_format"][name]["token_recall"]
            expected_format_f1 = (2 * expected_p * format_recall / (expected_p + format_recall)
                                  if expected_p + format_recall else 0.0)
            if (format_recall is None or abs(p - expected_p) > 0.0000021 or
                    abs(f - expected_format_f1) > 0.0000021):
                raise ValueError("Inconsistent V544 format precision/F1")
            safe_by_format[name] = {**values, "token_precision": p, "token_f1": f,
                                    "worst_case_token_precision": wp,
                                    "worst_case_ordered_token_recall": wo}
            worst_p.append(wp)
            worst_o.append(wo)
        else:
            if any(values[key] for key in values):
                raise ValueError("Nonzero V544 metrics for empty format")
            if any(entry.get(key) is not None for key in (
                "token_precision", "token_f1", "worst_case_token_precision",
                "worst_case_ordered_token_recall")):
                raise ValueError("Invalid empty V544 format rates")
            safe_by_format[name] = {**values, "token_precision": None, "token_f1": None,
                                    "worst_case_token_precision": None,
                                    "worst_case_ordered_token_recall": None}
    if (sums["cases"] != safe["cases"] or sums["actual_tokens"] != actual or
            sums["matched_tokens"] != matched or sums["unexpected_tokens"] != unexpected or
            sums["cases_below_precision_floor"] != cases_below_precision or
            sums["cases_below_order_floor"] != cases_below_order):
        raise ValueError("V544 format totals do not reconcile")
    if (not worst_p or abs(min(worst_p) - worst_precision) > 0.0000021 or
            not worst_o or abs(min(worst_o) - worst_order) > 0.0000021):
        raise ValueError("V544 worst-case rates do not reconcile")

    safe.update({
        "schema": SCHEMA_V2,
        "status": expected_status,
        "failed_thresholds": sorted(all_failures),
        "scope": "editable_ooxml_multiset_precision_recall_f1_and_ordered_token_coverage",
        "token_precision": precision,
        "reading_order": "object_extraction_sequence_only_not_visual_reading_order",
        "precision_order": {
            "actual_tokens": actual,
            "matched_tokens": matched,
            "unexpected_tokens": unexpected,
            "token_precision": precision,
            "token_f1": f1,
            "worst_case_token_precision": worst_precision,
            "worst_case_ordered_token_recall": worst_order,
            "cases_below_precision_floor": cases_below_precision,
            "cases_below_order_floor": cases_below_order,
            "thresholds": metric_thresholds,
            "by_format": safe_by_format,
        },
    })
    return safe


def format_office_quality_summary(report):
    safe = safe_office_receipt(report)
    if safe["schema"] == SCHEMA_V1:
        return _format_v1(report)
    metric = safe["precision_order"]
    lines = [
        f"Qualification Office éditable : {safe['status']}",
        f"Documents : {safe['cases']} ; objets éditables : {safe['editable_elements']}",
        f"Rappel des mots de référence : {safe['token_recall']:.2%} ; pire document : {safe['worst_case_token_recall']:.2%}",
        f"Précision des mots présents : {metric['token_precision']:.2%} ; F1 : {metric['token_f1']:.2%}",
        f"Mots présents non justifiés par la référence : {metric['unexpected_tokens']}",
        f"Rappel ordonné (séquence d’extraction, pire document) : {metric['worst_case_ordered_token_recall']:.2%}",
        f"Documents sous seuil de rappel : {safe['cases_below_recall_floor']} ; sous seuil de précision : {metric['cases_below_precision_floor']}",
        f"Documents sous seuil d’ordre d’extraction : {metric['cases_below_order_floor']} ; sans objets éditables suffisants : {safe['cases_below_editable_floor']}",
        f"Références déclarées humaines : {safe['human_reviewed_cases']}",
    ]
    for fmt in ("docx", "pptx", "xlsx"):
        slot = safe["by_format"][fmt]
        po = metric["by_format"][fmt]
        if slot["cases"]:
            lines.append(f"{fmt.upper()} : {slot['cases']} document(s), rappel {slot['token_recall']:.2%}, précision {po['token_precision']:.2%}, F1 {po['token_f1']:.2%}")
    if safe["failed_thresholds"]:
        lines.append("Seuils échoués : " + ", ".join(safe["failed_thresholds"]))
    lines.extend((
        "Mesure : mots contenus dans de véritables objets Office éditables ; les mots des images ne comptent pas.",
        "L’ordre compare les séquences d’objets extraites aux phrases de référence dans l’ordre déclaré ; il ne prouve pas l’ordre de lecture visuel.",
        "Fidélité visuelle, géométrie des tableaux, styles et positionnement non évalués.",
        "Provenance des annotations déclarative, non attestée indépendamment.",
    ))
    return "\n".join(lines)


def serialize_office_quality_receipt(report):
    return json.dumps(safe_office_receipt(report), sort_keys=True, ensure_ascii=False, indent=2) + "\n"
