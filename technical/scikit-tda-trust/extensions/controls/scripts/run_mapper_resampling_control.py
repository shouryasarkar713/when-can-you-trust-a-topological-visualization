#!/usr/bin/env python3
"""Extension D3 — Mapper input-resampling stability with a data-adaptive clusterer.

Same subsamples as Extension C (seed rule seed_base + offset + i; 80% without replacement), same
cover cell and PCA-1 lens (refit per subsample); clusterer = single-linkage at eps = c * median
5-NN distance of the FULL cloud. Reports node/component/cyclomatic distributions and the
reference-graph cyclomatic number. Numbers only.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import yaml

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(EXT / "scripts"))
from src.pipeline import mapper_structure_stats  # noqa: E402
from src.shapes import make_shape  # noqa: E402
from run_mapper_clusterer_control import median_knn_distance, mapper_single_linkage  # noqa: E402


def main() -> int:
    allc = yaml.safe_load((EXT / "configs" / "controls.yaml").read_text())
    d1, cfg = allc["mapper_clusterer_control"], allc["mapper_resampling_control"]
    shapes_cfg = yaml.safe_load((REPO / "configs" / "shapes.yaml").read_text())["shapes"]
    from sklearn.decomposition import PCA
    out = {"design": "D3 resampling control", "config": cfg, "eps_multipliers": d1["eps_multipliers"],
           "shapes": {}}
    cell = cfg["cell"]
    for shape in cfg["shapes"]:
        X = make_shape(shape, shapes_cfg[shape])
        n = len(X); size = int(round(cfg["fraction"] * n))
        d5 = median_knn_distance(X, int(d1["knn_k"]))
        blk = {"n_full": n, "subsample_size": size, "eps": {}}
        for c in d1["eps_multipliers"]:
            eps = c * d5
            ref = mapper_structure_stats(mapper_single_linkage(
                X, PCA(n_components=1).fit_transform(X), cell["n_cubes"], cell["perc_overlap"], eps))
            reps = []
            for i in range(int(cfg["n_replicates"])):
                seed = int(cfg["seed_base"]) + int(cfg["seed_offsets"][shape]) + i
                idx = np.sort(np.random.default_rng(seed).choice(n, size=size, replace=False))
                Xs = X[idx]
                g = mapper_single_linkage(Xs, PCA(n_components=1).fit_transform(Xs),
                                          cell["n_cubes"], cell["perc_overlap"], eps)
                st = mapper_structure_stats(g)
                reps.append({"rep": i, "seed": seed, **{k: v for k, v in st.items() if k != "cycles_caveat"}})
            cyc = [r["cyclomatic_number"] for r in reps]
            comp = [r["n_components"] for r in reps]
            blk["eps"][f"c{c}"] = {
                "eps_value": round(eps, 5),
                "reference": {k: v for k, v in ref.items() if k != "cycles_caveat"},
                "replicates": reps,
                "summary": {
                    "cyclomatic_counts": {str(v): cyc.count(v) for v in sorted(set(cyc))},
                    "n_with_cyclomatic_ge1": int(sum(1 for v in cyc if v >= 1)),
                    "n_with_cyclomatic_equal_reference": int(sum(1 for v in cyc if v == ref["cyclomatic_number"])),
                    "component_counts": {str(v): comp.count(v) for v in sorted(set(comp))},
                    "n_nodes_min_max": [min(r["n_nodes"] for r in reps), max(r["n_nodes"] for r in reps)],
                }}
            s = blk["eps"][f"c{c}"]["summary"]
            print(shape, f"c={c}", "ref cyc", ref["cyclomatic_number"], "cc", ref["n_components"],
                  "| cyc counts", s["cyclomatic_counts"], "| comp counts", s["component_counts"])
        out["shapes"][shape] = blk
    (EXT / "results" / "mapper_resampling_control.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
