# Independent code audit -- findings

Scope: src/{pipeline,similarity,shapes}.py; extensions/meteorology; extensions/stability; saved results; raw GSOD CSVs. Project root: `<original-project-copy>`. Scratch experiments: `E:\sciviz_scikittda\independent_rebuild\verification\audit_scratch\` (rawcheck.py, w1-w4.py, l1-l2.py, f_check.py, f2.py, f3.py, g1.py, g2.py, a1.py). Stack: ripser 0.6.15, persim 0.4.1, kmapper 2.1.0, numpy 2.5.4.

Verification labels: **executed** = reproduced by an independent code run; **read** = read-only inference from code/text.

## Summary

No BLOCKING finding: every headline number I recomputed (weather preprocessing counts, three of six H1 sweep configs, state-space PH, seasonality numerics, two LOYO folds, 90 resampling index sets, Mapper statistics) reproduces exactly. The problems are interpretive/statistical: (F-01) the Mapper '13/30' cycle-loss figure is relative to an atypical single reference and is not stable; (F-02) the 1.9%/4%/34% contrast is a denominator effect on an overlapping reference; (F-03) LOYO folds are not all one-year-out and cannot fail; (F-04) there is no null control (my nulls support the conclusion: r1 1.0-1.15 vs 4.7-7.3); plus wording/pre-specification overclaims (F-05).

| ID | Severity | Area | Summary |
|---|---|---|---|
| F-01 | MAJOR | G (Mapper resampling) | 'Cycle cue disappears in 13/30' is measured against ONE atypical reference graph and is itself a noisy count; most independent samples of the same annulus have no Mapper cycle at (10, 0.35). |
| F-02 | MAJOR | F/H (PH resampling, relative bottleneck) | The '1.9% / 4.0% / 34%' relative-bottleneck contrast is mostly a denominator effect, and the overlapping-subsample design understates sampling variability. |
| F-03 | MAJOR | E (Leave-one-year-out) | 10 of the 36 fold-configurations are not 'leave-one-year-out': an entire additional retained year contributes <=6 embedding windows (0 windows in 6 cases), and the design has almost no power to detect single-year dependence. |
| F-04 | MAJOR | C/H (missing null control; representation contrast) | No surrogate/null control for the delay-embedding result, and the 'negative representation contrast' (state-space r1=1.19) is guaranteed by construction rather than an empirical finding about where the annual signal lives. My controls support the project's qualitative conclusion. |
| F-05 | MINOR | C/D (pre-specification evidence) | Claims that the sweep and the seasonality window were 'pre-specified' / 'fixed before outputs were inspected' are not supported by any artifact in the repository; the sweep was designed knowing the annual period. |
| F-06 | MINOR | D (seasonality check) | 'Dominant FFT period 365.3 d' is the n/6 FFT bin, not a measured period; frequency resolution is about +-50 d. |
| F-07 | MINOR | B (weather config/docs consistency) | Stale/inconsistent counts between weather.yaml comments, README and the preprocessing report. |
| F-08 | MINOR | B (STP handling / sentinels) | STP exclusion is justified, but the cause is a truncated thousands digit (recoverable), STP's real sentinel in these files is 999.9 (6 rows) not 9999.9, and MAX/MIN have no sentinel entry. |
| F-09 | MINOR | B (sensitivity check not run) | The 4-feature 'documented sensitivity check' is only a day count; no analysis is ever run on it, and the '>5% pre-specified rule' is not implemented in code. |
| F-10 | MINOR | Reproducibility | Stability scripts abort in this (Windows) environment: the byte-identity guard fails by 1 ULP. |
| F-11 | MINOR | G (membership-Jaccard S) | S between a 400-point subsample graph and the 500-point reference has a structural ceiling of ~0.80 that is not mentioned beside the reported medians. |
| F-12 | INFO | A (gap ratio / essential class / distances) | Gap-ratio code and distance handling are correct for the data actually produced; latent edge-case behaviours noted. |
| F-13 | INFO | F (H0 caveat) | The report's H0 Wasserstein inflation caveat is correct; 'bottleneck is not affected' is slightly too strong. |
| F-14 | INFO | G/B (by-construction regularities) | Node count = 2 x n_cubes is a mechanical consequence of KMeans(k=2), presented in places as a replication; ONI 'two episodes' is a slight undercount. |

## Findings

### F-01 [MAJOR] 'Cycle cue disappears in 13/30' is measured against ONE atypical reference graph and is itself a noisy count; most independent samples of the same annulus have no Mapper cycle at (10, 0.35).

*Area:* G (Mapper resampling)  |  *Verification:* executed

**Evidence**
- Definition: cycle cue lost <=> cyclomatic_number E-V+C == 0 (src/pipeline.py:230; run_mapper_resampling.py:183). Recomputed from saved links: counts {0:13, 1:9, 2:8}, reference 2 -- reproduced exactly (executed: audit_scratch/f_check.py, g1.py).
- Same Mapper config on 30 INDEPENDENT annulus draws (same generator, new seeds 5000+i): n=500 -> cyclomatic {0:24, 1:6, 2:0}; n=400 -> {0:22, 1:8}. (g1.py)
- 30 fresh 80% subsamples of the SAME 500 points (seeds 99000+i): {0:18, 1:8, 2:4}; the headline 13/30 becomes 18/30 with a different seed set (binomial SE ~0.09). (g1.py)
- The full-data reference (seed-42 sample) has cyclomatic 2, which is atypical for this generator+config.

**Impact on stated claims:** The headline 'right by luck in fewer than half of these subsamples' / 'loses its cycle cue in 13/30' (report l.96, l.884-888, F9) is not a stable quantity. Subsampling is not what removes the cue: a typical sample of this annulus has no Mapper cycle at the reference cell; the reference was an upward outlier. The qualitative claim (Mapper cycle cue is an unreliable loop indicator while the H1 loop is prominent in all 30) survives and is arguably stronger, but the 13/30 figure and the 'subsample-induced loss' framing are overstated.

**Recommended fix:** Report the distribution of cyclomatic number over independent draws (and over subsamples) with an interval; present the reference graph as one realisation, not as truth; drop the 'right by luck' arithmetic.

### F-02 [MAJOR] The '1.9% / 4.0% / 34%' relative-bottleneck contrast is mostly a denominator effect, and the overlapping-subsample design understates sampling variability.

*Area:* F/H (PH resampling, relative bottleneck)  |  *Verification:* executed

**Evidence**
- Recomputed from ph_resampling.json: median H1 bottleneck / reference dominant persistence = 0.01927 (annulus), 0.04008 (fig-8), 0.34448 (blob) -- matches the report arithmetic. But the ABSOLUTE medians are 0.0288, 0.0193, 0.0481: all noise-scale and within a factor 2.5 of each other; the ratios differ because the denominators are 1.496, 0.481, 0.140 (render_stability_figures.py:176-178; summarize_stability.py:68-71).
- Independent n=500 draws (new seeds) vs the seed-42 reference: annulus relative H1 bottleneck median 0.0319 (vs 0.0193 for overlapping 80% subsamples, ~1.65x); blob 0.397 (vs 0.344). Dominant annulus H1 over independent draws 1.50-1.59, r1 12.4-22.0. (audit_scratch/f2.py, executed, 20 draws)

**Impact on stated claims:** 'Diagrams of a constructed feature are proportionally far more stable' is really 'the constructed loop is ~10-20x above the noise floor', which the gap ratio already says. Overlap with the reference makes all distances optimistic (the report acknowledges overlap qualitatively but never quantifies it). The qualitative ordering annulus < blob is preserved.

**Recommended fix:** Report absolute bottleneck next to a noise-floor baseline (bottleneck between two independent draws of the same shape); treat the % column as descriptive only; quantify overlap optimism as done here.

### F-03 [MAJOR] 10 of the 36 fold-configurations are not 'leave-one-year-out': an entire additional retained year contributes <=6 embedding windows (0 windows in 6 cases), and the design has almost no power to detect single-year dependence.

*Area:* E (Leave-one-year-out)  |  *Verification:* executed

**Evidence**
- Window rule: run_weather_loyo.py:167-171 embeds each contiguous block separately and silently skips blocks shorter than the span (sliding_window_embedding returns empty when span>=n, weather_lib.py:175-176). Fold -2020 leaves a 365-day 2019 block; fold -2023 leaves a 366-day 2024 block.
- Windows contributed by the short block (from weather_loyo.json blocks; audit_scratch/l2.py): fold 2020: tau45_d9 5, tau52_d8 1, tau60_d8 0, tau73_d6 0, tau90_d8 0; fold 2023: tau45_d9 6, tau52_d8 2, tau60_d8 0, tau73_d6 1, tau90_d8 0. So 'omit 2020' (or 2023) is effectively 'omit two years' for those configs (JSON n_windows_lost_to_gap = 365..630 reflects it).
- I independently re-ran folds -2022 and -2020 for tau73_d6 with my own year-split and z-scoring: n, dominant persistence and r1 identical to the JSON (1.8853/5.748 and 1.4321/4.954). Folds do exclude the held-out year; no window straddles the gap (no leakage) -- executed.
- Power: an annual harmonic alone explains 82.1% of the variance of z-TEMP (w3.py); any block of >=2-3 years of a near-sinusoid yields a dominant loop. The 36 embeddings share 4/6 of the data pairwise and are not independent replicates.

**Impact on stated claims:** Headline numbers (r1 range 4.376-7.754) are correct as computed and there is no leakage. But 'does not depend disproportionately on any single year' is nearly guaranteed by the data's near-sinusoidal structure, so the analysis cannot fail; '36 embeddings' overstates the evidence. Also the text 'r1 >= 4.38 in every fold' (report l.70, l.936) is false by rounding: the minimum is 4.376.

**Recommended fix:** Disclose the effective data used per fold-config; add single-year/two-year retained subsets and a surrogate null (F-04) to give the check teeth; say 'r1 >= 4.37'.

### F-04 [MAJOR] No surrogate/null control for the delay-embedding result, and the 'negative representation contrast' (state-space r1=1.19) is guaranteed by construction rather than an empirical finding about where the annual signal lives. My controls support the project's qualitative conclusion.

*Area:* C/H (missing null control; representation contrast)  |  *Verification:* executed

**Evidence**
- Recomputed (own parser, own embedding, ripser maxdim=1): shuffled series r1 = 1.14 (tau73_d6), 1.03 (60,8), 1.05 (45,9); AR(1) matched to anomaly lag-1 acf r1 1.11 (73,6); deseasonalised anomalies (2 annual harmonics removed) r1 1.02 (73,6), 1.08 (60,8), 1.02 (45,9) -- versus project 4.75 / 6.75 / 7.32. (audit_scratch/w2.py, executed)
- State-space PH is a function of the SET of daily vectors: permuting day order leaves it unchanged, so it cannot register temporal recurrence by construction. It is also a different object: 3-D, n=2188, median nearest-neighbour spacing 0.105 vs 0.627 for the (60,8) embedding (w4.py). Recomputed: 1049 H1 classes, dom 0.2103, r1 1.186 -- identical to saved JSON.
- meteorology/README.md:146-148 ('consistency across settings indicates the finding is not an artefact of one embedding choice'), :164-166 (sub-annual span is not a null control) -- the sweep itself contains no null.

**Impact on stated claims:** The qualitative conclusion (series near-annually periodic, loop is real) is CONFIRMED by my nulls. But the project's own evidence for it is non-discriminating: all six configs share the same data (82% annual harmonic) and the only 'control' differs in dimension, density and information content. 'Consistency across pre-specified settings' is not robustness in an inferential sense. The report's hedged wording mostly covers this, but README l.183-186 ('the annual signal lives in the temporal organization') and report l.1351-1355 ('a clean demonstration') go beyond the design.

**Recommended fix:** Run shuffled / phase-randomised / AR(1) / deseasonalised surrogates through the same six configs and report null r1 distributions; reword the state-space contrast as a by-construction illustration.

### F-05 [MINOR] Claims that the sweep and the seasonality window were 'pre-specified' / 'fixed before outputs were inspected' are not supported by any artifact in the repository; the sweep was designed knowing the annual period.

*Area:* C/D (pre-specification evidence)  |  *Verification:* read + executed (timestamps via ls/grep)

**Evidence**
- No VCS in the project (file mtimes are copy time, 2026-10-28). weather_analysis_results.json created_utc 2026-10-22T09:57:02Z equals the preprocessing-report timestamp -- the determinism re-run overwrote the original run, so the original run time is unrecoverable.
- EXTENSION_DESIGN.md:91-95 says the sweep is 'built around the observed annual-cycle scale'; 5 of 6 configs have spans 360-365 d or are the plan's reference or brackets; only (60,8) is attested as coming from the Rev2 plan (plan not in repo). weather.yaml comments (l.47-64) contain post-run facts, so the file was edited after results.
- seasonality_check.py:11-17 admits the check is post-hoc, yet lines 26-27 and 125, README:194, report l.591 and claims_evidence call [180,550] a 'pre-specified fixed analysis search window'. PROJECT_WORKLOG.md l.347 originally wrote 'pre-registered 180-550 d window'; the later terminology pass (worklog l.503; extensions/README.md:147) only relabelled it. The window was written into a script created after the sweep ran. The result is not sensitive to it (peak 360 d interior; acf 0.62-0.68 over 340-375 d), but 'pre-specified' is not demonstrable.
- Report l.345-347: 'Sweep configurations ... were fixed before outputs were inspected'.

**Impact on stated claims:** Wording overclaim only; no numerical impact. The r1>=3 convention is declared as such and my nulls (r1 ~1.0-1.15) show it separates signal from noise here.

**Recommended fix:** Replace with 'specified in the design document/config before the run per the worklog; not independently timestamped'; drop 'pre-specified' for the seasonality window.

### F-06 [MINOR] 'Dominant FFT period 365.3 d' is the n/6 FFT bin, not a measured period; frequency resolution is about +-50 d.

*Area:* D (seasonality check)  |  *Verification:* executed

**Evidence**
- n=2192; dominant bin k=6 -> period 2192/6 = 365.33; neighbouring bins 438.4 d and 313.1 d. That bin holds 82.1% of non-DC power; annual harmonic fit R^2 = 0.821. ACF peak lag 360 d in [180,550] (acf 0.676), acf(365)=0.673, acf(182)=-0.746 -- all reproduced exactly (w3.py, executed). ACF is the biased 1/N-normalised estimator with only 6 cycles.

**Impact on stated claims:** Numbers are correct; the precision implied by '365.3 d' and 'peak 360 d' is spurious (ACF is flat within 0.06 over 340-375 d). The 'near-annual' conclusion stands.

**Recommended fix:** Quote the FFT bin width and the flatness of the ACF peak; avoid 3-digit periods.

### F-07 [MINOR] Stale/inconsistent counts between weather.yaml comments, README and the preprocessing report.

*Area:* B (weather config/docs consistency)  |  *Verification:* executed

**Evidence**
- weather.yaml:48-57, 63-64: 'drop 131 days (5.98%)', 'primary missing 5 days, 0.23%', 'SLP: 5 (...+1)'. Raw data (own parser): primary cloud drops 4 days (0.182%), sensitivity cloud drops 129 days (5.885%) -- matching the report/README. The 5th SLP value is the 999.9 reading on 2020-12-01 that the code treats as valid.
- Report table l.570 gives r1=5.62 for tau30_d8 while README:133 gives 5.63 (JSON 5.625). The WDSP gap is 70 consecutive days Jan 1-Mar 11 2019 (all Jan-Feb plus 11 March days), 6 days Jan 2020, 33 in May-Jun 2020, 16 in Sep-Oct 2021 (raw parse), not just 'Jan-Feb 2019'.

**Impact on stated claims:** Cosmetic; headline counts in the report (2188 kept, 4 dropped, 2063 sensitivity) are correct.

**Recommended fix:** Update yaml comments; state the WDSP gaps exactly.

### F-08 [MINOR] STP exclusion is justified, but the cause is a truncated thousands digit (recoverable), STP's real sentinel in these files is 999.9 (6 rows) not 9999.9, and MAX/MIN have no sentinel entry.

*Area:* B (STP handling / sentinels)  |  *Verification:* executed

**Evidence**
- Raw: STP median 12.4, 94.75% < 900, 5.25% in 950-1050 (matches the report). SLP - (STP+1000 if STP<500) has median 4.9 hPa, IQR 4.8-5.0 (hydrostatic expectation ~5.0 hPa at 42.7 m): STP lost its leading '1' (1012.4 -> 012.4). (rawcheck.py, w3.py, executed)
- weather_lib.py:33 SENTINELS['STP']=9999.9 -> the six STP=999.9 rows (incl. 2021-04-04 where SLP is also missing) count as valid; the report says STP n_missing=0.
- weather_lib.py:32-36 has no MAX/MIN sentinel although both are in NUMERIC_FIELDS and converted F->C (l.46-47): a 9999.9 would become 5537.7 C. None occur in this data (raw scan; max MAX 98.1 F).

**Impact on stated claims:** No impact: STP, MAX, MIN are not used in any analysis. SLP=999.9 on 2020-12-01 is independently corroborated as a real reading (STP 994.7 + ~5 hPa = 999.8), so the project's decision to keep it is right.

**Recommended fix:** Add MAX/MIN sentinels; describe STP as digit-truncated rather than 'corrupted'.

### F-09 [MINOR] The 4-feature 'documented sensitivity check' is only a day count; no analysis is ever run on it, and the '>5% pre-specified rule' is not implemented in code.

*Area:* B (sensitivity check not run)  |  *Verification:* read + grep

**Evidence**
- grep: X_sensitivity / sensitivity_dates appear only in preprocess_weather.py:312-313 (written to NPZ), never read by run_weather_analysis.py or any other script. The yaml keys drop_rule and max_acceptable_primary_missing_fraction (weather.yaml:58-59) are never read by any .py file.

**Impact on stated claims:** README/report describe it as 'a documented sensitivity check quantifying the cost of adding wind' -- true only for the drop count. The redesign (dropping WDSP) is missingness-driven, not outcome-driven, so no bias in headline results.

**Recommended fix:** Either run PH/Mapper on the 2063-day cloud or call it 'a count'.

### F-10 [MINOR] Stability scripts abort in this (Windows) environment: the byte-identity guard fails by 1 ULP.

*Area:* Reproducibility  |  *Verification:* executed

**Evidence**
- run_ph_resampling.py:106-111 and run_mapper_resampling.py:144-148 use np.array_equal(make_shape(...), results/e1/data/{shape}.npy) and SystemExit otherwise. On the pinned stack (numpy 2.5.4) regenerated annulus and figure_eight differ from the saved arrays by max |diff| = 2.2e-16 (trig libm difference); blob and three_blobs are identical (f3.py, executed).
- With the regenerated points all saved results were nevertheless reproduced: PH rep0 H1 bottleneck 0.0347672 (json 0.034767), H1 Wasserstein 0.714832, H0 Wasserstein 3.68068, top-3 persistences; Mapper cyclomatic for all 30 annulus reps; global-membership mapping (first 10 reps).

**Impact on stated claims:** No effect on results; the scripts as written cannot be re-run elsewhere, and the 'byte-identical' wording is platform-specific.

**Recommended fix:** Use np.allclose(atol=1e-12) in the guard.

### F-11 [MINOR] S between a 400-point subsample graph and the 500-point reference has a structural ceiling of ~0.80 that is not mentioned beside the reported medians.

*Area:* G (membership-Jaccard S)  |  *Verification:* executed

**Evidence**
- Restricting the reference nodes to the sampled 400 points and comparing with the full reference gives S median 0.800 (0.786-0.821) (g2.py, executed). Reported medians 0.585 / 0.762 / 0.645 (report l.870-879) are therefore ~73% / 95% / 81% of the attainable maximum.

**Impact on stated claims:** S is declared exploratory, but a reader will take 0.585 as 'substantial movement' when ~0.2 of the deficit is mechanical.

**Recommended fix:** Print the ceiling next to every S, or normalise by it.

### F-12 [INFO] Gap-ratio code and distance handling are correct for the data actually produced; latent edge-case behaviours noted.

*Area:* A (gap ratio / essential class / distances)  |  *Verification:* executed + read

**Evidence**
- src/pipeline.py:36-51: descending sort, 1-based k, ratio p[k-1]/p[k]; verified by execution: unsorted [1,5,2,.5] -> r1=2.5, r2=2.0, r3=2.0; empty/single/zero p_{k+1} -> None; k<1 -> ValueError (a1.py).
- Latent: NaN input -> nan (not None); inf persistence -> inf; a perfectly clean single loop (p2=0) returns None rather than +inf, and summarize_stability.py:127-128 min() would raise on None. None of these occur (ripser called without thresh, maxdim=1: H1 deaths all finite; all weather and resampling ratios are defined).
- Infinite deaths: only the single H0 essential class (verified: 1 inf in H0, 0 in H1). h0_prominent_merges filters it (pipeline.py:68); persim 0.4.1 drops non-finite deaths in both bottleneck (bottleneck.py:63,72) and wasserstein (wasserstein.py:50,59) -- confirmed from the installed source. So full (500 pts, 499 finite H0) vs subsample (400 pts, 399 finite) is handled by diagonal matching.
- H0 and H1 distances are never pooled into one number (summarize_stability.py:64-67 keeps them separate). They are juxtaposed on a shared y-axis per panel in ph_resampling_dists.png (render_stability_figures.py:93-104) with a caption caveat. Wasserstein = persim order-1 with Euclidean ground metric (a sum), bottleneck = L-infinity: not interchangeable.

**Impact on stated claims:** None on headline numbers.

**Recommended fix:** Optional: raise on non-finite persistences in gap_ratio; put H0 and H1 on separate axes.

### F-13 [INFO] The report's H0 Wasserstein inflation caveat is correct; 'bottleneck is not affected' is slightly too strong.

*Area:* F (H0 caveat)  |  *Verification:* executed

**Evidence**
- Rep0: H0 Wasserstein vs full = 3.68; between two 400-point subsamples = 0.67 (cardinality-matched control). Finite H0 deaths: median 0.0547 (full) vs 0.0611 (sub); sum 28.2 vs 25.4 -- the distance is about the difference in total persistence. H0 bottleneck vs full 0.022 vs 0.0157 for 400-vs-400 (f2.py, executed).

**Impact on stated claims:** Subsampling shifts H0 death times upward (larger nearest-neighbour distances), so H0 bottleneck is mildly affected too. Descriptive only.

**Recommended fix:** Reword to 'less affected'.

### F-14 [INFO] Node count = 2 x n_cubes is a mechanical consequence of KMeans(k=2), presented in places as a replication; ONI 'two episodes' is a slight undercount.

*Area:* G/B (by-construction regularities)  |  *Verification:* executed + read

**Evidence**
- pipeline.py:203-207 / weather_lib.py:249-253: KMeans(n_clusters=2) is hard-wired, so every cover cube yields exactly 2 nodes; weather grid shows 10/20/30/40 nodes (weather_mapper_results.json). meteorology/README.md:105-109 and report l.70 present 'node count = 2xn_cubes replicates on real data'. Elsewhere acknowledged as an 'uninformative regularity'.
- weather.yaml:25-30 says 'roughly two ENSO episodes'; oni.data shows ONI >= 0.5 early 2019 and 2020-Q1, <= -0.5 from mid-2020 to early 2023, >= 0.5 from Apr 2023 (descriptive context only; no inference drawn).

**Impact on stated claims:** Cosmetic.

**Recommended fix:** Say 'mechanically 2 x n_cubes because k=2'.

## CONFIRMED CORRECT

- Raw data integrity: all 6 GSOD CSVs and oni.data SHA-256 equal provenance.json (sha256sum). 2192 rows, 2192 distinct dates, calendar-complete 2019-01-01..2024-12-31 (own csv-module parser, set difference against the date range): per-year 365/366/365/365/365/366; single station 72505394728, elevation 42.7.
- Sentinels/missingness from own parse: TEMP 0, DEWP 0, SLP 4 x '9999.9' (+1 '999.9' on 2020-12-01), STP 6 x '999.9', VISIB 2, WDSP 125, MXSPD 125, GUST 911, SNDP 2119, MAX/MIN/PRCP 0 -- equal to weather_preprocessing_report.json (except STP interpretation, F-08). Dropped dates 2019-04-20, 2021-04-04, 2023-09-18, 2024-12-30 equal the report.
- Primary cloud: 2188 days kept, z-scored AFTER dropping the 4 days; means (13.757, 5.702, 1016.693) and SDs (8.938, 10.144, 7.386) reproduced; PCA explained variance 0.68984/0.28625 reproduced (SVD). Sensitivity-cloud drop = 129 days reproduced. Units: F->C and mb identity (SLP 989-1046 hPa plausible), knots/inches conversions in weather_lib.py correct; TEMP lies within [MIN,MAX] for all rows, DEWP <= TEMP everywhere.
- Seasonal series: z-scoring (ddof=0) uses all 2192 days BEFORE windowing; TEMP is gapless so no window spans a gap and no incomplete windows arise; windows = n-(d-1)*tau at stride 1, all six n_points (1982, 1832, 1828, 1772, 1827, 1562) equal 2192-span.
- Independent recomputation of H1 persistence (own parser + own embedding + ripser 0.6.15, maxdim=1, default thresh, no n_perm): tau45_d9 dom 2.5706 r1 7.319 (n=1832, 1720 H1 classes), tau73_d6 dom 1.4168 r1 4.745 (n=1827, 1498), tau60_d8 dom 2.167 r1 6.753 (n=1772, 1616); the saved H1 diagrams in weather_seasonal_ph_dgms.npz are element-wise equal (np.allclose) for all three. State-space cloud (n=2188): 1049 classes, dom 0.2103, r1 1.186 reproduced.
- Scale invariance of r1: embedding raw degC vs z-scored (tau73_d6) gives r1 4.744627 vs 4.744628 and a dominant-persistence ratio of 8.9304 = SD of TEMP; r_k is invariant to the affine z-scoring, and dominant persistence differs across LOYO folds only through the retained SD (8.77-9.14 C). The claim in run_weather_loyo.py:15-17 is correct.
- LOYO: folds exclude the held-out calendar year by date (year_arr != fold_year), z-score is refit on retained days, windows are built within contiguous blocks (ordinal-day gaps) so no window contains held-out days (no leakage); two folds re-run independently (-2022, -2020, tau73_d6) with identical n, dominant persistence and r1. 36 fold-configs present; r1 range 4.376-7.754 (min fold 2024 tau73_d6; max fold 2020 tau45_d9).
- Seasonality-check numerics (FFT bin 365.33 d, power fraction 0.821, ACF peak lag 360, acf(365)=0.6732, acf(182)=-0.7462) reproduced.
- PH resampling design: seed rule seed=20261022+offset+i reproduces all 90 stored index sets exactly (np.random.default_rng(seed).choice(500,400,replace=False), sorted); sizes 400/500; 90 distinct seeds; each point appears 15-30 times (mean 24); Mapper replicate indices/seeds are identical to the PH replicate indices for all 3 shapes x 30 reps; reference diagrams (results/e1/*_ph_dgms.npz) equal a fresh ripser on the full cloud; rep0 distances and persistences reproduced (F-10).
- 'H1 loop prominent in 30/30' means: the ground-truth-rank gap ratio r_k (r1 for annulus) >= 3 in every replicate (annulus r1 13.205-25.631; figure-eight r2 7.348-13.815; blob r1 1.005-1.751, 0/30 >= 3). Dominant persistence ranges 1.439-1.575 / 0.4575-0.5115 / 0.0924-0.1813 reproduced. The statistic uses the supplied ground-truth rank (by design; the project says so).
- Mapper resampling: lens (PCA-1) is refit on each subsample (pipeline.py:202); memberships are mapped local->global through sub_idx (run_mapper_resampling.py:77-89) -- re-ran 10 reps and the global memberships equal the saved ones; nodes/edges/components/cyclomatic recomputed from saved links with networkx for all 90 graphs: 0 mismatches. PCA sign: PC1 loading signs identical across all 30 subsamples, and negating the lens gives identical membership sets in 30/30 -- no sign-ambiguity effect.
- E1 reference Mapper rebuild is verified against saved memberships before any comparison (run_mapper_resampling.py:158-165) -- guard logic is sound (modulo F-10 for the byte-identity guard).
- Distances are computed on raw (unrescaled) point clouds: synthetic generators are not standardised, so absolute values are in generator units; weather PH is on 1-D z-scored TEMP, the state-space cloud on 3-D z-scored features. No cross-dataset comparison of raw distances is made except the normalised ratio discussed in F-02.

## Pre-specified vs post-hoc (as far as the artifacts allow)

- Attested before outputs (design doc / plan): reference (tau=60, d=8) from the Rev2 plan; Mapper grid {5,10,15,20} x {0.35,0.50}; ground-truth ranks per shape (src/shapes.py); r_k>=3 convention; 30 x 80% resampling design and seed rule (stability.yaml). Only the worklog attests the ordering; no timestamps/VCS (F-05).
- Chosen knowing the answer (by design): the other five sweep configs (spans 210/360/364/365/630 d) bracket the annual period; none is a true null.
- Post-hoc by the project's own admission: seasonality check (FFT/ACF); its [180,550] search window and [30,800] band were set in a script written after the sweep.
- Feature redesign (drop WDSP) was triggered by missingness, not by outputs (acceptable); the '>5% rule' is not implemented in code (F-09).

## H. Statistical validity summary

- No p-values or confidence intervals are claimed; guards G1-G5 are stated repeatedly and are accurate. Nothing in the code computes a significance statistic.
- Items that exceed what the design supports: F-01 ('right by luck in fewer than half'), F-02 ('proportionally far more stable'), F-03 ('not dependent on any single year', '36 embeddings'), F-04 ('clean demonstration' that representation decides topology; six-config 'robustness'), F-05 ('fixed before outputs were inspected').
- Bug search: I found no code bug that changes a headline number.
