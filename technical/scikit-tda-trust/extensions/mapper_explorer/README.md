# Extension B — Mapper Sensitivity Explorer (Stage 3)

**Research question (RQ2, as answerable by this artifact):** can a compact,
fully-offline tool make Mapper's parameter-dependent structural changes
*inspectable, comparable, and reproducible* side-by-side with their saved
provenance — without recomputing anything and without overstating what the
comparison means?

**Status:** Stage 3 complete (2026-10-22). Awaiting review gate. Stage 4
(resampling stability) has **not** been started.

---

## 1. What this is (and is not)

A single-file, offline HTML viewer over the project's **saved** Mapper
experiment outputs. It displays the annulus and figure-eight parameter grids
(baseline E2), the no-loop blob sanity control, and the real-data weather
grid from Extension A — including the day-of-year lens variant — with point
clouds, saved persistence diagrams, reference-cell comparisons, and an export
facility. It never recomputes Mapper or persistent homology.

It is **not**:

- the first Mapper explorer (prior art: Mapper Interactive, PacificVis 2021;
  tda-mapper 2024; Ayasdi historically — see `PRIOR_ART.md`);
- a new graph-stability algorithm or metric;
- evidence about human readability: the project has **no participant
  study**, and this viewer makes no such claim.

## 2. Startup

No installation, no server, no network:

```
open extensions/mapper_explorer/viewer/index.html      # double-click works too
```

The file is self-contained (~0.6 MB): all data is inlined at build time;
there are no CDN scripts, hosted fonts, or images. Tested with headless
Chromium (offline mode ON, cold cache) on Linux x86_64 — see
`results/browser_test.json`. Any modern browser is expected to work;
Safari/Edge and mobile browsers are **untested**. If a browser blocks
file:// pages entirely, any static file server also works (e.g.
`python -m http.server` from the repository root), but no server is
required.

Keyboard: **←/→** move between parameter cells.

## 3. Rebuilding from saved results

```
# project venv active, from the repository root
python extensions/mapper_explorer/scripts/build_viewer.py
python -m pytest extensions/mapper_explorer/tests/ -q     # 19 tests
```

The builder reads only the saved outputs (E2 sensitivity + blob sanity,
Extension A weather mapper/analysis results, E1 point clouds and persistence
diagrams), verifies each cell's graph against its saved structure statistics,
computes the two deterministic layouts with the same seeds as the project
figures, and writes `viewer/index.html`, `data/explorer_data.json`, and
`results/build_report.json` (with source SHA-256 checksums). Missing inputs
produce a clear `BUILD ERROR` naming the missing artifact.

## 4. Required user-visible features → implementation & test evidence

| # | Required feature | Implementation | Test evidence |
|---|---|---|---|
| 1 | Dataset selection: annulus, figure-eight, no-loop blob, weather | sidebar `#dataset-select` (4 options, labelled with tier) | pytest `test_four_datasets_expected_cells`; browser: options enumerated |
| 2 | Parameter-cell control for grid datasets | `#cell-select` dropdown (labels show n/e/c) + prev/next buttons + ←/→ keys | pytest `test_every_cell_matches_saved_source`; browser: 9 weather options, keyboard nav verified |
| 3 | Graph rendering exactly matching the selected saved cell | SVG built from the embedded `graph.nodes/links` of that cell only | pytest: embedded graphs == source JSONs cell-for-cell; browser: annulus ref renders 20 nodes / 21 edges == saved stats |
| 4 | Visible resolution, overlap, lens, clustering config, seed | `#meta-panel` (n_cubes, perc_overlap, lens, clusterer, seed, n_points, tier) | pytest `test_required_ui_elements_present`; browser: metadata verified |
| 5 | Structural summaries: nodes, edges, components, defined cycle statistic | `#structure-panel`: 6 statistics incl. cyclomatic number with its definition (E−V+C, graph-theoretic) and max/mean basis-cycle length | pytest structure == saved sources; browser: weather (20,0.35) shows 40/49/2/11 |
| 6 | Comparison with the reference cell | reference graph panel + `#delta-table` (Δ nodes/edges/components/cyclomatic) + S vs reference | pytest `test_reference_cells_correct`, `test_S_values_match_sources`, `test_deltas_vs_reference_consistent`; browser: Δ = +20/+23/+1/+4, S=0.506 |
| 7 | Point cloud and persistence diagram views | `#cloud-canvas` + `#ph-canvas`; weather has a state-space ↔ seasonal-reference toggle | pytest diagrams present in data; browser: PH toggle values match saved analysis JSON |
| 8 | Native vs component-separated rendering, structure unmodified | layout radio (side-by-side default); both layouts precomputed in the builder from one graph object with fixed seeds | pytest `TestLayoutPreservation` (node sets identical, coordinates in unit box, deterministic rebuild); browser: toggle hides/shows panel, 20 node ids identical across layouts |
| 9 | Export of selected configuration + numerical/graph results | `#export-btn` downloads JSON (config, structure, graph, layouts, deltas, S, provenance + SHA-256, caveats) | pytest `TestExportConsistency` (inline HTML data == standalone JSON; provenance hashes re-verified); browser: exported object byte-identical to embedded cell |
| 10 | Explanatory labels separating point-cloud topology / PH features / graph structure / rendering choices | labelled sections A (point cloud — "not a Mapper output"), B (persistent homology — computed features), C (Mapper graph — saved structure), D (rendering choice — layout only, structure invariant) | pytest `test_required_ui_elements_present` (all four labels); browser: sections rendered |

**Interpretive safeguards retained** (banner + S note + cycles box):
S is an exploratory overlap indicator, not a canonical graph distance and
never a resolution-ranking on its own; a Mapper graph cycle is not
automatically a persistent loop (the no-loop blob cell is included
specifically to show cycles appearing without any H1 loop); a visually
connected graph is not automatically the correct interpretation; no claim of
improved human readability (no participant study exists).

## 5. Directory map

```text
viewer/template.html       viewer source (data placeholder /*__EXPLORER_DATA__*/)
viewer/index.html          BUILT self-contained artifact (open this)
scripts/build_viewer.py    builder: saved results -> data + viewer
data/explorer_data.json    standalone copy of the embedded data
results/build_report.json  build record (sizes, checksums, cell counts)
results/browser_test.json  offline + interaction test record
tests/test_explorer.py     19 pytest checks (data, layouts, export, HTML, errors)
figures/screenshot_*.png   5 screenshots from the real viewer (headless Chromium)
PRIOR_ART.md               documented prior-art search and novelty position
```

## 6. Limitations

- Display-only: the viewer cannot explore parameter cells that were not
  precomputed (by design — it is a saved-results inspector, not a compute
  tool; use Mapper Interactive for on-the-fly recomputation).
- Layouts are precomputed spring (seed 42) and the project's
  component-separated layout; other layouts are not offered, to keep
  rendering choices auditable.
- Tested on headless Chromium/Linux only; other browsers and platforms
  untested.
- The day-of-year lens cell is shown as a labelled descriptive variant with
  its calendar-encoding warning; S and deltas are not computed for it (it is
  a different lens, not a different cover cell of the same grid).
- Export contains the displayed values verbatim; it deliberately includes
  the caveats so exported snapshots cannot be silently de-contextualized.
