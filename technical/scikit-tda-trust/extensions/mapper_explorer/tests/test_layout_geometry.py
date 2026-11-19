"""Regression tests for the radius-aware component-separated layout of the offline explorer.

They check, for all 35 saved cells and with the radii the viewer actually draws:
  * structural invariants: the layout switch changes coordinates only (nodes, edges, memberships,
    components, cyclomatic number, node radii);
  * geometry: finite coordinates, no clipping, no circle overlap (centre distance >= R_i + R_j + clearance),
    separated component bounding boxes, singleton placement, determinism.
No browser is needed (the browser-level check of the same cells is the offline explorer test)."""
from __future__ import annotations

import json
import math
import re
import sys
from itertools import combinations
from pathlib import Path

import networkx as nx
import pytest

EXT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXT / "scripts"))
import layout_geometry as LG  # noqa: E402

DATA = EXT / "data" / "explorer_data.json"
TEMPLATE = EXT / "viewer" / "template.html"
HTML = EXT / "viewer" / "index.html"
TOL = 0.02          # documented numerical tolerance (drawing units, on a drawing 100 units wide)


def _cells():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    out = []
    for name, ds in d["datasets"].items():
        for c in ds["cells"]:
            out.append((name, c))
    return out


CELLS = _cells()
IDS = [f"{n}:{c['id']}" for n, c in CELLS]


def _graph(c):
    G = nx.Graph()
    G.add_nodes_from(c["graph"]["nodes"])
    for a, nb in c["graph"]["links"].items():
        for b in nb:
            G.add_edge(a, b)
    return G


def _edge_set(c):
    return {tuple(sorted((a, b))) for a, nb in c["graph"]["links"].items() for b in nb}


def _abs_positions(c):
    W, H = c["layout_separated_viewbox"]
    return {n: (p[0] * W, p[1] * H) for n, p in c["layout_separated"].items()}, W, H


def test_renderer_radius_rule_matches_the_layout_module():
    """The layout must use the renderer's own radius rule (template.html) and stroke width."""
    t = TEMPLATE.read_text(encoding="utf-8")
    m = re.search(r"var r = ([0-9.]+) \+ ([0-9.]+) \* Math\.sqrt\(members\.length / maxN\);", t)
    assert m, "radius rule not found in the viewer template"
    assert (float(m.group(1)), float(m.group(2))) == (LG.R_MIN, LG.R_RANGE)
    assert 'c.setAttribute("stroke-width", 0.28)' in t and LG.STROKE == 0.28
    # the embedded viewer carries the same rule
    h = HTML.read_text(encoding="utf-8")
    assert m.group(0) in h


def _fail(msgs):
    assert not msgs, "; ".join(msgs[:8]) + (f" (+{len(msgs) - 8} more)" if len(msgs) > 8 else "")


def test_structural_invariants_hold_for_every_cell():
    """Both layouts cover exactly the saved graph's nodes; edges, components, cyclomatic number and
    memberships come from the one saved graph, so the layout switch cannot change them."""
    bad = []
    for name, cell in CELLS:
        tag = f"{name}:{cell['id']}"
        nodes = set(cell["graph"]["nodes"])
        if set(cell["layout_native"]) != nodes or set(cell["layout_separated"]) != nodes:
            bad.append(f"{tag}: layout node ids differ from the graph")
        if len(_edge_set(cell)) != cell["structure"]["n_edges"] or len(nodes) != cell["structure"]["n_nodes"]:
            bad.append(f"{tag}: node/edge counts differ from the saved statistics")
        G = _graph(cell)
        if nx.number_connected_components(G) != cell["structure"]["n_components"]:
            bad.append(f"{tag}: component count")
        cyc = G.number_of_edges() - G.number_of_nodes() + nx.number_connected_components(G)
        if cyc != cell["structure"]["cyclomatic_number"]:
            bad.append(f"{tag}: cyclomatic number")
        for key in ("layout_native", "layout_separated"):
            if any(len(p) != 2 for p in cell[key].values()):
                bad.append(f"{tag}: {key} holds non-coordinate data")
    _fail(bad)


def test_node_radii_depend_only_on_membership():
    """The renderer sizes a node from its membership alone, so both layouts draw identical radii and
    node area stays proportional to membership (r = 1.6 + 4.6 sqrt(n / n_max))."""
    for name, cell in CELLS:
        r = LG.node_radii(cell["graph"]["nodes"])
        mx = max(len(v) for v in cell["graph"]["nodes"].values())
        for n, v in cell["graph"]["nodes"].items():
            assert r[n] == pytest.approx(1.6 + 4.6 * math.sqrt(len(v) / mx)), (name, cell["id"], n)


def test_coordinates_finite_and_circles_inside_the_drawing_area():
    bad = []
    for name, cell in CELLS:
        pos, W, H = _abs_positions(cell)
        R = LG.node_radii(cell["graph"]["nodes"])
        if W != 100.0 or H < LG.VIEW_H_NATIVE - 1e-6:
            bad.append(f"{name}:{cell['id']}: viewBox {W} x {H}")
        for n, (x, y) in pos.items():
            ro = LG.outer_radius(R[n])
            if not (math.isfinite(x) and math.isfinite(y)):
                bad.append(f"{name}:{cell['id']}:{n}: not finite")
            elif not (ro - TOL <= x <= W - ro + TOL and ro - TOL <= y <= H - ro + TOL):
                bad.append(f"{name}:{cell['id']}:{n}: circle clipped at ({x:.1f}, {y:.1f})")
    _fail(bad)


def test_no_circle_overlaps_using_rendered_radii():
    """d(i, j) >= R_i + R_j + delta for every pair, with the radii the viewer draws (not centre distances alone)."""
    bad = []
    for name, cell in CELLS:
        pos, W, H = _abs_positions(cell)
        R = LG.node_radii(cell["graph"]["nodes"])
        worst = math.inf
        for a, b in combinations(pos, 2):
            d = math.hypot(pos[a][0] - pos[b][0], pos[a][1] - pos[b][1])
            worst = min(worst, d - (LG.outer_radius(R[a]) + LG.outer_radius(R[b]) + LG.CLEARANCE))
        if worst < -TOL:
            bad.append(f"{name}:{cell['id']}: circles closer than R_i + R_j + clearance by {-worst:.3f}")
    _fail(bad)


def test_component_bounding_boxes_are_separated_by_the_padding():
    bad = []
    for name, cell in CELLS:
        pos, W, H = _abs_positions(cell)
        R = LG.node_radii(cell["graph"]["nodes"])
        boxes = []
        for comp in nx.connected_components(_graph(cell)):
            boxes.append((min(pos[n][0] - LG.outer_radius(R[n]) for n in comp), max(pos[n][0] + LG.outer_radius(R[n]) for n in comp),
                          min(pos[n][1] - LG.outer_radius(R[n]) for n in comp), max(pos[n][1] + LG.outer_radius(R[n]) for n in comp)))
        for (a0, a1, b0, b1), (c0, c1, d0, d1) in combinations(boxes, 2):
            if max(c0 - a1, a0 - c1, d0 - b1, b0 - d1) < LG.PADDING - TOL:
                bad.append(f"{name}:{cell['id']}: two component boxes closer than the padding")
    _fail(bad)


def test_singleton_components_are_placed_inside_and_apart():
    n_single = 0
    for name, cell in CELLS:
        G = _graph(cell)
        pos, W, H = _abs_positions(cell)
        for comp in nx.connected_components(G):
            if len(comp) == 1:
                n_single += 1
                (n,) = comp
                assert 0 < pos[n][0] < W and 0 < pos[n][1] < H, (name, cell["id"], n)
    assert n_single >= 5            # the saved cells do contain singleton components


def test_layout_is_deterministic_for_the_saved_cells():
    """Recomputing the layout from a saved graph reproduces the stored coordinates exactly."""
    for name, cell in CELLS:
        pos, box = LG.radius_aware_component_layout(cell["graph"]["nodes"], cell["graph"]["links"])
        assert pos == cell["layout_separated"], (name, cell["id"])
        assert box == cell["layout_separated_viewbox"], (name, cell["id"])


def test_layout_is_deterministic_on_repeat():
    name, cell = next((n, c) for n, c in CELLS if n == "weather" and c["id"] == "nc20_po0.35")
    a = LG.radius_aware_component_layout(cell["graph"]["nodes"], cell["graph"]["links"])
    b = LG.radius_aware_component_layout(cell["graph"]["nodes"], cell["graph"]["links"])
    assert a == b


def test_problem_cell_weather_20_035_is_separated_and_uncrowded():
    """The reported case: 40 nodes, 2 components. Two components visibly apart, no overlaps, roughly the
    area of the native panel (the drawing area may grow, the circles never shrink)."""
    name, cell = next((n, c) for n, c in CELLS if n == "weather" and c["id"] == "nc20_po0.35")
    assert cell["structure"]["n_components"] == 2 and cell["structure"]["n_nodes"] == 40
    pos, W, H = _abs_positions(cell)
    G = _graph(cell)
    comps = sorted(nx.connected_components(G), key=len)
    small, big = comps[0], comps[-1]
    assert len(small) == 1
    (sx, sy), = [pos[n] for n in small]
    R = LG.node_radii(cell["graph"]["nodes"])
    bx0 = min(pos[n][0] - R[n] for n in big)
    bx1 = max(pos[n][0] + R[n] for n in big)
    by0 = min(pos[n][1] - R[n] for n in big)
    by1 = max(pos[n][1] + R[n] for n in big)
    outside = not (bx0 <= sx <= bx1 and by0 <= sy <= by1)
    assert outside, "the singleton component must not sit inside the large component's bounds"
    assert H <= 2.0 * LG.VIEW_H_NATIVE


def test_unavoidable_growth_is_explicit_not_silent():
    """If the nodes need more room than the native panel, the drawing area (viewBox) grows; it is
    stored with the cell and never exceeds a documented bound."""
    for name, cell in CELLS:
        W, H = cell["layout_separated_viewbox"]
        assert W == 100.0
        assert LG.VIEW_H_NATIVE - 1e-6 <= H <= 3.0 * LG.VIEW_H_NATIVE, (name, cell["id"], H)
