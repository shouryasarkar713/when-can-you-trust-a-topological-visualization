"""Thin, config-driven wrappers around ripser / persim / kmapper + custom
visualisation helpers, shared by the experiment scripts.

Layering rule (engineering requirements): numeric results are computed and
saved by scripts; figures are re-rendered from saved results by
src/figures.py; report text lives elsewhere. This module owns computation
and the primary encodings only — it contains NO expected-outcome assertions.

matplotlib is forced to the Agg backend because every artifact in this
project is rendered headless to disk.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# ---------------------------------------------------------------- gap ratio

GAP_RATIO_CONVENTION = (
    "r_k = p_k / p_{k+1} with persistences sorted in descending order. "
    "The rank k is known from the synthetic construction of each dataset "
    "(annulus k=1, figure-eight k=2, controls: none); r_k is NOT a universal "
    "automatic loop-counting rule, and the 'prominent' threshold (r_k >= 3) "
    "is a stated convention, not a theorem."
)


def gap_ratio(persistences: Sequence[float], k: int) -> float | None:
    """Generalised persistence-gap ratio r_k = p_k / p_{k+1}.

    persistences need not be sorted (descending sort is applied here).
    k is the 1-based rank. Returns None when there are fewer than k+1
    STRICTLY POSITIVE persistences (ratio undefined / division by zero
    avoided). See GAP_RATIO_CONVENTION for the interpretation rules.
    """
    if k < 1:
        raise ValueError(f"Rank k must be >= 1, got {k}.")
    p = np.sort(np.asarray(persistences, dtype=float))[::-1]
    if len(p) < k + 1:
        return None
    if not p[k] > 0:
        return None
    return float(p[k - 1] / p[k])


def h1_persistences(dgm_h1: np.ndarray) -> np.ndarray:
    """H1 persistences (death - birth), sorted descending."""
    if len(dgm_h1) == 0:
        return np.array([])
    return np.sort(dgm_h1[:, 1] - dgm_h1[:, 0])[::-1]


def h0_prominent_merges(dgm_h0: np.ndarray, fraction: float = 0.5) -> int:
    """Count finite H0 classes with persistence above `fraction` * max.

    For the three-blob control this yields 2 (two late merges); with the
    essential class that reads as 3 components. The fraction is a stated
    convention for this known-construction check, not a clustering theorem.
    """
    finite = dgm_h0[np.isfinite(dgm_h0[:, 1])]
    if len(finite) == 0:
        return 0
    pers = finite[:, 1] - finite[:, 0]
    return int(np.sum(pers > pers.max() * fraction))

# ---------------------------------------------------------------- ripser

def compute_ph(X: np.ndarray, maxdim: int = 1) -> dict:
    """Run ripser and return {'dgms': [...], 'time_s': float}."""
    from ripser import ripser
    t0 = time.perf_counter()
    res = ripser(X, maxdim=maxdim)
    return {"dgms": res["dgms"], "time_s": time.perf_counter() - t0}


def ph_summary(X: np.ndarray, maxdim: int = 1, h1_rank: int | None = None) -> dict:
    """Measured persistence summary for one point cloud (no expectations inside).

    Includes r_1 always (calibration) and r_k at the supplied ground-truth
    rank when given and defined.
    """
    out = compute_ph(X, maxdim=maxdim)
    dgms = out["dgms"]
    s = {
        "n_points": int(len(X)),
        "H0_classes": int(len(dgms[0])),
        "ripser_time_s": round(out["time_s"], 4),
    }
    if maxdim >= 1 and len(dgms) > 1:
        s["H1_classes"] = int(len(dgms[1]))
        pers = h1_persistences(dgms[1])
        s["H1_top3_persistence"] = [round(float(x), 4) for x in pers[:3]]
        s["gap_ratio_r1_calibration"] = (
            round(gap_ratio(pers, 1), 3) if gap_ratio(pers, 1) is not None else None)
        if h1_rank is not None:
            rk = gap_ratio(pers, h1_rank)
            s[f"gap_ratio_r{h1_rank}_at_ground_truth_rank"] = (
                round(rk, 3) if rk is not None else None)
    s["gap_ratio_convention"] = GAP_RATIO_CONVENTION
    return s

# ---------------------------------------------------------------- persim

def diagram_distance(d1: np.ndarray, d2: np.ndarray, metric: str = "bottleneck") -> dict:
    """persim bottleneck / wasserstein distance between two diagrams."""
    from persim import bottleneck, wasserstein
    t0 = time.perf_counter()
    if metric == "bottleneck":
        val = float(bottleneck(d1, d2))
    elif metric == "wasserstein":
        val = float(wasserstein(d1, d2))
    else:
        raise ValueError(f"metric must be 'bottleneck' or 'wasserstein', got {metric!r}.")
    return {"metric": metric, "value": round(val, 5),
            "time_s": round(time.perf_counter() - t0, 4)}


def render_diagram(dgms: Sequence[np.ndarray], path: Path, title: str = "") -> Path:
    """Persistence diagram via persim.plot_diagrams (native encoding)."""
    from persim import plot_diagrams
    plot_diagrams(dgms, title=title)
    fig = plt.gcf()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_matching(d1: np.ndarray, d2: np.ndarray, path: Path, title: str = "",
                    metric: str = "bottleneck") -> dict:
    """Visualise a diagram matching via persim's *_matching (native encoding).

    persim 0.4.1 returns (distance, matching_ndarray) from *_(..., matching=True);
    older tutorials show (distance, (matching, indices)) — both are handled.
    """
    from persim import bottleneck, bottleneck_matching, wasserstein, wasserstein_matching
    if metric == "bottleneck":
        dist, matching = bottleneck(d1, d2, matching=True)
        plot_fn = bottleneck_matching
    elif metric == "wasserstein":
        dist, matching = wasserstein(d1, d2, matching=True)
        plot_fn = wasserstein_matching
    else:
        raise ValueError(f"metric must be 'bottleneck' or 'wasserstein', got {metric!r}.")
    if isinstance(matching, tuple):  # pre-0.4 API: (matching, indices)
        matching = matching[0]
    plot_fn(d1, d2, matching, labels=["dgm A", "dgm B"])
    fig = plt.gcf()
    if title:
        fig.suptitle(title)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return {"distance": round(float(dist), 5), "metric": metric}


def render_barcode(dgms: Sequence[np.ndarray], path: Path, title: str = "",
                   dim: int = 1, max_bars: int = 40) -> Path:
    """CUSTOM barcode renderer (persim ships diagrams, not barcodes).

    This is one of the glue-code items quantified by the E1 audit.
    """
    d = dgms[dim]
    pers = d[:, 1] - d[:, 0]
    order = np.argsort(pers)[::-1][:max_bars]
    fig, ax = plt.subplots(figsize=(4.2, 3.0), constrained_layout=True)
    for i, idx in enumerate(order):
        b, death = d[idx]
        ax.plot([b, death], [i, i], lw=1.4, c="tab:blue")
    ax.set_title(title or f"H{dim} barcode")
    ax.set_xlabel("filtration scale")
    ax.set_ylabel("classes (sorted by persistence)")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path

# ---------------------------------------------------------------- kmapper

MAPPER_CYCLES_CAVEAT = (
    "Mapper graph cycles are not automatically equivalent to true topological "
    "loops in the data: the no-loop control produces short noise-scale graph "
    "cycles while its H1 diagram correctly shows no dominant class. Cycle "
    "length and scale context distinguish loop-like structure from noise.")


def mapper_run(X: np.ndarray, n_cubes: int, perc_overlap: float,
               seed: int = 42, n_clusters: int = 2) -> dict:
    """Build one Mapper graph: PCA-1 lens, CubicalCover, seeded KMeans.

    Returns the kmapper graph dict (nodes/links/meta_data).
    """
    import kmapper as km
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    mapper = km.KeplerMapper()
    lens = PCA(n_components=1).fit_transform(X)
    return mapper.map(
        lens, X,
        cover=km.CubicalCover(n_cubes=n_cubes, perc_overlap=perc_overlap),
        clusterer=KMeans(n_clusters=n_clusters, random_state=seed, n_init=10),
    )


def mapper_structure_stats(graph: Mapping) -> dict:
    """Clearly defined graph-structure statistics for one Mapper graph.

    n_components uses networkx connected components (external dependency:
    kmapper does not declare networkx at runtime). cyclomatic_number =
    E - V + C counts independent cycles. basis_cycle_* summarise the lengths
    of a cycle basis (networkx.cycle_basis). See MAPPER_CYCLES_CAVEAT before
    interpreting any cycle statistic as a topological loop.
    """
    import kmapper as km
    G = km.to_networkx(graph)
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    n_comp = nx.number_connected_components(G)
    basis = nx.cycle_basis(G)
    lengths = [len(c) for c in basis]
    return {
        "n_nodes": int(n_nodes),
        "n_edges": int(n_edges),
        "n_components": int(n_comp),
        "cyclomatic_number": int(n_edges - n_nodes + n_comp),
        "max_basis_cycle_length": int(max(lengths)) if lengths else 0,
        "mean_basis_cycle_length": round(float(np.mean(lengths)), 2) if lengths else 0.0,
        "cycles_caveat": MAPPER_CYCLES_CAVEAT,
    }


def graph_to_jsonable(graph: Mapping) -> dict:
    """JSON-serialisable node memberships + links (for results files)."""
    return {
        "nodes": {name: [int(i) for i in members]
                  for name, members in graph["nodes"].items()},
        "links": {name: list(others) for name, others in graph["links"].items()},
    }


def render_mapper_static(graph: Mapping, path: Path, title: str = "") -> dict:
    """Static Mapper graph PNG: native km.draw_matplotlib, networkx fallback.

    Returns {'method': ...} recording which renderer succeeded (an E1
    capability-matrix datum). Both paths are seeded/deterministic.
    """
    import kmapper as km
    try:
        fig, ax = plt.subplots(figsize=(4.2, 4.2), constrained_layout=True)
        km.draw_matplotlib(graph, ax=ax, fig=fig, layout="kk")
        if title:
            ax.set_title(title)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return {"method": "native km.draw_matplotlib(layout='kk')"}
    except Exception as exc:  # noqa: BLE001 - recorded as an audit finding
        G = km.to_networkx(graph)
        sizes = [max(12.0, len(v) / 3.0) for v in graph["nodes"].values()]
        fig, ax = plt.subplots(figsize=(4.2, 4.2), constrained_layout=True)
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx(G, pos, node_size=sizes, with_labels=False,
                         node_color="tab:orange", ax=ax, width=0.6)
        if title:
            ax.set_title(title)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return {"method": f"networkx fallback (draw_matplotlib failed: "
                          f"{type(exc).__name__}: {exc})"}


_CDN_RE = re.compile(
    r"""(?:src|href)\s*=\s*["'](https?://[^"']+)["']|url\((https?://[^)]+)\)""")


def export_mapper_html(graph: Mapping, path: Path, title: str = "") -> dict:
    """Export the interactive HTML visualization and record its CDN imports.

    Verified finding: the single-file HTML loads its rendering libraries from
    content-delivery networks at view time, so it is NOT an offline artifact.
    Only claim offline support if a local-copy variant is implemented and
    tested — it is not, so none is claimed.
    """
    import kmapper as km
    mapper = km.KeplerMapper()
    t0 = time.perf_counter()
    mapper.visualize(graph, path_html=str(path), title=title)
    elapsed = time.perf_counter() - t0
    html = Path(path).read_text()
    urls = sorted({a or b for a, b in _CDN_RE.findall(html)})
    return {"time_s": round(elapsed, 4), "external_urls": urls}

# ---------------------------------------------------------------- baselines

def render_scatter(X: np.ndarray, path: Path, title: str = "") -> Path:
    """Raw-data scatter (the known-answer reference view for 2-D data)."""
    fig, ax = plt.subplots(figsize=(3.6, 3.6), constrained_layout=True)
    ax.scatter(X[:, 0], X[:, 1], s=6, alpha=0.7, c="tab:blue")
    ax.set_aspect("equal")
    if title:
        ax.set_title(title)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_pca_baseline(X: np.ndarray, path: Path, title: str = "") -> Path:
    """Conventional PCA(2) scatter baseline for the same data.

    For the 2-D synthetic core this is (up to rotation/reflection) the data
    itself; it is included because the audit compares workflow support, and
    the report never declares a universal winner across representation types.
    """
    from sklearn.decomposition import PCA
    Z = PCA(n_components=2).fit_transform(X)
    return render_scatter(Z, path, title=title or "PCA(2) baseline")
