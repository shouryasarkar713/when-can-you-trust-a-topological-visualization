<!-- titlepage
title: Q&A Preparation
subtitle: When Can You Trust a Topological Visualization? — anticipated questions and defensible answers
short: Q&A preparation — When Can You Trust a Topological Visualization?
field: Companion to | Final report and 14-slide presentation
field: Author | Shourya Sarkar
field: Date | 28 October 2026
status: Each answer states what the experiments establish, where the evidence is, and what is not claimed. Section numbers refer to the final report.
-->

# Q&A Preparation

## A. Contribution and positioning

**1. What does this project contribute beyond running three packages?**
An evaluation, not an algorithm: a 13-task capability audit; a Mapper sensitivity grid with a known-answer design and a no-loop control; a structured inspection of what the figures communicate; a weather case study with matched null controls; an offline explorer for saved results; resampling analyses; and control experiments that separate the effects of cover, clusterer, sampling and temporal order. The packages already provide the persistent-homology computation, diagram distances and the Mapper construction. No new algorithm, metric or theorem is claimed, and the gap ratio r_k and the membership-overlap indicator S are explicitly not canonical (Section 3.2).

**2. Isn't it already known that Mapper depends on its parameters and that Rips persistence is noise-sensitive?**
Yes (Carrière & Oudot 2018; Carrière, Michel & Oudot 2018; Belchí et al. 2020; Sen, Singh & Tiwari 2026 evaluate Mapper more generally). The project does not claim otherwise. What it adds is a reproducible demonstration on a specific, current software stack, a separation of what depends on data, parameters, clusterer and drawing, and controls showing that the clusterer rule and scale are part of that dependence.

**3. Why Scikit-TDA and not GUDHI or giotto-tda?**
The assignment evaluates a visualization system, and Scikit-TDA is a lean, pip-installable triad with citable software papers and a first-party Mapper visualization. GUDHI and giotto-tda are context. A comparison of ripser with GUDHI was left out of scope, so ripser's correctness is supported only by the known-answer signatures of the synthetic data, determinism and the upstream literature, not by agreement with a second implementation (Section 2.2).

**4. What is the single most important finding?**
That the reliability of a Mapper cycle cue depends on the clustering rule and its scale, while the persistence evidence for the constructed loops was present in every tested subsample and redraw. On the annulus: no cycle in 13/30 subsamples with forced two-cluster KMeans, exactly one cycle in 30/30 with single-linkage at 3 × the median 5-NN distance, absent in 22/30 at half that scale (Section 8.3). The practical message: ask which representation carries the claim and check what it depends on.

## B. Methods and metrics

**5. What does "dominant H1" mean exactly, and why r_k ≥ 3?**
r_k = p_k / p_{k+1}, where p are H1 persistences in descending order and k is the known number of loops (1 for the annulus, 2 for the figure-eight, 1 for real data). "Dominant" means r_k ≥ 3. The threshold is a stated convention, not a theorem; it has no uncertainty attached and was not tuned. The data separate the cases widely (loop data r_k ≥ 7.35; no-loop blob ≤ 1.75; weather nulls ≤ 1.22), so the conclusions do not hinge on 3 versus another value in this range. r_k is unchanged by constant rescaling (embedding raw and z-scored data gives 4.744627 and 4.744628), but raw persistences are not.

**6. Why is node count always 2 × n_cubes?**
Because the default clusterer is `KMeans(n_clusters=2)` in every cover interval. It is a mechanical consequence, not a finding about the data, and the reason a data-adaptive clusterer was tested; with single-linkage no cell has that node count.

**7. Is S a valid graph distance?**
No, and it is never called one. It compares membership sets greedily, ignores edges and components, is not normalized for node count, violates the triangle inequality (a unit-tested counterexample), and S = 1 does not imply identical graphs. Between a 400-point subsample and the 500-point reference it cannot exceed about 0.80 (median 0.800, range 0.786–0.822).

**8. Why bottleneck and Wasserstein, and can H0 and H1 values be compared?**
Bottleneck is a stable L∞ matching distance; the Wasserstein distance used here is an order-1 sum; they answer different questions, and H0 and H1 are never pooled. H0 Wasserstein is inflated when the numbers of classes differ (399 against 499 finite classes): 3.68 against the full reference, 0.67 against another subsample.

**9. How were the Mapper parameters and the clusterer scales chosen?**
The cover grid, reference cell, PCA-1 lens and ground-truth ranks were fixed in the design before the runs; the figure-eight contrast cell was chosen after the full grid was measured. The two single-linkage scales (1.5 and 3.0 × the median 5-NN distance) were written into the configuration before the control ran but after the default-rule results were known, and only these two were tried, so they are an exploratory choice. No order of design and analysis can be proven from time stamps (Section 10.3).

## C. Experiments and controls

**10. The blob has graph cycles but no dominant H1 class. Does that make Mapper cycles meaningless?**
No. It shows that graph cycles do not certify loops (G4). Under forced two-cluster KMeans the blob had cycles in all 30 independent draws (cyclomatic 2–8); under single-linkage at 3 × d₅ it had none in 29/30 but 3–10 components. Whether a no-loop sample produces cycles depends on the clusterer. Equally, the absence of a cycle does not prove the absence of a loop.

**11. Why is the static-cloud comparison not a null control?**
The 3-D cloud's persistence depends only on the set of days, so permuting the day order cannot change it, and it differs from the embedding in dimension, variables and density. The matched controls are the anomaly series (annual harmonics removed) and shuffled series, put through the same six configurations.

**12. What do the harmonic-removal and shuffle controls show — and not show?**
Under the criterion r₁ ≥ 3, the temperature embedding has a dominant H1 gap (r₁ = 4.75–7.32); the anomaly series (r₁ = 1.02–1.14) and ten shuffled series (r₁ = 1.01–1.22) do not. H1 classes still exist in the null embeddings; only a dominant one is absent. The two fitted harmonics explain 82.2 % of the variance. So the cue depends on the annual harmonic structure and on temporal order in these tests. It does not show that the annual cycle is the only source, that no loop exists in the anomaly series, or anything climatological. Limits: a two-term least-squares fit, shuffles that destroy all autocorrelation, ten shuffles at one configuration, no phase-randomised or autoregressive surrogates, one station.

**13. Is the weather result a climate finding?**
No. It shows that the method recovers a dominant H1 cue from a series with a strong annual component, a known feature of temperature data. Nothing is claimed about other stations, trends, ENSO or physical trajectories (G5).

**14. Were the embedding configurations and the seasonality window specified in advance?**
The reference (τ = 60, d = 8) came from the study plan; the other five were designed around the annual period knowing it; the seasonality check and its window were written after the sweep. No artifact time-stamps the order, so nothing is called pre-registered (Section 10.3). The FFT value of 365.3 days is the sixth frequency bin (2192/6), with neighbouring bins at 438 and 313 days.

**15. What does leave-one-year-out show?**
Only that no single year is needed for the cue, with limited power: in 10 of the 36 fold-configurations a second retained year contributes at most 6 windows (none at all in 5), and an annual harmonic explains 82 % of the variance. r₁ ranges from 4.376 to 7.754. It is not a hypothesis test or confidence interval.

**16. Resampling uses overlapping subsamples against the full data. Isn't that circular?**
It is descriptive (G1), which is why independent redraws were added: the H1 bottleneck median is 0.041 for the annulus against 0.029 for overlapping subsamples. The relative 1.9 % / 4.0 % / 34 % contrast mostly reflects the sizes of the reference features and is not used as evidence.

**17. Why is the annulus reference graph described as one realisation?**
The seed-42 reference has cyclomatic number 2, while independent redraws at the same cell give 0 in 20 of 30, 1 in 7 and 2 in 3 under forced two-cluster KMeans. A single reference is not truth, and the count of subsamples without a cycle itself varies with the seed set (binomial standard error about 0.09).

## D. Data, human factors and the explorer

**18. How was the weather data handled?**
NOAA GSOD, station 72505394728, 2019–2024: 2192 rows, a complete calendar, raw files verified by SHA-256 and by a fresh download. The primary cloud uses TEMP, DEWP and SLP (2188 days after dropping 4 days with missing SLP); adding WDSP would drop 129 days in seasonal clusters, and STP is excluded because 94.8 % of its values are below 900 hPa (a lost leading digit). No value was imputed.

**19. Did you run a user study?**
No. The planned classroom pilot was not conducted; no participants, recruitment, consent, blinding or response data exist. E3 is a structured inspection of 13 artifacts by the author, an invested observer, with an AI vision model as a viewing aid. It supports statements about the artifacts (unlabeled colours, the essential H0 point, ring-like noise cycles), not about viewers.

**20. How do you know the explorer is genuinely offline?**
A Playwright script drives Chrome 156 in a fresh context with the network disabled and every non-file request aborted and logged: no request besides the document, no external tags, no Performance-API resources, no console errors, and 222 of 222 comparisons against independently recomputed values across all 35 cells and exports, at six viewport sizes. The stock kmapper HTML in the same session throws `d3 is not defined` and draws 0 nodes.

**21. Is the explorer novel?**
Only in a narrow combination: saved results first, a single file, no server or CDN, per-cell provenance, embedded safeguards. Mapper Interactive and giotto-tda recompute on the fly; LoCoMapper quantifies local uncertainty under cover perturbation. The explorer cannot show cells that were not precomputed and shows one clusterer per dataset.

## E. Reproducibility and limits

**22. Can someone else reproduce this?**
Yes: a clean pinned Python 3.12 environment, commands in the README, seeds in YAML configuration. Results computed on Linux were re-executed on Windows 11: structural outputs identical, figures pixel-identical, floats within 1e-14, raw GSOD files byte-identical to a fresh NOAA download. One command runs all suites and checks and fails on any problem. Wall-clock timings are environment-dependent.

**23. What is platform-dependent?**
Timings, PNG bytes, text line endings (and hashes of text files that depend on them), and the last binary digit of trigonometric functions for the annulus and figure-eight clouds (2.2·10⁻¹⁶).

**24. What are the biggest threats to validity?**
One lens, one cover family, two clusterer families; two-dimensional synthetic shapes; one station and six years; clusterer scales tried only at two values and chosen after the default result; no cross-implementation check; no participants (Section 10.2).

**25. What would you do next?**
A clusterer-scale dimension in the explorer; a sweep over cover and scale with surrogate nulls; a GUDHI cross-check; additional stations; and, with proper design and approval, a participant study with counterbalanced orders and a registered analysis plan.
