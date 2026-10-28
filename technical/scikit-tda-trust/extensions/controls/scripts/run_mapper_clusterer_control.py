#!/usr/bin/env python3
"""Extension D1 — data-adaptive clusterer control for the Mapper parameter grid.

Same data (annulus / figure-eight / blob, seed 42, n=500), same PCA-1 lens, same cover grid as
E2; the ONLY change is the clusterer: single-linkage cut at eps = c * median 5-NN
distance (c in {1.5, 3.0}) instead of KMeans(k=2). Saves numbers only; no expectations inside.

Usage: python extensions/controls/scripts/run_mapper_clusterer_control.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import yaml

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
sys.path.insert(0, str(REPO))

from src.pipeline import mapper_structure_stats, graph_to_jsonable  # noqa: E402
from src.shapes import make_shape  # noqa: E402
from src.similarity import similarity_of_graphs  # noqa: E402


def median_knn_distance(X: np.ndarray, k: int) -> float:
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=k + 1).fit(X)
    d, _ = nn.kneighbors(X)
    return float(np.median(d[:, k]))


def mapper_single_linkage(X, lens, n_cubes, perc_overlap, eps):
    import kmapper as km
    from sklearn.cluster import AgglomerativeClustering
    mapper = km.KeplerMapper()
    return mapper.map(
        lens, X,
        cover=km.CubicalCover(n_cubes=n_cubes, perc_overlap=perc_overlap),
        clusterer=AgglomerativeClustering(n_clusters=None, distance_threshold=eps,
                                          linkage="single"),
    )


def main() -> int:
    cfg = yaml.safe_load((EXT / "configs" / "controls.yaml").read_text())["mapper_clusterer_control"]
    shapes_cfg = yaml.safe_load((REPO / "configs" / "shapes.yaml").read_text())
    shapes_cfg = shapes_cfg.get("shapes", shapes_cfg)
    from sklearn.decomposition import PCA
    out = {"design": "D1 clusterer control", "config": cfg, "shapes": {}}
    for shape in cfg["shapes"]:
        X = make_shape(shape, shapes_cfg[shape])
        lens = PCA(n_components=1).fit_transform(X)
        d5 = median_knn_distance(X, int(cfg["knn_k"]))
        sblock = {"n_points": int(len(X)), "median_5nn_distance": round(d5, 5), "eps": {}}
        for c in cfg["eps_multipliers"]:
            eps = c * d5
            cells = {}
            ref = cfg["reference_cell"]
            graphs = {}
            for nc in cfg["grid"]["n_cubes"]:
                for po in cfg["grid"]["perc_overlap"]:
                    g = mapper_single_linkage(X, lens, nc, po, eps)
                    graphs[(nc, po)] = g
                    st = mapper_structure_stats(g)
                    cells[f"nc{nc}_po{po}"] = {"n_cubes": nc, "perc_overlap": po,
                                               **{k: v for k, v in st.items() if k != "cycles_caveat"}}
            refg = graphs[(ref["n_cubes"], ref["perc_overlap"])]
            for (nc, po), g in graphs.items():
                cells[f"nc{nc}_po{po}"]["S_vs_reference"] = round(similarity_of_graphs(g, refg), 4)
            cyc = [v["cyclomatic_number"] for v in cells.values()]
            comp = [v["n_components"] for v in cells.values()]
            sblock["eps"][f"c{c}"] = {
                "multiplier": c, "eps_value": round(eps, 5), "cells": cells,
                "summary": {
                    "n_cells": len(cells),
                    "cyclomatic_values": sorted(set(cyc)),
                    "cells_with_cyclomatic_ge1": int(sum(1 for v in cyc if v >= 1)),
                    "components_values": sorted(set(comp)),
                    "cells_connected": int(sum(1 for v in comp if v == 1)),
                    "node_counts_min_max": [min(v["n_nodes"] for v in cells.values()),
                                            max(v["n_nodes"] for v in cells.values())],
                    "node_count_equals_2x_n_cubes_cells": int(sum(
                        1 for v in cells.values() if v["n_nodes"] == 2 * v["n_cubes"])),
                },
            }
            print(f"{shape} c={c} eps={eps:.4f}: cyclomatic {sorted(set(cyc))}, "
                  f"components {sorted(set(comp))}, "
                  f"reference cell -> {cells['nc10_po0.35']['n_nodes']} nodes/"
                  f"{cells['nc10_po0.35']['n_components']} cc/"
                  f"{cells['nc10_po0.35']['cyclomatic_number']} cyc")
        out["shapes"][shape] = sblock
    (EXT / "results").mkdir(exist_ok=True)
    (EXT / "results" / "mapper_clusterer_control.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
