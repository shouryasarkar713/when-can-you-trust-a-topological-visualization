#!/usr/bin/env python3
"""Render the Extension D figures from the saved results only (no recomputation)."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
RES, FIG = EXT / "results", EXT / "figures"
FIG.mkdir(exist_ok=True)
C = {"kmeans": "#0072B2", "sl3": "#009E73", "sl15": "#D55E00"}


def fig_mapper():
    base = json.loads((REPO / "extensions/stability/results/mapper_resampling.json").read_text())
    d3 = json.loads((RES / "mapper_resampling_control.json").read_text())
    shapes = ["annulus", "figure_eight", "blob"]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True, constrained_layout=True)
    for ax, shape in zip(axes, shapes):
        series = {
            "KMeans k=2\n(default)": [r["structure"]["cyclomatic_number"] for r in base["shapes"][shape]["replicates"]],
            "single-linkage\neps=3.0·d5": [r["cyclomatic_number"] for r in d3["shapes"][shape]["eps"]["c3.0"]["replicates"]],
            "single-linkage\neps=1.5·d5": [r["cyclomatic_number"] for r in d3["shapes"][shape]["eps"]["c1.5"]["replicates"]],
        }
        cols = [C["kmeans"], C["sl3"], C["sl15"]]
        vmax = max(max(v) for v in series.values())
        w = 0.26
        for j, (lab, vals) in enumerate(series.items()):
            cnt = [vals.count(v) for v in range(vmax + 1)]
            ax.bar(np.arange(vmax + 1) + (j - 1) * w, cnt, w, color=cols[j], label=lab)
        ax.set_title(shape.replace("_", "-"))
        ax.set_xlabel("graph cyclomatic number (E − V + C)")
        ax.set_xticks(range(vmax + 1))
    axes[0].set_ylabel("subsamples (of 30)")
    axes[0].legend(fontsize=7.5, frameon=False)
    fig.suptitle("Mapper cycle cue under 30 × 80% input subsamples: forced two-cluster KMeans vs data-adaptive single-linkage", fontsize=10)
    fig.savefig(FIG / "d3_mapper_resampling_clusterer.png", dpi=150)
    plt.close(fig)


def fig_weather():
    d = json.loads((RES / "weather_null_controls.json").read_text())
    keys = list(d["raw"])
    x = np.arange(len(keys))
    fig, ax = plt.subplots(figsize=(7.6, 3.8), constrained_layout=True)
    ax.bar(x - 0.2, [d["raw"][k]["gap_ratio_r1"] for k in keys], 0.38, color="#0072B2", label="TEMP series (as analysed)")
    ax.bar(x + 0.2, [d["anomaly"][k]["gap_ratio_r1"] for k in keys], 0.38, color="#E69F00",
           label="TEMP minus fitted annual harmonics")
    sh = [r["gap_ratio_r1"] for r in d["shuffle"]["replicates"]]
    ax.errorbar([3], [np.median(sh)], yerr=[[np.median(sh) - min(sh)], [max(sh) - np.median(sh)]], fmt="D",
                color="#CC79A7", capsize=3, label="10 shuffled series (reference config; median, range)")
    ax.axhline(3, color="k", ls="--", lw=1)
    ax.text(-0.45, 3.12, "r₁ = 3 convention", ha="left", fontsize=8,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5, alpha=0.9))
    ax.set_ylim(0, 8.2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"τ={d['raw'][k]['tau']}, d={d['raw'][k]['d']}" for k in keys], fontsize=8)
    ax.set_ylabel("gap ratio r₁ = p₁ / p₂ (H1)")
    ax.set_title("Matched null controls remove the dominant H1 cue (H1 gap ratio r₁ = p₁ / p₂)", fontsize=9.5)
    ax.legend(fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=1)
    fig.savefig(FIG / "d2_weather_null_controls.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig_mapper()
    fig_weather()
    print("wrote", sorted(p.name for p in FIG.glob("*.png")))
