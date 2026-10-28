# Extensions — Scikit-TDA Evaluation Project

Post-completion extension programme for *When Can You Trust a Topological
Visualization? A Task-Based Evaluation of the Scikit-TDA Ecosystem*.

> **Historical record.** The "Ground rules" and "Stage log" below were written while the extensions were being developed and are kept
> as written (including test counts of that time, the statement that no commits were made, and references to an earlier
> `extensions/final/` synthesis that is **not** part of this repository). The current deliverables, test counts and verification are in
> the root `README.md`, `submission/` and `technical/verification/`. Contemporaneous version-control history was not maintained
> during the project; this repository's history was constructed retrospectively.

The completed baseline project (repository root, `../`) is **frozen**:
`BASELINE_MANIFEST.json` records the SHA-256 hash of every baseline file,
and any later difference must be reported, never silently accepted. All new
work lives under this directory.

## Contents

| Directory | Extension | Research question | Status |
|---|---|---|---|
| `meteorology/` | A — real meteorological case study (NOAA GSOD, Central Park 2019–2024) | RQ1: when do topological visualizations reveal recurring seasonal structure in real data? | Stage 2 complete + Stage-3/4 corrections applied | 
| `mapper_explorer/` | B — Mapper sensitivity explorer (offline viewer over saved results) | RQ2: can a compact tool make parameter-dependent changes inspectable? | Stage 3 complete + Stage-4 prior-art update (reviewed) |
| `stability/` | C — robustness and resampling | RQ3: resampling stability vs parameter sensitivity | Stage 4 complete (reviewed) |
| `controls/` | D — control experiments D1–D5 (clusterer, resampling, caveat checks, independent draws, weather null controls) | tests of specific alternative explanations | complete (see `controls/README.md`) |
| `scripts/` | shared extension utilities (baseline manifest, verification) | — | Stage 1 (complete) |

Design rationale, restored/modified/out-of-scope decisions, and the
research-question mapping: [`EXTENSION_DESIGN.md`](EXTENSION_DESIGN.md).

## Ground rules

- **Baseline preservation.** The baseline runs independently of everything
  here. Its dependency pins (`../requirements.txt`) are unchanged. Nothing
  under `../` outside `extensions/` is written by extension code.
- **Environment.** Extension code that needs only the baseline stack runs
  under the project `.venv`. If a new package becomes necessary (e.g.
  `umap-learn`), it goes in `requirements-extension.txt` here, installed in
  a **separate** virtual environment, with version compatibility documented.
- **Honesty constraints carried over.** No participant study exists or will
  be simulated; the single-observer E3 inspection remains the only
  artifact-reading evidence; computational proxies are never described as
  human-readability evidence; no ENSO hypothesis test; descriptive bands
  are not confidence sets; no git commits/pushes/history changes.
- **Determinism.** Every experiment is configuration-driven
  (`<extension>/configs/*.yaml`), seeded, and saves numerical outputs
  before figures are rendered from them.

## Stage log

- **Stage 1 (complete, 2026-10-22).** Baseline re-verified:
  `scripts/verify_env.py` 38/38; `python -m pytest tests/ -q` → 60 passed.
  One pre-existing discrepancy found and handled per the documented
  final-pass procedure (see manifest `preexisting_discrepancy`). Manifest
  written: 145 baseline files, 5.1 MiB. Design document and directory
  structure created.
- **Stage 2 (Extension A — complete, 2026-10-22; awaiting user review).**
  GSOD Central Park 2019–2024 acquired with full provenance (2192/2192 rows,
  zero duplicates); deterministic preprocessing with documented feature-set
  redesign (WDSP missingness; primary cloud TEMP/DEWP/SLP, 4/2192 days
  dropped) and two explicit data-quality observations (STP corruption;
  ambiguous SLP 999.9); PCA + Mapper (8-cell grid) + state-space PH +
  6-configuration seasonal PH sweep executed and saved; 11 figures rendered
  from saved results (VLM-inspected, defects fixed); 38 extension tests +
  60 baseline tests pass; determinism check passes (22 outputs structurally
  identical, figures pixel-identical); baseline preservation verified
  145/145. Headline findings and the claims-to-evidence table:
  `meteorology/README.md`, `meteorology/results/claims_evidence.json`.
  **Stage 3 (Mapper explorer) is gated on review of these results.**
- **Stage 2 review + limited corrections (2026-10-22).** Extension A approved
  with mandated figure/wording corrections, all applied the same day:
  calendar-year ticks on the temperature series (duplicate "2020" removed);
  ONI panel title un-clipped (DESCRIPTIVE-ONLY qualification retained); PH
  sweep redrawn as a labelled scatter (points not connected; annual reference
  line retained); post-hoc periodogram/autocorrelation sanity check added
  (dominant period 365.3 d, ACF peak 360 d — not used to retune the sweep);
  README and claims A10/A11/A12 tightened + A14 added (recurrent seasonal or
  quasi-periodic structure framing; state-space result relabelled a negative
  representation contrast, not a formal statistical null control). No
  numerical result changed. After correction: 41 extension tests pass,
  determinism check passes (24 outputs), baseline preserved 145/145.
  **Stage 3 authorized.**
- **Stage 3 (Extension B — complete, 2026-10-22; awaiting review).** Part 1
  corrections applied first (see Stage-2 entry above). Part 3 prior-art
  search documented in `mapper_explorer/PRIOR_ART.md` (Mapper Interactive
  PacificVis 2021, tda-mapper 2024, Carriere-Oudot 2017, Brown et al. 2021,
  LoCoMapper 2026 snippet; search-tool outage disclosed; position:
  implementation and evaluation contribution only). Part 2: viewer built —
  `mapper_explorer/viewer/index.html`, a single 0.56 MB self-contained HTML
  file (data inlined from saved, checksummed outputs; zero CDN/server/
  network), 35 cells across 4 datasets (annulus 12, figure-eight 12, blob 2,
  weather 8 + day-of-year variant), all 10 required features implemented
  with interpretive safeguards; 19 pytest checks pass (data integrity vs
  sources, layout preservation, export consistency, HTML self-containment,
  builder error handling); offline cold-cache browser test with network
  disabled PASSES (zero http resource entries, zero console errors;
  interaction + export-consistency verified in-page; 5 screenshots
  VLM-inspected clean). Baseline preserved 145/145. **Stage 4 (resampling
  stability) is gated on review of this stage.**
- **Stage 4 (Extension C — complete, 2026-10-22; awaiting review).** Part A
  preflight: sweep-figure labels redrawn with leader lines (VLM-verified +
  3-programmatic bbox regression tests, meteorology suite now 44/44);
  PRIOR_ART.md LoCoMapper entry upgraded from snippet-only to the official
  IEEE VIS 2026 program record (Honorable Mention, abstract quoted verbatim,
  distinction section added). Part B: 30 deterministic 80% subsamples per
  shape x {annulus, figure-eight, blob}, bottleneck + Wasserstein to the
  E1 full-data reference, H0/H1 separate, seeds + indices stored —
  constructed features stable (annulus dominant H1 1.439–1.575 vs ref
  1.496; r1 >= 13.2 everywhere; relative H1 bottleneck 1.9%/4.0%/34%
  annulus/figure-eight/blob); runtime reported, not reduced (H0 bottleneck
  dominated: 355/200/296 s per shape). Part C: same subsamples at FIXED
  Mapper parameters — node count 20 in all 90 graphs (uninformative, E2
  pattern on the input axis); annulus Mapper cycle cue NOT stable
  (cyclomatic 0 in 13/30) while the H1 loop persists in 30/30; global
  point identity preserved throughout; S kept exploratory. Part D:
  leave-one-calendar-year-out with gap-safe windows — every fold x config
  retains a dominant H1 class (r1 >= 4.38; full-data 4.75–7.32), mid-series
  folds lose 210–630 windows (recorded); reported as a sensitivity
  analysis, not a climate claim. 29 stability tests; totals: meteorology
  44/44, explorer 19/19, baseline 60/60, env 38/38, baseline manifest
  145/145 byte-identical. Evidence map: `stability/results/
  claims_evidence.json` (S1–S12). **No further stage started (Stage-4
  gate).**
- **Stage 5 (final synthesis — complete, 2026-10-22).** Evidence consistency
  re-verified first: all Stage-4 headline numbers recomputed from the
  replicate files and cross-checked against the stored summaries (ALL
  PASS); viewer build/source hashes re-verified (6/6); prior-art citations
  re-verified against official records (Mapper Interactive PacificVis 2021,
  LoCoMapper IEEE VIS 2026 official program record, KeplerMapper JOSS,
  Scikit-TDA Zenodo, Strommen Climate Dynamics 60:1415–1445, Muszynski GMD
  12(2):613–628, Perea & Harer FoCM 15(5):799–838). Selected figures
  VLM-inspected; one genuine stale-label defect found (baseline
  `e2_sanity_blob.png` H1 panel legend reads "H₀") and corrected in a COPY
  under `extensions/final/figures/` rendered from the same saved results —
  baseline file untouched. Deliverables in `extensions/final/`:
  `Extended_Scikit_TDA_Evaluation.md` (14-chapter integrated report, ~12k
  words, 18 figures) + rendered DOCX (postcheck 0 errors) and PDF (41 pp,
  TOC caches filled 52/52); `presentation/Extension_Presentation_Slides.pptx`
  (16 slides, speaker notes on all, VLM-verified) + HTML sources +
  `speaker_notes.md`; `qa/Extension_QA_Preparation.docx/.pdf` (16 Q&As,
  postcheck 9/9); integrated `claims_evidence.json` (F1–F14);
  `verification_log.md`. Final verification in the pinned environment:
  verify_env 38/38, baseline 60/60, meteorology 44/44, explorer 19/19,
  stability 29/29, baseline manifest 145/145 byte-identical (after
  restoring the two `results/env/*` evidence files that a verify_env run
  had rewritten in the rebuilt workspace venv — restored byte-identically
  from the verified archive; incident recorded in
  `extensions/final/verification_log.md`). **Programme complete; no
  commits/pushes/publication.**

**Stage 5 cleanup (2026-10-28, editorial and reproducibility corrections
only).** Nine authorized corrections applied, no new experiments, no
numerical changes: author name written to the report cover (Shourya
Sarkar); "pre-registered" → "pre-specified fixed analysis search window"
seasonality wording (check re-run, all numerical fields identical);
representation-contrast and interchangeability wording restated as
measured contrasts; artifact-index label F1–F14 and explicit F1–F12
principal-claims table coverage; render-source designation (JS render
source, Markdown synchronized companion) with a new consistency gate
(`extensions/final/report/check_md_js_consistency.py`); portable evidence
verifier (`extensions/final/scripts/verify_evidence.py`, recomputes
headline numbers from saved outputs — ALL CHECKS PASSED); Stage-5
environment snapshot (`extensions/final/verification/`, freeze identical
to baseline 33/33); speaker notes shortened to 1,676 words with a
per-slide timing plan for the 10–12 minute slot and the slide-6 title
corrected to the measured-contrast wording; report DOCX/PDF rebuilt (TOC
52/52) and PPTX regenerated (16/16 notes). Two artifacts that reappeared
from a stale workspace snapshot during the environment rebuild (`pilot/`
and `scripts/analyze_e3_responses.py`, both legitimately deleted during
the original project per D-11/D-12) were investigated and removed; no
other drift found (full diff vs verified archive). Suites: 60/60, 44/44,
19/19, 29/29; baseline manifest 145/145 byte-identical. Details:
`extensions/final/verification_log.md` §C1–C6.
