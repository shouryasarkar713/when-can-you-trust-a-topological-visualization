# Speaker notes — When Can You Trust a Topological Visualization?

## Slide 1 — When can you trust a topological visualization?

This project evaluates how reliably a user can interpret persistence diagrams and Mapper graphs produced by the Scikit-TDA workflow. It asks whether the displayed structures reflect the data or are shaped by parameters and rendering, using synthetic shapes with known answers and one real weather record whose topology is unknown.

## Slide 2 — A topological picture is not the topology

A topological visualization is produced in stages. The data have a usually unknown structure; persistent homology gives evidence about it under a chosen metric; Mapper adds a lens, a cover and a clustering rule; and the drawing adds layout and colour. The reader's interpretation is a further stage. E3 was a single-observer inspection and does not generalise to other readers. A loop is called dominant when a gap ratio, defined shortly, reaches three, which is a convention.

## Slide 3 — Three questions, and what this project adds

The evaluation addresses three research questions. RQ1 asks which tasks the Scikit-TDA packages support natively. RQ2 asks how a Mapper graph changes with the cover and the clustering rule. RQ3 asks what the resulting figures communicate and where they become ambiguous. This is an evaluation, not a new algorithm.

## Slide 4 — Persistent homology tracks features as a distance threshold grows

Ripser computes persistent homology over increasing distance thresholds. Points closer than the threshold are connected; ripser builds this Vietoris-Rips structure from pairwise distances. As the threshold grows, components merge and loops form and later fill in. H0 tracks components, one of which never disappears, and H1 tracks loops. Each feature is plotted at the thresholds where it appears and disappears. Points far from the diagonal persist; this is evidence under one metric, not proof of shape.

## Slide 5 — Three known shapes give three different diagrams

Three synthetic clouds of 500 points have known answers: an annulus with one loop, a figure-eight with two and a Gaussian blob with none. The annulus produces one H1 point far above the diagonal, with persistence 1.496, and the figure-eight produces two, at 0.481. The blob produces only points near the diagonal, with a largest persistence of 0.140.

## Slide 6 — The gap ratio turns the diagram into a yes/no cue

The gap ratio makes this separation measurable. For an expected loop count k, the k-th largest H1 persistence is divided by the next one, so a large ratio means the expected features stand apart. It is 19.35 for the annulus, 9.75 for the figure-eight (k equal to two) and 1.45 for the blob. A feature is dominant when the ratio reaches three, an operational convention and not a theorem; for the weather data k is one.

## Slide 7 — Mapper builds a graph from a lens, a cover and a clusterer

A lens, here the first principal component, assigns a number to each point. Its range is divided into overlapping intervals, and the points in each interval are clustered. Each cluster is a node, and nodes sharing a point are connected. The default is KMeans with two clusters and ten intervals with thirty-five percent overlap. E minus V plus C counts independent graph cycles, not loops in the data.

## Slide 8 — RQ1: the triad computes; the surrounding workflow is yours

Experiment E1 audits thirteen workflow tasks. The packages natively provide persistent homology, plots, distances and static Mapper drawing; about 130 lines of custom code and scikit-learn and networkx supplied the rest. The standard HTML export needs the network and draws nothing offline.

## Slide 9 — E2, annulus: the cover decides which Mapper story you see

E2 varies the cover resolution and overlap on the annulus while the clustering procedure stays fixed. The heatmaps give components, independent cycles and membership overlap for twelve configurations. Five intervals produce a tree. The reference graph has twenty nodes, twenty-one edges and two cycles although the cloud has one loop. The node count is twice the interval count because KMeans was set to two clusters.

## Slide 10 — E2, figure-eight: the construction-consistent reading is easy to miss

The figure-eight tests whether the graph can show two expected loops, that is, one connected graph with two cycles. The reference graph has two components and one cycle. The expected structure appears only with twenty intervals and fifty percent overlap, a configuration highlighted after the full grid was measured.

## Slide 11 — E2, blob control: graph cycles appear where there is no loop

The blob has no loop and serves as a negative control. Its diagram has no dominant H1 feature, with a gap ratio of 1.45, yet the reference graph contains four independent cycles. A Mapper graph cycle therefore describes the constructed graph and is not evidence of a data loop.

## Slide 12 — Clusterer control: the clustering rule changes the cycle cue as much as the cover

The clusterer control tests whether the two-cluster KMeans rule contributes. It substitutes single-linkage clustering at two cut distances. At the larger scale the figure-eight is connected in every cell with two cycles at the reference cell; at the smaller scale all graphs fragment. Both scales were chosen after the KMeans results, so the control shows a possibility and recommends no setting.

## Slide 13 — RQ3, E3: two separate judgments of 13 figures by one observer

E3 inspected thirteen figures. No participant pilot was run; I rated each figure myself, with an AI vision model as a viewing aid. Eleven were clearly apparent and twelve matched the expected property fully. The ambiguous cases are the figure-eight diagram, because of an unlabeled colour convention and the essential H0 point, and the blob graph, because its noise cycles resemble a ring.

## Slide 14 — Weather: one station, six years, two analysis branches

The weather study applies the diagnostics to a real series with a known annual cycle: daily NOAA records for New York Central Park, 2019 to 2024, giving 2,192 days. Four days lack sea-level pressure, leaving 2,188 for the static cloud. Wind speed and station pressure were excluded, and nothing was imputed.

## Slide 15 — The static weather cloud shows no dominant loop, but its graph has many cycles

In the static cloud each day is a point of temperature, dew point and sea-level pressure; two principal components explain 97.6 percent of the variance. The diagram has no dominant H1 feature, with a gap ratio of 1.19, while the Mapper graphs have three to fourteen cycles. This is a contrast and not a null control, because it ignores temporal order.

## Slide 16 — A time-delay embedding turns one series into a point cloud

A time-delay embedding turns one series into a point cloud. With delay tau and dimension d, each point contains the temperature on one day and at later multiples of tau, for d values. With tau of sixty and d of eight, a point spans 420 days, giving 1,772 points; an annual pattern should place them near a closed curve.

## Slide 17 — All six embedding settings give a dominant H1 class

All six delay and dimension settings give a dominant H1 feature, with gap ratios from 4.75 to 7.32. They share one dataset, and five were designed around the annual period, so this is consistency and not independent replication.

## Slide 18 — Matched null controls do not reproduce a dominant H1 cue

Two null constructions test what produces the dominant feature. The anomaly series subtracts two fitted annual harmonic pairs, which explain 82.2 percent of the variance, and its gap ratio is 1.02 to 1.14 in all six settings. The shuffled series randomise the order; ten shuffles at the reference setting give 1.007 to 1.219. H1 features remain but none is dominant, so the cue is associated with annual structure and temporal order, although the shuffled null is weak.

## Slide 19 — The offline explorer makes saved Mapper parameter dependence inspectable

The offline explorer shows saved Mapper results in a single HTML file of thirty-five precomputed cells and recomputes nothing. A browser test with the network disabled passed 222 of 222 checks. It is demonstrated next.

## Slide 20 — Persistence evidence for constructed loops survived resampling

The next analyses vary the sample instead of the parameters: thirty subsamples of 400 points and thirty independent redraws per shape. The gap ratio stays between 13.2 and 25.6 for the annulus, 7.35 and 13.8 for the figure-eight, and 1.00 and 1.75 for the blob. Subsamples overlap the full dataset, so these distances are descriptive and not independent validation.

## Slide 21 — In the same samples, the Mapper cycle cue depended on the clusterer

Mapper on the same samples behaves differently. With KMeans the annulus graph has no cycle in thirteen of thirty subsamples, although the persistent-homology evidence for an H1 feature remains prominent there. Single-linkage at the larger scale gives one cycle in every subsample, but the scales were chosen post hoc.

## Slide 22 — Leave-one-year-out: no single year was necessary for the weather cue

The leave-one-year-out analysis removes each year in turn, giving thirty-six embeddings with gap ratios from 4.376 to 7.754. In ten, the window rule also removes a neighbouring year. No single year is therefore necessary under the tested settings, but no minimum data duration is established.

## Slide 23 — Answers to RQ1, RQ2 and RQ3

For RQ1, the triad natively supports the core computations, diagram plots and static Mapper drawing. For RQ2, Mapper structure depends on the cover, overlap, clusterer and its scale, whereas the persistent-homology evidence stayed prominent. For RQ3, most figures were clear; unlabeled colours, the essential point and noise-scale cycles caused ambiguity.

## Slide 24 — Three dependent variables, three sets of inputs

The outputs depend on different inputs: a diagram feature on the point cloud, metric and filtration; a Mapper feature also on the lens, cover and clusterer; the drawing on layout and colour. Graph cycles and H1 features are therefore not interchangeable evidence, although readers were not tested.

## Slide 25 — Limitations, threats to validity and non-claims

Several limitations affect interpretation. The shapes are two-dimensional with one seed each, only one lens and cover family were used, and the weather data come from one station with limited nulls. ripser was not compared with another implementation, and no participants were studied. The gap ratio and cyclomatic number are indicators, not measurements of loop counts, and some choices followed earlier results; without version control their order cannot be verified.

## Slide 26 — Reproducibility checks

Results computed on Linux were independently re-executed on Windows 11 with matching diagrams, graphs and counts. The documented run of 19 November passed 203 tests and 38 environment checks, with a separate browser test. The evidence verifier (126 registered facts) has been rerun since; the full suite has not.

## Slide 27 — Takeaway: trust follows the construction

Trust in a topological visualization depends on its construction: which representation carries the claim, which parameters it depends on, and which null control it withstands. Persistent-homology evidence was stable in the tested samples, the weather cue depended on annual structure and temporal order, and Mapper cycles varied with the clusterer. Future work includes a clusterer-scale explorer dimension, a ripser-GUDHI comparison, a second station and a participant study.

## Slide 28 — Supplementary Evidence and Additional Results

The main presentation ends here. The following slides contain supporting evidence: the full workflow audit, additional stimuli, details of the weather data, the remaining explorer views, resampling diagnostics, the chronology of design decisions and the configurations used. They are used to answer specific questions and are not part of the timed talk.

## Slide 29 — Positioning: what already exists and what this project adds

The project builds on established work in four areas. Persistent homology has a well-developed theory, including the stability theorem that makes distances between diagrams meaningful, and ripser implements it efficiently. Mapper has its own literature on how the cover and lens affect the graph, and tools such as Mapper Interactive, giotto-tda and tda-mapper allow its parameters to be explored by recomputation. Sliding-window embeddings of periodic signals provide the basis for the weather analysis. The contribution of this project is a known-answer evaluation of the Scikit-TDA workflow as distributed, with controls for clustering and sampling, together with a viewer for saved results; no new algorithm is claimed.

## Slide 30 — References (1 of 2): persistent homology, Mapper and tools

The references on persistent homology, Mapper and associated tools fall into three groups. The first contains the foundational papers on persistence, the stability theorem and the paper describing Ripser. The second contains the original Mapper paper and later analyses of its stability and parameter selection. The third lists interactive tools. Two recent items, an evaluation framework and LoCoMapper, were consulted only at abstract or program-page level, so general Mapper evaluation is treated as established work without further claims about them.

## Slide 31 — References (2 of 2): software, evaluation, weather and data

The second reference slide covers software, evaluation, weather and data sources. The package references are those requested by the Scikit-TDA, ripser and KeplerMapper documentation. The periodicity papers justify the sliding-window embedding applied to the temperature record, and the weather papers show that topological methods have been applied to climate data, mostly at reanalysis scale. The visualization papers support the separation of data, computation, drawing and reader used throughout the evaluation. The weather data originate from NOAA's National Centers for Environmental Information, and GUDHI appears only as the comparison reserved for future work.

## Slide 32 — Diagram distances and the overlap indicator S

Two measures require further explanation. The membership-overlap indicator S compares which points the nodes of two Mapper graphs contain. Each node of one graph is matched to the node of the other graph with the highest Jaccard overlap, meaning shared points divided by combined points; the same is done in the opposite direction, and the two averages are combined. S ignores edges and components and is not a metric, since one minus S violates the triangle inequality, and a value of one does not imply identical graphs. For four hundred points compared with the five hundred point reference, its maximum is about 0.80.

For persistence diagrams, the bottleneck distance is the largest matched distance and the Wasserstein distance is the sum of the matching costs, with points allowed to match the diagonal and the essential H0 class excluded. H0 and H1 are reported separately. A four hundred point subsample has 399 finite H0 classes against 499 for the reference, and the unmatched short classes inflate the H0 Wasserstein value.

## Slide 33 — E1: the full 13-task workflow audit

The complete audit lists the thirteen workflow tasks and the source of each capability. Six tasks are supported natively, three required custom code, one combines kmapper with scikit-learn, two depend on external packages, and the interactive HTML export is native but does not work offline. The custom glue code totals 130 non-blank, non-comment lines. Two details are relevant for users: neither ripser nor persim provides a barcode plot, and networkx, which is needed for component counts, is not a declared kmapper dependency.

## Slide 34 — E1: the native Mapper layout can overlap disconnected components

This E1 comparison shows the native Mapper drawing and a component-separated drawing of the three-blob graph. In the native layout the bounding boxes of the components overlap, with an overlap measure of 0.23 for the three-blob control and 0.036 for the figure-eight. The component-separated drawing in this figure moves the components apart but does not account for node sizes. The explorer uses a different component-separated layout that is based on the rendered node radii; in the saved cells it keeps circles from overlapping, at the cost of a taller drawing area when many large nodes require space. Both layouts change coordinates only and leave the graph unchanged.

## Slide 35 — E3: additional stimuli with the property I expected

Three additional stimuli from the E3 inspection illustrate the range of judgements. The annulus Mapper graph was expected to appear as a large ring-like cycle, with the qualification from E2 that this depends on the parameters. The blob scatter plot was expected to show no prominent loop, and the annulus scatter plot was expected to show a loop. Both scatter plots were clear, as were all scatter views, which is consistent with their showing the data directly. The expected properties were fixed from the data construction before the records were written, but the inspection remains a single-observer assessment with an AI viewing aid and no participant data.

## Slide 36 — Weather variables and missing values

The table summarises how each weather variable was used. Temperature and dew point are complete, whereas sea-level pressure is missing on four days, wind speed on 125, gusts on 911 and snow depth on 2,119; station pressure uses a missing-value code in six rows. Temperature, dew point and sea-level pressure form the static cloud. Including wind speed would have removed 129 days, mostly in early 2019 and 2020, and station pressure was excluded because a leading digit is missing in about 95 percent of its values. No values were imputed. The plotted series is shown in degrees Celsius, whereas the series used in the embedding is standardized, and the red lines mark the four dropped days.

## Slide 37 — Static weather cloud: the eight Mapper cells and the persistence diagram

The table reports all eight Mapper graphs of the static weather cloud. The graph is connected for up to fifteen intervals and has two components at twenty; the cyclomatic number ranges from three to fourteen, and the overlap indicator S from 0.445 to 1.000. The persistence diagram on the right contains 1,049 H1 classes, but the dominant class has a persistence of only 0.210, giving a gap ratio of 1.19. A day-of-year lens variant, which encodes the calendar directly, is included only as a labelled comparison. The static cloud differs from the embedding in dimension, variables and density, and permuting the days leaves it unchanged, so it cannot serve as a null control.

## Slide 38 — Seasonality check: a descriptive periodogram and autocorrelation

A periodogram and an autocorrelation provide a descriptive check on the periodicity of the temperature series. The strongest frequency corresponds to a period of 365.3 days and contains 82.1 percent of the power outside the mean; neighbouring frequencies correspond to periods of 313 and 438 days, so the resolution is limited to tens of days. The autocorrelation peaks at a lag of 360 days with a value of 0.676. These analyses were carried out after the embedding sweep, so they are post hoc, and they were not used to select any embedding parameter.

## Slide 39 — Weather nulls in detail: temperature vs anomaly series

The table compares the original and anomaly series in each of the six embedding configurations. The original series has gap ratios between about 4.7 and 7.3, whereas the anomaly series remains between 1.02 and 1.14. The ten shuffled series, evaluated at the reference configuration, give 1.007 to 1.219. The anomaly series still contains thousands of H1 classes, and its dominant persistence of 0.5 to 0.8 is not small; it is the ratio between the leading persistences, and not the absolute magnitude, that distinguishes the original series. Processing the unmodified series with the same code reproduces the saved sweep exactly.

## Slide 40 — Explorer: the weather and no-loop blob views

Two further saved cells are shown in the explorer. The weather cell with twenty intervals and thirty-five percent overlap has forty nodes, forty-nine edges, two components and eleven independent cycles, with a membership overlap of 0.506 relative to the reference cell. In the component-separated panel, the large component and the isolated node are drawn apart and the circles do not overlap, whereas the native layout on the left still contains overlapping nodes. The blob cell with twenty intervals and twenty percent overlap has six components and five cycles, although its persistence diagram contains no dominant H1 feature. The explorer displays the interpretive caveats beside the statistics, so that a screenshot retains them.

## Slide 41 — Diagram distances under resampling, and independent redraws

The figures summarise the distances between the persistence diagrams of the subsamples and the full-data diagram, reported separately for H0 and H1. The H0 Wasserstein distance requires a qualification: every subsample has 399 finite H0 classes against 499 for the reference, and the unmatched short classes inflate the distance, from 0.67 against another subsample to 3.68 against the reference in the first replicate. The median H1 bottleneck distances correspond to 1.9, 4.0 and 34 percent of the dominant persistence, but this mainly reflects the different sizes of the reference features. Independent redraws give larger medians than the overlapping subsamples, by about 1.4 times for the annulus and 1.8 times for the figure-eight.

## Slide 42 — Annulus Mapper graphs under resampling, and the ceiling of S

The annulus Mapper graphs of the first six subsamples are shown beside the full-data graph. The persistence diagrams of these samples all contain a prominent H1 feature, yet the Mapper graphs differ in their cycles, with some having none, some one and some two. The overlap indicator S has a sampling ceiling: restricting the reference nodes to the sampled points already gives 0.800, so the median of 0.585 is about three quarters of the attainable value. The number of subsamples without a cycle also depends on the seed set; fresh subsamples gave 18, 8 and 4 for zero, one and two cycles, and counts over thirty subsamples have a standard error of about 0.09.

## Slide 43 — Mapper graph statistics over all 30 subsamples (full figure)

The complete figure reports, for each shape and each of the thirty subsamples, the number of nodes, edges and components and the cyclomatic number, with the dashed line marking the full-data graph. The node count is constant at twenty by construction. The other statistics vary: the annulus cycle count fluctuates, the figure-eight sometimes loses a cycle, and the blob graph shows variable noise-scale structure. The cover parameters are fixed at the reference configuration, and the lens is recomputed for each subsample.

## Slide 44 — Cyclomatic number of the resampled graphs under three clustering rules

The histogram shows the distribution of the cyclomatic number over the thirty subsamples for each shape under three clustering rules: forced two-cluster KMeans, and single-linkage at three and at one and a half times the median neighbour distance. For the annulus, KMeans spreads over zero, one and two cycles, whereas single-linkage at the larger scale gives exactly one every time and the smaller scale mostly gives none. For the blob, KMeans produces noise-scale cycles and single-linkage produces almost none. Both single-linkage scales were chosen after the KMeans result was known and no others were tried, so the comparison demonstrates a possibility and not a recommended setting.

## Slide 45 — Clusterer effect on the other shapes, and independent redraws

The remaining numbers refine this comparison. For the annulus under KMeans, thirteen of thirty subsamples and twenty of thirty independent redraws have no cycle, whereas single-linkage at the larger scale gives one cycle in every sample. At that scale the figure-eight retains two cycles in one component in all thirty subsamples and in twenty-eight redraws, and the blob has almost no cycles but fragments into many components. At the smaller scale the graphs fragment, and forced KMeans produces noise-scale cycles in all thirty blob redraws. The scales were chosen post hoc.

## Slide 46 — Order of design and analysis: what can and cannot be verified

The table distinguishes decisions by what can be established about their timing. According to the project records, the expected loop counts, the gap-ratio convention, the resampling design, the E2 grid and the reference weather configuration were specified before the corresponding runs, although these records are not independently time-stamped. The other five embedding configurations were designed with knowledge of the annual period. The seasonality check was written after the embedding sweep, the figure-eight contrast cell was selected after the full grid had been measured, and the two single-linkage scales were chosen after the KMeans results were known. Version control was not maintained during the project, so the repository history is retrospective and does not document the original chronology.

## Slide 47 — Configurations and software environment

The table condenses the main configurations from the report appendix, together with the pinned software versions. All parameters and seeds are stored in configuration files, and every figure is rendered from saved results. The experiments were computed on Linux and re-executed on Windows 11. The differences between the platforms consist of floating-point round-off, many orders of magnitude below any reported quantity, together with wall-clock times and file metadata. All persistence diagrams, graphs and counts agreed.

## Slide 48 — Runtime and determinism

The runtime measurements describe the specific workloads reported in the study. In the persistence resampling, the H0 bottleneck distance accounts for 826 of the 833 seconds of recorded distance-computation time. Individual H0 bottleneck calls took between 0.2 and 75 seconds across the ninety resamples, and between 0.6 and 75 seconds for the blob alone; matching time in persim is strongly instance-dependent. The leave-one-year-out analysis, with thirty-six embeddings, accumulated about 250 seconds of ripser time, or roughly four minutes. Subsample indices, diagrams and Mapper graphs are deterministic for fixed seeds and configurations. These are observed runtimes and not a controlled performance benchmark.

---
Narration word count: 1540 (main talk, slides 1-27); at 130 words per minute: 11.8 minutes. Supplementary notes: 2125 words (slides 28-48), not part of the timed talk.
