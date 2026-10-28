#!/usr/bin/env python3
"""Extension D4 — independent-draw reference: noise-floor H1 bottleneck and Mapper cycle cue
over NEW samples of each synthetic shape (not subsamples of the seed-42 cloud). Numbers only."""
from __future__ import annotations
import inspect, json, sys
from pathlib import Path
import numpy as np
import yaml

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(EXT / "scripts"))
from src import shapes as S  # noqa: E402
from src.pipeline import mapper_run, mapper_structure_stats, compute_ph, h1_persistences, gap_ratio  # noqa: E402
from src.shapes import make_shape, GROUND_TRUTH_H1_RANK  # noqa: E402
from run_mapper_clusterer_control import median_knn_distance, mapper_single_linkage  # noqa: E402


def main() -> int:
    cfg = yaml.safe_load((EXT / "configs" / "controls.yaml").read_text())["independent_draws"]
    shp = yaml.safe_load((REPO / "configs" / "shapes.yaml").read_text())["shapes"]
    from persim import bottleneck
    from sklearn.decomposition import PCA
    out = {"design": "D4 independent draws", "config": cfg, "shapes": {}}
    for shape in cfg["shapes"]:
        ref = np.load(REPO / "results" / "e1" / f"{shape}_ph_dgms.npz")
        ref_h1 = ref["arr_1"] if "arr_1" in ref.files else ref[ref.files[1]]
        draws = []
        for i in range(int(cfg["n_draws"])):
            params = dict(shp[shape]); params["seed"] = int(cfg["seed_base"]) + i; params["n"] = int(cfg["n"])
            X = make_shape(shape, params)
            ph = compute_ph(X, maxdim=1)
            h1 = ph["dgms"][1]
            pers = h1_persistences(h1)
            k = GROUND_TRUTH_H1_RANK[shape] or 1
            km = mapper_structure_stats(mapper_run(X, cfg["cell"]["n_cubes"], cfg["cell"]["perc_overlap"]))
            eps = cfg["eps_multiplier"] * median_knn_distance(X, 5)
            sl = mapper_structure_stats(mapper_single_linkage(
                X, PCA(n_components=1).fit_transform(X), cfg["cell"]["n_cubes"], cfg["cell"]["perc_overlap"], eps))
            draws.append({"seed": params["seed"],
                          "dominant_H1": round(float(pers[0]), 4),
                          "gap_ratio_at_truth_rank": round(gap_ratio(pers, k), 3) if gap_ratio(pers, k) else None,
                          "rank_used": k,
                          "H1_bottleneck_vs_seed42_ref": round(float(bottleneck(h1, ref_h1)), 5),
                          "kmeans_cyclomatic": km["cyclomatic_number"], "kmeans_components": km["n_components"],
                          "sl_cyclomatic": sl["cyclomatic_number"], "sl_components": sl["n_components"]})
        bn = [d["H1_bottleneck_vs_seed42_ref"] for d in draws]
        cnt = lambda key: {str(v): [d[key] for d in draws].count(v) for v in sorted({d[key] for d in draws})}
        out["shapes"][shape] = {"draws": draws, "summary": {
            "H1_bottleneck_median_iqr": [round(float(np.median(bn)), 4), round(float(np.percentile(bn, 25)), 4),
                                         round(float(np.percentile(bn, 75)), 4)],
            "dominant_H1_min_max": [min(d["dominant_H1"] for d in draws), max(d["dominant_H1"] for d in draws)],
            "gap_ratio_min_max": [min(d["gap_ratio_at_truth_rank"] for d in draws),
                                  max(d["gap_ratio_at_truth_rank"] for d in draws)],
            "kmeans_cyclomatic_counts": cnt("kmeans_cyclomatic"), "kmeans_components_counts": cnt("kmeans_components"),
            "sl_cyclomatic_counts": cnt("sl_cyclomatic"), "sl_components_counts": cnt("sl_components")}}
        print(shape, out["shapes"][shape]["summary"], flush=True)
    (EXT / "results" / "independent_draws.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
