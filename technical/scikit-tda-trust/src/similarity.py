"""Membership-overlap similarity S between two Mapper graphs.

STATUS (R-2 in IMPLEMENTATION_NOTES.md): S is a CUSTOM EXPLORATORY OVERLAP
INDICATOR. It is not a canonical graph metric, not a distance, and not a
substitute for structural statistics or representative graphs.

Definition. For Mapper graphs G1, G2 whose nodes carry membership sets
N1, N2 (each node = set of point indices in its cluster), with
J(A, B) = |A ∩ B| / |A ∪ B| (J(∅, ∅) := 1 by convention):

    S(G1, G2) = 1/2 * [ mean_{n ∈ N1} ( max_{m ∈ N2} J(n, m) )
                      + mean_{m ∈ N2} ( max_{n ∈ N1} J(m, n) ) ]

Verified mathematical properties (unit-tested in tests/test_similarity.py):

* Symmetric: S(G1, G2) = S(G2, G1); bounded: 0 ≤ S ≤ 1; S(G, G) = 1.
* CORRECTED S = 1 CONDITION: S = 1 if and only if the two graphs have the
  same SET OF DISTINCT membership sets. Node multiplicities may differ
  (duplicate memberships) and edges may differ — S = 1 does NOT imply the
  graphs are identical. Counterexample kept in the tests: 3 nodes with a
  duplicated membership vs 2 nodes score S = 1.
* NOT a metric: 1 − S violates the triangle inequality (exact counterexample
  in the tests: A = [{1,2,3}], B = [{1,2,3},{4,5,6}], C = [{4,5,6}] gives
  d(A,C) = 1.0 > d(A,B) + d(B,C) = 0.5).
* Edge-blind: S ignores edges, components, and layout entirely.
* Greedy: per-node best match, not an optimal assignment — can understate
  similarity.
* Unnormalized for node count: DO NOT rank graphs across different cover
  resolutions (different n_cubes) by S.

Interpretation guidance: S is read only against a pre-specified reference
cell of the SAME shape and SAME resolution family, always beside node/edge/
component counts, cycle statistics, and representative panels.
"""
from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import numpy as np

MembershipSets = list[frozenset[int]]


def jaccard(a: frozenset, b: frozenset) -> float:
    """Jaccard overlap of two membership sets; J(∅, ∅) := 1."""
    union = len(a | b)
    if union == 0:
        return 1.0
    return len(a & b) / union


def memberships_from_graph(graph: Mapping) -> MembershipSets:
    """Extract node membership sets from a kmapper graph dict.

    graph["nodes"] maps node name -> sequence of point indices.
    """
    nodes = graph.get("nodes")
    if nodes is None:
        raise ValueError(
            "Not a kmapper graph dict: missing 'nodes' key. "
            f"Got keys: {sorted(graph) if isinstance(graph, Mapping) else type(graph)}.")
    return [frozenset(v) for v in nodes.values()]


def memberships_from_json(nodes: Mapping[str, Sequence[int]]) -> MembershipSets:
    """Rebuild membership sets from a JSON-serialised {'name': [indices]} map."""
    return [frozenset(v) for v in nodes.values()]


def _mean_best_forward(a: MembershipSets, b: MembershipSets) -> float:
    """Mean over nodes of A of the best Jaccard match among B's nodes.

    Conventions for degenerate cases: an empty node list scores 0.0 (no
    nodes to match), and a nonempty list has no candidates when B is empty,
    also 0.0. kmapper graphs always have at least one node, so these cases
    exist only to keep the helper total.
    """
    if not a or not b:
        return 0.0
    return float(np.mean([max(jaccard(s, t) for t in b) for s in a]))


def similarity(m1: MembershipSets, m2: MembershipSets) -> float:
    """Symmetric mean of best-membership-Jaccard overlaps (see module docstring)."""
    f12 = _mean_best_forward(m1, m2)
    f21 = _mean_best_forward(m2, m1)
    return (f12 + f21) / 2.0


def similarity_of_graphs(g1: Mapping, g2: Mapping) -> float:
    """Convenience wrapper over kmapper graph dicts."""
    return similarity(memberships_from_graph(g1), memberships_from_graph(g2))


def memberships_equal(m1: MembershipSets, m2: MembershipSets) -> bool:
    """Exact multiset equality of membership sets (determinism control)."""
    return sorted(map(sorted, m1)) == sorted(map(sorted, m2))


#: Printed beside every table that includes S (blueprint limitation list).
SIMILARITY_CAVEAT = (
    "S is a custom exploratory overlap indicator (symmetric mean of best "
    "membership-Jaccard matches), not a metric and not a canonical Mapper "
    "graph similarity; it is greedy, edge-blind, and not normalized for node "
    "count, so it must not be used to rank graphs across different cover "
    "resolutions. Read it only against the pre-specified reference cell, "
    "beside component counts and representative graphs."
)
