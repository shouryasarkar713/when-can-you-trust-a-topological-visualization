# Extension A — Real Meteorological Case Study (RQ1)

**Research question (RQ1):** Under what conditions do topological
visualizations reveal recurring seasonal structure in real meteorological
data, and how do representation and parameter choices affect the resulting
interpretation?

**Status:** Stage 2 complete (2026-10-22); limited Stage-3 accuracy and
figure corrections applied the same day (review-mandated: calendar-year
ticks on the temperature-series figure, un-clipped ONI panel title, sweep
redrawn as a labelled scatter, post-hoc seasonality sanity check added,
wording tightened — see §8). No numerical result was changed. All results
below are measured outputs of the saved pipeline; the claims-to-evidence
table (`results/claims_evidence.json`) maps every claim to its artifacts.

---

## 1. Data and provenance

| Item | Value |
|---|---|
| Station | NY City Central Park, NY US — `72505394728` (40.77898 N, −73.96925 E, 42.7 m) |
| Source | NOAA NCEI GSOD access directory (`…/access/{year}/{station}.csv`), official, registration-free |
| Window | 2019-01-01 … 2024-12-31 (six complete years) |
| Rows | 2192 observed = 2192 expected (365+366+365+365+365+366); zero duplicate dates; calendar-complete |
| Checksums | SHA-256 per raw file in `data_provenance/provenance.json`; raw files immutable |
| Retrieval | 2026-10-22, HTTP 200 on all seven fetches (6 GSOD + ONI) |
| ONI | `psl.noaa.gov/data/correlation/oni.data` (1950–2026, 925 monthly values, 4 sentinels) — **descriptive context only** |

Units verified against the fetched schema and converted before any distance
computation: TEMP/DEWP/MAX/MIN °F→°C, WDSP/MXSPD/GUST knots→m/s, PRCP
inches→mm, SLP/STP mb→hPa (identity). Sentinels: 9999.9 (temperature and
pressure fields), 999.9 (wind/visibility/snow), 99.99 (precipitation).

## 2. Preprocessing (deterministic; `scripts/preprocess_weather.py`)

Pipeline: load → validate (schema, station identity, per-year counts, date
uniqueness/continuity/coverage) → sentinel→NaN → unit conversion →
missingness report → clouds → z-score → save (cleaned CSV, analysis NPZ,
report JSON with output checksums). No imputation anywhere.

**Feature-set redesign (documented, pre-specified rule triggered).** The
Revision 2 plan's state-space cloud is TEMP/DEWP/SLP/WDSP (R⁴). Measured
missingness: WDSP is absent 125 of 2192 days — *all* of Jan–Feb 2019 (59
consecutive days), most of May–Jun 2020 (33 days), and Sep–Oct 2021 — so
the plan's cloud would have to delete winter 2019 outright (129 days,
5.9%, seasonally biased). Per the pre-specified rule (>5% ⇒ redesign, not
silent acceptance), the **primary cloud is TEMP/DEWP/SLP** (4 days dropped,
0.18%, unstructured) and the 4-feature cloud is retained as a **documented
sensitivity check** (`weather_analysis.npz: X_sensitivity`, 2063 days).

**Data-quality observations (explicit, in `weather_preprocessing_report.json`).**
- **STP is excluded from all analyses**: systematically corrupted in this
  station's files (94.8% of values < 900 hPa; median 12.4 hPa at a 42.7 m
  station; only 5.2% in the plausible 950–1050 hPa range).
- **SLP on 2020-12-01 reads 999.9** — the wind-family sentinel value in the
  SLP field, but bracketed by plausible neighbors (1010.4 → 999.9 → 1011.9
  hPa), i.e. also consistent with a real passing storm. Treated as valid
  data per the documented schema (only 9999.9 is the SLP sentinel);
  alternative reading would remove 1 of 2188 days (0.046%).
- TEMP and DEWP have **zero** missing values in six years — the seasonal
  series is gapless (no interpolation question arises).

**Analysis-ready separations.** Raw CSVs (immutable) → cleaned CSV (all
fields, converted units, NaN) → analysis NPZ (z-scored clouds, labeled
arrays). The seasonal PH series is the full 2192-day z-scored TEMP series.

## 3. Representations compared (same analysis-ready observations)

The representations answer different questions; no universal single score
is declared (plan §11.1 fairness framework).

### 3.1 PCA (`figures/weather_pca_panels.png`)

PC1 (69.0% variance) loads on TEMP+DEWP (thermal axis, negative SLP weight);
PC2 (28.6%) loads on SLP (pressure axis); 97.6% cumulative — the 3-feature
cloud is effectively two-dimensional. Seasons organize along PC1 in a
recurrent band (the annual cycle), with the pressure axis spreading days
within a season. The ONI-phase panel is **descriptive context only**, with
the power statement in the caption: ~two ENSO episodes in-window; no
station-level ENSO hypothesis is tested; the reanalysis-scale TDA-climate
literature does not transfer to single-station scale without the very test
this design cannot power.

### 3.2 Mapper (PCA-1 lens; `figures/weather_mapper_{reference,lens_comparison,grid}.png`)

Configuration discipline: PCA-1 lens (unsupervised — effectively the
thermal axis), KMeans k=2 seed=42, cover grid fixed **before** inspecting
outputs: {5,10,15,20}×{0.35,0.50}; reference cell (10, 0.35) = the baseline
E2 reference.

Measured findings:

| Cell | Nodes | Edges | Components | Cyclomatic | S vs ref |
|---|---|---|---|---|---|
| (5, 0.35) | 10 | 12 | 1 | 3 | 0.551 |
| (5, 0.50) | 10 | 13 | 1 | 4 | 0.445 |
| **(10, 0.35) ref** | 20 | 26 | 1 | 7 | 1.000 |
| (10, 0.50) | 20 | 27 | 1 | 8 | 0.685 |
| (15, 0.35) | 30 | 38 | 1 | 9 | 0.558 |
| (15, 0.50) | 30 | 40 | 1 | 11 | 0.665 |
| (20, 0.35) | 40 | 49 | **2** | 11 | 0.506 |
| (20, 0.50) | 40 | 52 | **2** | 14 | 0.666 |

- **The baseline E2 pattern replicates on real data**: node count = 2×n_cubes
  in all 8 cells (the same uninformative regularity); the graph is connected
  for n_cubes ≤ 15 and **fragments into 2 components at n_cubes = 20 under
  both overlaps**. Resolution, not overlap, is the dominant sensitivity axis
  — exactly the annulus finding from the synthetic tier.
- S (exploratory membership-Jaccard vs reference) ranges 0.445–1.000 —
  substantial membership movement across user-reasonable settings. S is an
  overlap indicator, not a graph distance, and never ranks resolutions
  alone.
- The reference graph organizes by thermal state (node mean z-TEMP
  polarizes across the graph). Its graph cycles are structural objects —
  **not** automatic evidence of topological loops (baseline no-loop-control
  caveat).
- Day-of-year lens (same cell): 20 nodes, 27 edges, 1 component — similar
  shape, but it **encodes calendar information directly**; shown only as a
  labelled descriptive comparison beside the unsupervised PCA-lens result.

### 3.3 Seasonal-cycle persistent homology (`figures/weather_seasonal_ph_*.png`)

**Parameter semantics fixed explicitly** (not copied blindly from the plan).
The embedding is time-delay: point *i* = (x[i], x[i+τ], …, x[i+(d−1)τ]) of
the z-scored daily TEMP series; **span = (d−1)·τ days**; stride 1. The
plan's "window 60 days, dimension 8" is interpreted as τ=60, d=8 → span
420 d ≈ 1.15 annual periods, kept as the pre-specified reference. The sweep
brackets the annual scale T = 365.25 d:

| τ, d | Span (d) | Span/T | n points | Dominant H1 (z-units) | r₁ |
|---|---|---|---|---|---|
| 30, 8 | 210 | 0.57 | 1982 | 1.998 | 5.63 |
| 45, 9 | 360 | 0.99 | 1832 | **2.571** | **7.32** |
| 52, 8 | 364 | 1.00 | 1828 | 2.039 | 4.92 |
| **60, 8 (ref)** | **420** | **1.15** | 1772 | 2.167 | 6.75 |
| 73, 6 | 365 | 1.00 | 1827 | 1.417 | 4.75 |
| 90, 8 | 630 | 1.72 | 1562 | 2.121 | 5.76 |

Measured findings:

- **Every one of the six configurations produces exactly one dominant H1
class** (r₁ between 4.7 and 7.3, all above the stated r₁ ≥ 3 convention) —
**consistent with recurrent seasonal or quasi-periodic structure in the
embedded temperature series** at the studied scales. This consistency
across pre-specified settings indicates the finding is not an artefact of
one embedding choice; it is strongest near one-period spans (r₁ = 7.32 at
span 360 d) and weakest with the fewest coordinates (τ=73, d=6), in line
with SW1PerS-style window≈period guidance (Perea & Harer, 2015). **It does
not, by itself, prove that the climate process follows a simple closed
physical trajectory, and it does not independently validate an annual
period** — the post-hoc periodogram/autocorrelation cross-check (§3.5)
shows the series itself is near-annually recurrent, but no annual-
specificity hypothesis test is attempted here.
- The 2-D PCA projection of the reference 8-D embedding
  (`weather_embedding_pca.png`) shows the closed band with a hole, seasons
  progressing around it — the visual counterpart of the dominant H1 class.
  The quantitative evidence is the persistence diagram; the projection is a
  rendering.
- **Interpretation guard.** A dominant H1 class in a sliding-window
  embedding evidences recurrent quasi-periodic structure of the embedded
  series at the studied scale — **not** proof that the climate process
  follows a simple closed physical trajectory. The sub-annual span (210 d)
  is *not* a null control: any non-commensurate delay embedding of a
  periodic signal traces a closed curve; the negative representation
  contrast is the state-space cloud below. The sweep figure shows the six
  discrete (τ, d) configurations as a labelled scatter — τ and embedding
  dimension vary jointly, so no smooth response surface is implied.

### 3.4 State-space PH — the negative representation contrast (`figures/weather_state_space_ph.png`)

Vietoris–Rips PH of the 3-D z-scored daily state-space cloud itself:
1049 H1 classes, dominant persistence 0.21, **r₁ = 1.19 — no dominant
loop.** This is a **negative representation contrast, not a formal
statistical null control**: the state-space cloud and the sliding-window
delay embedding are *different constructions* of the same daily
observations (static feature geometry vs. temporal recurrence), so the
cloud is not a null sample against which a hypothesis is tested — it is a
second representation whose topology answers a different question. The
contrast shows that the dominant H1 class depends on the temporal
construction: the annual signal lives in the *temporal* organization
(recurrence in time, recovered by the sliding-window embedding), not in
the static geometry of daily weather states, which day-to-day weather
variability fills in. This is the cleanest demonstration in the extension
that "where you look" (feature space vs temporal embedding) determines
what topology you see — and it is reported as a result, not hidden.

### 3.5 Post-hoc seasonality sanity check (`figures/weather_seasonality_check.png`)

Added at Stage 3 (review-suggested, optional): an FFT periodogram and a
normalized autocorrelation of the z-scored daily TEMP series — the same
series the sweep embeds. Measured: **dominant FFT period 365.3 d**
(30–800 d search band), **autocorrelation peak lag 360 d** within the
pre-specified fixed analysis search window of 180–550 d, acf(365) = +0.67,
acf(182) = −0.75
(anti-phase half-year — the signature of a near-sinusoidal annual cycle).
The series itself is therefore near-annually recurrent, consistent with
the recurrent structure the sliding-window PH recovers.

Scope: this check is **post-hoc and descriptive** — computed only after
the sweep was pre-specified, run, and saved; it was **not** used to
select, retune, or re-rank any embedding parameter, and it is not an
annual-specificity hypothesis test. `weather_seasonality_check.json`
records the method, search bands, arrays, and this scope statement.

## 4. Deviations from the original plans

| Deviation | Reason |
|---|---|
| Primary cloud is 3-feature (TEMP/DEWP/SLP), not the Rev2 4-feature set | WDSP missingness structure (all Jan–Feb 2019) would delete winter; pre-specified >5% rule triggered a documented redesign; 4-feature cloud kept as sensitivity check |
| No t-SNE; UMAP not run (yet) | t-SNE dropped from the default set (UMAP covers the stochastic-embedding role; would need separate extension requirements file per preservation rules) |
| One station, not two | Gate discipline: second station only after one-station review |
| ENSO exhibit is phase-colored PCA panel only | Descriptive context with embedded power statement (adversarial-review W3 honored) |
| Sweep re-derived from parameter semantics (τ, d, span) instead of copying "60-day window, d=8" | Master-prompt requirement; plan's values kept as reference after span analysis |

## 5. Limitations

- Single station, single variable class; no spatial or vertical structure;
  findings do not generalize to other stations or climates without the
  gated second station.
- The ONI coloring cannot support any ENSO claim (power statement).
- r₁ ≥ 3 "prominence" is a stated convention, not a theorem (baseline
  GAP_RATIO_CONVENTION carried over).
- The seasonal sweep covers **six configurations in which τ and embedding
  dimension vary jointly**; it demonstrates robustness across six sensible
  pre-specified settings, not a full two-dimensional response surface, and
  the labelled-scatter figure deliberately implies no interpolation
  between configurations.
- The seasonality check (§3.5) is post-hoc and descriptive; it is not an
  annual-specificity test and played no role in choosing embedding
  parameters.
- Mapper runtimes (~0.1 s/cell) and ripser runtimes (7–29 s/run) are
  wall-clock, environment-dependent, and labeled as such.
- No human-reader evidence: nothing here measures what a person sees in
  these figures; the baseline E3 single-observer inspection remains the
  only artifact-reading evidence in the project, and it did not cover these
  new figures.

## 6. Reproduce

```bash
# from the repository root, project venv active
python extensions/meteorology/scripts/fetch_gsod.py          # network; idempotent
python extensions/meteorology/scripts/preprocess_weather.py  # deterministic
python extensions/meteorology/scripts/run_weather_analysis.py        # ~2.5 min
python extensions/meteorology/scripts/seasonality_check.py    # post-hoc check
python extensions/meteorology/scripts/render_weather_figures.py      # from saved results
python -m pytest extensions/meteorology/tests/ -q            # 44 tests
python extensions/meteorology/scripts/determinism_check.py  # full re-run identity
```

All parameters live in `configs/weather.yaml`; nothing is hard-coded.
Numerical outputs are saved before figures; figures render from saved
results only. The determinism check re-runs preprocess → analysis →
seasonality check → figures and passes: all output files structurally
identical across re-runs (figures pixel-identical; JSON volatile fields =
timestamps and wall-clock times only).

## 7. Directory map

```text
configs/weather.yaml            all parameters (station, schema, units, sweep)
data_provenance/raw/            immutable raw CSVs + oni.data
data_provenance/provenance.json URLs, timestamps, checksums, schema facts
data_provenance/processed/      cleaned CSV + analysis NPZ (+checksums in report)
wx/weather_lib.py               shared library (parsing, validation, embedding, ONI)
scripts/                        fetch, preprocess, analysis, seasonality check,
                                figures, determinism
results/                        preprocessing report, analysis results, mapper
                                results, diagrams NPZ, embedding NPZ, seasonality
                                check, claims table
figures/                        12 PNGs + captions.json
tests/                          44 tests (units, sentinels, dates, embedding,
                                output schemas, figures, seasonality, claims table)
```

## 8. Stage-3 correction log (2026-10-22)

Review-mandated corrections; **no numerical result changed** (the analysis
results and diagram NPZ files are untouched — the determinism re-run after
correction confirms all outputs regenerate identically):

| Changed artifact | Change | Reason |
|---|---|---|
| `figures/weather_temp_series.png` | x-ticks moved to true January-1 positions (2019…2024, each once) | the old uniform 365-day tick arithmetic drifted against the calendar (2020 has 366 days) and produced a duplicated "2020" label |
| `figures/weather_pca_panels.png` | ONI panel title wrapped to two lines | the title was clipped at the figure edge; the DESCRIPTIVE-ONLY qualification is retained and now fully visible |
| `figures/weather_seasonal_ph_sweep.png` | redrawn as a labelled scatter; points not connected; reference config starred; annual reference line and r₁ = 3 convention line retained | the old connected-line rendering implied a smooth response curve from six discrete configurations in which τ and embedding dimension vary jointly |
| `figures/weather_seasonality_check.png` + `results/weather_seasonality_check.json` + `scripts/seasonality_check.py` | added | review-suggested optional post-hoc periodogram/autocorrelation sanity check; explicitly not used to retune the sweep |
| `figures/captions.json` | sweep, state-space-barcode, seasonal-reference-barcode captions revised; seasonality caption added | wording tightened per review |
| `README.md`, `results/claims_evidence.json` | wording tightened (A10/A11/A12 revised, A14 added) | dominant-H1 finding stated as consistent with recurrent seasonal or quasi-periodic structure; state-space result called a negative representation contrast, not a formal statistical null control; single-station / six-configuration / prominence-threshold limitations kept explicit |
| `scripts/render_weather_figures.py`, `scripts/determinism_check.py`, `tests/test_weather_outputs.py` | figure code corrected; determinism re-run list extended; 3 new seasonality tests | implementation of the corrections above |

## 9. Stage-4 correction log (2026-10-22)

Review-mandated preflight correction; **no numerical result changed**
(`weather_analysis_results.json`, the diagram NPZ files and every other
figure are untouched; the sweep figure re-renders deterministically —
identical checksum across repeated runs):

| Changed artifact | Change | Reason |
|---|---|---|
| `figures/weather_seasonal_ph_sweep.png` | labels redrawn with thin leader lines and hand-placed anchors (`render_sweep_figure` in the render script); the annual-period note moved to the top of each panel; six discrete configurations, reference star, annual line and r₁ = 3 convention line all retained | the Stage-3 offset-based labels overlapped: in the left panel the reference label sat on the annual-period note and on its own star; in the right panel the τ=52/d=8 and τ=73/d=6 labels (spans 364 and 365 days) collided and the reference label covered its star — confirmed by VLM inspection of the actual figure |
| `figures/captions.json` | sweep caption extended with the Stage-4 note (leader-line labels); all Stage-3 honesty statements retained verbatim | record the correction |
| `scripts/render_weather_figures.py` | sweep rendering extracted into the module-level function `render_sweep_figure(analysis)` which returns the annotation artists | enables the programmatic regression test |
| `tests/test_weather_outputs.py` | +3 tests (`TestSweepLabelPlacement`): no two label bounding boxes intersect in either panel; no label box covers a data marker; all six configurations labelled with the annual-period and reference annotations present | regression check for the overlap defect, rendered from the saved results |
