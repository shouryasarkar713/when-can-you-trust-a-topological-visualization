# E2 Interpretation Notes — Stable and Unstable Readings (Phase 2)

Evidence-based summary of interpretation stability across the 24-cell E2
grid. Every number below is traceable to `results/e2/e2_sensitivity.csv`
(per-cell table), `results/e2/e2_sensitivity.json` (memberships + metadata),
and `results/e2/e2_blob_sanity.json` (no-loop control). Controls held fixed:
PCA-1 lens, KMeans(n_clusters=2, random_state=42, n_init=10), data seed 42,
Euclidean metric, n=500, noise 0.05.

**Standing caveats.** (1) A cycle in the constructed Mapper graph does not
automatically imply a genuine topological loop in the underlying data (see
the sanity control below). (2) The membership-overlap score S is a custom
exploratory indicator — greedy, edge-blind, not a metric, not normalized
across resolutions; it is never used alone to rank cells. Interpretation
rests on component counts, cyclomatic numbers, cycle-basis lengths, and the
representative panels.

## Annulus (one prominent loop by construction)

* **Stable region.** All 12 cells except (20, 0.20) yield a CONNECTED graph
  (1 component). At the reference cell (10, 0.35) the graph has 20 nodes,
  21 edges, cyclomatic number 2, and a LONG 16-node basis cycle — the
  loop-like signal. The neighbouring cells (10, 0.50) and (15, 0.35 /
  15, 0.50) keep a long dominant cycle (16 / 24 / 22 nodes).
* **Unstable readings.**
  * *Signal vanishes at low resolution.* At n_cubes=5 (all three overlaps)
    the graph is a TREE (cyclomatic 0, longest basis cycle 0): a user sees
    no loop at all — the annulus reads as "no structure".
  * *Fragmentation at the extreme corner.* At (20, 0.20) the graph splits
    into 2 components (40 nodes, 39 edges) with only short 4-node cycles:
    the annulus reads as "two clusters".
* **S range** 0.449–1.000 vs the reference cell (exploratory only).

## Figure-eight (two co-dominant loops by construction)

* **The reference cell itself is the unstable reading.** At (10, 0.35) the
  graph fragments into 2 components (20 nodes, 19 edges) with only short
  4-node cycles: a user reasonably reads "two disconnected clusters",
  which misrepresents the data (one connected curve with two loops).
* **Worse at the extreme corner.** (20, 0.20) fragments into 4 components
  — the "number of clusters" reading changes again (2 → 4) within the
  plausible parameter range.
* **Construction-consistent readings exist.** (20, 0.50): connected, 40
  nodes, 41 edges, cyclomatic 2, two 20-node basis cycles — the closest
  structural match to "two loops of one object". (10, 0.50) and (15, 0.50)
  are also connected with cycles (3 and 4 short-to-medium cycles).
* **S range** 0.457–1.000 vs the reference cell (exploratory only).
* Reading the Mapper graph alone, a user CANNOT tell which of these
  parameter regimes they are in — this is the E2 headline: the qualitative
  interpretation (clusters vs loops vs nothing) changes with reasonable
  cover-parameter choices, and the ecosystem provides no guidance for
  choosing among them.

## Node count is uninformative

As verified in Phase 1 and across all 24 cells now: n_nodes = 2 x n_cubes
in every cell for both shapes (kmapper's cover x 2 clusters per element).
Node count carries no signal about the data; only component and cycle
structure does.

## No-loop sanity control (blob)

The blob (isotropic Gaussian, NO loop by construction) produces Mapper
graphs WITH cycles at both diagnostic settings:
* (10, 0.35) reference setting: 1 component, cyclomatic 4, longest basis
  cycle 6 — four SHORT noise-scale cycles.
* (20, 0.20) extreme setting: 6 components, cyclomatic 5, longest basis
  cycle 10 — fragmentation AND noise cycles.
Meanwhile the H1 persistence diagram of the SAME data shows no dominant
class (top-3 persistences 0.1396/0.0962/0.0924, r_1 calibration 1.451 <
the stated prominence convention of 3).

**Critical distinction.** A cycle in the constructed Mapper graph does not
automatically imply a genuine topological loop in the underlying data.
Cycle LENGTH and scale context separate the loop-like signal (annulus
reference: 16-node basis cycle on 500 points spread over the band) from
noise-scale cycles (blob: 6-node cycles). A naive "count the cycles"
reading of the blob's Mapper graph would report 4 loops that do not exist.

## Where the figures are

* `figures/e2/e2_sensitivity_summary_{annulus,figure_eight}.png` — 3-panel
  grid overview (components, cyclomatic number, S).
* `figures/e2/e2_representative_panels_{annulus,figure_eight}.png` —
  reference vs contrast cell, native renderer.
* `figures/e2/e2_readability_{annulus,figure_eight}.png` — native vs
  component-separated rendering of the reference cell (readability).
* `figures/e2/e2_sanity_blob.png` — the cycles-vs-loops contrast for the
  no-loop control (two Mapper cells + H1 diagram).
All figures are re-rendered from saved results by `src/figures.py --all`
without recomputation; captions travel with each figure as `.caption.txt`.
