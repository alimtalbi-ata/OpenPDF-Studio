"""Bounded token precision and extraction-order metrics for editable Office outputs.
The order score is a subsequence match against annotated phrase order; it is not
visual reading-order or layout validation. Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
from typing import Sequence

MAX_TOKENS_PER_CASE = 5000


def measure_precision_order(expected_tokens: Sequence[str],
                            actual_tokens: Sequence[str]) -> dict:
    """Measure multiset precision/recall/F1 and ordered-token recall.

    The expected sequence is formed by concatenating annotation phrases in their
    declared order. The actual sequence follows OOXML paragraph/cell/shape
    traversal order. Each expected occurrence is matched at most once. An
    earliest-next-occurrence scan gives a deterministic longest common
    subsequence length without quadratic dynamic-programming memory.
    """
    if not isinstance(expected_tokens, (list, tuple)) or not expected_tokens:
        raise ValueError("At least one expected token is required")
    if not isinstance(actual_tokens, (list, tuple)):
        raise ValueError("Actual token sequence must be a list or tuple")
    if len(expected_tokens) > MAX_TOKENS_PER_CASE or len(actual_tokens) > MAX_TOKENS_PER_CASE:
        raise ValueError("Office precision/order token budget exceeded")
    if any(type(token) is not str or not token for token in expected_tokens):
        raise ValueError("Invalid expected token")
    if any(type(token) is not str or not token for token in actual_tokens):
        raise ValueError("Invalid actual token")

    expected_counts = Counter(expected_tokens)
    actual_counts = Counter(actual_tokens)
    expected_total = len(expected_tokens)
    actual_total = len(actual_tokens)
    matched = sum(min(count, actual_counts[token])
                  for token, count in expected_counts.items())
    precision = matched / actual_total if actual_total else 0.0
    recall = matched / expected_total
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    positions = defaultdict(list)
    for index, token in enumerate(actual_tokens):
        positions[token].append(index)
    cursor = -1
    ordered_matches = 0
    for token in expected_tokens:
        occurrences = positions.get(token)
        if not occurrences:
            continue
        candidate = bisect_right(occurrences, cursor)
        if candidate < len(occurrences):
            cursor = occurrences[candidate]
            ordered_matches += 1
    ordered_recall = ordered_matches / expected_total
    return {
        "actual_tokens": actual_total,
        "matched_tokens": matched,
        "unexpected_tokens": actual_total - matched,
        "token_precision": precision,
        "token_recall": recall,
        "token_f1": f1,
        "ordered_matches": ordered_matches,
        "ordered_token_recall": ordered_recall,
    }
