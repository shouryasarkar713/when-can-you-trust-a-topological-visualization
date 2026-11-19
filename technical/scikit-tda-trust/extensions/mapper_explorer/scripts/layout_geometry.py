"""Radius-aware component-separated layout for the offline Mapper explorer (rendering only).

Why this module exists
----------------------
The first component-separated layout (src.figures.component_separated_layout followed by the explorer's
independent per-axis normalisation) placed node CENTRES only. Each component was rescaled into a band
that is 0.325 units tall in a stack of bands about 1.3 units high, and the whole stack was then stretched
independently in x and y into the drawing area. For a graph such as the weather cell (20, 0.35) (40 nodes,
2 components) that flattened the large component to roughly a quarter of its natural height while the
rendered circles (radius 1.6 - 6.2 drawing units, independent of the layout) kept their size, so the
circles of one component covered each other. Node radii were never part of the layout calculation.

What it does
------------
* The radius of every node is computed with the SAME rule as the renderer (viewer/template.html):
      r = 1.6 + 4.6 * sqrt(members / max members in the cell)         (drawing units)
  plus half the stroke width. Node area therefore stays proportional to the membership size.
* Each connected component is laid out on its own: seeded spring layout (initial structure), scaled so
  that edges have a visible length, then relaxed with circle-collision constraints
      d(i, j) >= R_i + R_j + CLEARANCE
  (R = rendered outer radius) and a weak pull that keeps long edges from stretching.
* Components are packed with a shelf algorithm using their complete rendered bounds
  (circles included) plus PADDING. The drawing area is 100 units wide and grows taller when the
  components need more room; nodes are never shrunk.
* Deterministic: sorted node order, fixed seed, no randomness. Only coordinates are produced: the graph
  (nodes, edges, memberships) is never modified.
"""
from __future__ import annotations

import math

import networkx as nx
import numpy as np

VIEW_W = 100.0
VIEW_H_NATIVE = 100.0 * 380 / 460      # native panel: viewBox 0 0 100 82.61 (canvas 460 x 380)
R_MIN, R_RANGE = 1.6, 4.6              # must equal the renderer in viewer/template.html
STROKE = 0.28                          # circle stroke width in the renderer
CLEARANCE = 0.8                        # required gap between circle edges (drawing units)
EDGE_GAP = 1.0                         # initial visible edge length between circle edges
PADDING = 3.0                          # gap between component bounding boxes
MARGIN = 1.5                           # keeps every circle inside the drawing area
DISP_TOL = 0.80                        # RMS relaxation displacement allowed, in mean node radii
FILL_TARGET = 0.30                     # circle area / component bounding-box area to aim for
OVERLAP_TOL = 1e-3                     # documented tolerance of the relaxation (drawing units)


def node_radii(nodes: dict) -> dict:
    """Rendered circle radius per node (same rule as the viewer)."""
    mx = max([len(v) for v in nodes.values()] + [1])
    return {n: R_MIN + R_RANGE * math.sqrt(len(v) / mx) for n, v in nodes.items()}


def outer_radius(r: float) -> float:
    return r + STROKE / 2.0


def _relax(P: np.ndarray, R: np.ndarray, E: list, max_iter: int = 4000) -> bool:
    """Push overlapping circles apart (Jacobi iterations); weakly pull overlong edges. True when converged."""
    n = len(P)
    if n < 2:
        return True
    need = R[:, None] + R[None, :] + CLEARANCE
    np.fill_diagonal(need, 0.0)
    angles = (np.arange(n)[:, None] * 2.399963 + np.arange(n)[None, :] * 1.0)
    for _ in range(max_iter):
        for i, j in E:
            d = P[j] - P[i]
            dist = float(np.hypot(d[0], d[1]))
            rest = (R[i] + R[j] + CLEARANCE + EDGE_GAP) * 2.0
            if dist > rest:
                f = 0.03 * (dist - rest) / dist
                P[i] += d * f
                P[j] -= d * f
        diff = P[None, :, :] - P[:, None, :]                      # diff[i, j] = P[j] - P[i]
        dist = np.hypot(diff[..., 0], diff[..., 1])
        over = need - dist
        np.fill_diagonal(over, 0.0)
        mask = over > 0
        if not mask.any():
            return True
        if over.max() < OVERLAP_TOL:
            return True
        safe = np.where(dist < 1e-9, 1.0, dist)
        ux = np.where(dist < 1e-9, np.cos(angles), diff[..., 0] / safe)
        uy = np.where(dist < 1e-9, np.sin(angles), diff[..., 1] / safe)
        push = np.where(mask, over / 2.0 + 1e-4, 0.0)
        P[:, 0] -= (push * ux).sum(axis=1) * 0.6
        P[:, 1] -= (push * uy).sum(axis=1) * 0.6
    return False


def _bounds(P: np.ndarray, R: np.ndarray):
    return (float((P[:, 0] - R).min()), float((P[:, 0] + R).max()),
            float((P[:, 1] - R).min()), float((P[:, 1] + R).max()))


def _component_layout(sub: nx.Graph, names: list, Rmap: dict, avail_w: float):
    """Centre coordinates (array in `names` order) of one component, collision-free, width <= avail_w."""
    n = len(names)
    R = np.array([outer_radius(Rmap[k]) for k in names])
    if n == 1:
        return np.zeros((1, 2)), R
    idx = {k: i for i, k in enumerate(names)}
    E = [(idx[a], idx[b]) for a, b in sub.edges()]
    p = nx.spring_layout(sub, seed=42)
    P = np.array([p[k] for k in names], dtype=float)
    P -= P.mean(axis=0)
    # align the principal axis with x so that wide components use the drawing width, not its height
    _, _, vt = np.linalg.svd(P, full_matrices=False)
    P = P @ vt.T
    ulen = [float(np.hypot(*(P[i] - P[j]))) for i, j in E]
    med = float(np.median(ulen)) if ulen and np.median(ulen) > 1e-9 else 1.0
    target = float(np.median([R[i] + R[j] for i, j in E])) + CLEARANCE + EDGE_GAP
    P0 = P * (target / med)
    meanR = float(R.mean())
    # smallest scale at which the collision relaxation only has to make small corrections: the seeded
    # spring layout then keeps its overall shape (rings stay rings) instead of being rearranged
    s = 0.6
    Q = None
    for _ in range(60):
        cand = P0 * s
        Q = cand.copy()
        conv = _relax(Q, R, E)
        disp = float(np.sqrt(((Q - cand) ** 2).sum(axis=1).mean()))
        if conv and disp < DISP_TOL * meanR:
            break
        s *= 1.06
    P = Q
    # breathing room: expand uniformly until circles fill at most FILL_TARGET of the component's bounds
    # (never past the drawing width); expansion cannot create overlaps
    area_circles = float((math.pi * R ** 2).sum())
    for _ in range(60):
        x0, x1, y0, y1 = _bounds(P, R)
        if area_circles / ((x1 - x0) * (y1 - y0)) <= FILL_TARGET or (x1 - x0) * 1.05 > avail_w:
            break
        P = P * 1.05
    # keep the component inside the drawing width: squeeze x, stretch y (area preserved), re-relax
    for _ in range(40):
        x0, x1, _, _ = _bounds(P, R)
        width = x1 - x0
        if width <= avail_w:
            break
        f = max(0.8, (avail_w / width) * 0.985)
        P[:, 0] *= f
        P[:, 1] /= f
        _relax(P, R, E)
    return P, R


def radius_aware_component_layout(nodes: dict, links: dict, margin: float = MARGIN):
    """Return (positions, box): positions normalised to the drawing box, box = [100, height].

    `nodes` maps node id -> member point list, `links` maps node id -> neighbour list (saved graph format).
    """
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for a, nbrs in links.items():
        for b in nbrs:
            G.add_edge(a, b)
    Rmap = node_radii(nodes)
    comps = sorted(nx.connected_components(G), key=lambda c: (-len(c), sorted(map(str, c))))
    avail_w = VIEW_W - 2 * margin
    parts = []
    for comp in comps:
        names = sorted(comp, key=str)
        sub = nx.Graph()
        sub.add_nodes_from(names)
        sub.add_edges_from(G.subgraph(names).edges())
        P, R = _component_layout(sub, names, Rmap, avail_w)
        x0, x1, y0, y1 = _bounds(P, R)
        P = P - np.array([x0, y0])                   # component box starts at (0, 0)
        parts.append({"names": names, "P": P, "R": R, "w": x1 - x0, "h": y1 - y0})
    # shelf packing (largest component first); rows are filled left to right
    x = y = row_h = 0.0
    placed = []
    row = []
    for part in parts:
        if row and x + part["w"] > avail_w:
            placed.append((row, y, row_h))
            y += row_h + PADDING
            x = row_h = 0.0
            row = []
        row.append((part, x))
        x += part["w"] + PADDING
        row_h = max(row_h, part["h"])
    if row:
        placed.append((row, y, row_h))
    total_h = (placed[-1][1] + placed[-1][2]) if placed else 0.0
    H = max(VIEW_H_NATIVE, total_h + 2 * margin)
    y_off = (H - total_h) / 2.0
    pos = {}
    for row, ry, rh in placed:
        row_w = sum(p["w"] for p, _ in row) + PADDING * (len(row) - 1)
        x_off = (VIEW_W - row_w) / 2.0
        for part, rx in row:
            cy = (rh - part["h"]) / 2.0              # vertical centring inside the row
            for k, name in enumerate(part["names"]):
                px = x_off + rx + part["P"][k, 0]
                py = y_off + ry + cy + part["P"][k, 1]
                pos[name] = [round(px / VIEW_W, 5), round(py / H, 5)]
    return pos, [VIEW_W, round(H, 3)]
