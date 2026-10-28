#!/usr/bin/env python3
"""Extension A step 4 — render every weather figure FROM SAVED RESULTS ONLY.

No recomputation: reads results/*.json|npz|npy and the processed NPZ. Every
figure is reproducible from stored outputs (master-prompt requirement).

Figures:
  1  weather_temp_series.png        — TEMP series overview + missingness marks
  2  weather_pca_panels.png         — PCA scatter by season | by ONI phase
  3  weather_mapper_reference.png   — reference Mapper graph (PCA lens),
                                      native vs component-separated rendering
  4  weather_mapper_lens_comparison.png — PCA lens vs day-of-year lens
  5  weather_mapper_grid.png        — 8-cell grid panel + structure stats + S
  6  weather_seasonal_ph_reference.png — reference SW run: diagram + barcode
  7  weather_seasonal_ph_sweep.png  — sweep summary (dominance + r_1 vs span)
  8  weather_state_space_ph.png     — state-space cloud PH (negative
                                      representation contrast)
  9  weather_embedding_pca.png      — reference embedding 2-D PCA projection
 10  weather_seasonality_check.png  — post-hoc periodogram/ACF sanity check

Stage-3 corrections (2026-10-22): calendar-year ticks for fig 1 (the old
365-day arithmetic duplicated "2020"); wrapped ONI panel title in fig 2
(was clipped); fig 7 redrawn as a labelled scatter — points are NOT
connected, since tau and embedding dimension vary jointly across six
discrete configurations; fig 10 added (renders the post-hoc seasonality
check saved by seasonality_check.py). Numerical results unchanged.

Stage-4 correction (2026-10-22): fig 7 labels redrawn with leader lines
and hand-placed anchors (render_sweep_figure) — the Stage-3 offset-based
labels overlapped near the three near-annual configurations (spans
360/364/365 d) and near the reference star; the annual-period note moved
to the top of each panel. Numerical results unchanged; a label-overlap
regression test was added (tests/test_weather_outputs.py).

Usage: python extensions/meteorology/scripts/render_weather_figures.py
(requires results/weather_seasonality_check.json — run
extensions/meteorology/scripts/seasonality_check.py first)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

EXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(EXT_ROOT / "wx"))

from src.figures import component_separated_layout  # noqa: E402 (baseline reuse)
from src.pipeline import render_barcode, render_diagram  # noqa: E402

RESULTS = EXT_ROOT / "results"
FIGS = EXT_ROOT / "figures"
FIGS.mkdir(parents=True, exist_ok=True)  # independent-rebuild fix
DATA_NPZ = EXT_ROOT / "data_provenance" / "processed" / "weather_analysis.npz"

SEASON_COLORS = {"DJF": "#2176ff", "MAM": "#2ca02c", "JJA": "#ff7f0e", "SON": "#8c564b"}
ONI_COLORS = {"ElNino": "#d62728", "Neutral": "#7f7f7f", "LaNina": "#1f77b4",
              "Unknown": "#cccccc"}
CAPTIONS = {}


def _save(fig, name, caption):
    path = FIGS / name
    fig.savefig(path, dpi=150)
    plt.close(fig)
    CAPTIONS[name] = caption
    print(f"  {name}")
    return path


def _graph_from_json(gj):
    G = nx.Graph()
    for name, members in gj["nodes"].items():
        G.add_node(name, members=members)
    for a, others in gj["links"].items():
        for b in others:
            G.add_edge(a, b)
    return G


def _node_color(gj, z_temp):
    """Mean z-scored TEMP of each node's member days (continuous, honest)."""
    return [float(np.mean(z_temp[np.asarray(m)])) for _, m in sorted(gj["nodes"].items())]


def _draw_mapper(ax, gj, z_temp, title, separated=False, seed=42):
    G = _graph_from_json(gj)
    if separated:
        pos = component_separated_layout(G, seed=seed)
    else:
        pos = nx.spring_layout(G, seed=seed)
    colors = _node_color(gj, z_temp)
    sizes = [60 + 640 * (len(m) / max(1, max(len(mm) for mm in gj["nodes"].values())))
             for _, m in sorted(gj["nodes"].items())]
    ec = nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.35, width=1.2)
    nc = nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors, node_size=sizes,
                                cmap="coolwarm", edgecolors="black", linewidths=0.4,
                                vmin=-1.5, vmax=1.5)
    ax.set_title(title, fontsize=9)
    ax.axis("off")
    return nc


def render_sweep_figure(analysis):
    """Build the seasonal-PH parameter-sweep figure (labelled scatter).

    Stage-4 revision of the Stage-3 labelled scatter: every configuration
    label sits at a hand-chosen anchor in data coordinates with a thin
    leader line back to its point, because the Stage-3 point-offset labels
    overlapped near the three near-annual configurations (spans 360/364/365
    d) and near the reference star; the annual-period note moved to the top
    of each panel (it previously collided with labels near the bottom).

    Returns (fig, axes, texts, points): texts[panel] lists the six
    configuration-label Text artists plus the annual-period annotation,
    points[panel] lists the (x, y) data coordinates of the six markers —
    both are consumed by the label-overlap regression test
    (tests/test_weather_outputs.py::TestSweepLabelPlacement).
    """
    sweep = analysis["seasonal_ph"]["sweep"]
    ref_sw = analysis["seasonal_ph"]["reference"]
    confs = sorted(sweep.items(), key=lambda kv: kv[1]["span_days"])
    # Label anchors in data coordinates: config -> (x, y, ha, va) per panel.
    # The three near-annual configs (spans 360/364/365) fan out to distinct
    # regions (up-left / down-right / further down-right); each reference
    # label sits above-right of its star.
    anchors = {
        "dominant_H1_persistence": {
            "tau30_d8": (196, 2.20, "right", "center"),
            "tau45_d9": (338, 2.78, "right", "bottom"),
            "tau52_d8": (397, 1.70, "left", "center"),
            "tau73_d6": (400, 1.24, "left", "center"),
            "tau60_d8": (448, 2.62, "left", "center"),
            "tau90_d8": (612, 2.36, "right", "center"),
        },
        "gap_ratio_r1": {
            "tau30_d8": (196, 5.95, "right", "center"),
            "tau45_d9": (336, 7.95, "right", "center"),
            "tau52_d8": (402, 5.38, "left", "center"),
            "tau73_d6": (402, 4.10, "left", "center"),
            "tau60_d8": (447, 7.18, "left", "center"),
            "tau90_d8": (612, 6.12, "right", "center"),
        },
    }
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0), constrained_layout=True)
    panels = [(axes[0], "dominant_H1_persistence",
               "dominant H1 persistence (z-units)", "#1f77b4", (1.0, 3.2)),
              (axes[1], "gap_ratio_r1", "gap ratio $r_1$", "#d62728", (2.6, 8.8))]
    texts, points = {}, {}
    for pi, (ax, stat, ylabel, color, ylim) in enumerate(panels):
        texts[pi], points[pi] = [], []
        for key, c in confs:
            is_ref = key == ref_sw
            x, y = c["span_days"], c[stat]
            ax.plot(x, y, "*" if is_ref else "o", ms=14 if is_ref else 7,
                    color="#e6a800" if is_ref else color,
                    markeredgecolor="black", markeredgewidth=0.5 if is_ref else 0.0,
                    zorder=3 if is_ref else 2,
                    label="reference config" if is_ref else None)
            points[pi].append((x, y))
            lx, ly, ha, va = anchors[stat][key]
            texts[pi].append(ax.annotate(
                r"$\tau$=%d, d=%d%s" % (c["tau"], c["d"], " (ref)" if is_ref else ""),
                (x, y), xytext=(lx, ly), textcoords="data",
                ha=ha, va=va, fontsize=7,
                arrowprops=dict(arrowstyle="-", lw=0.6, color="0.45",
                                shrinkA=2, shrinkB=5)))
        ax.set_xlim(105, 690)
        ax.set_xlabel("embedding span $(d-1)\\tau$ [days] — six discrete configurations")
        ax.set_ylabel(ylabel)
        ax.set_ylim(*ylim)
        ax.axvline(365.25, color="green", lw=0.9, alpha=0.7, zorder=1)
        texts[pi].append(ax.text(372, ylim[1] - 0.06, "T = 365.25 d (annual period)",
                                 fontsize=6, color="green", va="top", ha="left"))
        ax.legend(loc="lower right", fontsize=6, framealpha=0.9)
    axes[0].set_title("Dominant H1 persistence per configuration")
    axes[1].axhline(3, color="gray", lw=0.8, ls="--")
    axes[1].text(115, 3.18, "$r_1$ = 3 convention", fontsize=6, color="gray",
                 va="bottom", ha="left")
    axes[1].set_title("Persistence-gap ratio $r_1$ per configuration")
    return fig, axes, texts, points


def main() -> int:
    FIGS.mkdir(exist_ok=True)
    data = np.load(DATA_NPZ, allow_pickle=True)
    analysis = json.loads((RESULTS / "weather_analysis_results.json").read_text())
    mapper_res = json.loads((RESULTS / "weather_mapper_results.json").read_text())

    dates_all = [str(d) for d in data["dates"]]
    seasons_all = [str(s) for s in data["seasons"]]
    temp_c = data["temp_c"]
    z_primary = data["X_primary"]
    oni_phase_all = [str(p) for p in data["oni_phase"]]

    import datetime as dt
    dnum = np.array([dt.date.fromisoformat(d).toordinal() for d in dates_all])

    # ---------- 1. TEMP series ----------
    fig, ax = plt.subplots(figsize=(9.5, 3.0), constrained_layout=True)
    for s, c in SEASON_COLORS.items():
        m = np.array([x == s for x in seasons_all])
        ax.plot(dnum[m], temp_c[m], ".", ms=1.6, color=c, label=s)
    # missing primary-feature days
    pp = analysis if False else None  # (kept simple: use preprocessing report)
    prep = json.loads((RESULTS / "weather_preprocessing_report.json").read_text())
    drop_dates = prep["primary_cloud"]["dropped_dates"]
    if drop_dates:
        dd = [dt.date.fromisoformat(d).toordinal() for d in drop_dates]
        ax.vlines(dd, temp_c.min(), temp_c.max(), color="red", lw=1.0, alpha=0.8)
        ax.plot([], [], color="red", lw=1.0, label="dropped day (missing SLP)")
    ax.set_xlabel("date")
    ax.set_ylabel("TEMP (degC)")
    ax.set_title("Daily mean temperature, NY Central Park 2019-2024 (GSOD, unit-converted)")
    ax.legend(loc="upper right", ncols=5, fontsize=7, framealpha=0.9)
    # Calendar-year ticks at their true January-1 positions. (Stage-3 fix:
    # uniform 365-day tick arithmetic drifts against the calendar — 2020 is a
    # 366-day year — and produced a duplicated "2020" label.)
    years = sorted({dt.date.fromisoformat(d).year for d in dates_all})
    ticks = [dt.date(y, 1, 1).toordinal() for y in years]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlim(dnum[0] - 20, dnum[-1] + 20)
    _save(fig, "weather_temp_series.png",
          "Daily TEMP (degC) colored by meteorological season; red lines mark the "
          "4 days dropped from the primary cloud (missing SLP). TEMP itself has no "
          "missing values in 2192 days.")

    # ---------- 2. PCA panels ----------
    coords = np.load(RESULTS / "weather_pca_coords.npy")
    pdates = [str(d) for d in data["primary_dates"]]
    pseasons = [str(s) for s in data["primary_seasons"]]
    poni = [str(p) for p in data["primary_oni_phase"]]
    evr = analysis["pca"]["explained_variance_ratio"]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
    for s, c in SEASON_COLORS.items():
        m = np.array([x == s for x in pseasons])
        axes[0].plot(coords[m, 0], coords[m, 1], ".", ms=2.5, color=c, label=s)
    axes[0].set_title("PCA of weather cloud, colored by season")
    axes[0].set_xlabel(f"PC1 ({evr[0]*100:.1f}% var)")
    axes[0].set_ylabel(f"PC2 ({evr[1]*100:.1f}% var)")
    axes[0].legend(fontsize=7, loc="upper left")
    for p, c in ONI_COLORS.items():
        m = np.array([x == p for x in poni])
        if m.any():
            axes[1].plot(coords[m, 0], coords[m, 1], ".", ms=2.5, color=c, label=p, alpha=0.75)
    axes[1].set_title("Same projection, colored by ONI phase\n"
                      "(DESCRIPTIVE ONLY — no ENSO hypothesis tested)")
    axes[1].set_xlabel(f"PC1 ({evr[0]*100:.1f}% var)")
    axes[1].set_ylabel(f"PC2 ({evr[1]*100:.1f}% var)")
    axes[1].legend(fontsize=7, loc="upper left")
    _save(fig, "weather_pca_panels.png",
          f"PCA (cumulative {analysis['pca']['cumulative_explained_variance']*100:.1f}% "
          "variance in 2 PCs) of the z-scored TEMP/DEWP/SLP cloud. Left: seasonal "
          "organization. Right: ONI phase coloring is DESCRIPTIVE CONTEXT ONLY — "
          "no station-level ENSO hypothesis is tested; the 2019-2024 window holds "
          "roughly two ENSO episodes (power statement).")

    # ---------- 3. Mapper reference ----------
    ref_key = mapper_res["reference_cell"]
    ref_cell = mapper_res["cells"][ref_key]
    st = ref_cell["structure"]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.4), constrained_layout=True)
    nc = _draw_mapper(axes[0], ref_cell["graph"], z_primary[:, 0],
                      f"PCA-1 lens, ({ref_cell['n_cubes']}, {ref_cell['perc_overlap']}) — native layout")
    _draw_mapper(axes[1], ref_cell["graph"], z_primary[:, 0],
                 "same graph — component-separated layout", separated=True)
    cbar = fig.colorbar(nc, ax=axes, shrink=0.75, pad=0.02)
    cbar.set_label("node mean z-TEMP", fontsize=8)
    _save(fig, "weather_mapper_reference.png",
          f"Reference Mapper graph (PCA-1 lens, n_cubes={ref_cell['n_cubes']}, "
          f"overlap={ref_cell['perc_overlap']}, KMeans k=2 seed=42): {st['n_nodes']} nodes, "
          f"{st['n_edges']} edges, {st['n_components']} component(s), cyclomatic number "
          f"{st['cyclomatic_number']}. Node color = mean z-scored temperature of member "
          "days. Mapper graph cycles are not automatically topological loops (baseline "
          "no-loop control); note the cold-warm polarization along the graph.")

    # ---------- 4. lens comparison ----------
    doy = mapper_res["day_of_year"]
    dst = doy["structure"]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.4), constrained_layout=True)
    nc = _draw_mapper(axes[0], ref_cell["graph"], z_primary[:, 0],
                      "UNSUPERVISED PCA-1 lens (reference)")
    _draw_mapper(axes[1], doy["graph"], z_primary[:, 0],
                 "day-of-year lens (encodes calendar directly)")
    cbar = fig.colorbar(nc, ax=axes, shrink=0.75, pad=0.02)
    cbar.set_label("node mean z-TEMP", fontsize=8)
    _save(fig, "weather_mapper_lens_comparison.png",
          f"Lens comparison at the reference cell: PCA-1 lens vs day-of-year lens "
          f"({dst['n_nodes']} nodes, {dst['n_edges']} edges, {dst['n_components']} comp). "
          "The day-of-year lens ENCODES calendar information directly — seasonal "
          "separation under it is partially built in and must be read beside the "
          "unsupervised PCA-lens result (left).")

    # ---------- 5. mapper grid ----------
    cells = mapper_res["cells"]
    keys = [f"nc{nc}_po{po}" for nc in (5, 10, 15, 20) for po in (0.35, 0.50)]
    fig, axes = plt.subplots(4, 2, figsize=(8.5, 13.5), constrained_layout=True)
    for ax, key in zip(axes.flat, keys):
        c = cells[key]
        s = c["structure"]
        _draw_mapper(ax, c["graph"], z_primary[:, 0],
                     f"({c['n_cubes']}, {c['perc_overlap']})  S_ref={c['membership_jaccard_S_vs_reference']:.2f}\n"
                     f"{s['n_nodes']}n {s['n_edges']}e {s['n_components']}c cyc={s['cyclomatic_number']}")
    fig.suptitle("Mapper parameter grid — weather cloud, PCA-1 lens "
                 "(node color: mean z-TEMP; S = exploratory overlap indicator)",
                 fontsize=9)
    _save(fig, "weather_mapper_grid.png",
          "The pre-specified parameter grid on the weather cloud. Node count = 2 x n_cubes "
          "in all 8 cells (same uninformative pattern as baseline E2); the graph stays "
          "connected for n_cubes<=15 and fragments into 2 components at n_cubes=20 under "
          "both overlaps — the baseline E2 parameter-sensitivity finding replicates on "
          "real data.")

    # ---------- 6. seasonal PH reference ----------
    dgms_npz = np.load(RESULTS / "weather_seasonal_ph_dgms.npz")
    ref_sw = analysis["seasonal_ph"]["reference"]
    sw_ref = analysis["seasonal_ph"]["sweep"][ref_sw]
    dgms = [dgms_npz[f"{ref_sw}_dgm0"], dgms_npz[f"{ref_sw}_dgm1"]]
    fig, ax = plt.subplots(figsize=(5.2, 4.2), constrained_layout=True)
    render_diagram(dgms, FIGS / "_tmp_diag.png", title="")
    tmp = plt.imread(FIGS / "_tmp_diag.png")
    ax.imshow(tmp)
    ax.axis("off")
    ax.set_title(f"SW embedding tau=60, d=8 (span 420 d)\n"
                 f"dominant H1 = {sw_ref['dominant_H1_persistence']}, r_1 = {sw_ref['gap_ratio_r1']}",
                 fontsize=9)
    render_barcode(dgms, FIGS / "weather_seasonal_ph_reference_barcode.png",
                   title=f"Seasonal H1 barcode — tau=60 d=8 (reference)", dim=1, max_bars=30)
    CAPTIONS["weather_seasonal_ph_reference_barcode.png"] = (
        "H1 barcode of the reference sliding-window embedding: one long bar (the "
        "dominant H1 class — consistent with recurrent seasonal or quasi-periodic "
        "structure in the embedded series, not proof of a simple closed physical "
        "climate trajectory) followed by short noise-scale classes. Custom renderer "
        "(persim ships diagrams, not barcodes — baseline E1 audit finding).")
    _save(fig, "weather_seasonal_ph_reference_diagram.png",
          f"Persistence diagram of the reference sliding-window embedding "
          f"(tau=60 d, d=8, span 420 d, n={sw_ref['n_points']} points in R^8). One H1 class "
          f"dominates (persistence {sw_ref['dominant_H1_persistence']} z-units, "
          f"r_1={sw_ref['gap_ratio_r1']}); r_1>=3 is the stated convention, not a theorem. "
          "A dominant H1 class evidences recurrent quasi-periodic structure of the "
          "embedded series — NOT proof of a simple closed physical climate trajectory.")
    (FIGS / "_tmp_diag.png").unlink()

    # ---------- 7. sweep summary (labelled scatter; points NOT connected) ----------
    fig, _axes, _texts, _pts = render_sweep_figure(analysis)
    _save(fig, "weather_seasonal_ph_sweep.png",
          "Seasonal-cycle PH parameter sweep as a LABELLED SCATTER (Stage-3 "
          "revision: points are NOT connected — tau and embedding dimension d "
          "vary jointly across six discrete configurations; no smooth response "
          "surface is implied. Stage-4 revision: labels use leader lines with "
          "hand-placed anchors so that no two labels overlap). Every "
          "configuration yields one dominant H1 class "
          "(r_1 between 4.7 and 7.3, above the stated r_1 >= 3 convention) — "
          "consistent with recurrent seasonal or quasi-periodic structure in the "
          "embedded temperature series; this does not by itself prove a simple "
          "closed physical climate trajectory or independently validate an "
          "annual period (post-hoc sanity check: weather_seasonality_check.png). "
          "The sub-annual span is NOT a null control: any non-commensurate delay "
          "embedding of a periodic signal traces a closed curve; the negative "
          "representation contrast is the state-space cloud "
          "(weather_state_space_ph.png).")

    # ---------- 8. state-space PH ----------
    ss = np.load(RESULTS / "weather_state_space_dgms.npz")
    ss_dgms = [ss["dgm0"], ss["dgm1"]]
    ssp = analysis["state_space_ph"]
    fig, ax = plt.subplots(figsize=(5.2, 4.2), constrained_layout=True)
    render_diagram(ss_dgms, FIGS / "_tmp_diag2.png", title="")
    tmp = plt.imread(FIGS / "_tmp_diag2.png")
    ax.imshow(tmp)
    ax.axis("off")
    ax.set_title(f"State-space cloud (TEMP/DEWP/SLP)\n"
                 f"dominant H1 = {ssp['dominant_H1_persistence']}, r_1 = {ssp['gap_ratio_r1']}",
                 fontsize=9)
    _save(fig, "weather_state_space_ph.png",
          f"Vietoris-Rips PH of the 3-D z-scored daily state-space cloud itself: "
          f"{ssp['H1_classes']} H1 classes, dominant persistence "
          f"{ssp['dominant_H1_persistence']}, r_1={ssp['gap_ratio_r1']} — NO dominant "
          "loop. The annual signal is a property of the TEMPORAL organization "
          "(recurrence in time, recovered by the sliding-window embedding), not of "
          "the static geometry of daily weather states, which weather variability "
          "fills in.")

    (FIGS / "_tmp_diag2.png").unlink()
    render_barcode(ss_dgms, FIGS / "weather_state_space_ph_barcode.png",
                   title="State-space H1 barcode (no dominant class)", dim=1, max_bars=30)
    CAPTIONS["weather_state_space_ph_barcode.png"] = (
        "H1 barcode of the 3-D state-space cloud: no dominant bar — the visual "
        "counterpart of the state-space NEGATIVE REPRESENTATION CONTRAST "
        "(contrast with the seasonal barcode).")

    # ---------- 9. embedding PCA projection ----------
    emb_npz = np.load(RESULTS / "weather_reference_embedding.npz", allow_pickle=True)
    pca2d = emb_npz["pca2d"]
    wseas = [str(s) for s in emb_npz["window_start_season"]]
    fig, ax = plt.subplots(figsize=(5.8, 5.0), constrained_layout=True)
    for s, c in SEASON_COLORS.items():
        m = np.array([x == s for x in wseas])
        ax.plot(pca2d[m, 0], pca2d[m, 1], ".", ms=1.8, color=c, label=s, alpha=0.8)
    ax.set_title("Reference SW embedding projected to 2-D PCA\n(color = season of window start)")
    ax.set_xlabel("emb-PC1")
    ax.set_ylabel("emb-PC2")
    ax.legend(fontsize=7)
    _save(fig, "weather_embedding_pca.png",
          "The 8-D reference sliding-window embedding projected to its first two "
          "PCA components: a closed band with a hole — the visual counterpart of "
          "the dominant H1 class. Colors follow the season of each window's start "
          "day and progress around the loop, as expected for an annual cycle. A "
          "2-D projection of an 8-D embedding is a rendering, not the computed "
          "topology; the quantitative evidence is the persistence diagram.")

    # ---------- 10. post-hoc seasonality sanity check ----------
    seas = json.loads((RESULTS / "weather_seasonality_check.json").read_text())
    per = np.asarray(seas["periodogram"]["periods_days"])
    pwr = np.asarray(seas["periodogram"]["power"])
    dom_p = seas["periodogram"]["dominant_period_days"]
    lags = np.asarray(seas["autocorrelation"]["lags_days"])
    acf = np.asarray(seas["autocorrelation"]["acf"])
    peak_l = seas["autocorrelation"]["peak_lag_days"]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6), constrained_layout=True)
    axes[0].plot(per, pwr, "-", lw=1.0, color="#1f77b4")
    axes[0].axvline(365.25, color="green", lw=0.9, alpha=0.7)
    axes[0].axvline(dom_p, color="#d62728", lw=0.9, ls="--", alpha=0.8)
    axes[0].set_xlim(30, 800)
    axes[0].set_ylim(bottom=0)
    axes[0].set_xlabel("period [days]")
    axes[0].set_ylabel("spectral power")
    axes[0].set_title(f"FFT periodogram, daily TEMP\n"
                      f"dominant non-DC period = {dom_p:.1f} d (green: 365.25 d)",
                      fontsize=9)
    axes[1].plot(lags, acf, "-", lw=1.0, color="#d62728")
    axes[1].axvline(365.25, color="green", lw=0.9, alpha=0.7)
    axes[1].axvline(peak_l, color="#1f77b4", lw=0.9, ls="--", alpha=0.8)
    axes[1].axhline(0, color="gray", lw=0.5)
    axes[1].set_xlim(0, 800)
    axes[1].set_xlabel("lag [days]")
    axes[1].set_ylabel("autocorrelation")
    axes[1].set_title(f"Autocorrelation, daily TEMP\n"
                      f"peak lag in [180, 550] d = {peak_l:.0f} d (green: 365.25 d)",
                      fontsize=9)
    _save(fig, "weather_seasonality_check.png",
          "POST-HOC SANITY CHECK (added at Stage 3; NOT used to select or retune "
          "any embedding parameter — the sweep was pre-specified and saved "
          "first): FFT periodogram and autocorrelation of the z-scored daily "
          "TEMP series itself. The series carries near-annual periodicity "
          f"(dominant period {dom_p:.0f} d; autocorrelation peak lag {peak_l:.0f} d "
          "within the 180-550 d search window), consistent with the recurrent "
          "structure recovered by the sliding-window PH. This is a descriptive "
          "cross-check, not a hypothesis test.")

    # captions file
    (FIGS / "captions.json").write_text(json.dumps(CAPTIONS, indent=2) + "\n")
    print(f"Rendered {len(CAPTIONS)} figures + captions.json into {FIGS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
