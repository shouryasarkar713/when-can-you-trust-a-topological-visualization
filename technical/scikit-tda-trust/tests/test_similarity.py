"""Membership-overlap similarity S — verified mathematical properties (R-2).

S is a custom exploratory overlap indicator, NOT a canonical metric. These
tests pin down: symmetry, bounds, identity, the CORRECTED S=1 condition,
edge-blindness, and an exact triangle-inequality counterexample for 1-S.
"""
import pytest

from similarity import (jaccard, memberships_equal, memberships_from_graph,
                        similarity, similarity_of_graphs)

FS = frozenset


def test_jaccard_basics():
    assert jaccard(FS({1, 2, 3}), FS({1, 2, 3})) == 1.0
    assert jaccard(FS({1, 2}), FS({3, 4})) == 0.0
    assert jaccard(FS({1, 2}), FS({2, 3})) == pytest.approx(1 / 3)
    assert jaccard(FS(), FS()) == 1.0          # convention: both empty match
    assert jaccard(FS(), FS({1})) == 0.0


def test_symmetry_and_bounds():
    a = [FS({1, 2, 3}), FS({4, 5})]
    b = [FS({1, 2}), FS({3, 4, 5, 6}), FS({7})]
    s1, s2 = similarity(a, b), similarity(b, a)
    assert s1 == s2
    assert 0.0 <= s1 <= 1.0


def test_identity():
    g = [FS({1, 2, 3}), FS({4, 5}), FS({6})]
    assert similarity(g, g) == 1.0


def test_corrected_s_equals_one_condition():
    """S = 1 IFF the same DISTINCT membership sets appear in both graphs.

    Node multiplicities may differ (duplicated memberships) — the blueprint's
    original 'S = 1 exactly when the node sets are identical' is corrected
    here. 3 nodes (one duplicated) vs 2 nodes: S = 1.
    """
    dup = [FS({1, 2, 3, 4}), FS({1, 2, 3, 4}), FS({5, 6})]
    plain = [FS({1, 2, 3, 4}), FS({5, 6})]
    assert similarity(dup, plain) == 1.0
    assert len(dup) != len(plain)  # different node counts, same S


def test_s_below_one_when_distinct_sets_differ():
    a = [FS({1, 2, 3}), FS({4, 5})]
    b = [FS({1, 2, 3}), FS({4, 5, 6})]
    assert similarity(a, b) < 1.0
    # adding a genuinely new membership set also drops S below 1
    c = a + [FS({9})]
    assert similarity(a, c) < 1.0


def test_edge_blindness():
    """S is a function of memberships only; edges are invisible to it.

    (The graphs carried into similarity() are membership lists; this test
    documents that two graphs with identical memberships but different links
    cannot be distinguished by S.)
    """
    m = [FS({1, 2}), FS({3}), FS({4, 5})]
    assert similarity(m, list(m)) == 1.0  # same memberships, any link structure


def test_triangle_inequality_violation_exact():
    """1 - S is NOT a metric: d(A,C) > d(A,B) + d(B,C).

    Exact expected values (hand-computed, verified):
      A = [{1,2,3}], B = [{1,2,3},{4,5,6}], C = [{4,5,6}]
      S(A,B) = (1 + 0.5)/2 = 0.75 ; S(B,C) = 0.75 ; S(A,C) = 0
      d(A,C) = 1.0 > d(A,B) + d(B,C) = 0.5
    """
    A = [FS({1, 2, 3})]
    B = [FS({1, 2, 3}), FS({4, 5, 6})]
    C = [FS({4, 5, 6})]
    sAB, sBC, sAC = similarity(A, B), similarity(B, C), similarity(A, C)
    assert sAB == pytest.approx(0.75)
    assert sBC == pytest.approx(0.75)
    assert sAC == pytest.approx(0.0)
    assert (1 - sAC) > (1 - sAB) + (1 - sBC)


def test_greedy_understatement_possible():
    """Greedy best-match can understate similarity (limitation, by design)."""
    fine = [FS({1, 2}), FS({3, 4}), FS({5, 6})]
    coarse = [FS({1, 2, 3, 4, 5, 6})]
    s = similarity(fine, coarse)
    assert 0.0 < s < 1.0  # same points, but memberships do not line up


def test_empty_graph_conventions():
    assert similarity([], []) == 0.0  # degenerate: no nodes to match
    assert similarity([], [FS({1})]) == 0.0


def test_determinism_control_helper():
    g = {"nodes": {"n1": [1, 2, 3], "n2": [4, 5]}, "links": {}}
    h = {"nodes": {"nX": [4, 5], "nY": [1, 2, 3]}, "links": {}}
    assert memberships_equal(memberships_from_graph(g), memberships_from_graph(h))
    assert similarity_of_graphs(g, g) == 1.0
    with pytest.raises(ValueError, match="kmapper graph"):
        memberships_from_graph({})
