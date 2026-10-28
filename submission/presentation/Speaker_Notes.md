# Speaker notes — When Can You Trust a Topological Visualization?

## Slide 1 — When can you trust a topological visualization?

Good morning. This talk is about a simple question: when you look at a persistence diagram or a Mapper graph, how much should you believe it? I evaluated the Scikit-TDA tools, ripser, persim and KeplerMapper, on data whose answer I know and on one real weather record. I will show what the tools give you, where the pictures can mislead, and which controls separate the effects of parameters, clustering, sampling and temporal order.

## Slide 2 — A topological picture is not the topology

The key move is to keep four things apart. The true topology of the data. The persistent homology evidence, which is relative to a metric and a filtration. The Mapper graph, which depends on a lens, a cover, a clustering rule and its parameters. And the drawing itself. A fifth factor, how a person reads the picture, I cannot measure, because no participant study was conducted. Throughout, a dominant loop means a gap ratio of at least three, a chosen convention and not a law of topology.

## Slide 3 — What was evaluated, and how

The system is the Scikit-TDA triad. There are three core experiments: a capability audit, a Mapper parameter sensitivity grid with a no-loop control, and a structured inspection of the figures by one observer. Three extension studies add real weather data, an offline explorer, and resampling robustness. Five control experiments test specific alternative explanations. The synthetic shapes have known answers: an annulus with one loop, a figure-eight with two, and a blob with none.

## Slide 4 — E1: the ecosystem computes; you assemble the rest

Experiment one asks what the tools do for you. Computing persistent homology, drawing diagrams and computing distances are native. Generators, barcodes and the harness are custom code, about 130 counted lines. Component and cycle counts need networkx, and the lens and clustering come from scikit-learn. The stock KeplerMapper HTML export loads D3 and fonts from the internet; in a cold, offline browser it throws d3 is not defined and draws zero nodes. The native static layout can also pile disconnected components on top of each other.

## Slide 5 — E2: cover parameters change the Mapper story

Experiment two sweeps the cover. On the annulus the Mapper graph is a tree with five intervals, a connected graph with two cycles at the reference setting, and fragments at the finest setting. The figure-eight splits into two components at the reference cell. Notice that node count is exactly two times the number of intervals in all 24 cells. That is not a finding about the data. It happens because the clusterer is KMeans with two clusters in every interval. The next slide tests how much of the pattern comes from that rule.

## Slide 6 — The clustering rule and scale decide whether the cycle cue survives

This control asks whether the forced two-cluster rule drives the cycle result. With KMeans and two clusters, the annulus graph has no cycle in 13 of 30 subsamples and 20 of 30 independent redraws. With a data-adaptive single-linkage clusterer at three times the median five-nearest-neighbour distance, it has exactly one cycle in all 30 subsamples and all 30 redraws. At half that scale the graph fragments and the cycle is absent in 22 of 30. I chose these two scales after seeing the KMeans result, and I tried only two. So this is an exploratory existence demonstration that a data-adaptive clusterer can preserve the cycle cue. It is not an independent confirmation of a recommended scale. What it does show is that the cue depends on the clustering rule and its scale.

## Slide 7 — E3: what the artifacts communicate — one observer, not a study

Experiment three was designed as a classroom pilot. That study did not happen, and I do not imply otherwise. What exists is a structured inspection of thirteen figures by one invested observer, the author, who used an AI vision model as a viewing aid. Eleven properties were clearly apparent, two were ambiguous. Both ambiguities concern encodings: the diagram has no legend and the essential component point is drawn far from the diagonal, and a noise-scale Mapper cycle looks like a ring. This is evidence about the figures, not about how people read them.

## Slide 8 — Weather: a strong H1 cue in a temporal embedding

On real data, I used six years of daily observations from Central Park, with raw files verified by hash. A sliding-window embedding of the temperature series shows one dominant H1 class in all six configurations, with gap ratios between 4.75 and 7.32. But the six share one dataset and were designed around the annual period, so they show consistency, not replication. The static three-dimensional cloud with ratio 1.19 is not a null control: persistence of a point cloud ignores day order, so it cannot register recurrence by construction.

## Slide 9 — Matched null controls remove the dominant H1 cue

So I added matched null controls: same embedding, same six configurations, same ripser call. First, subtract a fitted annual cycle, two harmonics that explain 82 percent of the variance. The gap ratio falls to between 1.02 and 1.14. Second, shuffle the days: ratios between 1.01 and 1.22, none reaching the threshold of three. H1 classes are still present in these embeddings; what is absent is a dominant one under the stated criterion. So the cue depends on the annual harmonic structure and on temporal order in these tests. It does not prove the annual cycle is the only source, and it is not a climate finding.

## Slide 10 — Offline explorer: inspect parameter dependence without a server

Extension B is an offline explorer. One HTML file shows 35 saved Mapper cells with their parameters, statistics, a reference comparison, the persistence diagram and an export with provenance. It recomputes nothing; Mapper Interactive and giotto-tda recompute on the fly and are more general. I tested it in a fresh Chrome session with the network disabled, covering every cell and every export: 222 of 222 checks pass, with no external requests and no console errors, and the layout holds from phone width to a wide desktop. It is a display tool for saved results, not a new algorithm.

## Slide 11 — Persistence evidence for a loop holds in every sample — with caveats

On robustness: the constructed loops are far above the noise floor in every one of sixty subsamples, and the blob never reaches the threshold. Three caveats. Subsamples overlap the reference, so they understate variability; thirty independent redraws give a bottleneck median of 0.041 for the annulus instead of 0.029. The relative percentages mostly reflect the size of the reference features. And leave-one-year-out is weaker than its name: in 10 of 36 fold-configurations a second year contributes almost nothing, and the annual cycle makes the check hard to fail.

## Slide 12 — What to do with a topological picture

So what should a practitioner do? Ask which representation carries the claim. Treat Mapper structure as dependent on lens, cover, clusterer and scale until shown otherwise. Use a null control that shares the construction, such as surrogates, rather than a different representation. State thresholds as conventions and report distributions over resamples rather than one reference. And remember both directions: a graph cycle is not a loop in the data, and a missing cycle does not show a missing loop. I do not claim that people routinely confuse these. I claim the two kinds of evidence are not interchangeable.

## Slide 13 — Limits and non-claims

The limits are part of the result. There is no participant study. Everything uses one lens, one cover family and two clusterer families, on two-dimensional synthetic shapes and one station. I did not cross-check ripser against another implementation, and I do not rank Mapper against PCA, t-SNE or UMAP. Overlapping resamples are descriptive, there are no p-values or confidence sets, and the gap ratio and S are custom indicators. No artifact fixes the order of design and analysis, so nothing is called pre-registered: the sweep was designed knowing the annual period, the seasonality check came after, and the clusterer scales were chosen after the default result. And the weather result is not a climate claim.

## Slide 14 — Reproducible and checked from outside

To close: results were computed on Linux and independently re-executed in a clean pinned environment on Windows. Structural outputs, diagrams and counts are identical, figures are pixel identical and floats agree to ten to the minus fourteen. One command runs every test suite and verification step and fails on any problem, and an evidence verifier re-derives the numbers in the report and slides from the result files. The take-away: trust follows the construction. Know which representation you are reading, which parameters it depends on, and which null control it has to beat. Thank you.

---
Narration word count: 1324; at 130 words per minute: 10.2 minutes.
