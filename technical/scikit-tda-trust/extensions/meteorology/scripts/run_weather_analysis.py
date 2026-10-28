#!/usr/bin/env python3
"""Extension A step 3 — the analysis runs (numerical results ONLY; figures are
rendered separately from saved outputs by render_weather_figures.py).

Runs, in order:
  A. PCA on the primary z-scored cloud (TEMP/DEWP/SLP): coordinates,
     explained variance.
  B. Mapper on the primary cloud: PCA-1 lens over the pre-specified grid
     {5,10,15,20} x {0.35,0.50} (reference cell (10,0.35) = baseline E2
     reference), plus the day-of-year lens at the reference cell as a
     descriptive comparison. Graph memberships + structure stats saved.
  C. Persistence of the primary 3-D state-space cloud itself (H1 loop check
     in feature space, distinct from the temporal embedding).
  D. Seasonal-cycle PH: sliding-window embeddings of the z-scored daily
     TEMP series for the pre-specified sweep (6 configurations bracketing
     the annual scale); ripser diagrams + diagnostics + runtimes saved.

Every run saves its numerical outputs BEFORE any figure exists. No
expected-outcome assertions live here (baseline discipline).

Usage: python extensions/meteorology/scripts/run_weather_analysis.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

EXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(EXT_ROOT / "wx"))

from src.pipeline import (  # noqa: E402 (baseline reuse)
    compute_ph,
    graph_to_jsonable,
    mapper_structure_stats,
)
from src.similarity import similarity_of_graphs  # noqa: E402
from weather_lib import (  # noqa: E402
    SW_EMBEDDING_CONVENTION,
    YEARDAY_NOTE,
    day_of_year_lens,
    embedding_span_days,
    mapper_run_with_lens,
    seasonal_ph_diagnostics,
    sliding_window_embedding,
)

RESULTS = EXT_ROOT / "results"
NPZ_PATH = EXT_ROOT / "data_provenance" / "processed" / "weather_analysis.npz"


def main() -> int:
    cfg = yaml.safe_load((EXT_ROOT / "configs" / "weather.yaml").read_text())
    data = np.load(NPZ_PATH, allow_pickle=True)
    X = data["X_primary"]                     # (n,3) z-scored
    pdates = [str(d) for d in data["primary_dates"]]
    pseasons = [str(s) for s in data["primary_seasons"]]
    poni = [str(p) for p in data["primary_oni_phase"]]
    temp_z = data["temp_z"]
    temp_c = data["temp_c"]
    dates_all = [str(d) for d in data["dates"]]
    seasons_all = [str(s) for s in data["seasons"]]

    out: dict = {"step": "run_weather_analysis",
                 "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "n_days_primary": int(X.shape[0]),
                 "primary_features": [str(f) for f in data["primary_features"]],
                 "mapper_cycles_caveat": (
                     "Mapper graph cycles are not automatically topological loops "
                     "(baseline E2 no-loop control); structural statistics are "
                     "reported beside every graph.")}

    # ---------------- A. PCA ----------------
    from sklearn.decomposition import PCA
    t0 = time.perf_counter()
    pca = PCA(n_components=cfg["pca"]["n_components"])
    coords = pca.fit_transform(X)
    out["pca"] = {
        "explained_variance_ratio": [round(float(v), 5) for v in pca.explained_variance_ratio_],
        "cumulative_explained_variance": round(float(np.sum(pca.explained_variance_ratio_)), 5),
        "components": [[round(float(c), 4) for c in comp] for comp in pca.components_],
        "time_s": round(time.perf_counter() - t0, 4),
        "note": "PCA on the z-scored primary cloud; deterministic (SVD).",
    }
    np.save(RESULTS / "weather_pca_coords.npy", coords)

    # ---------------- B. Mapper ----------------
    mk = cfg["mapper"]["kmeans"]
    seed = int(mk["random_state"])
    n_cl = int(mk["n_clusters"])
    ref = cfg["mapper"]["reference"]
    grid_nc = cfg["mapper"]["grid"]["n_cubes"]
    grid_po = cfg["mapper"]["grid"]["perc_overlap"]

    # PCA-1 lens (unsupervised) — same lens family as baseline E2.
    lens_pca = coords[:, 0].reshape(-1, 1)
    cells = {}
    for nc in grid_nc:
        for po in grid_po:
            t0 = time.perf_counter()
            g = mapper_run_with_lens(lens_pca, X, nc, po, seed=seed, n_clusters=n_cl)
            dt = time.perf_counter() - t0
            key = f"nc{nc}_po{po}"
            cells[key] = {
                "n_cubes": nc, "perc_overlap": po, "lens": "PCA-1",
                "time_s": round(dt, 3),
                "structure": mapper_structure_stats(g),
                "graph": graph_to_jsonable(g),
            }
            print(f"  mapper {key}: {cells[key]['structure']['n_nodes']} nodes, "
                  f"{cells[key]['structure']['n_edges']} edges, "
                  f"{cells[key]['structure']['n_components']} comp "
                  f"({dt:.1f}s)")

    ref_key = f"nc{ref['n_cubes']}_po{ref['perc_overlap']}"
    out["mapper_reference_cell"] = ref_key
    # membership-Jaccard S of every cell vs the reference cell (EXPLORATORY
    # overlap indicator only — NOT a canonical graph distance; never used
    # alone to rank resolutions; structure stats reported beside it).
    for key, cell in cells.items():
        cell["membership_jaccard_S_vs_reference"] = (
            round(similarity_of_graphs(cells[key]["graph"], cells[ref_key]["graph"]), 3))
    out["mapper_S_caveat"] = (
        "S is the baseline's exploratory membership-overlap indicator "
        "(mean best-match Jaccard); it is NOT a canonical graph distance and "
        "is never used alone to rank parameter choices.")

    # day-of-year lens at the reference cell (descriptive comparison)
    if cfg["mapper"]["day_of_year_lens"]["enabled"]:
        lens_doy = day_of_year_lens(pdates)
        t0 = time.perf_counter()
        g = mapper_run_with_lens(lens_doy, X, ref["n_cubes"], ref["perc_overlap"],
                                 seed=seed, n_clusters=n_cl)
        out["mapper_day_of_year"] = {
            "cell": ref_key, "lens": "day-of-year (normalized)",
            "note": YEARDAY_NOTE,
            "time_s": round(time.perf_counter() - t0, 3),
            "structure": mapper_structure_stats(g),
            "graph": graph_to_jsonable(g),
        }

    # persist mapper results (without the heavy graph JSON in the summary)
    out["mapper_grid"] = {
        k: {kk: vv for kk, vv in c.items() if kk != "graph"} for k, c in cells.items()}
    mapper_json = {"reference_cell": ref_key, "cells": cells,
                   "day_of_year": out.get("mapper_day_of_year")}
    (RESULTS / "weather_mapper_results.json").write_text(json.dumps(mapper_json, indent=2))

    # ---------------- C. state-space PH ----------------
    t0 = time.perf_counter()
    ph_space = compute_ph(X, maxdim=1)
    out["state_space_ph"] = {
        **seasonal_ph_diagnostics(ph_space["dgms"]),
        "ripser_time_s": round(ph_space["time_s"], 3),
        "note": ("Vietoris-Rips PH of the 3-D z-scored state-space cloud "
                 "itself — distinct from the temporal sliding-window "
                 "embedding; a loop here would be a loop in daily weather "
                 "states, not in time."),
    }
    np.savez_compressed(RESULTS / "weather_state_space_dgms.npz",
                        **{f"dgm{i}": d for i, d in enumerate(ph_space["dgms"])})
    print(f"  state-space PH: {out['state_space_ph']['H1_classes']} H1 classes, "
          f"dominant {out['state_space_ph']['dominant_H1_persistence']}, "
          f"r_1={out['state_space_ph']['gap_ratio_r1']} ({ph_space['time_s']:.1f}s)")

    # ---------------- D. seasonal PH sweep ----------------
    sw = cfg["seasonal_ph"]
    sweep_results = {}
    sweep_diagrams = {}
    for conf in sw["sweep"]:
        tau, d = int(conf["tau"]), int(conf["d"])
        span = embedding_span_days(tau, d)
        t0 = time.perf_counter()
        emb = sliding_window_embedding(temp_z, tau, d, stride=int(sw["stride"]))
        if emb.shape[0] == 0:
            sweep_results[f"tau{tau}_d{d}"] = {
                "tau": tau, "d": d, "span_days": span,
                "status": "EMPTY_EMBEDDING", "n_points": 0}
            continue
        ph = compute_ph(emb, maxdim=int(sw["maxdim"]))
        diag = seasonal_ph_diagnostics(ph["dgms"])
        sweep_results[f"tau{tau}_d{d}"] = {
            "tau": tau, "d": d, "span_days": span,
            "span_over_annual_period": round(span / 365.25, 3),
            "n_points": int(emb.shape[0]), "dim": int(emb.shape[1]),
            "series": sw["series"], "series_dates": [dates_all[0], dates_all[-1]],
            "status": "OK",
            "ripser_time_s": round(ph["time_s"], 3),
            "embedding_time_s": round(time.perf_counter() - t0 - ph["time_s"], 3),
            **diag,
        }
        sweep_diagrams[f"tau{tau}_d{d}"] = ph["dgms"]
        print(f"  SW tau={tau} d={d} span={span}d n={emb.shape[0]}: "
              f"dominant H1 {diag['dominant_H1_persistence']}, "
              f"r_1={diag['gap_ratio_r1']} ({ph['time_s']:.1f}s)")

    out["seasonal_ph"] = {
        "convention": SW_EMBEDDING_CONVENTION,
        "stride": int(sw["stride"]),
        "reference": f"tau{sw['reference']['tau']}_d{sw['reference']['d']}",
        "prominence_convention": sw["prominence_convention"],
        "interpretation_guard": (
            "A dominant H1 class in a sliding-window embedding evidences a "
            "recurrent quasi-periodic structure of the embedded series at the "
            "studied scale; it is NOT proof that the underlying climate "
            "process follows a simple closed physical trajectory."),
        "sweep": sweep_results,
    }
    # save diagrams (float64 arrays; reproducible via the saved series + params)
    np.savez_compressed(
        RESULTS / "weather_seasonal_ph_dgms.npz",
        **{f"{key}_dgm{dim}": d for key, dgms in sweep_diagrams.items()
           for dim, d in enumerate(dgms)})
    # save the reference embedding's PCA projection for figure rendering
    from sklearn.decomposition import PCA as PCA2
    ref_key_sw = out["seasonal_ph"]["reference"]
    ref_tau, ref_d = sw["reference"]["tau"], sw["reference"]["d"]
    ref_emb = sliding_window_embedding(temp_z, int(ref_tau), int(ref_d),
                                       stride=int(sw["stride"]))
    emb_pca = PCA2(n_components=2).fit_transform(ref_emb)
    starts = np.arange(0, len(temp_z) - embedding_span_days(int(ref_tau), int(ref_d)),
                       int(sw["stride"]))
    emb_season = [seasons_all[min(i, len(seasons_all) - 1)] for i in starts]
    np.savez_compressed(RESULTS / "weather_reference_embedding.npz",
                        embedding=ref_emb, pca2d=emb_pca,
                        window_start_index=starts,
                        window_start_dates=np.array([dates_all[i] for i in starts]),
                        window_start_season=np.array(emb_season))

    out["status"] = "OK"
    (RESULTS / "weather_analysis_results.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"Saved: weather_analysis_results.json, weather_mapper_results.json, "
          f"weather_seasonal_ph_dgms.npz, weather_state_space_dgms.npz, "
          f"weather_reference_embedding.npz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
