#!/usr/bin/env python3
"""Extension D5 — two quantitative checks of caveats stated in the report.

(1) S ceiling: for each of the 30 saved annulus subsamples, restrict the reference graph's node
    memberships to the sampled points and compute S against the full reference. This is the
    largest S a subsample graph could attain by sampling alone.
(2) H0 cardinality: H0 Wasserstein of subsample A vs the 500-point reference (399 vs 499 finite
    classes) compared with subsample A vs subsample B (399 vs 399).
"""
import json, sys
from pathlib import Path
import numpy as np
import yaml

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
sys.path.insert(0, str(REPO))
from src.similarity import similarity  # noqa: E402
from src.pipeline import compute_ph  # noqa: E402


def main():
    cfg = yaml.safe_load((EXT / "configs" / "controls.yaml").read_text())["caveat_checks"]
    shape = cfg["s_ceiling"]["shape"]
    mc = json.loads((REPO / "extensions/stability/results/mapper_resampling.json").read_text())
    ref_memb = json.loads((REPO / "results/e1" / f"{shape}_mapper_memberships.json").read_text())
    ref_nodes = ref_memb["nodes"] if "nodes" in ref_memb else ref_memb
    ref_sets = [frozenset(v) for v in ref_nodes.values()]
    out = {"s_ceiling": {"shape": shape, "values": []}, "h0_cardinality": {}}
    for rep in mc["shapes"][shape]["replicates"]:
        keep = set(rep["indices"])
        restricted = [frozenset(x for x in s if x in keep) for s in ref_sets]
        restricted = [s for s in restricted if s]
        out["s_ceiling"]["values"].append(round(similarity(restricted, ref_sets), 4))
        out["s_ceiling"].setdefault("reported_S", []).append(rep["membership_jaccard_S_vs_reference"])
    v = out["s_ceiling"]["values"]
    out["s_ceiling"]["summary"] = {"median": round(float(np.median(v)), 4), "min": min(v), "max": max(v),
                                   "reported_S_median": round(float(np.median(out["s_ceiling"]["reported_S"])), 4)}
    from persim import wasserstein, bottleneck
    from src.shapes import make_shape
    shp = yaml.safe_load((REPO / "configs/shapes.yaml").read_text())["shapes"][shape]
    X = make_shape(shape, shp)
    ph = compute_ph(X, 1)["dgms"][0]
    ia = np.array(mc["shapes"][shape]["replicates"][cfg["h0_cardinality"]["rep_a"]]["indices"])
    ib = np.array(mc["shapes"][shape]["replicates"][cfg["h0_cardinality"]["rep_b"]]["indices"])
    pa, pb = compute_ph(X[ia], 1)["dgms"][0], compute_ph(X[ib], 1)["dgms"][0]
    out["h0_cardinality"] = {
        "finite_H0_classes": {"reference": int(np.isfinite(ph[:, 1]).sum()), "sub_a": int(np.isfinite(pa[:, 1]).sum()),
                              "sub_b": int(np.isfinite(pb[:, 1]).sum())},
        "wasserstein_sub_a_vs_reference": round(float(wasserstein(pa, ph)), 4),
        "wasserstein_sub_a_vs_sub_b": round(float(wasserstein(pa, pb)), 4),
        "bottleneck_sub_a_vs_reference": round(float(bottleneck(pa, ph)), 4),
        "bottleneck_sub_a_vs_sub_b": round(float(bottleneck(pa, pb)), 4)}
    (EXT / "results" / "caveat_checks.json").write_text(json.dumps(out, indent=1) + "\n")
    print(out["s_ceiling"]["summary"], out["h0_cardinality"])


main()
