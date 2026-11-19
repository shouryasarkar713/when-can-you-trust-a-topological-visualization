<!-- titlepage
title: Q&A Preparation
subtitle: When Can You Trust a Topological Visualization? — anticipated questions and defensible answers
short: Q&A preparation — When Can You Trust a Topological Visualization?
field: Companion to | Final report and presentation (27 main slides, supplementary slides 29–48)
field: Author | Shourya Sarkar
field: Date | 28 October 2026
status: Each answer states what the experiments establish, where the evidence is, and what is not claimed. Section numbers refer to the final report.
-->

# Q&A Preparation

## A. Concepts

**1. What does ripser actually compute?**
It builds a Vietoris–Rips filtration from pairwise distances. Starting from the points and a distance threshold, two points are joined when their distance is at most the threshold, and a triangle or higher simplex is filled in when all its vertices are pairwise within the threshold. Raising the threshold gives a growing sequence of complexes, and ripser records the threshold at which each connected component (H0) and each loop (H1) is born and dies; the experiments use `maxdim = 1`. The growing-ball picture is only an intuition: a ball radius corresponds to half the distance threshold, and the two constructions are not identical (Section 5.1).

**2. How does Mapper build its graph?**
A lens assigns each point a number (here the first principal component, PC1). The lens range is cut into overlapping intervals (the cover, `CubicalCover`). The points in each interval are clustered (default: KMeans with k = 2), each cluster becomes a node, and two nodes are joined when their clusters share a data point (Section 5.2).

**3. Why is a Mapper graph cycle not a loop in the data?**
A cycle is a property of the constructed graph, which depends on the lens, cover, clusterer and its scale. The no-loop blob produced graph cycles under the default KMeans rule (all 30 independent draws, cyclomatic number 2–8), while single-linkage at 3 × the median fifth-nearest-neighbour distance gave no cycle in 29/30 of those draws. Conversely, the annulus has a loop but the KMeans graph had no cycle in 13/30 subsamples (Sections 6.2, 9.3).

**4. Why are H0 and H1 kept separate?**
They measure different things (clusters and loops), have different scales and different cardinalities, so I never pool them, and their distances are not comparable in magnitude. H0 Wasserstein distances are additionally inflated when diagrams have different numbers of classes: 399 finite H0 classes in a 400-point subsample against 499 in the reference (Section 9.2).

**5. What does "dominant H1" mean, and why a threshold of 3?**
For H1 persistences sorted in descending order, r_k = p_k / p_{k+1}, where k is the expected number of loops: 1 for the annulus, 2 for the figure-eight, and 1 for real data as a diagnostic convention. "Dominant" means r_k ≥ 3. The threshold is an operational convention, not a theorem, and carries no uncertainty statement. I did not run a threshold-sensitivity experiment, so I do not claim the conclusions are insensitive to it. The observed gaps are far from the threshold in the constructed shapes (annulus r₁ ≥ 13.2 in the subsamples), but that is an observation, not a sensitivity analysis (Section 5.3).

**6. Why is the node count always 2 × n_cubes?**
I configured KMeans with k = 2, which asks for two clusters in each cover interval, and in every tested interval it did produce two non-empty clusters. The node count of 2 × n_cubes is therefore a mechanical consequence of the configured clusterer. It is not evidence about topology, and it is the reason a data-adaptive clusterer was tested; with single-linkage the node count no longer equals 2 × n_cubes in any cell (Section 6.3).

**7. Is S a valid graph distance?**
No. S is a similarity indicator, and it is not called a distance. It compares membership sets greedily, ignores edges and components, is not normalized for node count, and S = 1 does not imply identical graphs. The derived dissimilarity 1 − S violates the triangle inequality, so it is not a metric either. For a 400-point subsample against the 500-point reference its attainable maximum is about 0.80 (median 0.800, range 0.786–0.822), and I use it only as an exploratory indicator (Section 5.3).

**8. Why bottleneck and Wasserstein distances?**
The bottleneck distance is a maximum over matched pairs (L∞) and is stable under small data changes; the Wasserstein distance used here is an order-1 sum with Euclidean ground metric. They answer different questions, so their magnitudes are not interchangeable (Section 5.3).

## B. Contribution and design choices

**9. What does this project contribute beyond running three packages?**
An evaluation, not an algorithm: a 13-task capability audit; a Mapper sensitivity grid with a known-answer design and a no-loop control; a structured inspection of what the figures communicate; a weather case study with matched null controls; resampling analyses; an offline explorer for saved results; and control experiments that separate the effects of cover, clusterer, sampling and temporal order. The packages already provide the persistent-homology computation and the Mapper construction. The gap ratio r_k and the membership-overlap indicator S are custom indicators with stated limits and are explicitly not canonical (Section 2.3).

**10. Isn't it already known that Mapper depends on its parameters?**
Yes (Carrière and Oudot, 2018; Carrière, Michel and Oudot, 2018; Belchí et al., 2020; Sen, Singh and Tiwari, 2026 evaluate Mapper more generally). The project does not claim otherwise. What it adds is a reproducible known-answer demonstration for the Scikit-TDA workflow as shipped, including the effect of the clustering rule and of input sampling (Section 3.6).

**11. Why Scikit-TDA and not GUDHI or giotto-tda?**
The assignment evaluates a visualization system, and Scikit-TDA is a compact, pip-installable triad with citable software papers and a first-party Mapper visualization. A comparison of ripser with GUDHI was left out of scope, so ripser's correctness is supported only by the known-answer signatures of the synthetic data, determinism and the upstream literature, not by agreement with a second implementation (Section 2.4).

**12. What is the single most important finding?**
The reliability of a Mapper cycle cue depends on the clustering rule and its scale, while the persistence evidence for the constructed loops was present in every tested subsample and independent redraw. On the annulus: no cycle in 13/30 subsamples with KMeans (k = 2), exactly one cycle in 30/30 with single-linkage at 3 × the median fifth-nearest-neighbour distance, and absent in 22/30 at half that scale (Section 9.3). The practical message: ask which representation carries the claim and check what it depends on.

**13. How were the Mapper parameters and the clusterer scales chosen?**
The cover grid, reference cell, PC1 lens and ground-truth ranks were fixed in the design before the runs; the figure-eight contrast cell (20, 0.50) was chosen after the full grid was measured. The two single-linkage scales (1.5 and 3.0 × the median fifth-nearest-neighbour distance) were written into the configuration before the control ran but after the default-rule results were known, and only these two were tried, so they are an exploratory choice and the result at 3.0 is an existence demonstration, not a recommended setting. No order of design and analysis can be proven from time stamps (Section 11.3).

## C. Experiments and controls

**14. The blob has graph cycles but no dominant H1 class. Does that make Mapper cycles meaningless?**
No. It shows that graph cycles do not certify loops. Under forced two-cluster KMeans the blob had cycles in all 30 independent draws (cyclomatic 2–8); under single-linkage at 3 × the median fifth-nearest-neighbour distance it had none in 29/30 but 3–10 components. Equally, the absence of a cycle does not prove the absence of a loop (Section 9.3).

**15. What do the two E3 counts mean?**
They are two separate judgments recorded for each of the 13 figures. Visual clarity: 11 figures were judged clearly apparent and 2 ambiguous. Match with the property expected from the data construction: 12 matched fully and 1 partially. They are not one measurement and should not be added or merged. The two ambiguous figures show different problems: the figure-eight diagram has unlabeled H0/H1 colours and an essential H0 point that is drawn on a dashed line far from the diagonal, and the no-loop blob's Mapper graph shows noise-scale cycles that read as a ring (Section 6.4).

**16. Did you run a user study?**
No. The planned classroom pilot was not conducted; no participants, recruitment, consent, blinding or response data exist. E3 is a structured inspection of 13 artifacts by the author, an invested observer who designed the data and had seen the E1 and E2 results, with an AI vision model as a viewing aid. It supports statements about what the artifacts communicate and nothing about human accuracy or readability (Section 6.4).

**17. Why is the static three-dimensional cloud not a null control?**
Its persistence depends only on the set of days, so permuting the day order cannot change it, and it differs from the temporal embedding in dimension (three against eight), variables and density. Its r₁ = 1.19 is an illustration of what a cloud without temporal information shows. The matched controls are the anomaly and shuffled series (Section 7.3).

**18. What do the harmonic-removal and shuffle controls show, and not show?**
For the temperature series, r₁ = 4.75–7.32 over six (τ, d) settings. The anomaly series, after subtracting two fitted annual harmonic pairs (82.2 % of the variance), was run at all six settings and gave r₁ = 1.02–1.14. The ten shuffled series were run at the reference setting only, because of cost, and gave r₁ = 1.007–1.219 (median 1.06). H1 classes remain in the null embeddings; what is absent is a dominant one under r₁ ≥ 3. The tests show dependence on the annual harmonic structure and on temporal order in this series. They do not show that the annual cycle is the only source, or that no loop exists in the anomaly series. Shuffling destroys all autocorrelation, so it is a weak null, and phase-randomised or autoregressive surrogates were not tested (Section 7.4).

**19. Is the weather result a climate finding?**
No. It shows that the method recovers a dominant H1 cue from a series with a strong annual component, a known feature of temperature data. Nothing is claimed about other stations, trends, ENSO or physical mechanisms (Section 7.4).

**20. Were the embedding configurations and the seasonality window specified in advance?**
The reference (τ = 60, d = 8) came from the study plan; the other five were designed around the annual period knowing it; the seasonality check and its search window were written after the sweep. No artifact time-stamps the order, so nothing is called pre-registered. The six configurations share one dataset, so their agreement is consistency, not independent replication (Sections 7.3, 11.3).

**21. What does leave-one-year-out show?**
Only that no single year is needed for the cue (r₁ = 4.376–7.754 over 36 fold-configurations), with limited power. In 10 of the 36 fold-configurations a retained single-year block contributes at most 6 windows (none at all in 5), so a neighbouring year is effectively also omitted. An annual harmonic explains about 82 % of the variance of the full series, but the analysis does not establish a minimum data duration or test every multi-year block; it shows only that no single year is necessary under the configurations tested. It is a sensitivity analysis, not a test or an interval (Section 9.4).

**22. Resampling uses overlapping subsamples against the full data. Isn't that circular?**
It is descriptive, which is why independent redraws were added: the H1 bottleneck median is 0.041 for the annulus against 0.029 for the overlapping subsamples, so overlap makes the distances look smaller. The relative 1.9 % / 4.0 % / 34 % contrast is descriptive and mainly reflects the different sizes of the reference features (Section 9.2).

**23. Why is the annulus reference graph described as one realisation?**
The seed-42 reference has cyclomatic number 2, while independent redraws at the same cell give 0 in 20 of 30, 1 in 7 and 2 in 3 under KMeans. A single reference is not truth, and the subsample counts carry a binomial standard error of about 0.09 in the proportion (Section 9.3).

## D. Data and the explorer

**24. How was the weather data handled?**
The Global Summary of the Day (GSOD) of the National Oceanic and Atmospheric Administration (NOAA), station 72505394728, 2019–2024: 2192 rows, a complete calendar, raw files verified by SHA-256 and by a fresh download. The primary cloud uses temperature, dew point and sea-level pressure (2188 days after dropping 4 days with missing sea-level pressure); adding wind speed would drop 129 days in seasonal clusters, and station pressure is excluded because 94.8 % of its values are below 900 hPa (a lost leading digit). No value was imputed (Section 7.1).

**25. How do you know the explorer is genuinely offline?**
A Playwright script drives Chrome 156 in a fresh context with the network disabled and every non-file request aborted and logged. It found no request besides the document, no external tags and no console errors, and 222 of 222 checks passed across all 35 cells; the stock KeplerMapper export in the same session draws 0 nodes (Section 8.2).

**26. Is the explorer novel?**
Only in a narrow combination: saved results first, a single file, no server or content-delivery network, per-cell provenance, embedded safeguards. Mapper Interactive and giotto-tda recompute on the fly and are more general; LoCoMapper quantifies local uncertainty under cover perturbation. The explorer cannot show cells that were not precomputed and shows one clusterer per dataset (Section 8.3).

## E. Reproducibility and limits

**27. Can someone else reproduce this?**
Yes: a clean pinned Python 3.12 environment, commands in the README, seeds in YAML configuration. Results computed on Linux were re-executed on Windows 11 with identical structural outputs and diagrams, pixel-identical figures and floating-point round-off of at most 8.9·10⁻¹⁵. The automated tests (203 passed, 0 failed, 0 skipped), the 38-assertion environment check and the saved-result and numerical-claim checks run from one command; the offline explorer validation is a separate browser test (Section 12).

**28. What is platform-dependent?**
Timings, PNG bytes, text line endings (and hashes of text files that depend on them), and the last binary digit of trigonometric functions for the annulus and figure-eight clouds (2.2·10⁻¹⁶).

**29. What are the biggest threats to validity?**
One lens, one cover family, two clusterer families; two-dimensional synthetic shapes; one station and six years; clusterer scales tried only at two values and chosen after the default result; no cross-check of ripser; a single AI-assisted observer; an operational threshold of r_k ≥ 3; and a chronology that cannot be verified (Section 11).

**30. What would you do next?**
A clusterer-scale dimension in the explorer; a sweep over cover and scale with surrogate nulls; a GUDHI cross-check; additional stations; and, with proper design and approval, a participant study with counterbalanced orders (Section 13).
