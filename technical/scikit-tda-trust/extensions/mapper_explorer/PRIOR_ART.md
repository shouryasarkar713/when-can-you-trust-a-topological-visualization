# Prior-Art Review — Mapper Sensitivity Explorer (Stage 3, Extension B)

**Search date:** 2026-10-22 (UTC). **Stage-4 update:** 2026-10-22 (UTC) —
the LoCoMapper entry was upgraded from snippet-only evidence to the official
IEEE VIS 2026 program record (see section 3 and the fetch log); no other
finding changed.
**Searcher:** project author, via available web tooling (WebSearch + WebFetch).
**Scope (bounded, per Stage-3 authorization):** existing tools and papers on
(1) Mapper Interactive and similar parameter-exploration interfaces;
(2) Mapper parameter selection and stability diagnostics;
(3) sensitivity heatmaps and small-multiple visualizations for Mapper graphs;
(4) offline, reproducible Mapper visualization workflows.

## Exact queries run (verbatim)

Via WebSearch (web tool):

1. `Mapper Interactive parameter exploration tool Mapper graph visualization`
2. `Mapper parameter selection stability diagnostics topological data analysis`
3. `sensitivity heatmap small multiples Mapper graphs visualization`
4. `offline reproducible Mapper visualization workflow KeplerMapper`
5. `TDAMapper GUDHI Mapper interactive viewer parameter tuning`
6. `Carriere Oudot structure stability one-dimensional mapper arxiv`
7. `KeplerMapper van Veen JOSS paper visualization`
8. `GUDHI mapper module python visualization`
9. `probabilistic convergence stability random mapper graphs Brown Bobrowski Munch Wang`
10. `TDAmapper R package ggplot2 mapper visualization`
11. `Mapper parameter sweep resolution overlap sensitivity analysis visualization`

Via WebFetch (direct page inspection):

- `https://github.com/MapperInteractive/MapperInteractive`
- `https://export.arxiv.org/abs/2011.03209` (Mapper Interactive paper)
- `https://export.arxiv.org/abs/1511.05823` (Carrière & Oudot)
- attempted: `https://export.arxiv.org/api/query?...` (arXiv API — query
  parameters were stripped by the fetch layer; the API returned an error; the
  API route was abandoned in favor of direct abstract pages and WebSearch)
- attempted: `https://www.sci.utah.edu/~beiwang/publications/LoCoMapper_BeiWang_2026.pdf`
  (Stage 3: fetch limit reached before this page could be read; superseded by
  the Stage-4 fetches below)

Stage-4 fetches (LoCoMapper verification, 2026-10-22):

- `https://am.ieeevis.org/year/2026/program/content/9e4af3b5-5f6d-4b27-ba09-7ea919068da0`
  — the official IEEE VIS 2026 program record: exact title, full author list,
  verbatim abstract, session (Uncertainty Visualization), and Honorable
  Mention note. Primary source for section 3.
- `https://ieeevis.org/year/2026/program/paper/9e4af3b5-5f6d-4b27-ba09-7ea919068da0`
  — attempted as the canonical domain equivalent; the fetch returned the
  site's "non-existing webpage" error (single-page-app routing), so the
  am.ieeevis.org content mirror above was used instead. Both URLs surfaced
  the same paper record in search results.
- `https://xinyuanryanyan.github.io` — first author's page; corroborates the
  venue (IEEE VIS Workshop on Uncertainty Visualization, 2026) and the author
  list; its "paper" link points to a sign-in-gated PDF that was not fetched.

Stage-4 WebSearch queries (verbatim): `LoCoMapper IEEE VIS 2026`,
`LoCoMapper local structural uncertainty Mapper graphs Bei Wang`,
`"LoCoMapper" visualization`.

**Tool-failure disclosure (honesty):** the first two WebSearch batches
(queries 1–5, run twice) returned "No results found" for every query,
including the trivial query `Mapper Interactive` — a tool outage, not a true
empty result. The outage was not silently accepted: searches were retried
later the same session and succeeded (queries 6–11), and every source below
was verified against a fetched page or the search-result content. Two arXiv
paper-ID guesses made during the outage (1512.02956, 1905.03376) turned out
to be unrelated papers; both fetches are recorded here and were discarded.
The LoCoMapper entry was initially snippet-only (the PDF exceeded the fetch
limit); the Stage-4 fetch of the official IEEE VIS 2026 program record
retired that limitation — section 3 now cites the verbatim abstract from
am.ieeevis.org.

## Sources inspected and findings

### 1. Parameter-exploration interfaces (closest prior art for the viewer)

**Mapper Interactive** — Youjia Zhou, Nithin Chalapathi, Archit Rathore,
Yaodong Zhao, Bei Wang. *Mapper Interactive: A Scalable, Extendable, and
Interactive Toolbox for the Visual Exploration of High-Dimensional Data.*
IEEE Pacific Visualization (PacificVis) 2021; arXiv:2011.03209.
- Web-based framework for interactive Mapper analysis; on-the-fly recomputation
  of Mapper graphs under user parameter changes; extensible analysis modules;
  CLI computes graphs for 1M×256 points in ~3 min (claimed 4× faster than
  vanilla KeplerMapper).
- Technology: Python + JavaScript + HTML on Flask (local server at
  127.0.0.1:8080), built on KeplerMapper, scikit-learn, NetworkX (per the
  GitHub repository).
- **Relation to this project:** Mapper Interactive is a *computation*
  explorer — it recomputes Mapper under new parameters and requires a local
  server process. It is not a saved-results viewer, is not single-file, and
  does not embed per-cell provenance or the interpretive safeguards this
  project requires (S-score caveats, cycles-vs-loops guard, no-readability-
  claim banner).

**tda-mapper (Python library)** — Luca Simi, 2024 (readthedocs).
- Efficient Mapper construction with scikit-learn integration; Plotly /
  Matplotlib / PyVis visualization backends; an "interactive app" providing
  a web-based interface with real-time parameter adjustment.
- **Relation:** another compute-on-the-fly explorer; Plotly/PyVis backends
  pull substantial JavaScript from CDN by default; not a saved-grid viewer.

**KeplerMapper** — Hendrik Jacob van Veen, Nathaniel Saul, David Eargle,
Sam W. Mangham. *Kepler Mapper: A flexible Python implementation of the
Mapper algorithm.* JOSS 4(42):1315, 2019. (Verified via the official docs,
kepler-mapper.scikit-tda.org.)
- The library this project's baseline already evaluates. Ships a static
  D3-based HTML visualization per run; the baseline E1 audit documented that
  it loads D3.js 6.1.1 and FileSaver 2.0.2 from CDN and fails offline.
  One graph per run — no parameter-grid comparison.

**GUDHI Mapper/GIC/Nerve cover complexes** (gudhi.inria.fr Python docs).
- Mapper construction with configurable resolutions/gains; outputs TXT files
  for visualization with neato (Graphviz) or a KeplerMapper script; no
  interactive parameter exploration.

**TDAmapper (R)** — Paul Pearson et al. (GitHub paultpearson/TDAmapper).
- Mapper construction in R; static igraph/ggplot2 plots. No interactivity.

**mappeR (R, CRAN)** — George Clare Kennedy, Univ. of Iowa Applied Topology;
CRAN version 2.4.0, published 2026-01-27.
- Mapper graph construction package (testthat-tested); construction library,
  not a sensitivity viewer.

**Ayasdi Core** (commercial, historical — not fetched this session): the
original proprietary Mapper platform with interactive parameter tuning;
common knowledge in the field; included here for completeness, not as a
verified source.

### 2. Parameter selection and stability diagnostics (theory)

**Structure and Stability of the 1-Dimensional Mapper** — Mathieu Carrière,
Steve Oudot. SoCG 2016; Foundations of Computational Mathematics 2018;
arXiv:1511.05823.
- Theoretical framework relating the Mapper to the Reeb graph; predicts which
  Reeb features appear in the Mapper given the cover's position relative to
  critical values; quantifies per-feature (in)stability; convergence to the
  Reeb graph as cover granularity → 0. This is the theoretical backbone for
  why parameter positioning matters — the phenomenon our E2 grid measures
  empirically.

**Probabilistic Convergence and Stability of Random Mapper Graphs** —
Adam Brown, Omer Bobrowski, Elizabeth Munch, Bei Wang. Journal of Applied
and Computational Topology 2021 (doi:10.1007/s41468-020-00063-x);
arXiv:1909.03488.
- Studies convergence between (random) Mapper graphs and Reeb graphs under
  sampling of the space; stability in the statistical sense.

### 3. Sensitivity visualization for Mapper graphs (research frontier)

**LoCoMapper: Local Structural Uncertainty Analysis of Mapper Graphs under
Cover Perturbations** — Xinyuan Yan (Scientific Computing and Imaging
Institute, University of Utah), Jixian Li (University of Texas at Austin),
Bei Wang (University of Utah). *IEEE VIS 2026 Workshop on Uncertainty
Visualization* — **Honorable Mention**. Verified 2026-10-22 against the
official program record at
`https://am.ieeevis.org/year/2026/program/content/9e4af3b5-5f6d-4b27-ba09-7ea919068da0`
(abstract quoted verbatim below); venue corroborated by the first author's
page. This supersedes the Stage-3 snippet-only entry.

Abstract (verbatim): "Mapper graphs provide compact topological summaries
of high-dimensional data, but small changes in cover parameters can
substantially alter their topology, making it difficult to distinguish
persistent structures from those that arise only under particular parameter
configurations. Despite growing interest in uncertainty visualization,
methods for representing uncertainty in Mapper graphs remain largely
unexplored. We present LoCoMapper, a framework that takes a first step
toward uncertainty-aware visualization of Mapper graphs by characterizing
their local structural sensitivity to perturbations of the cover parameters.
Given a reference Mapper graph, LoCoMapper aligns local regions of the
reference graph with corresponding regions in an ensemble of perturbed
graphs and summarizes their variation using two node-level measures: local
structural consistency, which quantifies the preservation of local topology
across reliable alignments, and ensemble support, which captures the amount
of reliable evidence supporting that estimate. Jointly visualizing these
measures on the reference graph enables users to distinguish robust,
sensitive, and weakly supported regions. We demonstrate the effectiveness of
LoCoMapper on a controlled two-dimensional dataset, a synthetic
three-dimensional ant dataset, and word embeddings from a fine-tuned BERT
model."

**Distinction from this project's explorer.** LoCoMapper and this project's
viewer address different objects with different methods:

- *What varies.* LoCoMapper quantifies local structural uncertainty under
  **cover-parameter perturbations** — it computes an ensemble of perturbed
  Mapper graphs from the same underlying data (parameter sensitivity).
  This project's explorer displays a **precomputed parameter grid** saved by
  the audited E2/weather experiments, and its Stage-4 companion study
  separates parameter sensitivity from **input-sampling stability** (different
  subsamples, fixed parameters) — a variation axis LoCoMapper does not
  address in its abstract.
- *What is computed.* LoCoMapper introduces algorithmic content: alignment
  of local graph regions across the ensemble plus two node-level uncertainty
  measures (local structural consistency, ensemble support). This project's
  explorer introduces no algorithm — it renders saved graphs, saved structure
  statistics, and the baseline's exploratory membership-Jaccard S with
  explicit caveats, and never recomputes Mapper or persistent homology.
- *Artifact form.* LoCoMapper is a research framework demonstrated on a
  controlled 2-D dataset, a 3-D ant dataset, and BERT word embeddings. The
  explorer is a single self-contained offline HTML file whose purpose is
  side-by-side inspection of this project's own saved cells with per-cell
  provenance and embedded interpretive safeguards — an implementation and
  evaluation artifact for this project's review workflow, not a research
  framework.

LoCoMapper is therefore the closest research-grade prior art for *visualizing
Mapper sensitivity*, and it goes materially beyond what this project
attempts: it quantifies uncertainty, whereas this project only makes
saved sensitivity cells inspectable. No claim in this project competes with
or subsumes it.

General sensitivity-visualization literature (cobweb plots, spatial
sensitivity fields — e.g. arXiv:2408.03817, hal-02490440) exists for
simulation models broadly, but nothing specific to Mapper grids surfaced in
the bounded queries beyond the works above.

### 4. Offline, reproducible Mapper workflows

- KeplerMapper's HTML output is the de-facto offline artifact, but its CDN
  dependency makes it fail cold-cache offline (this project's baseline E1
  audit measured this failure; the finding stands).
- Mapper Interactive runs a local Flask server — offline-capable after
  installation, but not a static artifact and not dependency-light.
- No prior tool found in the bounded search that ships a **single
  self-contained HTML file, with all data inlined from saved, hashed
  experiment outputs, zero external resources, and no server** — the design
  this extension adopts. This is a modest engineering property, not a
  scientific claim; several tools could be reconfigured toward it.

## Resulting novelty position

**The explorer is positioned as an implementation and evaluation
contribution, nothing stronger.** Concretely:

- It is **not** the first Mapper explorer (Ayasdi historically; Mapper
  Interactive 2021; tda-mapper 2024 precede it).
- It proposes **no** new graph-stability algorithm or metric (Carrière–Oudot
  and Brown et al. own that space; the membership-Jaccard S already exists
  in this project's baseline E2 as an exploratory indicator).
- Its specific combination — (a) saved-results-first: displays only
  precomputed cells from this project's audited experiments, never
  recomputing Mapper or persistent homology; (b) single-file, zero-CDN,
  zero-server offline operation; (c) per-cell provenance (source file,
  parameters, seed, structure statistics) carried from the saved JSONs;
  (d) embedded interpretive safeguards (S is exploratory, not a metric;
  graph cycles ≠ persistent loops; connected graph ≠ correct reading; no
  human-readability claim given the absence of a participant study) —
  is a deliberate engineering and honesty design for THIS project's review
  workflow, and is not claimed as a general research contribution.
- RQ2 evidence from the viewer is correspondingly modest: it demonstrates
  that a compact offline artifact can make the parameter-dependence of
  Mapper structure *inspectable and comparable side-by-side with
  provenance*; it does not demonstrate improved human readability (no
  participant study exists in this project).
