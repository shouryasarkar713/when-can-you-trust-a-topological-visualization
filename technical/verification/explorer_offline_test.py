"""Independent cold-cache OFFLINE browser test of the standalone Mapper explorer.

Usage: python explorer_offline_test.py <viewer index.html> <source-results-root> <out_dir>

* fresh browser context per run (cold cache, no storage), network disabled at the browser level
  (context offline=True) AND every non-file:// request is aborted + logged
* records: all requests attempted, console messages, page errors, failed requests,
  Performance-API resource entries
* iterates EVERY dataset x EVERY cell, reads the rendered DOM (statistics panel, SVG node/edge
  counts) and compares with values derived independently from the exported graph and from the
  SOURCE results (own networkx implementation of V/E/C/cyclomatic and own Jaccard S)
* clicks Export for EVERY cell and compares window.__lastExport with the source
* viewport matrix: horizontal-overflow and clipped-label heuristics + screenshots
"""
import json, sys
from pathlib import Path
import numpy as np
import networkx as nx
from playwright.sync_api import sync_playwright

viewer = Path(sys.argv[1]).resolve()
src = Path(sys.argv[2]).resolve()
out = Path(sys.argv[3]).resolve()
out.mkdir(parents=True, exist_ok=True)


def jac(a, b):
    u = len(a | b)
    return 1.0 if u == 0 else len(a & b) / u


def S(m1, m2):
    def f(A, B):
        return float(np.mean([max(jac(x, y) for y in B) for x in A]))
    return (f(m1, m2) + f(m2, m1)) / 2


def stats(nodes, links):
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for a, bs in links.items():
        for b in bs:
            G.add_edge(a, b)
    C = nx.number_connected_components(G)
    return dict(n_nodes=G.number_of_nodes(), n_edges=G.number_of_edges(), n_components=C,
                cyclomatic_number=G.number_of_edges() - G.number_of_nodes() + C)


# ---- independent expectations from SOURCE results (not from the viewer's embedded data)
e2 = json.loads((src / "results/e2/e2_sensitivity.json").read_text(encoding="utf8"))
wx = json.loads((src / "extensions/meteorology/results/weather_mapper_results.json").read_text(encoding="utf8"))
expect = {}
for blk in e2["shapes"]:
    for c in blk["cells"]:
        key = f"nc{c['n_cubes']}_po{c['perc_overlap']}"
        expect.setdefault(blk["shape"], {})[key] = c["graph"]
for k, c in wx["cells"].items():
    expect.setdefault("weather", {})[k] = c["graph"]

result = {"viewer": str(viewer), "checks": [], "requests": [], "console": [],
          "page_errors": [], "failed_requests": []}


def check(name, ok, detail=""):
    result["checks"].append({"name": name, "pass": bool(ok), "detail": str(detail)[:300]})


with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=True)
    result["browser_version"] = br.version
    ctx = br.new_context(viewport={"width": 1440, "height": 1000}, offline=True,
                         accept_downloads=True, service_workers="block")

    def route(r):
        u = r.request.url
        result["requests"].append({"url": u[:200], "type": r.request.resource_type})
        if u.startswith(("file://", "data:", "blob:")):
            r.continue_()
        else:
            r.abort()
    ctx.route("**/*", route)
    page = ctx.new_page()
    page.on("console", lambda m: result["console"].append({"type": m.type, "text": m.text[:200]}))
    page.on("pageerror", lambda e: result["page_errors"].append(str(e)[:300]))
    page.on("requestfailed", lambda r: result["failed_requests"].append(r.url[:200]))
    page.goto(viewer.as_uri(), wait_until="load")
    page.wait_for_timeout(500)
    result["performance_resource_entries_initial"] = page.evaluate(
        "performance.getEntriesByType('resource').map(e=>e.name)")
    ext_refs = page.evaluate(
        "[...document.querySelectorAll('script[src],link[href],img[src],iframe[src]')].map(e=>e.src||e.href)")
    result["external_tag_references"] = ext_refs
    check("no external script/link/img/iframe tags", len(ext_refs) == 0, ext_refs)
    check("only file:// document request on load",
          all(r["url"].startswith("file://") for r in result["requests"]), result["requests"][:5])

    datasets = page.evaluate("[...document.querySelectorAll('#dataset-select option')].map(o=>o.value)")
    result["datasets"] = datasets
    n_cell = 0
    exports = {}
    for ds in datasets:
        page.select_option("#dataset-select", ds)
        cell_ids = page.evaluate("[...document.querySelectorAll('#cell-select option')].map(o=>o.value)")
        for cid in cell_ids:
            page.select_option("#cell-select", cid)
            vals = page.evaluate("""() => {
              const st = [...document.querySelectorAll('#structure-panel .stat')].map(
                  d => [d.querySelector('span').textContent, d.querySelector('b').textContent]);
              const svg = document.querySelector('#graph-selected svg');
              return {stats: Object.fromEntries(st),
                      n_circles: svg.querySelectorAll('circle').length,
                      n_lines: svg.querySelectorAll('line').length};
            }""")
            page.wait_for_timeout(700)   # Chrome throttles rapid programmatic downloads
            try:
                with page.expect_download(timeout=5000):
                    page.click("#export-btn")
                result["downloads_received"] = result.get("downloads_received", 0) + 1
            except Exception:
                result["downloads_missed"] = result.get("downloads_missed", 0) + 1
            exp = page.evaluate("window.__lastExport")
            check(f"{ds}/{cid}: export object corresponds to the selected cell",
                  exp["selected_cell"]["id"] == cid and exp["dataset"]["id"] == ds)
            exports[(ds, cid)] = exp
            g = exp["selected_cell"]["graph"]
            mine = stats(list(g["nodes"].keys()), g["links"])
            shown = {"n_nodes": int(vals["stats"]["nodes"]), "n_edges": int(vals["stats"]["edges"]),
                     "n_components": int(vals["stats"]["components"]),
                     "cyclomatic_number": int(vals["stats"]["cyclomatic number"])}
            check(f"{ds}/{cid}: displayed stats == independent recomputation", mine == shown,
                  f"shown={shown} mine={mine}")
            check(f"{ds}/{cid}: SVG circles == nodes", vals["n_circles"] == mine["n_nodes"],
                  f"{vals['n_circles']} vs {mine['n_nodes']}")
            n_link_entries = sum(len(v) for v in g["links"].values())
            check(f"{ds}/{cid}: SVG lines == link entries", vals["n_lines"] == n_link_entries,
                  f"{vals['n_lines']} vs {n_link_entries}")
            eg = expect.get(ds, {}).get(cid)
            if eg is not None:
                en = eg["nodes"] if "nodes" in eg else eg
                same = ({k: sorted(v) for k, v in en.items()} ==
                        {k: sorted(v) for k, v in g["nodes"].items()})
                check(f"{ds}/{cid}: exported memberships == source-result memberships", same)
            n_cell += 1
        refx = [e for (d, c), e in exports.items() if d == ds and e["selected_cell"]["is_reference"]]
        if refx:
            rm = [set(v) for v in refx[0]["selected_cell"]["graph"]["nodes"].values()]
            for (d, c), e in exports.items():
                if d != ds:
                    continue
                m = [set(v) for v in e["selected_cell"]["graph"]["nodes"].values()]
                sv = e["selected_cell"]["similarity_to_reference_S"]
                if sv is not None:
                    dec = len(str(sv).split(".")[1]) if "." in str(sv) else 0
                    tol = 0.5 * 10 ** (-dec) + 1e-9   # S is shown at the precision stored in the source results
                    check(f"{ds}/{c}: S(viewer) == S(independent) within source rounding ({dec} d.p.)",
                          abs(S(m, rm) - sv) <= tol, f"{sv} vs {S(m, rm):.5f}")
    result["n_cells_exercised"] = n_cell

    page.select_option("#dataset-select", "weather")
    vp = []
    for (w, h) in [(1920, 1080), (1440, 900), (1366, 768), (1024, 768), (768, 1024), (390, 844)]:
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(250)
        m = page.evaluate("""() => {
          const de = document.documentElement;
          const clipped = [];
          document.querySelectorAll('h1,h2,h3,label,button,dt,dd,.stat,.note,.def,.warn-box,td,th,summary,li').forEach(e => {
            const cs = getComputedStyle(e);
            if (e.scrollWidth > e.clientWidth + 1 && cs.overflowX !== 'visible' && e.clientWidth > 0)
              clipped.push((e.id||e.className||e.tagName)+':'+e.scrollWidth+'>'+e.clientWidth);
          });
          const over = [];
          document.querySelectorAll('body *').forEach(e => {
            const r = e.getBoundingClientRect();
            if (r.right > de.clientWidth + 2 && r.width > 0) over.push((e.id||e.className||e.tagName).toString().slice(0,30));
          });
          return {scrollW: de.scrollWidth, clientW: de.clientWidth,
                  clipped: clipped.slice(0,10), overflowing: [...new Set(over)].slice(0,10)};
        }""")
        m["viewport"] = f"{w}x{h}"
        page.screenshot(path=str(out / f"viewer_{w}x{h}.png"), full_page=True)
        vp.append(m)
    result["viewport_matrix"] = vp
    for m in vp:
        check(f"viewport {m['viewport']}: no horizontal page overflow",
              m["scrollW"] <= m["clientW"] + 1, m)
        check(f"viewport {m['viewport']}: no clipped text elements", len(m["clipped"]) == 0, m["clipped"])
    result["performance_resource_entries_final"] = page.evaluate(
        "performance.getEntriesByType('resource').map(e=>e.name)")
    br.close()

nonfile = [r for r in result["requests"] if not r["url"].startswith(("file://", "data:", "blob:"))]
check("zero attempted non-file requests (whole session)", len(nonfile) == 0, nonfile[:5])
check("zero console errors/warnings", all(c["type"] not in ("error", "warning") for c in result["console"]),
      result["console"][:5])
check("zero uncaught page errors", len(result["page_errors"]) == 0, result["page_errors"])
check("zero Performance-API resource entries (final)",
      len(result["performance_resource_entries_final"]) == 0, result["performance_resource_entries_final"][:3])
result["summary"] = {"n_checks": len(result["checks"]), "n_pass": sum(c["pass"] for c in result["checks"]),
                     "failed": [c for c in result["checks"] if not c["pass"]][:25]}
(out / "explorer_offline_test.json").write_text(json.dumps(result, indent=1), encoding="utf8")
print(json.dumps(result["summary"], indent=1)[:4000])
