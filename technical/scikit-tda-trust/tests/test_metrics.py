"""Corrected persistence-gap ratio r_k = p_k / p_{k+1} (R-1).

The rank k is the KNOWN GROUND-TRUTH rank of a synthetic dataset (annulus 1,
figure-eight 2); r_k is not a universal automatic loop-counting rule — these
tests verify the arithmetic and the edge cases, never that rule.
"""
import numpy as np
import pytest

from pipeline import gap_ratio, h1_persistences, h0_prominent_merges


def test_basic_ratio():
    assert gap_ratio([10.0, 1.0], 1) == pytest.approx(10.0)


def test_unsorted_input_is_sorted_descending():
    assert gap_ratio([1.0, 10.0], 1) == pytest.approx(10.0)


def test_figure_eight_regime():
    """Two co-dominant classes: r_1 ~ 1 (expected), r_2 separates signal."""
    p = [0.481, 0.4807, 0.0493]
    assert gap_ratio(p, 1) == pytest.approx(0.481 / 0.4807, rel=1e-3)
    assert gap_ratio(p, 2) == pytest.approx(0.4807 / 0.0493, rel=1e-3)


def test_annulus_regime():
    p = [1.496, 0.077, 0.073]
    assert gap_ratio(p, 1) == pytest.approx(1.496 / 0.077, rel=1e-3)


def test_insufficient_classes_returns_none():
    assert gap_ratio([3.0, 1.0], 2) is None
    assert gap_ratio([], 1) is None
    assert gap_ratio([5.0], 1) is None


def test_zero_persistence_returns_none():
    """A zero/infinite-death noise class must not create a spurious ratio."""
    assert gap_ratio([5.0, 0.0], 1) is None
    assert gap_ratio([5.0, 3.0, 0.0], 2) is None


def test_invalid_rank_raises():
    with pytest.raises(ValueError, match=">= 1"):
        gap_ratio([1.0, 2.0], 0)


def test_numpy_and_list_inputs_agree():
    a = [4.0, 2.0, 1.0]
    assert gap_ratio(a, 1) == gap_ratio(np.array(a), 1)


def test_h1_persistences_sorted():
    d = np.array([[0.0, 1.0], [0.5, 0.6], [0.1, 0.9]])
    pers = h1_persistences(d)  # persistences 1.0, 0.1, 0.8
    assert list(pers) == pytest.approx([1.0, 0.8, 0.1])


def test_h0_prominent_merges_three_blob_regime():
    """Two late merges above half the max finite persistence."""
    d0 = np.array([[0.0, 1.96], [0.0, 1.61], [0.0, 0.44], [0.0, np.inf]])
    assert h0_prominent_merges(d0, fraction=0.5) == 2
    # degenerate: no finite classes
    assert h0_prominent_merges(np.array([[0.0, np.inf]])) == 0
