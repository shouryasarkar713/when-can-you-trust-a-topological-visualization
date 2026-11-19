"""Main-talk slides (text and speaker notes). Every number is derived from a result file;
see technical/verification/claims_register.json."""

from slides_common import BX, C, CB, CG, CO, CP, F, GREYC, I, T, TB  # noqa: F401

SLIDES_MAIN = [
    # 1
    {"kind": "title",
     "title": "When can you trust a topological visualization?",
     "subtitle": "A task-based evaluation of the Scikit-TDA ecosystem (ripser, persim) and KeplerMapper",
     "footer": "Shourya Sarkar · Scientific Visualization — Evaluation of Visualization Systems · 28 October 2026",
     "notes": """This project evaluates how reliably a user can interpret persistence diagrams and Mapper graphs produced by the Scikit-TDA workflow. It asks whether the displayed structures reflect the data or are shaped by parameters and rendering, using synthetic shapes with known answers and one real weather record whose topology is unknown."""},

    # 2
    {"title": "A topological picture is not the topology",
     "layout": "boxes",
     "boxes": [("The data's true shape", "What the shape really is. Usually unknown; known here only because the data are synthetic.", CB),
               ("Persistent homology", "Evidence that ripser finds under one distance measure. A loop counts as dominant when the gap ratio r_k = p_k / p_{k+1} is at least 3, a convention and not a theorem.", CG),
               ("Mapper graph", "Depends on the lens, the cover, the clusterer and its scale. A cycle in the graph is not automatically a loop in the data.", CO),
               ("The drawing", "Layout and colours can hide components or suggest structure without changing the graph.", CP)],
     "body": ["A fifth factor is how a person reads the picture. This study has no participant study.",
              "In r_k, the p values are the H1 persistences in descending order and k is the expected number of loops: 1 for the annulus, 2 for the figure-eight, and 1 as a diagnostic convention for real data."],
     "size": 14,
     "notes": """A topological visualization is produced in stages. The data have a usually unknown structure; persistent homology gives evidence about it under a chosen metric; Mapper adds a lens, a cover and a clustering rule; and the drawing adds layout and colour. The reader's interpretation is a further stage. E3 was a single-observer inspection and does not generalise to other readers. A loop is called dominant when a gap ratio, defined shortly, reaches three, which is a convention."""},

    # 3
    F("Three questions, and what this project adds",
      [BX(0.6, 1.5, 7.3, 1.45, "RQ1 · Workflow (E1)", ["Which tasks does the triad do natively, which need other packages, and which need custom code?"], CG, 15),
       BX(0.6, 3.05, 7.3, 1.45, "RQ2 · Sensitivity (E2, controls, explorer)", ["How much do cover resolution, overlap and clustering rule change a Mapper graph's structural reading?"], CO, 15),
       BX(0.6, 4.6, 7.3, 1.45, "RQ3 · Communication (E3)", ["What do persistence diagrams and Mapper graphs make visible, and which ambiguities arise?"], CB, 15),
       T(8.2, 1.45, 4.6, 0.5, ["**What the project adds**"], 19),
       T(8.2, 1.95, 4.6, 3.3, ["A task-based evaluation of the Scikit-TDA workflow",
                              "Known-answer synthetic experiments",
                              "Custom indicators with stated limits",
                              "Controls for cover, clusterer, sample and temporal order",
                              "An offline viewer for saved Mapper results"], 17, bullet=True),
       T(0.6, 6.2, 12.2, 0.75, ["Persistent homology, Mapper and Mapper explorers already have established literature and tools. No new algorithm is claimed, and this is not the first Mapper explorer (references in the supplementary section)."], 14, color=GREYC)],
      """The evaluation addresses three research questions. RQ1 asks which tasks the Scikit-TDA packages support natively. RQ2 asks how a Mapper graph changes with the cover and the clustering rule. RQ3 asks what the resulting figures communicate and where they become ambiguous. This is an evaluation, not a new algorithm."""),

    # 4
    F("Persistent homology tracks features as a distance threshold grows",
      [I("method_ph.png", 0.6, 1.4, 12.1, 3.0),
       C(0.6, 4.4, 12.1, "Schematic illustration on 36 synthetic points; not an experimental result. Ripser uses pairwise distances (Vietoris–Rips); growing balls are only an intuition.", 11, 0.4),
       T(0.7, 4.85, 5.9, 2.1, ["**H0** = connected components; one class never dies (the essential class)", "**H1** = loops", "**Persistence** = death − birth; experiments use maxdim = 1"], 18, bullet=True),
       T(6.9, 4.85, 5.9, 2.1, ["Points near the diagonal are short-lived, usually noise", "A long bar is evidence under the chosen metric and filtration, not proof of the true topology"], 18, bullet=True)],
      """Ripser computes persistent homology over increasing distance thresholds. Points closer than the threshold are connected; ripser builds this Vietoris-Rips structure from pairwise distances. As the threshold grows, components merge and loops form and later fill in. H0 tracks components, one of which never disappears, and H1 tracks loops. Each feature is plotted at the thresholds where it appears and disappears. Points far from the diagonal persist; this is evidence under one metric, not proof of shape."""),

    # 5
    F("Three known shapes give three different diagrams",
      [I("shapes_clouds_diagrams.png", 0.5, 1.4, 8.6, 5.5),
       T(9.3, 1.5, 3.6, 5.3, ["**Annulus:** one loop; 500 points, noise 0.05", "**Figure-eight:** two loops; 500 points", "**Blob:** no loop; 500 Gaussian points, σ = 0.45", "Dominant H1 persistence: **1.496**, **0.481**, **0.140**", "Seed 42, ripser maxdim = 1"], 17, bullet=True)],
      """Three synthetic clouds of 500 points have known answers: an annulus with one loop, a figure-eight with two and a Gaussian blob with none. The annulus produces one H1 point far above the diagonal, with persistence 1.496, and the figure-eight produces two, at 0.481. The blob produces only points near the diagonal, with a largest persistence of 0.140."""),

    # 6
    F("The gap ratio turns the diagram into a yes/no cue",
      [T(0.7, 1.4, 12.1, 0.6, ["**r_k = p_k / p_{k+1}**, with the H1 persistences sorted from largest to smallest and k the known loop count"], 20),
       I("gap_ratio_shapes.png", 0.5, 2.05, 12.3, 3.9),
       T(0.7, 6.0, 12.1, 1.0, ["k = 1 for the annulus, 2 for the figure-eight, and 1 as a diagnostic convention for real data. **r_k ≥ 3 is an operational convention**, not a theorem or a confidence statement. The blob's top two persistences are similar, so no loop dominates."], 15)],
      """The gap ratio makes this separation measurable. For an expected loop count k, the k-th largest H1 persistence is divided by the next one, so a large ratio means the expected features stand apart. It is 19.35 for the annulus, 9.75 for the figure-eight (k equal to two) and 1.45 for the blob. A feature is dominant when the ratio reaches three, an operational convention and not a theorem; for the weather data k is one."""),

    # 7
    F("Mapper builds a graph from a lens, a cover and a clusterer",
      [I("method_mapper.png", 0.6, 1.35, 12.1, 3.15),
       C(0.6, 4.5, 12.1, "Schematic illustration on 36 synthetic points, not an experimental result. The panels use an illustrative x-coordinate lens and single-linkage clustering; the E2 default is below.", 11, 0.4),
       T(0.7, 4.95, 6.2, 2.0, ["**Default (E2):** PC1 lens, CubicalCover, KMeans k = 2", "**Reference cell:** 10 cover intervals, overlap 0.35", "**Cyclomatic number** E − V + C counts independent graph cycles"], 17, bullet=True),
       T(7.1, 4.95, 5.7, 2.0, ["Nodes = clusters; edges = shared points", "A graph cycle is a statement about the graph, **not automatically about a loop in the data**", "Cells are written (n_cubes, overlap)"], 17, bullet=True)],
      """A lens, here the first principal component, assigns a number to each point. Its range is divided into overlapping intervals, and the points in each interval are clustered. Each cluster is a node, and nodes sharing a point are connected. The default is KMeans with two clusters and ten intervals with thirty-five percent overlap. E minus V plus C counts independent graph cycles, not loops in the data."""),

    # 8
    F("RQ1: the triad computes; the surrounding workflow is yours",
      [BX(0.6, 1.4, 4.0, 1.25, "ripser 0.6.15", ["Vietoris–Rips persistent homology"], CG, 14, hsize=15),
       BX(4.7, 1.4, 4.0, 1.25, "persim 0.4.1", ["Diagram distances and plots"], CB, 14, hsize=15),
       BX(8.8, 1.4, 4.0, 1.25, "kmapper 2.1.0", ["Mapper construction, HTML export"], CO, 14, hsize=15),
       TB(0.6, 2.95, 12.2, [["Support level (13 tasks)", "Tasks"],
                           ["Native", "install · persistent homology · diagram plot · diagram distances · matching plot · static Mapper drawing"],
                           ["Custom code", "data generators · H1 barcode · reproduction harness (130 counted lines of glue)"],
                           ["Other packages", "scikit-learn: PCA lens, KMeans · networkx: node, edge, component counts"],
                           ["Native, not offline", "HTML export loads D3, FileSaver and a web font from the network: 0 nodes, 0 edges drawn offline"]],
          [2.2, 8.4], size=15, row_h=0.62),
       T(0.7, 6.15, 12.1, 0.8, ["External to the triad: scikit-learn, networkx, NumPy, SciPy, Matplotlib. Native static layout can overlap components (bounding-box overlap 0.23 on three blobs, 0.036 on the figure-eight)."], 14, color=GREYC)],
      """Experiment E1 audits thirteen workflow tasks. The packages natively provide persistent homology, plots, distances and static Mapper drawing; about 130 lines of custom code and scikit-learn and networkx supplied the rest. The standard HTML export needs the network and draws nothing offline."""),

    # 9
    F("E2, annulus: the cover decides which Mapper story you see",
      [T(0.7, 1.4, 12.1, 0.8, ["**Design:** annulus and figure-eight, 12 cells each (n_cubes 5, 10, 15, 20 × overlap 0.20, 0.35, 0.50), 500 points, noise 0.05, seed 42; PC1 lens, CubicalCover, KMeans k = 2"], 15),
       I("e2_annulus_heatmaps_slide.png", 0.5, 2.15, 12.3, 3.55),
       T(0.7, 5.8, 12.1, 1.2, ["Five intervals: a tree, no cycle · reference cell: **20 nodes, 21 edges, 1 component, cyclomatic number 2** · (20, 0.20): **2 components** · overlap indicator S: 0.449–1.000"], 16)],
      """E2 varies the cover resolution and overlap on the annulus while the clustering procedure stays fixed. The heatmaps give components, independent cycles and membership overlap for twelve configurations. Five intervals produce a tree. The reference graph has twenty nodes, twenty-one edges and two cycles although the cloud has one loop. The node count is twice the interval count because KMeans was set to two clusters."""),

    # 10
    F("E2, figure-eight: the construction-consistent reading is easy to miss",
      [I("e2_figure_eight_heatmaps_slide.png", 0.5, 1.4, 12.3, 3.9),
       T(0.7, 5.4, 12.1, 1.6, ["Reference cell: **20 nodes, 19 edges, 2 components, cyclomatic number 1** (fragmented)", "(5, 0.35) and (5, 0.50): no cycle · (20, 0.20): **4 components** · S: 0.457–1.000", "The connected two-cycle reading appears at **(20, 0.50)**, a cell I highlighted after seeing the full grid"], 16, bullet=True)],
      """The figure-eight tests whether the graph can show two expected loops, that is, one connected graph with two cycles. The reference graph has two components and one cycle. The expected structure appears only with twenty intervals and fifty percent overlap, a configuration highlighted after the full grid was measured."""),

    # 11
    F("E2, blob control: graph cycles appear where there is no loop",
      [I("e2_blob_control_slide.png", 0.5, 1.4, 12.3, 3.85),
       T(0.7, 5.35, 12.1, 1.65, ["Reference cell: **20 nodes, 23 edges, 1 component, cyclomatic number 4**; longest basis cycle 6 nodes", "H1 gap ratio only **r₁ = 1.451**, below the dominance threshold", "At (20, 0.20): **6 components**, cyclomatic number 5"], 17, bullet=True)],
      """The blob has no loop and serves as a negative control. Its diagram has no dominant H1 feature, with a gap ratio of 1.45, yet the reference graph contains four independent cycles. A Mapper graph cycle therefore describes the constructed graph and is not evidence of a data loop."""),

    # 12
    F("Clusterer control: the clustering rule changes the cycle cue as much as the cover",
      [T(0.7, 1.4, 12.1, 0.85, ["Same data, PC1 lens and 12-cell grid; only the clusterer changes: forced KMeans k = 2 → single-linkage cut at ε = c × median 5-nearest-neighbour distance, c = 1.5 or 3.0"], 15),
       TB(0.6, 2.3, 12.2, [["Shape, c", "Reference cell: nodes / components / cycles", "Cells connected (of 12)", "Cells with ≥ 1 cycle (of 12)"],
                           ["Annulus, c = 3.0", "17 / 1 / 1", "10", "11"],
                           ["Annulus, c = 1.5", "27 / 3 / 1", "0", "8"],
                           ["Figure-eight, c = 3.0", "13 / 1 / 2", "12", "8"],
                           ["Figure-eight, c = 1.5", "29 / 5 / 0", "0", "0"],
                           ["Blob, c = 3.0", "26 / 9 / 0", "0", "3"],
                           ["Blob, c = 1.5", "79 / 36 / 0", "0", "2"]],
          [2.6, 4.2, 2.6, 2.8], size=15, row_h=0.46),
       T(0.7, 5.7, 12.1, 1.3, ["At c = 3.0 the figure-eight is connected in all 12 cells with two cycles at the reference cell; halving the scale fragments every shape", "**Post hoc:** both scales were chosen after the KMeans results, and only two were tried: an existence demonstration, not a recommended setting"], 16, bullet=True)],
      """The clusterer control tests whether the two-cluster KMeans rule contributes. It substitutes single-linkage clustering at two cut distances. At the larger scale the figure-eight is connected in every cell with two cycles at the reference cell; at the smaller scale all graphs fragment. Both scales were chosen after the KMeans results, so the control shows a possibility and recommends no setting."""),

    # 13
    F("RQ3, E3: two separate judgments of 13 figures by one observer",
      [BX(0.6, 1.4, 3.9, 1.5, "Visual clarity", ["11 of 13 figures judged clearly apparent; 2 of 13 ambiguous"], CB, 17),
       BX(4.65, 1.4, 3.9, 1.5, "Expected-property match", ["12 of 13 matched fully; 1 of 13 matched partially"], CG, 17),
       T(8.75, 1.4, 4.1, 1.6, ["One observer, the author, who designed the data and had seen earlier results", "AI vision model as a viewing aid; no blinding"], 14, bullet=True),
       I("e3_stimulus_S08.png", 0.9, 3.05, 3.5, 3.5),
       I("e3_stimulus_S11.png", 8.9, 3.05, 3.5, 3.5),
       T(4.6, 3.2, 4.2, 3.4, ["**Left:** figure-eight diagram. The loop count depends on an unlabeled H0/H1 colour convention and the essential H0 point.", "**Right:** no-loop blob Mapper graph. Noise-scale cycles read as a ring."], 14, bullet=True),
       C(0.6, 6.6, 12.2, "Stimuli S08 and S11 as inspected. A participant pilot was planned but not run: no participant data exist, so the counts say nothing about human accuracy or readability.", 11, 0.4)],
      """E3 inspected thirteen figures. No participant pilot was run; I rated each figure myself, with an AI vision model as a viewing aid. Eleven were clearly apparent and twelve matched the expected property fully. The ambiguous cases are the figure-eight diagram, because of an unlabeled colour convention and the essential H0 point, and the blob graph, because its noise cycles resemble a ring."""),

    # 14
    F("Weather: one station, six years, two analysis branches",
      [I("weather_analysis_pipeline.png", 0.5, 1.4, 7.6, 3.9),
       T(8.3, 1.4, 4.6, 5.5, ["**NOAA GSOD**, Central Park station 72505394728", "1 Jan 2019 – 31 Dec 2024: **2,192** daily rows", "No imputation; TEMP and DEWP are gapless", "4 days lack SLP: **2,188** days for the static cloud (TEMP, DEWP, SLP)", "WDSP would drop 129 days, so it is excluded; STP is excluded (lost leading digit)"], 16, bullet=True),
       T(0.7, 5.45, 7.4, 1.4, ["Branch 1: static three-variable cloud → PCA, Mapper, persistent homology", "Branch 2: temperature series → time-delay embedding → H1 gap ratio vs matched nulls"], 15, bullet=True)],
      """The weather study applies the diagnostics to a real series with a known annual cycle: daily NOAA records for New York Central Park, 2019 to 2024, giving 2,192 days. Four days lack sea-level pressure, leaving 2,188 for the static cloud. Wind speed and station pressure were excluded, and nothing was imputed."""),

    # 15
    F("The static weather cloud shows no dominant loop, but its graph has many cycles",
      [I("weather_grid_top.png", 0.5, 1.35, 6.1, 4.45),
       I("weather_grid_bottom.png", 6.75, 1.35, 6.1, 4.45),
       C(0.5, 5.8, 12.3, "Eight Mapper graphs of the static cloud (report Figure 7.3): rows n_cubes = 5, 10 (left) and 15, 20 (right); overlap 0.35 and 0.50; node colour is mean standardized temperature", 11, 0.4),
       T(0.7, 6.2, 12.1, 0.85, ["2,188 days, TEMP, DEWP, SLP: **PC1 explains 69.0 %**, PC2 28.6 %, **97.6 %** together · H1 gap ratio **r₁ = 1.19** (no dominant class) · connected for n_cubes ≤ 15, **2 components at n_cubes = 20**, cyclomatic number 3–14 · PC1 lens, KMeans k = 2, reference (10, 0.35). **Not a matched null control.**"], 14)],
      """In the static cloud each day is a point of temperature, dew point and sea-level pressure; two principal components explain 97.6 percent of the variance. The diagram has no dominant H1 feature, with a gap ratio of 1.19, while the Mapper graphs have three to fourteen cycles. This is a contrast and not a null control, because it ignores temporal order."""),

    # 16
    F("A time-delay embedding turns one series into a point cloud",
      [I("delay_window_illustration.png", 0.5, 1.4, 7.4, 3.8),
       I("weather_embedding_pca.png", 8.1, 1.4, 4.7, 4.05),
       T(0.7, 5.3, 7.2, 1.7, ["x_i = (x[i], x[i+τ], …, x[i+(d−1)τ]); stride 1", "Reference (τ, d) = (60, 8): span **420 days**, **1,772 windows** from 2,192 days"], 16, bullet=True),
       C(8.1, 5.45, 4.7, "Reference embedding projected on PC1 and PC2, coloured by season (report Figure 7.7). The projection is a drawing; the evidence is the persistence diagram.", 11, 0.7),
       T(8.1, 6.2, 4.7, 0.7, ["If temperature repeats yearly, the cloud should be a closed band"], 14)],
      """A time-delay embedding turns one series into a point cloud. With delay tau and dimension d, each point contains the temperature on one day and at later multiples of tau, for d values. With tau of sixty and d of eight, a point spans 420 days, giving 1,772 points; an annual pattern should place them near a closed curve."""),

    # 17
    F("All six embedding settings give a dominant H1 class",
      [TB(0.6, 1.5, 5.4, [["(τ, d)", "r₁", "Dominant persistence"],
                          ["(30, 8)", "5.625", "1.998"], ["(45, 9)", "7.319", "2.571"], ["(52, 8)", "4.922", "2.039"],
                          ["(60, 8) reference", "6.753", "2.167"], ["(73, 6)", "4.745", "1.417"], ["(90, 8)", "5.761", "2.121"]],
          [2.2, 1.2, 2.2], size=15, row_h=0.45, hl=(4,)),
       I("weather_seasonal_ph_sweep.png", 6.2, 1.5, 6.7, 2.8),
       C(6.2, 4.3, 6.7, "Dominant H1 persistence (left) and gap ratio r₁ (right) against embedding span (report Figure 7.4)", 11, 0.4),
       T(0.7, 4.85, 12.1, 2.1, ["All six reach the r₁ ≥ 3 convention: **r₁ = 4.75–7.32**", "Spans bracket the annual period of 365.25 days (green line, right figure)", "One dataset, and five settings were designed knowing the annual period: **consistency, not independent replication**"], 17, bullet=True)],
      """All six delay and dimension settings give a dominant H1 feature, with gap ratios from 4.75 to 7.32. They share one dataset, and five were designed around the annual period, so this is consistency and not independent replication."""),

    # 18
    F("Matched null controls do not reproduce a dominant H1 cue",
      [I("d2_weather_null_controls.png", 0.5, 1.4, 7.4, 3.7),
       C(0.5, 5.1, 7.4, "Gap ratio per setting (report Figure 7.8). Dashed line: r₁ = 3.", 11, 0.3),
       T(8.1, 1.4, 4.8, 3.9, ["**Anomaly series:** two annual harmonic pairs subtracted (82.2 % of the variance); all six settings give **r₁ = 1.02–1.14**", "**Ten shuffled series:** reference setting only, **r₁ = 1.007–1.219**, median 1.06", "H1 classes remain; the dominant one disappears"], 16, bullet=True),
       T(0.7, 5.5, 12.1, 1.5, ["Limits: harmonic removal may leave seasonal structure; shuffling is a weak null; only ten shuffles at one setting; no phase-randomised or autoregressive surrogate; one station", "No climate or causal claim. The static cloud (1.19) is not a matched null."], 15, bullet=True)],
      """Two null constructions test what produces the dominant feature. The anomaly series subtracts two fitted annual harmonic pairs, which explain 82.2 percent of the variance, and its gap ratio is 1.02 to 1.14 in all six settings. The shuffled series randomise the order; ten shuffles at the reference setting give 1.007 to 1.219. H1 features remain but none is dominant, so the cue is associated with annual structure and temporal order, although the shuffled null is weak."""),

    # 19
    F("The offline explorer makes saved Mapper parameter dependence inspectable",
      [I("explorer_annulus_reference.png", 0.5, 1.4, 5.4, 5.2),
       C(0.5, 6.6, 5.4, "Annulus reference cell (report Figure 8.1)", 11, 0.3),
       T(6.1, 1.4, 6.8, 5.5, ["One **0.57 MB** HTML file: **35 precomputed Mapper cells** (annulus 12, figure-eight 12, blob 2, weather 9)", "Configuration, statistics, native and component-separated layouts, reference comparison, input cloud and diagram, JSON export with SHA-256", "**Chrome 156, network off: 222/222 checks** passed; values recomputed independently and matched to the saved results", "Limits: display-only, precomputed cells, one clusterer per dataset, one browser engine; not the first Mapper explorer"], 16, bullet=True)],
      """The offline explorer shows saved Mapper results in a single HTML file of thirty-five precomputed cells and recomputes nothing. A browser test with the network disabled passed 222 of 222 checks. It is demonstrated next."""),

    # 20
    F("Persistence evidence for constructed loops survived resampling",
      [BX(0.6, 1.4, 5.9, 1.4, "Parameter sensitivity", ["Vary cover or clusterer; data fixed (E2, weather grid, explorer)"], CO, 14, hsize=15),
       BX(6.7, 1.4, 6.1, 1.4, "Input-sampling stability", ["Vary the sample; parameters fixed: 30 subsamples of 400 of 500 points, plus 30 independent redraws"], CG, 14, hsize=15),
       TB(0.6, 3.0, 6.4, [["Shape", "Dominant persistence, 30 subsamples", "30 independent redraws"],
                          ["Annulus", "1.439–1.575", "1.447–1.587"],
                          ["Figure-eight", "0.458–0.511", "0.445–0.553"],
                          ["Blob", "0.092–0.181", "0.078–0.157"]],
          [1.7, 2.7, 2.5], size=14, row_h=0.55),
       T(0.6, 5.3, 6.4, 1.7, ["Gap ratios: annulus r₁ = 13.2–25.6, figure-eight r₂ = 7.35–13.8, blob r₁ = 1.00–1.75", "No blob replicate reaches r_k ≥ 3 (0/30)"], 15, bullet=True),
       I("ph_resampling_persistence.png", 7.1, 3.0, 5.8, 1.95),
       C(7.1, 5.0, 5.8, "Top three H1 persistences of 30 resamples per shape (report Figure 9.1)", 11, 0.4),
       T(7.1, 5.5, 5.8, 1.5, ["Overlapping subsamples share points with the reference, so distances are descriptive, not independent validation"], 14, color=GREYC)],
      """The next analyses vary the sample instead of the parameters: thirty subsamples of 400 points and thirty independent redraws per shape. The gap ratio stays between 13.2 and 25.6 for the annulus, 7.35 and 13.8 for the figure-eight, and 1.00 and 1.75 for the blob. Subsamples overlap the full dataset, so these distances are descriptive and not independent validation."""),

    # 21
    F("In the same samples, the Mapper cycle cue depended on the clusterer",
      [I("mapper_resampling_cc.png", 0.5, 1.35, 4.9, 4.9),
       C(0.5, 6.25, 4.9, "Components and cyclomatic number over 30 subsamples (right half of report Figure 9.4); red dashes: full-data graph; node count is 20 by construction", 10, 0.55),
       TB(5.7, 1.45, 7.2, [["KMeans k = 2, 30 subsamples", "Components", "Cyclomatic number"],
                           ["Annulus", "1: 24, 2: 6", "0: 13, 1: 9, 2: 8"],
                           ["Figure-eight", "2: 24, 1: 6", "0: 12, 1: 18"],
                           ["Blob", "1: 10, 2: 12, 3: 8", "1–6"]],
          [2.6, 2.1, 2.5], size=14, row_h=0.5),
       T(5.7, 3.6, 7.2, 1.9, ["Annulus, KMeans: no cycle in 13/30 subsamples and 20/30 independent redraws", "Annulus, single-linkage at 3.0: one cycle in 30/30 subsamples and 30/30 independent redraws; at 1.5 the cycle is absent in 22/30"], 16, bullet=True),
       T(5.7, 5.4, 7.2, 1.55, ["The loop is in every sample, but the graph cycle comes and goes with the clustering rule. Scales were chosen post hoc: **this does not show that diagrams are generally stable and graphs generally unstable.**"], 15)],
      """Mapper on the same samples behaves differently. With KMeans the annulus graph has no cycle in thirteen of thirty subsamples, although the persistent-homology evidence for an H1 feature remains prominent there. Single-linkage at the larger scale gives one cycle in every subsample, but the scales were chosen post hoc."""),

    # 22
    F("Leave-one-year-out: no single year was necessary for the weather cue",
      [I("weather_loyo.png", 0.5, 1.4, 12.3, 3.9),
       T(0.7, 5.4, 12.1, 1.6, ["6 omitted-year folds × 6 embedding settings = 36 embeddings: **r₁ = 4.376–7.754**", "In 10 of the 36 fold-configurations, the gap-safe window rule also drops a neighbouring year", "A sensitivity analysis, not a hypothesis test, confidence interval or minimum-duration result"], 16, bullet=True)],
      """The leave-one-year-out analysis removes each year in turn, giving thirty-six embeddings with gap ratios from 4.376 to 7.754. In ten, the window rule also removes a neighbouring year. No single year is therefore necessary under the tested settings, but no minimum data duration is established."""),

    # 23
    F("Answers to RQ1, RQ2 and RQ3",
      [BX(0.6, 1.4, 4.0, 3.9, "RQ1: workflow", ["Native: persistent homology, diagram plots and distances, static Mapper", "Custom or other packages: generators, barcodes, graph statistics, harness", "Boundary: the HTML export fails offline"], CG, 17, bullet=True),
       BX(4.7, 1.4, 4.0, 3.9, "RQ2: sensitivity", ["Cover, overlap, clusterer and its scale change the Mapper reading", "Persistence evidence for constructed loops stayed prominent in every sample", "Boundary: tested data, lens, covers and two scales only"], CO, 17, bullet=True),
       BX(8.8, 1.4, 4.0, 3.9, "RQ3: communication", ["Figures mostly showed what they were built to show", "Unlabeled colours, the essential H0 point and noise-scale cycles caused ambiguity", "Boundary: one invested observer; no human readability claim"], CB, 17, bullet=True),
       T(0.7, 5.6, 12.1, 1.1, ["Persistence, Mapper graph structure and rendered appearance are **different kinds of evidence**."], 20)],
      """For RQ1, the triad natively supports the core computations, diagram plots and static Mapper drawing. For RQ2, Mapper structure depends on the cover, overlap, clusterer and its scale, whereas the persistent-homology evidence stayed prominent. For RQ3, most figures were clear; unlabeled colours, the essential point and noise-scale cycles caused ambiguity."""),

    # 24
    F("Three dependent variables, three sets of inputs",
      [TB(0.6, 1.5, 12.2, [["What you read", "What it depends on", "Evidence in this study"],
                           ["Persistence-diagram feature", "Point cloud, metric, filtration", "Dominant H1 class stable in all tested samples; null controls fail to reproduce it"],
                           ["Mapper-graph feature", "Point cloud, lens, cover, overlap, clusterer and its scale", "Cycles, fragments and tree readings change with cover and clusterer"],
                           ["Rendered drawing", "Layout, positioning, colour, rendering", "Layout can hide components; colours can mislead"],
                           ["Interpretation", "The reader and context", "Not measured: no participant study"]],
          [2.9, 3.8, 5.5], size=15, row_h=0.75),
       T(0.7, 5.5, 12.1, 1.4, ["Ask of any topological picture **which of these it is** and which parameters it depends on. The experiments do not show that people confuse graph cycles with loops; they show the two are not interchangeable."], 18)],
      """The outputs depend on different inputs: a diagram feature on the point cloud, metric and filtration; a Mapper feature also on the lens, cover and clusterer; the drawing on layout and colour. Graph cycles and H1 features are therefore not interchangeable evidence, although readers were not tested."""),

    # 25
    F("Limitations, threats to validity and non-claims",
      [BX(0.6, 1.4, 4.0, 5.4, "Limitations", ["2-D synthetic shapes, one seed each", "One lens, one cover family, two clusterer families (two scales)", "One station, six years; weak nulls", "No ripser vs GUDHI check", "Distances: H0 Wasserstein inflated; subsamples overlap the reference", "r_k ≥ 3 and S are conventions", "No participant study; one browser engine"], CO, 16, bullet=True),
       BX(4.7, 1.4, 4.0, 5.4, "Threats to validity", ["Construct: r_k and cyclomatic number are stand-ins", "Internal: ground-truth rank supplied; scales chosen post hoc", "External: tested data only", "Conclusion: no p-values; counts of 30 carry SE about 0.09", "Chronology cannot be verified: records place the grid, lens and loop counts before their runs; the extra weather settings, seasonality check, contrast cell and two scales came after"], CB, 15, bullet=True),
       BX(8.8, 1.4, 4.0, 5.4, "Non-claims", ["No human readability result", "No new algorithm or metric", "Not the first Mapper explorer", "No climate or causal claim", "A graph cycle does not prove a loop, and a missing one does not disprove it", "No claim about the true topology of any dataset", "Sensitivity analyses are not tests"], CP, 16, bullet=True)],
      """Several limitations affect interpretation. The shapes are two-dimensional with one seed each, only one lens and cover family were used, and the weather data come from one station with limited nulls. ripser was not compared with another implementation, and no participants were studied. The gap ratio and cyclomatic number are indicators, not measurements of loop counts, and some choices followed earlier results; without version control their order cannot be verified."""),

    # 26
    F("Reproducibility checks",
      [T(0.7, 1.45, 6.3, 5.4, ["**Software:** Python 3.12; ripser 0.6.15, persim 0.4.1, kmapper 2.1.0; scikit-learn 1.9.1, networkx 3.7, NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2",
                              "**Experiments:** computed on Linux, re-executed independently on Windows 11; saved structural outputs, diagrams, graphs and counts matched, and regenerated figures were pixel-identical",
                              "**Release check on Windows 11:** 203 automated tests passed, 38/38 environment assertions; the offline browser test (222/222) is separate"], 19, bullet=True),
       BX(7.3, 1.5, 5.5, 3.1, "What the verifier covers", ["It re-derives 126 registered numerical claims from saved results and checks them against the documents named for each", "Unregistered numbers and figure contents remain manual checks"], CG, 17, bullet=True),
       T(7.3, 4.9, 5.5, 2.0, ["Code, data and checks: github.com/shouryasarkar713/when-can-you-trust-a-topological-visualization"], 16, color=CB)],
      """Results computed on Linux were independently re-executed on Windows 11 with matching diagrams, graphs and counts. The documented run of 19 November passed 203 tests and 38 environment checks, with a separate browser test. The evidence verifier (126 registered facts) has been rerun since; the full suite has not."""),

    # 27
    F("Takeaway: trust follows the construction",
      [T(0.7, 1.45, 12.0, 1.4, ["Know **which representation** carries the claim, **which parameters** it depends on, and **which null control** it has to beat."], 26),
       T(0.7, 3.0, 12.0, 0.5, ["**Future work**"], 20),
       T(0.7, 3.5, 12.0, 3.4, ["Clusterer-scale dimension in the explorer; a sweep over cover and scale with surrogate nulls",
                              "Cross-check ripser against GUDHI on the key diagrams",
                              "A second weather station and a window-aware time-series bootstrap",
                              "A principled graph distance for Mapper stability",
                              "A participant study with counterbalanced order and a registered analysis plan"], 21, bullet=True)],
      """Trust in a topological visualization depends on its construction: which representation carries the claim, which parameters it depends on, and which null control it withstands. Persistent-homology evidence was stable in the tested samples, the weather cue depended on annual structure and temporal order, and Mapper cycles varied with the clusterer. Future work includes a clusterer-scale explorer dimension, a ripser-GUDHI comparison, a second station and a participant study."""),
]
