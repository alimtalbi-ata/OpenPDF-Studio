"""V558 bounded PDF-to-Office visual, geometry and editable-text fidelity gate.

The evaluator compares a source PDF with a PDF rendered from an Office output.
It does not prove that the declared renderer actually produced the supplied PDF.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import argparse
from collections import Counter
import difflib
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

import fitz
from PIL import Image, ImageChops

from openpdf_ocr_reference_corpus_v539 import _digest, _file, _json, ID_RE
from openpdf_office_reference_v542 import _office_preflight, _source_pdf_preflight
from openpdf_precision_order_v544 import measure_precision_order

SCHEMA = "openpdf.office.visual-fidelity.corpus.v558"
ANNOTATION_SCHEMA = "openpdf.office.visual-fidelity.annotation.v558"
REPORT_SCHEMA = "openpdf.office.visual-fidelity.report.v558"
FORMATS = {".docx", ".xlsx", ".pptx"}
MAX_CASES = 32
MAX_PAGES_PER_PDF = 32
MAX_TOTAL_PAGES = 96
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_OFFICE_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 128 * 1024
MAX_ANNOTATION_BYTES = 256 * 1024
MAX_TOKENS_PER_CASE = 5000
MAX_TOTAL_TOKENS = 50000
MAX_WORDS_PER_PAGE = 1200
MAX_PAGE_PIXELS = 8_000_000
MAX_TOTAL_PIXELS = 100_000_000
RENDER_DPI = 96
CHANGE_PIXEL_THRESHOLD = 16
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
RENDERER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ +()-]{0,79}$")
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
THRESHOLD_KEYS = frozenset({
    "max_page_count_delta",
    "max_page_dimension_delta_pct",
    "max_mean_abs_pixel_error",
    "max_changed_pixel_fraction",
    "min_text_precision",
    "min_text_recall",
    "min_ordered_token_recall",
    "max_mean_word_center_drift_pct",
    "min_mean_word_box_iou",
    "min_human_reviewed",
})
DEFAULT_THRESHOLDS = {
    "max_page_count_delta": 0,
    "max_page_dimension_delta_pct": 1.0,
    "max_mean_abs_pixel_error": 8.0,
    "max_changed_pixel_fraction": 0.02,
    "min_text_precision": 0.95,
    "min_text_recall": 0.95,
    "min_ordered_token_recall": 0.95,
    "max_mean_word_center_drift_pct": 1.0,
    "min_mean_word_box_iou": 0.90,
    "min_human_reviewed": 0,
}
REPORT_KEYS = frozenset({
    "schema", "status", "scope", "visual_fidelity", "reading_order",
    "renderer_provenance", "text_layer_required", "screenshot",
    "manifest_sha256", "evidence_set_sha256", "cases",
    "human_reviewed_cases", "synthetic_cases", "source_pages",
    "rendered_pages", "pages_compared", "max_page_count_delta",
    "max_page_dimension_delta_pct", "mean_abs_pixel_error",
    "changed_pixel_fraction", "reference_tokens", "actual_tokens",
    "matched_tokens", "text_precision", "text_recall",
    "ordered_token_recall", "matched_word_boxes",
    "mean_word_center_drift_pct", "mean_word_box_iou",
    "thresholds", "failed_thresholds",
})


def _tokens(value: str) -> list[str]:
    if type(value) is not str:
        raise ValueError("Invalid PDF text token")
    return TOKEN_RE.findall(unicodedata.normalize("NFKC", value).casefold())


def _sha(value, label):
    if type(value) is not str or not SHA_RE.fullmatch(value):
        raise ValueError("Invalid SHA-256 in visual-fidelity annotation")
    return value


def _finite_number(value, label, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("Invalid visual-fidelity threshold: " + label)
    return float(value)


def _thresholds(value):
    if not isinstance(value, dict) or set(value) != THRESHOLD_KEYS:
        raise ValueError("Incomplete visual-fidelity thresholds")
    if type(value["max_page_count_delta"]) is not int or not 0 <= value["max_page_count_delta"] <= MAX_PAGES_PER_PDF:
        raise ValueError("Invalid page-count threshold")
    if type(value["min_human_reviewed"]) is not int or not 0 <= value["min_human_reviewed"] <= MAX_CASES:
        raise ValueError("Invalid human-review threshold")
    return {
        "max_page_count_delta": value["max_page_count_delta"],
        "max_page_dimension_delta_pct": _finite_number(value["max_page_dimension_delta_pct"], "max_page_dimension_delta_pct", 0, 100),
        "max_mean_abs_pixel_error": _finite_number(value["max_mean_abs_pixel_error"], "max_mean_abs_pixel_error", 0, 255),
        "max_changed_pixel_fraction": _finite_number(value["max_changed_pixel_fraction"], "max_changed_pixel_fraction", 0, 1),
        "min_text_precision": _finite_number(value["min_text_precision"], "min_text_precision", 0, 1),
        "min_text_recall": _finite_number(value["min_text_recall"], "min_text_recall", 0, 1),
        "min_ordered_token_recall": _finite_number(value["min_ordered_token_recall"], "min_ordered_token_recall", 0, 1),
        "max_mean_word_center_drift_pct": _finite_number(value["max_mean_word_center_drift_pct"], "max_mean_word_center_drift_pct", 0, 100),
        "min_mean_word_box_iou": _finite_number(value["min_mean_word_box_iou"], "min_mean_word_box_iou", 0, 1),
        "min_human_reviewed": value["min_human_reviewed"],
    }


def _safe_pdf_pages(path, *, source):
    try:
        if source:
            _source_pdf_preflight(path)
        document = fitz.open(str(path))
    except Exception:
        raise ValueError("Invalid or unreadable PDF evidence") from None
    if document.needs_pass or not 1 <= document.page_count <= MAX_PAGES_PER_PDF:
        document.close()
        raise ValueError("Encrypted PDF or page-count budget exceeded")
    return document


def _page_pixel_size(page):
    rect = page.rect
    width, height = float(rect.width), float(rect.height)
    if not math.isfinite(width) or not math.isfinite(height) or width <= 0 or height <= 0:
        raise ValueError("Invalid PDF page dimensions")
    scale = RENDER_DPI / 72.0
    pixel_width = max(1, math.ceil(width * scale))
    pixel_height = max(1, math.ceil(height * scale))
    if pixel_width > 5000 or pixel_height > 5000 or pixel_width * pixel_height > MAX_PAGE_PIXELS:
        raise ValueError("PDF raster dimensions exceed the visual-fidelity budget")
    return width, height, pixel_width, pixel_height


def _page_words(page):
    width, height = float(page.rect.width), float(page.rect.height)
    tokens = []
    boxes = []
    try:
        words = page.get_text("words", sort=True)
    except Exception:
        raise ValueError("PDF text extraction failed") from None
    if len(words) > MAX_WORDS_PER_PAGE:
        raise ValueError("PDF word-box budget exceeded")
    for word in words:
        if len(word) < 5:
            continue
        x0, y0, x1, y1, text = word[:5]
        pieces = _tokens(text)
        if not pieces:
            continue
        box = (
            max(0.0, min(1.0, float(x0) / width)),
            max(0.0, min(1.0, float(y0) / height)),
            max(0.0, min(1.0, float(x1) / width)),
            max(0.0, min(1.0, float(y1) / height)),
        )
        if box[2] < box[0] or box[3] < box[1]:
            raise ValueError("Invalid PDF word geometry")
        for piece in pieces:
            tokens.append(piece)
            # A multi-token word fragment shares its extracted word rectangle.
            boxes.append((piece, box))
    return tokens, boxes


def _render_gray(page):
    try:
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(RENDER_DPI / 72.0, RENDER_DPI / 72.0),
            colorspace=fitz.csRGB,
            alpha=False,
            annots=True,
        )
        if pixmap.width * pixmap.height > MAX_PAGE_PIXELS:
            raise ValueError("Rendered page exceeds raster budget")
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples).convert("L")
    except ValueError:
        raise
    except Exception:
        raise ValueError("PDF page rendering failed") from None


def _box_metrics(left, right):
    ax0, ay0, ax1, ay1 = left
    bx0, by0, bx1, by1 = right
    aw, ah = max(0.0, ax1 - ax0), max(0.0, ay1 - ay0)
    bw, bh = max(0.0, bx1 - bx0), max(0.0, by1 - by0)
    intersection_w = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    intersection_h = max(0.0, min(ay1, by1) - max(ay0, by0))
    intersection = intersection_w * intersection_h
    union = aw * ah + bw * bh - intersection
    iou = intersection / union if union > 0 else 0.0
    acx, acy = (ax0 + ax1) / 2, (ay0 + ay1) / 2
    bcx, bcy = (bx0 + bx1) / 2, (by0 + by1) / 2
    drift_pct = math.hypot(acx - bcx, acy - bcy) * 100 / math.sqrt(2)
    return drift_pct, iou


def _geometry_matches(source_pages, rendered_pages):
    drift_sum = iou_sum = 0.0
    matched = 0
    for source_boxes, rendered_boxes in zip(source_pages, rendered_pages):
        left_tokens = [item[0] for item in source_boxes]
        right_tokens = [item[0] for item in rendered_boxes]
        # Raster/text budgets cap each page; autojunk avoids quadratic behavior
        # on repetitive legal boilerplate. Text order itself uses the exact V544 LCS.
        matcher = difflib.SequenceMatcher(None, left_tokens, right_tokens, autojunk=True)
        for left_start, right_start, length in matcher.get_matching_blocks():
            for offset in range(length):
                drift, iou = _box_metrics(
                    source_boxes[left_start + offset][1],
                    rendered_boxes[right_start + offset][1],
                )
                drift_sum += drift
                iou_sum += iou
                matched += 1
    return matched, drift_sum, iou_sum


def _validated_annotation(path, source_sha, office_sha, rendered_sha):
    annotation = _json(path, MAX_ANNOTATION_BYTES)
    required = {
        "schema", "source_sha256", "office_sha256", "rendered_pdf_sha256",
        "origin", "renderer", "renderer_version",
    }
    if not isinstance(annotation, dict) or set(annotation) != required:
        raise ValueError("Invalid visual-fidelity annotation schema")
    if annotation["schema"] != ANNOTATION_SCHEMA:
        raise ValueError("Unsupported visual-fidelity annotation schema")
    if (_sha(annotation["source_sha256"], "source") != source_sha or
            _sha(annotation["office_sha256"], "Office") != office_sha or
            _sha(annotation["rendered_pdf_sha256"], "rendered PDF") != rendered_sha):
        raise ValueError("Visual-fidelity annotation is not bound to the evidence")
    if annotation["origin"] not in ("human_reviewed", "synthetic_known_at_generation"):
        raise ValueError("Invalid visual-fidelity annotation provenance")
    if annotation["renderer"] not in ("libreoffice", "microsoft_office", "other"):
        raise ValueError("Invalid declared Office renderer")
    version = annotation["renderer_version"]
    if type(version) is not str or not RENDERER_RE.fullmatch(version):
        raise ValueError("Invalid declared renderer version")
    return annotation


def evaluate_office_visual_fidelity_corpus(manifest):
    """Compare source PDF and PDF preview of its Office candidate using bounded metrics."""
    manifest = Path(manifest)
    data = _json(manifest, MAX_MANIFEST_BYTES)
    if (not isinstance(data, dict) or set(data) != {"schema", "cases", "thresholds"}
            or data["schema"] != SCHEMA):
        raise ValueError("Invalid visual-fidelity manifest")
    cases = data["cases"]
    if not isinstance(cases, list) or not 2 <= len(cases) <= MAX_CASES:
        raise ValueError("Visual-fidelity corpus requires 2 to 32 cases")
    thresholds = _thresholds(data["thresholds"])
    if thresholds["min_human_reviewed"] > len(cases):
        raise ValueError("Impossible human-review threshold")

    manifest_sha = _digest(manifest, MAX_MANIFEST_BYTES)
    ids = set()
    source_shas, office_shas, rendered_shas = set(), set(), set()
    evidence_hashes = []
    humans = source_pages_total = rendered_pages_total = pages_compared = 0
    total_pixels = total_pixel_error = changed_pixels = 0
    total_reference_tokens = total_actual_tokens = matched_tokens = ordered_matches = 0
    geometry_matches = 0
    geometry_drift_sum = geometry_iou_sum = 0.0
    max_page_count_delta = 0
    max_dimension_delta_pct = 0.0
    corpus_pixel_budget = corpus_page_budget = corpus_token_budget = 0

    for case in cases:
        required_case = {"id", "source_pdf", "office_file", "rendered_pdf", "annotations"}
        if not isinstance(case, dict) or set(case) != required_case:
            raise ValueError("Invalid visual-fidelity case")
        identifier = case["id"]
        if type(identifier) is not str or not ID_RE.fullmatch(identifier) or identifier in ids:
            raise ValueError("Invalid or duplicate visual-fidelity case ID")
        ids.add(identifier)
        root = manifest.parent
        source, office, rendered, annotation_path = (
            _file(root, case[key])
            for key in ("source_pdf", "office_file", "rendered_pdf", "annotations")
        )
        if (source.suffix.lower() != ".pdf" or rendered.suffix.lower() != ".pdf"
                or office.suffix.lower() not in FORMATS
                or len({source, office, rendered, annotation_path}) != 4):
            raise ValueError("Invalid or duplicate visual-fidelity evidence path")

        source_sha = _digest(source, MAX_PDF_BYTES)
        office_sha = _digest(office, MAX_OFFICE_BYTES)
        rendered_sha = _digest(rendered, MAX_PDF_BYTES)
        annotation_sha = _digest(annotation_path, MAX_ANNOTATION_BYTES)
        if source_sha in source_shas or office_sha in office_shas or rendered_sha in rendered_shas:
            raise ValueError("Duplicate visual-fidelity evidence across cases")
        source_shas.add(source_sha)
        office_shas.add(office_sha)
        rendered_shas.add(rendered_sha)
        annotation = _validated_annotation(annotation_path, source_sha, office_sha, rendered_sha)
        humans += int(annotation["origin"] == "human_reviewed")
        _office_preflight(office)

        # Check PDF parsing, page dimensions and aggregate raster budget before rendering.
        try:
            _source_pdf_preflight(source)
            source_doc = fitz.open(str(source))
            rendered_doc = fitz.open(str(rendered))
        except Exception:
            raise ValueError("Invalid or unreadable PDF evidence") from None
        try:
            if (source_doc.needs_pass or rendered_doc.needs_pass
                    or not 1 <= source_doc.page_count <= MAX_PAGES_PER_PDF
                    or not 1 <= rendered_doc.page_count <= MAX_PAGES_PER_PDF):
                raise ValueError("Encrypted PDF or page-count budget exceeded")
            corpus_page_budget += source_doc.page_count + rendered_doc.page_count
            if corpus_page_budget > MAX_TOTAL_PAGES:
                raise ValueError("Visual-fidelity page budget exceeded")

            source_dims = [_page_pixel_size(page) for page in source_doc]
            rendered_dims = [_page_pixel_size(page) for page in rendered_doc]
            estimated_pixels = sum(item[2] * item[3] for item in source_dims + rendered_dims)
            corpus_pixel_budget += estimated_pixels
            if corpus_pixel_budget > MAX_TOTAL_PIXELS:
                raise ValueError("Visual-fidelity corpus raster budget exceeded")

            source_tokens, rendered_tokens = [], []
            source_boxes_by_page, rendered_boxes_by_page = [], []
            for page in source_doc:
                tokens, boxes = _page_words(page)
                source_tokens.extend(tokens)
                source_boxes_by_page.append(boxes)
            for page in rendered_doc:
                tokens, boxes = _page_words(page)
                rendered_tokens.extend(tokens)
                rendered_boxes_by_page.append(boxes)
            if not source_tokens or not rendered_tokens:
                raise ValueError("Text layer missing; OCR both PDFs before visual-fidelity evaluation")
            if (len(source_tokens) > MAX_TOKENS_PER_CASE
                    or len(rendered_tokens) > MAX_TOKENS_PER_CASE
                    or corpus_token_budget + len(source_tokens) + len(rendered_tokens) > MAX_TOTAL_TOKENS):
                raise ValueError("Visual-fidelity text-token budget exceeded")
            corpus_token_budget += len(source_tokens) + len(rendered_tokens)
            token_metrics = measure_precision_order(source_tokens, rendered_tokens)
            total_reference_tokens += len(source_tokens)
            total_actual_tokens += len(rendered_tokens)
            matched_tokens += token_metrics["matched_tokens"]
            ordered_matches += token_metrics["ordered_matches"]

            local_delta = abs(source_doc.page_count - rendered_doc.page_count)
            max_page_count_delta = max(max_page_count_delta, local_delta)
            common_pages = min(source_doc.page_count, rendered_doc.page_count)
            for index in range(common_pages):
                sw, sh = float(source_doc[index].rect.width), float(source_doc[index].rect.height)
                rw, rh = float(rendered_doc[index].rect.width), float(rendered_doc[index].rect.height)
                dimension_delta = max(abs(sw - rw) / sw, abs(sh - rh) / sh) * 100
                max_dimension_delta_pct = max(max_dimension_delta_pct, dimension_delta)

                source_image = _render_gray(source_doc[index])
                rendered_image = _render_gray(rendered_doc[index])
                actual_pixels = source_image.width * source_image.height + rendered_image.width * rendered_image.height
                if actual_pixels > MAX_TOTAL_PIXELS:
                    raise ValueError("Rendered page exceeds aggregate pixel budget")
                # Compare a common raster canvas while retaining physical page-size
                # differences as a separate, unresized metric.
                if rendered_image.size != source_image.size:
                    rendered_image = rendered_image.resize(source_image.size, Image.Resampling.BILINEAR)
                difference = ImageChops.difference(source_image, rendered_image)
                histogram = difference.histogram()
                pixel_count = source_image.width * source_image.height
                total_pixel_error += sum(value * amount for value, amount in enumerate(histogram))
                changed = difference.point(lambda value: 255 if value > CHANGE_PIXEL_THRESHOLD else 0)
                changed_pixels += changed.histogram()[255]
                total_pixels += pixel_count
                pages_compared += 1

            matched_boxes, drift_sum, iou_sum = _geometry_matches(
                source_boxes_by_page[:common_pages], rendered_boxes_by_page[:common_pages]
            )
            geometry_matches += matched_boxes
            geometry_drift_sum += drift_sum
            geometry_iou_sum += iou_sum
        finally:
            rendered_doc.close()
            source_doc.close()

        for evidence_path, expected_sha, limit in (
            (source, source_sha, MAX_PDF_BYTES),
            (office, office_sha, MAX_OFFICE_BYTES),
            (rendered, rendered_sha, MAX_PDF_BYTES),
            (annotation_path, annotation_sha, MAX_ANNOTATION_BYTES),
        ):
            if _digest(evidence_path, limit) != expected_sha:
                raise ValueError("Visual-fidelity evidence changed during evaluation")
        evidence_hashes.extend((source_sha, office_sha, rendered_sha, annotation_sha))
        source_pages_total += len(source_dims)
        rendered_pages_total += len(rendered_dims)

    if _digest(manifest, MAX_MANIFEST_BYTES) != manifest_sha:
        raise ValueError("Visual-fidelity manifest changed during evaluation")
    if pages_compared <= 0 or total_pixels <= 0:
        raise ValueError("No comparable PDF page pixels")
    text_precision = matched_tokens / total_actual_tokens if total_actual_tokens else 0.0
    text_recall = matched_tokens / total_reference_tokens if total_reference_tokens else 0.0
    ordered_recall = ordered_matches / total_reference_tokens if total_reference_tokens else 0.0
    mean_pixel_error = total_pixel_error / total_pixels
    changed_fraction = changed_pixels / total_pixels
    mean_drift = geometry_drift_sum / geometry_matches if geometry_matches else 100.0
    mean_iou = geometry_iou_sum / geometry_matches if geometry_matches else 0.0

    failed = []
    checks = (
        (max_page_count_delta <= thresholds["max_page_count_delta"], "max_page_count_delta"),
        (max_dimension_delta_pct <= thresholds["max_page_dimension_delta_pct"], "max_page_dimension_delta_pct"),
        (mean_pixel_error <= thresholds["max_mean_abs_pixel_error"], "max_mean_abs_pixel_error"),
        (changed_fraction <= thresholds["max_changed_pixel_fraction"], "max_changed_pixel_fraction"),
        (text_precision >= thresholds["min_text_precision"], "min_text_precision"),
        (text_recall >= thresholds["min_text_recall"], "min_text_recall"),
        (ordered_recall >= thresholds["min_ordered_token_recall"], "min_ordered_token_recall"),
        (mean_drift <= thresholds["max_mean_word_center_drift_pct"], "max_mean_word_center_drift_pct"),
        (mean_iou >= thresholds["min_mean_word_box_iou"], "min_mean_word_box_iou"),
        (humans >= thresholds["min_human_reviewed"], "min_human_reviewed"),
    )
    failed.extend(name for passed, name in checks if not passed)
    return {
        "schema": REPORT_SCHEMA,
        "status": "FAIL" if failed else "PASS",
        "scope": "PDF page-count, normalized word geometry, grayscale raster and editable-text sequence comparison",
        "visual_fidelity": "sampled_grayscale_raster_and_word_geometry",
        "reading_order": "extractable_text_token_sequence_only_not_human_visual_reading_order",
        "renderer_provenance": "declared_not_attested",
        "text_layer_required": True,
        "screenshot": False,
        "manifest_sha256": manifest_sha,
        "evidence_set_sha256": hashlib.sha256("\n".join(sorted(evidence_hashes)).encode("ascii")).hexdigest(),
        "cases": len(cases),
        "human_reviewed_cases": humans,
        "synthetic_cases": len(cases) - humans,
        "source_pages": source_pages_total,
        "rendered_pages": rendered_pages_total,
        "pages_compared": pages_compared,
        "max_page_count_delta": max_page_count_delta,
        "max_page_dimension_delta_pct": round(max_dimension_delta_pct, 6),
        "mean_abs_pixel_error": round(mean_pixel_error, 6),
        "changed_pixel_fraction": round(changed_fraction, 6),
        "reference_tokens": total_reference_tokens,
        "actual_tokens": total_actual_tokens,
        "matched_tokens": matched_tokens,
        "text_precision": round(text_precision, 6),
        "text_recall": round(text_recall, 6),
        "ordered_token_recall": round(ordered_recall, 6),
        "matched_word_boxes": geometry_matches,
        "mean_word_center_drift_pct": round(mean_drift, 6),
        "mean_word_box_iou": round(mean_iou, 6),
        "thresholds": thresholds,
        "failed_thresholds": failed,
    }


def safe_visual_fidelity_receipt(report):
    """Whitelist and validate a privacy-preserving V558 report before GUI/export."""
    if type(report) is not dict or set(report) != REPORT_KEYS:
        raise ValueError("Invalid visual-fidelity receipt schema")
    if report["schema"] != REPORT_SCHEMA or report["status"] not in ("PASS", "FAIL"):
        raise ValueError("Unsupported visual-fidelity receipt")
    if report["renderer_provenance"] != "declared_not_attested" or report["screenshot"] is not False:
        raise ValueError("Invalid visual-fidelity receipt provenance")
    for name in ("manifest_sha256", "evidence_set_sha256"):
        _sha(report[name], name)
    integer_fields = (
        "cases", "human_reviewed_cases", "synthetic_cases", "source_pages",
        "rendered_pages", "pages_compared", "max_page_count_delta",
        "reference_tokens", "actual_tokens", "matched_tokens", "matched_word_boxes",
    )
    for name in integer_fields:
        if type(report[name]) is not int or report[name] < 0:
            raise ValueError("Invalid visual-fidelity receipt count")
    rate_fields = (
        "max_page_dimension_delta_pct", "mean_abs_pixel_error",
        "changed_pixel_fraction", "text_precision", "text_recall",
        "ordered_token_recall", "mean_word_center_drift_pct", "mean_word_box_iou",
    )
    ranges = {
        "max_page_dimension_delta_pct": (0, 100),
        "mean_abs_pixel_error": (0, 255),
        "changed_pixel_fraction": (0, 1),
        "text_precision": (0, 1),
        "text_recall": (0, 1),
        "ordered_token_recall": (0, 1),
        "mean_word_center_drift_pct": (0, 100),
        "mean_word_box_iou": (0, 1),
    }
    for name in rate_fields:
        low, high = ranges[name]
        _finite_number(report[name], name, low, high)
    thresholds = _thresholds(report["thresholds"])
    if type(report["failed_thresholds"]) is not list or any(
        type(name) is not str or name not in THRESHOLD_KEYS for name in report["failed_thresholds"]
    ):
        raise ValueError("Invalid visual-fidelity receipt threshold list")
    if type(report["text_layer_required"]) is not bool or report["text_layer_required"] is not True:
        raise ValueError("Unsupported visual-fidelity receipt scope")
    if report["scope"] != "PDF page-count, normalized word geometry, grayscale raster and editable-text sequence comparison":
        raise ValueError("Unsupported visual-fidelity receipt scope")
    if report["visual_fidelity"] != "sampled_grayscale_raster_and_word_geometry":
        raise ValueError("Unsupported visual-fidelity receipt scope")
    if report["reading_order"] != "extractable_text_token_sequence_only_not_human_visual_reading_order":
        raise ValueError("Unsupported visual-fidelity receipt scope")
    if report["cases"] != report["human_reviewed_cases"] + report["synthetic_cases"]:
        raise ValueError("Inconsistent visual-fidelity receipt counts")
    if thresholds["min_human_reviewed"] > report["human_reviewed_cases"] and report["status"] == "PASS":
        raise ValueError("Inconsistent visual-fidelity receipt status")
    # Round-trip through strict JSON-compatible primitives without exposing input paths.
    clean = json.loads(json.dumps(report, allow_nan=False, ensure_ascii=False))
    return clean


def format_visual_fidelity_summary(report):
    report = safe_visual_fidelity_receipt(report)
    status = "CONFORME" if report["status"] == "PASS" else "NON CONFORME"
    lines = [
        "Fidelite PDF / Word / Excel / PowerPoint : " + status,
        f"Pages comparees : {report['pages_compared']} (source {report['source_pages']}, rendu {report['rendered_pages']})",
        f"Erreur raster moyenne (niveaux de gris) : {report['mean_abs_pixel_error']:.3f} / 255",
        f"Pixels modifies (> {CHANGE_PIXEL_THRESHOLD}/255) : {report['changed_pixel_fraction'] * 100:.2f} %",
        f"Precision texte : {report['text_precision'] * 100:.2f} %",
        f"Rappel texte : {report['text_recall'] * 100:.2f} %",
        f"Rappel de l'ordre d'extraction : {report['ordered_token_recall'] * 100:.2f} %",
        f"Derive moyenne des centres de mots : {report['mean_word_center_drift_pct']:.3f} % de diagonale normalisee",
        f"IoU moyenne des boites de mots : {report['mean_word_box_iou']:.3f}",
        f"Difference maximale de dimensions de page : {report['max_page_dimension_delta_pct']:.3f} %",
        "Provenance du moteur de rendu : declaree, non attestee.",
        "Ces mesures ne prouvent pas la fidelite visuelle humaine ni la provenance du PDF de rendu.",
    ]
    if report["failed_thresholds"]:
        lines.append("Seuils en echec : " + ", ".join(report["failed_thresholds"]))
    else:
        lines.append("Tous les seuils configures sont respectes.")
    return "\n".join(lines)


def serialize_visual_fidelity_receipt(report):
    return json.dumps(safe_visual_fidelity_receipt(report), sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Bounded PDF/Office visual and editable-text fidelity comparison"
    )
    parser.add_argument("manifest", type=Path, help="SHA-bound corpus JSON")
    parser.add_argument("--receipt", type=Path, help="new private JSON receipt path; never overwrites")
    args = parser.parse_args(argv)
    try:
        report = evaluate_office_visual_fidelity_corpus(args.manifest)
        serialized = serialize_visual_fidelity_receipt(report)
        if args.receipt:
            with args.receipt.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
        print(serialized, end="")
        return 0 if report["status"] == "PASS" else 2
    except Exception as exc:
        # Keep local paths, PDF content and archive member names out of CLI errors.
        print(json.dumps({
            "schema": REPORT_SCHEMA,
            "status": "ERROR",
            "reason": type(exc).__name__,
        }, sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
