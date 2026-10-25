"""Bounded token precision and extraction-order metrics for editable Office outputs.
The order score is an exact longest-common-subsequence (LCS) comparison against
annotated phrase order; it is not visual reading-order or layout validation.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

MAX_TOKENS_PER_CASE = 5000


def measure_precision_order(expected_tokens: Sequence[str],
                            actual_tokens: Sequence[str]) -> dict:
    """Measure multiset precision/recall/F1 and ordered-token recall.

    The expected sequence is formed by concatenating annotation phrases in their
    declared order. The actual sequence follows OOXML paragraph/cell/shape
    traversal order. Each expected occurrence is matched at most once. A
    bit-parallel LCS recurrence computes the exact ordered match count with
    bounded integer bitsets instead of quadratic dynamic-programming memory.
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

    # Bit-parallel LCS: bit i marks occurrences of an actual token at position i.
    # This is exact for reordered sequences such as expected A,B,C / actual B,C,A,
    # where a greedy forward scan would incorrectly report only one ordered match.
    actual_position_masks = {}
    for index, token in enumerate(actual_tokens):
        actual_position_masks[token] = actual_position_masks.get(token, 0) | (1 << index)
    state = 0
    for token in expected_tokens:
        x = state | actual_position_masks.get(token, 0)
        y = (state << 1) | 1
        state = x & ~(x - y)
    ordered_matches = state.bit_count()
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
