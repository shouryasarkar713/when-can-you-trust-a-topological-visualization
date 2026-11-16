# Extensions — Scikit-TDA evaluation project

Studies that extend the three core experiments (E1–E3) of *When Can You Trust a Topological Visualization? A Task-Based Evaluation of
the Scikit-TDA Ecosystem*. The core experiments live in the parent directory; their results are protected by
`BASELINE_MANIFEST.json`, which records the SHA-256 hash of every core file. Nothing in this directory writes into the core
directories.

## Contents

| Directory | Study | Question |
|---|---|---|
| `meteorology/` | Weather case study (NOAA Global Summary of the Day, Central Park, 2019–2024) | When do topological visualizations reveal recurring seasonal structure in real data? |
| `mapper_explorer/` | Offline Mapper sensitivity explorer (a single HTML file over saved results) | Can parameter-dependent changes of a Mapper graph be made inspectable offline? |
| `stability/` | Resampling and leave-one-year-out analyses | How do diagrams and graphs change when the sample changes rather than the parameters? |
| `controls/` | Control experiments D1–D5 (clusterer, resampling, independent redraws, caveat checks, weather null controls) | Do specific alternative explanations account for the Mapper and weather results? |
| `scripts/` | Baseline manifest tools | — |

Design rationale and the mapping of studies to research questions: [`EXTENSION_DESIGN.md`](EXTENSION_DESIGN.md). The report in
`submission/report/` describes the studies and their results.

## Ground rules

- **Honesty constraints.** No participant study exists and none is simulated; the single-observer E3 inspection is the only evidence
  about how the figures read. Computational proxies are never described as evidence of human readability. There is no hypothesis
  test of the El Niño–Southern Oscillation, and descriptive bands are not confidence sets.
- **Determinism.** Every experiment is configuration-driven (`<study>/configs/*.yaml`), seeded, and saves its numerical outputs
  before any figure is rendered from them.
- **Environment.** Extension code runs in the same pinned environment as the core experiments
  (`../requirements.txt`).
