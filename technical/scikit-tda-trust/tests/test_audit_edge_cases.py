"""Independent-audit edge-case tests (added 2026-10-28; not part of the original 60).

Targets behaviours the original suite did not pin down: gap ratio with inf / NaN / zero /
empty inputs, H1 persistences with infinite deaths, S symmetry/triangle-inequality
counterexample, cyclomatic-number identities, and gap-ratio scale invariance (the property
the leave-one-year-out analysis relies on).
"""
import math
import numpy as np
import pytest

from src.pipeline import gap_ratio, h1_persistences, mapper_structure_stats
from src.similarity import similarity, jaccard


def test_gap_ratio_basic_and_unsorted():
    assert gap_ratio([1.0, 4.0, 2.0], 1) == pytest.approx(2.0)      # 4/2
    assert gap_ratio([1.0, 4.0, 2.0], 2) == pytest.approx(2.0)      # 2/1


def test_gap_ratio_undefined_cases_return_none():
    assert gap_ratio([], 1) is None
    assert gap_ratio([3.0], 1) is None
    assert gap_ratio([3.0, 0.0], 1) is None          # zero denominator
    assert gap_ratio([3.0, -1.0], 1) is None         # non-positive denominator


def test_gap_ratio_latent_edge_behaviour_is_pinned():
    """Documented latent behaviour (not triggered by any data in this project: ripser is called
    without a threshold, so H1 deaths are finite). Pinned here so a change is noticed.
    inf / finite -> inf; inf / inf -> nan (RuntimeWarning); NaN input -> nan."""
    import warnings
    assert gap_ratio([np.inf, 2.0, 1.0], 1) == math.inf
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        assert math.isnan(gap_ratio([np.inf, np.inf, 1.0], 1))
        assert math.isnan(gap_ratio([np.nan, 2.0, 1.0], 1))


def test_gap_ratio_rank_must_be_positive():
    with pytest.raises(ValueError):
        gap_ratio([1.0, 2.0], 0)


def test_gap_ratio_is_scale_invariant():
    p = np.array([2.7, 1.1, 0.4, 0.3])
    assert gap_ratio(p, 1) == pytest.approx(gap_ratio(37.5 * p, 1))


def test_h1_persistences_empty_and_sorted():
    assert len(h1_persistences(np.empty((0, 2)))) == 0
    out = h1_persistences(np.array([[0.0, 0.2], [0.1, 0.9], [0.3, 0.5]]))
    assert list(out) == sorted(out, reverse=True)


def test_h1_persistences_infinite_death_propagates():
    out = h1_persistences(np.array([[0.1, np.inf], [0.2, 0.5]]))
    assert math.isinf(out[0])


def test_similarity_triangle_inequality_counterexample():
    A = [frozenset({1, 2, 3})]
    B = [frozenset({1, 2, 3}), frozenset({4, 5, 6})]
    C = [frozenset({4, 5, 6})]
    d = lambda x, y: 1 - similarity(x, y)
    assert d(A, C) > d(A, B) + d(B, C)               # 1 - S is not a metric


def test_similarity_not_injective_on_graphs():
    one = [frozenset({1, 2}), frozenset({3})]
    dup = [frozenset({1, 2}), frozenset({3}), frozenset({3})]
    assert similarity(one, dup) == pytest.approx(1.0)  # S = 1 does not imply identical graphs


def test_jaccard_empty_convention():
    assert jaccard(frozenset(), frozenset()) == 1.0


def test_cyclomatic_identity_on_known_graphs():
    # ring of 5 nodes -> cyclomatic 1; two disjoint triangles -> cyclomatic 2, 2 components
    ring = {"nodes": {f"n{i}": [i] for i in range(5)},
            "links": {f"n{i}": [f"n{(i+1) % 5}"] for i in range(5)}}
    st = mapper_structure_stats(ring)
    assert (st["n_nodes"], st["n_edges"], st["n_components"], st["cyclomatic_number"]) == (5, 5, 1, 1)
    two = {"nodes": {f"n{i}": [i] for i in range(6)},
           "links": {"n0": ["n1"], "n1": ["n2"], "n2": ["n0"], "n3": ["n4"], "n4": ["n5"], "n5": ["n3"]}}
    st = mapper_structure_stats(two)
    assert (st["n_components"], st["cyclomatic_number"]) == (2, 2)
