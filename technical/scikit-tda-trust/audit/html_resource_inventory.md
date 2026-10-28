# E1 HTML Resource Inventory — KeplerMapper Interactive Export

Audit of the external resources referenced by the HTML files generated in
this repository (`figures/e1/{annulus,figure_eight,blob,three_blobs}_mapper.html`,
produced by `kmapper.visualize`, kmapper 2.1.0). All four files reference the
identical resource set (verified by URL extraction on each file). Evidence
sources: (a) HTML source inspection, (b) live browser network log, (c) a
genuine cold-cache offline browser test — see
`results/e1/offline_browser_test.json`.

## External resources

| # | URL | Element / role | Purpose | Required for the graph to render? | Evidence |
|---|-----|----------------|---------|-----------------------------------|----------|
| 1 | `https://cdnjs.cloudflare.com/ajax/libs/d3/6.1.1/d3.js` | `<script src>` | D3.js — draws the graph (SVG node groups, edge lines, force layout, tooltips) | **YES — hard dependency** | HTML inspection; network log (loaded online); offline test: `typeof d3 === false`, 0 nodes, 0 edges rendered |
| 2 | `https://cdn.jsdelivr.net/npm/file-saver@2.0.2/dist/FileSaver.min.js` | `<script src>` | FileSaver.js — used only by the "capture canvas" download button (`saveAs(fileToSave, fileName)`) | No — rendering works without it; only the PNG-download feature needs it | HTML inspection (sole call site is the capture handler); network log |
| 3 | `https://fonts.googleapis.com/css?family=Roboto+Mono:700,300` (+ `fonts.gstatic.com` woff2) | `<link rel=stylesheet>` | Google Fonts "Roboto Mono" webfont — typography only; browser falls back to system monospace if unavailable | No — cosmetic | HTML inspection; network log (both CSS and woff2 fetched online) |
| 4 | `http://i.imgur.com/axOG6GJ.jpg` | `<link rel="icon">` | Browser-tab favicon image (a small kmapper logo) — decorative | No — cosmetic; moreover the request was **rate-limited (HTTP 429) even in the online test** | HTML inspection; network log (429 online, failed offline) |

## Inline (no network) content

- The KeplerMapper logo displayed in the page header is an inline
  `data:image/png;base64` URI, not the imgur URL.
- SVG filters (`url(#drop-shadow-glow)`, `url(#drop-shadow-pulse)`) are
  internal references.
- The complete graph data (`var graph = {nodes, links, ...}`) and all styles
  and page text are embedded in the single file.
- Several `stackoverflow.com` URLs appear only inside code comments
  (attribution notes), not as resource loads.

## Findings

1. **The single-file HTML export is not an offline artifact.** The graph is
   rendered client-side by D3 fetched from a CDN at view time. Verified by a
   genuine browser test: cold cache + network disabled → D3 fails to load →
   the SVG canvas stays empty (0 node groups, 0 edge lines); only the inline
   static text sections display. Procedure and screenshots:
   `results/e1/offline_browser_test.json`, `results/e1/browser_test/*.png`.
2. **A warm cache can mask the dependency.** Reloading offline after an
   online visit still rendered (scripts served from Chromium's cache). Any
   offline claim based on such a reload would be misleading; the accepted
   test uses a fresh session with offline enabled before navigation.
3. **Even the online experience has an external fragility**: the imgur
   favicon was rate-limited (HTTP 429) during the online test. This does
   not affect the graph, but it shows third-party availability leaking into
   the artifact.
4. **Static PNG figures remain the dependable presentation fallback** for
   offline contexts (e.g., the course presentation). Bundling D3/FileSaver
   locally is feasible but out of scope for the core experiments and is not
   implemented; no offline-support claim beyond the test above is made.
