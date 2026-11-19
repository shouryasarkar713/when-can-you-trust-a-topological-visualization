"""Offline browser test of the explorer's two graph renderings on representative saved cells.

Usage: python explorer_layout_browser_test.py <viewer index.html> <out.json>

For each tested cell (weather (20, 0.35) is the cell that exposed the original overlap; the others cover a
connected weather cell, the annulus and figure-eight reference cells, a highly fragmented blob control and
the figure-eight cell with four components) and for the three layout modes (side-by-side, native, separated):

  * the network is switched off (context offline) and every non-file request is aborted and logged;
  * no console error / warning and no page error;
  * the layout switch works (the right panels are shown/hidden) and the statistics panel text is identical
    in all modes;
  * every node of the saved graph is drawn exactly once and every edge exactly once, in both renderings;
  * a node has the same radius in both renderings (taken from the DOM);
  * in the component-separated drawing no two circles overlap (distance >= r_i + r_j + stroke + 0.8 - 0.02)
    and every circle lies inside the viewBox;
  * the exported JSON keeps graph, provenance and both layouts.
"""
import json
import math
import sys
from itertools import combinations
from pathlib import Path

from playwright.sync_api import sync_playwright

viewer = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
CASES = [("weather", "nc20_po0.35"), ("weather", "nc20_po0.5"), ("weather", "nc10_po0.35"), ("annulus", "nc10_po0.35"),
         ("figure_eight", "nc10_po0.35"), ("figure_eight", "nc20_po0.2"), ("blob", "nc20_po0.2"), ("annulus", "nc20_po0.5")]
CLEAR, TOL, STROKE = 0.8, 0.02, 0.28

requests, console, page_errors = [], [], []
results, failures = [], []


def fail(msg):
    failures.append(msg)


def svg_nodes(page, sel):
    return page.evaluate("""(sel) => {
      const svg = document.querySelector(sel + ' svg'); if (!svg) return null;
      const vb = svg.getAttribute('viewBox').split(' ').map(Number);
      const circles = [...svg.querySelectorAll('circle')].map(c => ({
        name: c.querySelector('title').textContent.split(' — ')[0],
        cx: +c.getAttribute('cx'), cy: +c.getAttribute('cy'), r: +c.getAttribute('r')}));
      return { vb: vb, circles: circles, lines: svg.querySelectorAll('line').length };
    }""", sel)


with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(offline=True, viewport={"width": 1440, "height": 900}, service_workers="block")
    page = ctx.new_page()

    def route(r):
        u = r.request.url
        if u.startswith("file:"):
            r.continue_()
        else:
            requests.append(u)
            r.abort()

    ctx.route("**/*", route)
    page.on("console", lambda m: console.append((m.type, m.text)) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("request", lambda r: requests.append(r.url) if not r.url.startswith("file:") else None)
    page.goto(viewer.as_uri(), wait_until="load")
    for ds, cid in CASES:
        page.select_option("#dataset-select", ds)
        page.select_option("#cell-select", cid)
        page.wait_for_timeout(300)
        tag = f"{ds}:{cid}"
        stats_by_mode, shown = {}, {}
        side = {}
        for mode in ("side", "native", "separated"):
            page.check(f"input[name=layout][value={mode}]")
            page.wait_for_timeout(200)
            stats_by_mode[mode] = page.inner_text("#structure-panel") if page.locator("#structure-panel").count() else page.inner_text("body")[:2000]
            shown[mode] = (page.locator("#box-selected").is_visible(), page.locator("#box-separated").is_visible())
            if mode == "side":
                side["native"] = svg_nodes(page, "#graph-selected")
                side["separated"] = svg_nodes(page, "#graph-separated")
            elif mode == "native":
                side["native_only"] = svg_nodes(page, "#graph-selected")
            else:
                side["separated_only"] = svg_nodes(page, "#graph-selected")
        page.check("input[name=layout][value=side]")
        # layout switching works
        if shown["side"] != (True, True) or shown["native"] != (True, False) or shown["separated"] != (True, False):
            fail(f"{tag}: layout switching shows wrong panels {shown}")
        # statistics identical across modes
        if len({stats_by_mode[m] for m in stats_by_mode}) != 1:
            fail(f"{tag}: statistics text differs between layout modes")
        page.click("#export-btn")
        exp = page.evaluate("window.__lastExport")
        sel = exp["selected_cell"]
        nodes = sel["graph"]["nodes"]
        n_edges = sum(len(v) for v in sel["graph"]["links"].values())
        for key in ("native", "separated", "native_only", "separated_only"):
            d = side[key]
            if d is None:
                fail(f"{tag}: no svg for {key}")
                continue
            if len(d["circles"]) != len(nodes) or {c["name"] for c in d["circles"]} != set(nodes):
                fail(f"{tag}: {key}: nodes drawn != saved nodes")
            if d["lines"] != n_edges:
                fail(f"{tag}: {key}: edges drawn {d['lines']} != saved {n_edges}")
        # same radius for the same node in both renderings
        rn = {c["name"]: c["r"] for c in side["native"]["circles"]}
        rs = {c["name"]: c["r"] for c in side["separated"]["circles"]}
        if rn != rs:
            fail(f"{tag}: node radii differ between renderings")
        # geometry of the separated drawing, measured on the DOM
        sep = side["separated"]
        W, H = sep["vb"][2], sep["vb"][3]
        worst = math.inf
        clipped = 0
        for c in sep["circles"]:
            ro = c["r"] + STROKE / 2
            if not (ro - TOL <= c["cx"] <= W - ro + TOL and ro - TOL <= c["cy"] <= H - ro + TOL):
                clipped += 1
        for a, c2 in combinations(sep["circles"], 2):
            d = math.hypot(a["cx"] - c2["cx"], a["cy"] - c2["cy"])
            worst = min(worst, d - (a["r"] + c2["r"] + STROKE + CLEAR))
        if clipped:
            fail(f"{tag}: {clipped} circles outside the separated viewBox")
        if worst < -TOL:
            fail(f"{tag}: separated circles overlap (worst margin {worst:.3f})")
        # export keeps provenance and both layouts
        if not (exp.get("provenance") and exp["selected_cell"]["layouts"]["native"] and exp["selected_cell"]["layouts"]["component_separated"]):
            fail(f"{tag}: export lacks provenance or layouts")
        results.append({"cell": tag, "nodes": len(nodes), "edges": n_edges, "separated_viewbox": sep["vb"][2:], "min_circle_margin": round(worst, 3),
                        "native_overlapping_pairs_in_dom": sum(1 for a, c2 in combinations(side["native"]["circles"], 2)
                                                               if math.hypot(a["cx"] - c2["cx"], a["cy"] - c2["cy"]) < a["r"] + c2["r"])})
    b.close()

summary = {"viewer": str(viewer.name), "cells_tested": len(CASES), "external_requests": requests, "console_errors_or_warnings": console,
           "page_errors": page_errors, "failures": failures, "per_cell": results,
           "pass": not failures and not requests and not console and not page_errors}
out.write_text(json.dumps(summary, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k != "per_cell"}, indent=1))
for r in results:
    print(r)
sys.exit(0 if summary["pass"] else 1)
