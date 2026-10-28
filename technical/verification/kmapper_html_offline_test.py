"""Cold-cache, network-disabled test of the STOCK kmapper HTML export (baseline figures/e1/*.html)."""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
html = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2])
res = {"file": html.name, "requests": [], "console_errors": []}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(offline=True, service_workers="block")
    pg = ctx.new_page()
    pg.on("request", lambda r: res["requests"].append(r.url[:120]))
    pg.on("console", lambda m: res["console_errors"].append(m.text[:140]) if m.type == "error" else None)
    pg.on("pageerror", lambda e: res["console_errors"].append("pageerror: " + str(e)[:140]))
    pg.goto(html.as_uri(), wait_until="load"); pg.wait_for_timeout(1500)
    res["svg_circles"] = pg.evaluate("document.querySelectorAll('svg circle').length")
    res["svg_lines"] = pg.evaluate("document.querySelectorAll('svg line').length")
    res["external_tags"] = pg.evaluate("[...document.querySelectorAll('script[src],link[href],img[src]')].map(e=>e.src||e.href)")
    b.close()
res["cdn_references_in_source"] = sorted(set(__import__("re").findall(r"https?://[^\"' )<>]+", html.read_text(encoding="utf8"))))
out.write_text(json.dumps(res, indent=1)); print(json.dumps({k: (v if k not in ("requests",) else len(v)) for k, v in res.items()})[:1500])
