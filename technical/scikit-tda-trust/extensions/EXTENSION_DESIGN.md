# Extension Design — Restoring Selected Ideas from the Planning Documents

**Project:** *When Can You Trust a Topological Visualization? A Task-Based
Evaluation of the Scikit-TDA Ecosystem* (completed baseline) plus the
extension programme defined here.
**Inputs synthesized:** `Scikit-TDA_Evaluation_Research_Plan` (Revision 1,
20 Oct 2026), `ScikitTDA_Adversarial_Review_Report` (21 Oct 2026),
`ScikitTDA_Research_Plan_Rev2` (21 Oct 2026), the Final Implementation
Blueprint, and the completed baseline repository (`../`, manifest:
`BASELINE_MANIFEST.json`).
**Date:** 22 October 2026.

This document states which original ideas the extension restores, which it
modifies, which remain out of scope, and why — then maps every selected
extension to a research question and an evidence requirement. It deliberately
does **not** restore every experiment from the original plan: the objective
is to improve the project, not to maximize the number of experiments.

---

## 1. Where the baseline sits relative to the planning documents

The completed baseline executed the blueprint's three-experiment design,
which corresponds to the Revision 2 plan as follows:

| Revision 2 plan element | Baseline status |
|---|---|
| V0 verification harness | Done as `scripts/verify_env.py` + 60-test suite |
| E1 arm (b) Mapper parameter sensitivity | Done as **baseline E2** (24-cell grid, annulus + figure-eight, membership-Jaccard fingerprint S, no-loop blob control) |
| E1 arm (a) persistence resampling | **Not executed** (blueprint cut it) — restored here as Extension C |
| E1 arm (c) baseline reseeding (t-SNE/UMAP) | Not executed — remains optional (see §4) |
| E2 real-data comparative case study (GSOD) | **Not executed** (course-scope cut) — restored here as Extension A |
| E3 task-based readability pilot | Executed as the **pre-specified fallback**: structured single-observer inspection (participant study impossible; constraint change 2026-10-22) |
| E4 performance micro-benchmark | Partially absorbed into E1 audit timings; not extended |

The adversarial review's central warning — *computational metrics alone do
not establish what a visualization communicates* — remains binding on every
extension: no computational proxy added here may be described as evidence
about human readability, and the absence of a participant study stays
explicit in all extension documents.

## 2. The three extension research questions

- **RQ1 — Real scientific applicability.** Under what conditions do
  topological visualizations reveal recurring seasonal structure in real
  meteorological data, and how do representation and parameter choices
  affect the conclusions?
- **RQ2 — Sensitivity-aware visualization.** Can a compact visualization
  tool make Mapper's parameter-dependent structural changes easier to
  inspect, compare and reproduce?
- **RQ3 — Robustness.** How much do persistence diagrams and Mapper graph
  summaries change under reasonable resampling of the same underlying
  dataset, and how does this differ from changes induced by Mapper
  parameter choices?

Framing discipline (carried over from the review): this project does not
invent persistent homology or Mapper. Its contributions are the reproducible
evaluation, the scientific case study, the custom analysis instruments, the
visualization prototype, and the evidence-backed limitations.

## 3. Selected extensions

### 3.1 Extension A — Real meteorological case study (RQ1)

**Restores** Revision 2's E2 sub-designs (a) state-space comparison and
(b) the seasonal loop, i.e. Candidate D's core on a single station: NOAA
GSOD daily observations for New York Central Park (station `72505394728`),
2019–2024 complete years.

**Modifications relative to the original plan** (each traceable to a
documented reason):

1. **One station, not two.** The plan's second (tropical) station is
   deferred until the one-station pipeline is reproducible and reviewed
   (Stage-2 gate). A second station adds a confound before the first
   pipeline is trusted.
2. **ENSO is descriptive context only, never a hypothesis test.** The
   adversarial review's Weakness 3 (≈2 ENSO episodes in 2019–2024 — a power
   statement, not a design; reanalysis-scale literature cannot anchor
   station-scale claims) is honored: if an ONI-phase-colored exhibit is
   included at all, it carries the power statement beside it.
3. **Representation set starts at PCA + Mapper + persistence diagrams.**
   t-SNE is dropped from the default set (it answers the same
   neighborhood-preservation question as UMAP with worse documented global
   geometry); UMAP is an optional add-on *after* the first three
   representations work reliably, and only with a separate extension
   requirements file (new dependency; baseline pins untouched).
4. **Day-of-year lens is a labelled descriptive comparison, always shown
   beside the unsupervised PCA-lens result** (the plan's own leakage
   caveat: that lens encodes the calendar answer it visualizes).
5. **Sliding-window parameters are re-derived, not copied.** The plan's
   "window 60 days, embedding dimension 8" is treated as a starting point;
   the implementation defines lag τ and dimension d explicitly with
   window span (d−1)·τ, and the sweep is built around the observed
   annual-cycle scale (see `meteorology/README.md` § seasonal PH).

**Evidence requirements.** Raw-data provenance record with checksums and
retrieval dates; deterministic preprocessing with sentinel handling,
unit conversion, and quantified missingness (no silent imputation);
analysis-ready matrix separated from raw and cleaned data; saved numerical
outputs (diagrams, gap diagnostics, runtimes) *before* figure generation;
a parameter sweep with a fixed reference configuration and pre-specified
alternatives — negative or unstable results reported as results, not tuned
away; a claims-to-evidence table; automated tests for schema, sentinels,
unit conversion, embedding determinism, and output schemas.

**Interpretation guard.** A dominant H1 class in a sliding-window embedding
is evidence of a recurrent quasi-periodic structure in the embedded series
at the studied scale — not proof that the climate process itself follows a
simple closed physical trajectory. Weather–topology literature operates
mostly at reanalysis/model scale (Strommen et al., 2022; Muszynski et al.,
2019); the station-scale transfer is exactly what this extension tests.

### 3.2 Extension B — Mapper sensitivity explorer (RQ2)

**Restores** Gap 3 of the research plan (*no cross-parameter visualization
of Mapper itself*): the fingerprint heatmap + representative-graph panels
already computed by baseline E2, turned into a compact, offline-capable
inspection tool. It also addresses Gap 4's provenance item (parameter
provenance display) in minimal form.

**Modifications.** Implemented as a standalone local browser viewer with
embedded JavaScript/SVG over precomputed JSON results — *not* a kmapper
pull request and *not* a server application. Because the baseline's
offline browser test proved the KeplerMapper HTML export fails without
network (CDN D3/fonts), the viewer's core inspection features must not
depend on remote scripts, fonts, or images, verified by an actual
cold-cache network-disabled test of the delivered artifact.

**Prior-art positioning (required before any novelty language).** Mapper
Interactive (Zhou et al., 2020) and the parameter-selection literature
(Carriere, Michel & Oudot, 2017; Carriere & Oudot, 2018) exist; the
extension is positioned as an **implementation and evaluation
contribution** — a minimal, reproducible, offline viewer bound to a saved
24-cell experiment — not a novel algorithm or a claim of interactivity
novelty. A documented search (queries, sources, date) is a Stage-3
deliverable.

**Evidence requirements.** Working viewer; startup/usage guide;
UI-control-to-configuration mapping; annulus + figure-eight + no-loop-blob
examples; a weather example if Extension A provides appropriate results;
tests that the viewer displays the correct precomputed cell and statistics;
export-consistency and structural-invariant tests; screenshots generated
from the actual tool; evaluation by technical checks plus the established
single-observer inspection procedure — **with no claim of human-usability
improvement** (that would require participant evidence, which does not and
will not exist in this project).

### 3.3 Extension C — Robustness and resampling (RQ3)

**Restores** Revision 2's E1 arm (a): persistence-diagram resampling —
30 resamples at 80% (starting design, not a magic number), bottleneck and
Wasserstein distances against the full-data diagram, summarized as
distributions relative to dominant persistence. Descriptive variability
bands, if computed, are documented precisely and are **not** labelled
confidence sets (Fasy et al., 2014 guarantees explicitly not claimed).

**Adds** the Mapper input-sampling arm the plan never executed: Mapper
parameters fixed, input subsampled deterministically — component counts,
nodes/edges, cyclomatic number, renderings — with node-membership
comparisons made on **global point identities** (never local row indices
across different subsets).

**Modifications.** The plan's resampling shapes were annulus, torus, and
an HTRU2 subsample; the extension uses the baseline's **annulus,
figure-eight, and no-loop blob** instead, because (i) the saved E2 grid
gives a parameter-instability reference on exactly these shapes, making
"sample instability vs parameter instability" a like-for-like comparison,
and (ii) HTRU2's role as the real-data bridge is now served by actual
meteorological data in Extension A.

**Separation discipline (binding).** Fixed parameters, altered sample =
input-sampling stability. Fixed data, altered parameters = parameter
sensitivity (baseline E2). The two are reported separately and never
collapsed into one score.

**Evidence requirements.** Seed-deterministic resampling; every distance
stored; distance-distribution plots; graph-structure comparison tables; a
sensitivity-versus-resampling summary; an explicit statement of what the
experiment adds beyond the E2 grid; a modest time-series-appropriate
robustness check on the Extension A seasonal analysis if Extension A
succeeds (block resampling respecting temporal dependence, or a documented
limitation if too expensive).

## 4. Explicitly out of scope (and why)

| Idea | Source | Reason it stays out |
|---|---|---|
| ENSO hypothesis test (H4b) | Rev1 | Adversarial W3: ~2 episodes in-window; underpowered by construction. Descriptive exhibit only. |
| Second/third weather station | Rev1/Rev2 optional | Gate discipline: only after one-station review (Stage-2 gate). |
| DREiMac circular coordinates | Rev1/Rev2 optional | New package + new paradigm; not needed for RQ1–RQ3; deferred. |
| GUDHI cross-validation | Rev2 optional | New dependency; cross-library validation is not decision-relevant for RQ1–RQ3 here. |
| Sparse-input Ripser recipe | Rev2 optional (Gap 5) | Documentation contribution; deferred — no experiment in this programme needs n > 2,000 dense points. |
| Human-participant study | — | Hard constraint (2026-10-22). E3 remains a structured single-observer artifact inspection; nothing may claim general human readability. |
| t-SNE baseline arm | Rev1 E4 | UMAP covers the stochastic-embedding baseline role with better-documented global behavior; t-SNE adds a redundant runtime cost. Optional only if reviewers request it. |
| HTRU2 / digits benchmark tier | Rev1 Tier 2 | Real meteorological data now serves the real-data role; benchmark tier adds breadth, not decision-relevant information for RQ1–RQ3. |
| Performance micro-benchmark | Rev1 E5 / Rev2 E4 | Baseline already records runtime anchors; RQ1–RQ3 need no new scaling curves. Runtimes of new runs are still recorded per-run. |
| Fasy-style confidence guarantees | Rev1 E2 | Explicit honesty rule: descriptive bands only, guarantees never claimed. |
| Mapper "winner" declaration | Rev1 E4 framing | Representations answer different questions; no universal single score (plan §11.1 fairness framework). |

## 5. Stage gates (from the master prompt, restated as contract)

- **Stage 1 gate:** baseline re-verified (verify 38/38, tests 60/60), manifest
  created, directory structure in place, pre-existing discrepancies recorded.
- **Stage 2 gate (STOP):** Extension A executed end-to-end with evidence;
  report to user; Mapper explorer may not begin until review.
- **Stage 3 gate:** viewer works on saved data, offline test passed,
  prior-art search documented.
- **Stage 4 gate:** resampling experiments executed; separation discipline
  verified.
- **Stage 5:** synthesis report (`extensions/EXTENSION_REPORT.md`), baseline
  manifest re-checked, fresh-environment reproducibility, claims mapped to
  artifacts.

## 6. Preservation rules (binding on all extension work)

1. Never overwrite baseline report/presentation/QA/E1/E2 results, figures,
   or the inspection record; the manifest hashes are the contract.
2. New results live under `extensions/` subdirectories only.
3. Baseline dependency pins unchanged; new packages go in a separate
   extension requirements file where practical.
4. No git commits, pushes, resets, rebases, or history changes.
5. No fabricated results, provenance, execution success, or literature
   novelty; no volunteer-study simulation.
6. The baseline project must continue to run independently of the
   extensions.
