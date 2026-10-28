#!/usr/bin/env python3
"""Stage 4 Part C — Mapper input-sampling stability (synthetic data).

What varies here: the SAMPLED OBSERVATIONS (the same 30 deterministic 80%
subsamples as Part B — identical seed rule). What does NOT vary: the Mapper
configuration, fixed at the documented baseline reference settings
(n_cubes=10, perc_overlap=0.35, PCA-1 lens, KMeans k=2 seed 42, n_init 10).

This is DISTINCT from baseline E2 parameter sensitivity (same data, different
cover parameters). The scientific question is whether structural
interpretations are stable across input subsampling at fixed parameters —
not whether one graph has a universally correct score.

Per replicate, recorded with full traceability:
  * the subsample seed and the global indices of the sampled observations;
  * node memberships expressed in GLOBAL point identity (indices into the
    full baseline point cloud), never local subsample rows — local row
    indices from different subsamples are never compared;
  * node, edge and connected-component counts;
  * the cyclomatic number, DEFINED as  E - V + C  (number of independent
    cycles of an undirected graph: edges minus vertices plus components);
  * baseline cycle-basis summaries (max/mean basis cycle length), reported
    only as additional structure descriptors (graph cycles are not
    automatically topological loops — baseline caveat);
  * the custom membership-Jaccard S vs the full-data reference graph,
    computed on GLOBAL point identities. S remains an EXPLORATORY overlap
    indicator only (greedy, edge-blind, not a metric, not normalized for
    node count) and is never the sole stability measure.

The reference graph is the baseline E1 full-data Mapper graph: rebuilt with
the same pinned configuration and verified membership-identical to the E1
saved memberships JSON before any comparison is made.

Usage: python extensions/stability/scripts/run_mapper_resampling.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import yaml

EXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.pipeline import mapper_run, mapper_structure_stats  # noqa: E402
from src.shapes import make_shape  # noqa: E402
from src.similarity import (  # noqa: E402
    SIMILARITY_CAVEAT,
    memberships_from_json,
    similarity,
)

RESULTS = EXT_ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)  # independent-rebuild fix: fresh trees lack the dir
E1_DATA = REPO_ROOT / "results" / "e1" / "data"
E1_MEMB = REPO_ROOT / "results" / "e1"

CYCLOMATIC_DEFINITION = (
    "cyclomatic number = E - V + C (edges minus vertices plus connected "
    "components) = the number of independent cycles of an undirected graph; "
    "graph cycles are not automatically topological loops in the data "
    "(baseline no-loop control caveat).")


def subsample_indices(n: int, size: int, seed: int) -> np.ndarray:
    """Same seed rule as Part B — identical subsamples by construction."""
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n, size=size, replace=False))


def memberships_global(graph: dict, sub_idx: np.ndarray) -> dict[str, list[int]]:
    """Node memberships with LOCAL subsample rows mapped to GLOBAL point ids.

    kmapper node memberships index into the rows of the input (subsample)
    array; the i-th sampled observation is global point sub_idx[i]. All
    cross-graph comparisons in this extension use these global ids.
    """
    out = {}
    for name, members in graph["nodes"].items():
        loc = np.asarray(members, dtype=int)
        glob = sorted(int(sub_idx[i]) for i in loc)
        out[name] = glob
    return out


def graph_from_memberships(nodes: dict[str, list[int]],
                            links: dict[str, list[str]]) -> nx.Graph:
    G = nx.Graph()
    for name, members in nodes.items():
        G.add_node(name, members=members)
    for a, others in links.items():
        for b in others:
            G.add_edge(a, b)
    return G


def main() -> int:
    t_start = time.perf_counter()
    cfg = yaml.safe_load((EXT_ROOT / "configs" / "stability.yaml").read_text())
    shapes_cfg = yaml.safe_load((REPO_ROOT / "configs" / "shapes.yaml").read_text())
    rs = cfg["resampling"]
    mc = cfg["mapper"]
    n_rep = int(rs["n_replicates"])
    frac = float(rs["fraction"])
    seed_base = int(rs["seed_base"])

    out: dict = {
        "step": "run_mapper_resampling",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": {
            "n_replicates": n_rep,
            "fraction": frac,
            "seed_base": seed_base,
            "seed_offsets": {k: int(v) for k, v in rs["seed_offsets"].items()},
            "seed_rule": "seed(shape, rep i) = seed_base + seed_offsets[shape] + i "
                         "(identical subsamples to run_ph_resampling.py)",
            "mapper_fixed": {
                "n_cubes": int(mc["n_cubes"]),
                "perc_overlap": float(mc["perc_overlap"]),
                "kmeans": {k: int(v) for k, v in mc["kmeans"].items()},
                "lens": str(mc["lens"]),
            },
            "varied": "input sample only (NOT cover parameters; see baseline E2 "
                      "for the parameter-sensitivity question)",
        },
        "cyclomatic_number_definition": CYCLOMATIC_DEFINITION,
        "similarity_caveat": SIMILARITY_CAVEAT,
        "global_identity_note": (
            "All membership comparisons use GLOBAL point ids (indices into the "
            "full baseline point cloud). Local subsample row indices from "
            "different subsamples are never compared."),
        "shapes": {},
    }

    for shape in cfg["shapes"]:
        params = shapes_cfg["shapes"][shape]
        X = make_shape(shape, params)
        saved = np.load(E1_DATA / f"{shape}.npy")
        if not np.allclose(X, saved, rtol=0.0, atol=1e-12):  # independent-rebuild: libm trig differs by 1 ULP across platforms
            raise SystemExit(
                f"BUILD ERROR: regenerated {shape} differs from the baseline "
                "E1 saved point cloud — refusing to proceed.")
        n = len(X)
        size = int(round(frac * n))

        # Reference: rebuild with the pinned config; verify against E1 saved.
        t0 = time.perf_counter()
        ref_graph = mapper_run(X, int(mc["n_cubes"]), float(mc["perc_overlap"]),
                               seed=int(mc["kmeans"]["random_state"]),
                               n_clusters=int(mc["kmeans"]["n_clusters"]))
        t_ref = time.perf_counter() - t0
        e1_memb = json.loads((E1_MEMB / f"{shape}_mapper_memberships.json").read_text())
        ref_nodes = {k: [int(i) for i in v] for k, v in ref_graph["nodes"].items()}
        if sorted(map(sorted, ref_nodes.values())) != \
                sorted(map(sorted, ([list(v) for v in e1_memb["nodes"].values()]))):
            raise SystemExit(
                f"BUILD ERROR: rebuilt reference Mapper graph for {shape} does "
                "not match the baseline E1 saved memberships — refusing to "
                "proceed.")
        ref_stats = mapper_structure_stats(ref_graph)
        ref_memb_sets = [frozenset(v) for v in ref_nodes.values()]
        print(f"{shape}: reference rebuilt + verified vs E1 "
              f"({ref_stats['n_nodes']}n {ref_stats['n_edges']}e "
              f"{ref_stats['n_components']}c cyc={ref_stats['cyclomatic_number']})")

        reps = []
        t_shape = time.perf_counter()
        for i in range(n_rep):
            seed = seed_base + int(rs["seed_offsets"][shape]) + i
            idx = subsample_indices(n, size, seed)
            t0 = time.perf_counter()
            graph = mapper_run(X[idx], int(mc["n_cubes"]),
                               float(mc["perc_overlap"]),
                               seed=int(mc["kmeans"]["random_state"]),
                               n_clusters=int(mc["kmeans"]["n_clusters"]))
            t_map = time.perf_counter() - t0
            stats = mapper_structure_stats(graph)
            glob = memberships_global(graph, idx)
            memb_sets = [frozenset(v) for v in glob.values()]
            # S vs reference, GLOBAL point identities both sides
            s_val = similarity(memb_sets, ref_memb_sets)
            reps.append({
                "rep": i,
                "seed": int(seed),
                "indices": [int(v) for v in idx],
                "n_points": size,
                "structure": stats,
                "memberships_global": glob,
                "links": {a: list(b) for a, b in graph["links"].items()},
                "membership_jaccard_S_vs_reference": round(s_val, 4),
                "mapper_time_s": round(t_map, 3),
            })
        t_shape_elapsed = time.perf_counter() - t_shape

        out["shapes"][shape] = {
            "n_full": n,
            "subsample_size": size,
            "reference": {
                "structure": ref_stats,
                "memberships_global": ref_nodes,
                "links": {a: list(b) for a, b in ref_graph["links"].items()},
                "rebuild_time_s": round(t_ref, 3),
                "verified_identical_to_e1_saved": True,
            },
            "replicates": reps,
            "runtime_s_total": round(t_shape_elapsed, 1),
        }
        cyc = [r["structure"]["cyclomatic_number"] for r in reps]
        ncomp = [r["structure"]["n_components"] for r in reps]
        print(f"  30 reps in {t_shape_elapsed:.1f}s; cyclomatic "
              f"{min(cyc)}..{max(cyc)}, components {min(ncomp)}..{max(ncomp)}")

    out["runtime_s_total"] = round(time.perf_counter() - t_start, 1)
    (RESULTS / "mapper_resampling.json").write_text(json.dumps(out, indent=1))
    print(f"saved {RESULTS / 'mapper_resampling.json'} "
          f"(total {out['runtime_s_total']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
