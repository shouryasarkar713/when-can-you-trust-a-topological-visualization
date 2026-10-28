# Stage 4 — Resampling and Robustness Experiments (`extensions/stability/`)

**Status: COMPLETE (Stage-4 gate reached; no further stage started).**
All numerical outputs were saved BEFORE any figure was rendered; every figure
renders from saved results only; the baseline is byte-identical (verified by
`extensions/scripts/verify_baseline_unchanged.py`, 145/145).

## 1. What this extension is (and is not)

Three components, per the Stage-4 authorization:

| Part | Question | Varies | Fixed |
|---|---|---|---|
| B | persistence-diagram resampling stability | the input sample (30 x 80% subsamples per shape) | pinned ripser config (`maxdim=1`), shapes, reference diagrams |
| C | Mapper input-sampling stability | the SAME 30 x 80% subsamples | Mapper parameters (10, 0.35, PCA-1 lens, KMeans k=2 seed 42) |
| D | weather single-year dependence | which calendar year is omitted (6 folds) | all six documented seasonal-embedding configurations |

**Input-sampling stability (this extension) is a different question from
parameter sensitivity (baseline E2 and the meteorology Mapper grid):** there,
the same data are analyzed under different cover parameters; here, different
subsamples of the same data are analyzed under fixed parameters. Both kinds of
variation are reported separately; neither yields a "universally correct"
score, and no result here ranks Mapper against PCA/t-SNE/UMAP.

**Interpretation guards that apply to every number below:**

1. The persistence-diagram distances are measured against the FULL-DATA
   reference, which OVERLAPS every 80% subsample. They are descriptive
   resampling-stability quantities — not independent validation, not unbiased
   generalization estimates, and the spread of 30 distances is a variability
   band, NOT a formal confidence set.
2. A diagram distance is a METRIC value, not a statistical hypothesis test:
   there is no null distribution, no p-value and no rejection region anywhere
   in this extension (methodology note stored in
   `results/ph_resampling.json`).
3. The custom membership-Jaccard `S` remains an EXPLORATORY overlap indicator
   (greedy, edge-blind, not a metric, not normalized for node count; `S = 1`
   does not imply identical graphs). It is reported for completeness and is
   never the sole stability measure.
4. Mapper graph cycles are not automatically topological loops (baseline
   no-loop-control caveat); the cyclomatic number is `E - V + C` (edges minus
   vertices plus connected components — the number of independent cycles of
   an undirected graph; definition stored in `results/mapper_resampling.json`).
5. The weather component is a SENSITIVITY ANALYSIS on six years of
   single-station data: not a population-level climate claim, not a formal
   confidence interval, not a hypothesis test. A dominant H1 class evidences
   recurrent quasi-periodic structure of the embedded series — not proof of a
   simple closed physical climate trajectory (same wording rule as the
   meteorology extension).
6. No human-participant study exists in this project; nothing here claims
   improved readability for readers.

## 2. Method (exact configurations and seeds)

Everything is configuration-driven from `configs/stability.yaml` (no
hard-coded parameters in scripts):

* **Subsampling design (Parts B and C share it):** 30 deterministic
  80%-without-replacement subsamples per shape; `numpy.random.default_rng`
  with seed rule `seed(shape, rep i) = 20261022 + offset[shape] + i`, offsets
  annulus 0 / figure-eight 1000 / blob 2000 — 90 pairwise-distinct seeds.
  Every replicate stores its seed AND its sorted sampling indices.
* **Datasets:** the baseline generators reused verbatim — each script
  regenerates the shape from `configs/shapes.yaml` and REFUSES to run unless
  it is byte-identical to the baseline E1 saved point cloud
  (`results/e1/data/{shape}.npy`).
* **Part B reference diagrams:** the baseline E1 full-data diagrams
  (`results/e1/{shape}_ph_dgms.npz`), pinned ripser `maxdim=1`. Metrics:
  bottleneck + Wasserstein (both supported by the pinned persim 0.4.1),
  computed per homology dimension (H0 and H1 kept separate, never pooled).
  persim drops the essential H0 class (infinite death) from both diagrams
  before computing distances — recorded in the results metadata.
  Pre-specified gap diagnostics per construction (not re-chosen after
  inspection): r1 at ground-truth rank 1 for the annulus, r2 at rank 2 for
  the figure-eight, r1 calibration-only for the blob.
* **Part C Mapper:** reference graph rebuilt with the pinned baseline
  configuration and verified membership-identical to the E1 saved JSON
  before any comparison. Memberships are stored in GLOBAL point identity
  (indices into the full 500-point cloud) — local subsample row indices are
  never compared across subsamples. `S` is computed on global identities on
  both sides.
* **Part D LOYO:** for each omitted year, the retained days are re-z-scored
  within the retained series (r_k gap ratios are invariant to this affine
  rescaling; dominant persistence is reported in retained-series z-units),
  and sliding windows are built STRICTLY WITHIN the contiguous calendar
  blocks — a window never crosses the gap created by the omitted year. The
  number of windows lost to the gap is recorded. Days are NOT resampled
  independently (strong autocorrelation; embedding windows span 210-630
  days) and no block bootstrap concatenation is used (it would create
  artificial delay windows at block boundaries).

**Resumability note (sandbox constraint):** single-process wall time is
limited in this workspace, so Parts B and D checkpoint per replicate / per
fold and can be resumed; the merge happens automatically when all
replicates/folds are complete. The wall-clock fields in the outputs are
therefore accumulated across invocations (per-replicate ripser and distance
timings are stored individually and are exact).

## 3. Results (each tied to its exact artifact)

### 3.1 Part B — persistence-diagram resampling stability
(`results/ph_resampling.json`, figures `ph_resampling_dists.png`,
`ph_resampling_persistence.png`, `ph_resampling_cross_shape.png`,
summary `results/stability_summary.json`)

| shape | ref dom. H1 | resample dom. H1 range | H1 bottleneck med (IQR) | gap diagnostic (all 30) |
|---|---|---|---|---|
| annulus | 1.496 | 1.439 – 1.575 | 0.029 (0.023–0.051) | r1: 13.2 – 25.6 (ref 19.3) |
| figure-eight | 0.481 | 0.458 – 0.511 | 0.019 (0.016–0.024) | r2: 7.35 – 13.8 (ref 9.75) |
| blob (control) | 0.140 | 0.092 – 0.181 | 0.048 (0.044–0.053) | r1 calibration only |

* **Stable features (examples):** the annulus dominant loop persistence and
  the figure-eight co-dominant pair vary far less than their own scale; the
  rank-appropriate gap diagnostic stays far above the stated convention in
  every resample. Computed from all 30 resamples — no favorable subset was
  selected after inspecting outcomes.
* **Varying features (examples):** the blob's top persistence swings by
  ~2x in relative terms; noise-scale H1 classes (counts and small
  persistences) vary freely in all shapes.
* **Cross-shape comparison:** H1 bottleneck distance / reference dominant
  persistence has median 1.9% (annulus), 4.0% (figure-eight) and 34%
  (blob) — diagrams of a constructed feature are proportionally far more
  stable than diagrams with no constructed feature
  (`ph_resampling_cross_shape.png`; descriptive scale normalization, not a
  statistic).
* **H0 note:** every subsample has exactly 399 finite H0 classes vs 499 in
  the reference; each unmatched short class adds Wasserstein transport
  cost, so H0 Wasserstein values (~2-3.6) are structurally inflated by the
  class-count difference. The bottleneck (a max) is not affected this way.
  H0 bottleneck medians: 0.022 / 0.017 / 0.056.

### 3.2 Part C — Mapper input-sampling stability
(`results/mapper_resampling.json`, figures `mapper_resampling_structure.png`,
`mapper_resampling_graphs_{annulus,figure_eight,blob}.png`,
`mapper_resampling_layouts.png`)

| shape | reference | nodes (30 reps) | components | cyclomatic | S vs ref (median, range) |
|---|---|---|---|---|---|
| annulus | 20n 21e 1c cyc=2 | **20 in all 30** | 1: 24, 2: 6 | 0: 13, 1: 9, 2: 8 | 0.585 (0.478–0.792) |
| figure-eight | 20n 19e 2c cyc=1 | **20 in all 30** | 2: 24, 1: 6 | 1: 18, 0: 12 | 0.762 (0.702–0.813) |
| blob (control) | 20n 23e 1c cyc=4 | **20 in all 30** | 1: 10, 2: 12, 3: 8 | 1–6 (ref 4) | 0.645 (0.466–0.753) |

* **Node count is 20 in all 90 resample graphs** — the same uninformative
  `2 x n_cubes` pattern as baseline E2, now demonstrated on the
  input-sampling axis rather than the parameter axis.
* **The annulus Mapper cycle cue is not stable under input subsampling**
  (cyclomatic 0 in 13/30 resamples) even though the underlying H1 loop is
  prominent in all 30 (Part B) — the baseline "Mapper cycles are not
  automatically loops" caveat now has a quantified input-sampling instance.
* The figure-eight 2-component reading holds in 24/30; the no-loop blob is
  the most structurally variable. `S` medians 0.59–0.76 with wide ranges —
  exploratory only (see guard 3).
* `mapper_resampling_layouts.png` shows, for each shape, the
  maximum-component-deviation resample under native vs component-separated
  layout: the graph is identical and only the rendering changes — a reading
  aid, not a structural claim (the same distinction the Mapper explorer's
  layout toggle makes).

### 3.3 Part D — weather leave-one-year-out sensitivity
(`results/weather_loyo.json`, figure `weather_loyo.png`)

* **Every fold x configuration retains one dominant H1 class with
  r1 >= 4.38** (full-data range 4.75–7.32; stated convention r1 >= 3): the
  seasonal-cycle finding does not depend disproportionately on any single
  observed year of the six. Fold dominant-H1 ranges per config are in
  `results/stability_summary.json` (`weather_loyo` section).
* Structural cost of the gap-safe window rule: mid-series folds lose
  210–630 windows per configuration (edge folds lose 0); the tau=90
  configuration drops to 567 windows in the 2021/2022 folds and still
  yields r1 >= 5.1.
* Per-fold re-z-scoring changes the retained mean (13.66–13.90 degC) and sd
  (8.77–9.11 degC) only slightly; r_k ratios are invariant to the
  rescaling, dominant persistence is reported in retained-series z-units.

## 4. Reproduce

```bash
cd <repo root>
.venv/bin/python extensions/stability/scripts/run_ph_resampling.py       # ~15 min, resumable
.venv/bin/python extensions/stability/scripts/run_mapper_resampling.py  # ~6 s
.venv/bin/python extensions/stability/scripts/run_weather_loyo.py       # ~10 min, resumable
.venv/bin/python extensions/stability/scripts/summarize_stability.py    # instant
.venv/bin/python extensions/stability/scripts/render_stability_figures.py
.venv/bin/python -m pytest extensions/stability/tests/ -q                # 29 tests
.venv/bin/python extensions/scripts/verify_baseline_unchanged.py
```

Environment: the pinned baseline environment (see `results/env/pip_freeze.txt`
of the baseline; ripser 0.6.15, persim 0.4.1, kmapper 2.1.0, numpy 2.5.4,
scipy 1.18.1, matplotlib 3.11.2, networkx 3.7, scikit-learn 1.9.1). **No new
dependency was added** — the extension uses only baseline-pinned packages, so
no separate requirements file is needed and the baseline's pinned
requirements are untouched.

**Measured runtimes (reported, not silently reduced):** the design kept the
pre-specified 30 replicates; the H0 bottleneck computations dominated Part B
(annulus 355 s, figure-eight 200 s, blob 296 s cumulative; individual H0
bottleneck calls ranged 0.6–75 s — persim's Hopcroft-Karp implementation is
strongly instance-dependent). Part D took ~9.5 min for 36 embeddings
(ripser 6–25 s each; per-run timings stored). These runtimes are recorded in
the results files.

## 5. Separating the kinds of evidence (Part-F requirement)

* **Mathematical / computational correctness:** the cyclomatic definition
  (E - V + C) and its toy-graph checks; gap-ratio r_k = p_k/p_{k+1} matching
  the baseline helper; bottleneck of a diagram with itself = 0; Wasserstein
  symmetry; byte-identity of regenerated shapes, subsample indices and the
  Mapper reference rebuild. All asserted in
  `tests/test_stability.py` (29 tests).
* **Variation from subsampling:** Parts B and C — all numbers above.
* **Variation from parameter choices:** NOT re-measured here; it is the
  baseline E2 result (and the meteorology Mapper grid). This extension
  deliberately holds parameters fixed to keep the two variation axes
  separable.
* **Visual changes and interpretation ambiguity:** graph layouts (spring
  layout seed 42; component-separated variant) are rendering choices —
  `mapper_resampling_layouts.png` demonstrates that the same graph reads
  differently under the two layouts; structural claims rest on recorded
  statistics and memberships, never on pixel positions.
* **Custom metrics' limitations:** guard 3 (S is exploratory, greedy,
  edge-blind, not a metric); the relative-distance normalization in the
  cross-shape figure is descriptive, not a statistic.
* **What remains untested:** other subsample fractions (only 80% was
  pre-specified); bootstrap or jackknife schemes (deliberately not used on
  the weather series — see method); Mapper parameter x subsample interaction
  (would require a full grid x resample factorial); any claim about human
  reading of the graphs (no participant study); shapes beyond the three
  baseline constructions; other stations or climate variables.

## 6. Directory map

```
extensions/stability/
  configs/stability.yaml            all seeds + parameters (nothing hard-coded)
  scripts/run_ph_resampling.py      Part B (checkpointed, resumable)
  scripts/run_mapper_resampling.py  Part C
  scripts/run_weather_loyo.py       Part D (checkpointed, resumable)
  scripts/summarize_stability.py    aggregates -> stability_summary.json
  scripts/render_stability_figures.py  9 figures from saved results only
  results/ph_resampling.json        90 replicates, seeds, indices, distances
  results/mapper_resampling.json    90 replicates, global memberships, links
  results/weather_loyo.json         6 folds x 6 configs, block structure
  results/stability_summary.json    cross-shape tables + guards
  results/claims_evidence.json      S1-S12 claim-to-artifact map
  figures/*.png + captions.json     9 figures with embedded guards
  tests/test_stability.py           29 tests (schemas, determinism, identity,
                                    statistics, figures, baseline manifest)
```

## 7. Deviations and known defects

* **None scientific.** All pre-specified counts kept (30 replicates, 6 folds,
  6 configurations). No numerical output of the baseline or of earlier
  extensions was modified.
* Engineering deviation (disclosed): Part B's independent-reference check
  (optional per the authorization) was NOT added — the full-data reference is
  used, with the overlap documented everywhere; an independent-reference
  variant would double the H0-bottleneck runtime without changing the
  descriptive character of the results.
* Sandbox constraint (disclosed): long runs needed several resumable
  invocations (per-replicate / per-fold checkpoints); this affected only
  wall-clock bookkeeping, not any numerical value (verified: an accidental
  full re-run of the blob shape reproduced all values exactly; only
  wall-clock time fields differ).
* The `RuntimeWarning: divide by zero` emitted by the BASELINE
  `src/figures.py:118` during component-separated layout rendering is a
  guarded `np.where` idiom (span=0 single-node component); the baseline file
  is intentionally not modified (preservation rule) and the rendered result
  is correct.
