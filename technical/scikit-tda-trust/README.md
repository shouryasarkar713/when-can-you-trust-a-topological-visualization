# When Can You Trust a Topological Visualization?

A task-based evaluation of the **Scikit-TDA ecosystem** (`ripser` · `persim` ·
`kmapper`) for a Scientific Visualization course project ("Evaluation of
Visualization Systems", 15%).

**Research questions.** (RQ1) Which visualization-workflow tasks does the
triad support natively, which need external packages, which need custom code?
(RQ2) How sensitive are KeplerMapper visualizations to reasonable changes in
cover resolution and overlap — enough to change the structural interpretation
a user draws? (RQ3) For a predefined set of scientific exploration tasks,
what structural information is visible in Scikit-TDA's persistence diagrams
and Mapper visualizations, and what interpretation ambiguities arise from
parameter sensitivity and rendering choices? — answered by a **structured
single-observer task-based inspection** (the planned participant study was
NOT conducted; see below).

The full specification is the **Final Implementation Blueprint**
(`../download/ScikitTDA_Final_Project_Blueprint.md` in the planning
workspace); implementation-critical corrections and deviations are recorded
in [`IMPLEMENTATION_NOTES.md`](IMPLEMENTATION_NOTES.md). Read that file
first: it documents the corrected persistence-gap ratio r_k, the corrected
membership-overlap indicator S, the Phase-2 findings (offline browser test,
native-layout overlap, cross-process layout defect + fix, clean-copy
reproducibility), the Phase-3 single-observer inspection design, and every
deviation.

> **E3 note (honesty).** The classroom readability pilot was **not
> conducted** — a project constraint change (2026-10-22) made any
> participant study impossible. No participants were recruited or observed
> and no participant data exist. E3 is executed exclusively as the
> blueprint's pre-specified fallback: a *structured task-based inspection by
> a single observer* (`e3_inspection/PROTOCOL.md`,
> `e3_inspection/METHODS_NOTE.md`). Its results describe the produced
> artifacts and one observer's reading of them — never measured human
> accuracy or population-level readability.

## Status (Phase 3 — complete)

All three experiments are complete. E1 (13-task capability audit, all
demonstrated with path-verified evidence) and E2 (full 24-cell sensitivity
grid on both primary shapes + no-loop sanity control) are
reproducibility-verified: a clean exported copy with a fresh Python 3.12
environment reproduced **22/22 structural outputs identically and 32/32
figures pixel-identically** (`results/repro/comparison_report.json`).
E3 was executed as the single-observer inspection: 13 neutral-ID stimuli
rendered from saved results, inspected in one fixed-order pass, recorded in
`e3_inspection/inspection_record.csv`, validated and summarized in
`results/e3/inspection_summary.{json,md}`. The final report, presentation,
and Q&A preparation document are in `report/` and `presentation/`.

## Setup (Linux, Python 3.12; verified)

Native Windows is untested — use WSL2 there (blueprint Section 8). Verified
from a clean exported copy with a fresh venv (2026-10-22).

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows/WSL2: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt    # pinned stack (~20 s, prebuilt wheels)
pip install -r requirements-dev.txt  # pytest, only needed to run tests
```

## Run (execution order)

```bash
python scripts/verify_env.py          # assert pins + API surface + smoke (fails loudly)
python scripts/run_e1_audit.py        # E1: 13-task audit + capability matrix + evidence log
python scripts/run_e2_sensitivity.py  # E2: 24-cell grid (annulus + figure-eight) + blob sanity control
python scripts/run_e3_readability.py  # E3 MATERIALS: stimuli + key + blank inspection worksheet
python src/figures.py --all           # re-render every E2/readability figure from saved results only
python -m pytest tests/ -q            # unit + output-validity + determinism-regression tests
```

E3 analysis (after the record is completed by hand — it already is):

```bash
python scripts/analyze_e3_inspection.py   # validates the record; writes results/e3/ summary
```

or with make: `make verify && make e1 && make e2 && make e3 && make figures && make test`
(`make all` chains them); `make e3-analysis` summarizes the completed
inspection record. `make glue` recomputes the glue-code accounting;
`make repro` runs the clean-copy / fresh-environment test.

## Reproduce

Every number in the report is traceable to a file under `results/`; E2 and
readability figures are re-rendered from `results/` by `src/figures.py`
without recomputation (E1 audit-stage figures are rendered by the audit
pipeline itself). All seeds and parameters live in `configs/*.yaml` —
nothing is hard-coded in scripts. Reruns are deterministic, including
ACROSS PROCESSES (a hash-randomization defect in the custom layout was
found by the clean-copy test and fixed; regression-tested under different
`PYTHONHASHSEED` values). Wall-clock timings are the only
environment-dependent outputs and are labeled as such.

The one **authored** (non-regenerated) experimental artifact is
`e3_inspection/inspection_record.csv` — the completed single-observer
inspection record. Everything else in E3 is regenerated deterministically.

## Repository layout

```text
configs/        shapes.yaml, e1_audit.yaml, e2_sensitivity.yaml, e3_readability.yaml
src/            shapes.py, pipeline.py, similarity.py, figures.py
scripts/        verify_env, run_e1_audit, run_e2_sensitivity, run_e3_readability,
                analyze_e3_inspection (validates + summarizes the record),
                count_glue_code, compare_runs, clean_clone_test.sh
tests/          test_shapes, test_metrics (gap ratio r_k), test_similarity (S),
                test_signatures (ground-truth checks), test_outputs (validity +
                determinism regressions), test_e3_inspection (record schema)
results/        env/, e1/ (incl. layout_overlap, offline_browser_test),
                e2/ (24-cell grid, blob sanity, interpretation notes),
                e3/ (inspection summary), repro/ (comparison report + log)
figures/        e1/, e2/ — rendered artifacts + caption files
audit/          capability_matrix.csv (13 tasks x 7 columns), evidence_log.md,
                glue_code_accounting.json, html_resource_inventory.md
e3_inspection/  PROTOCOL.md, METHODS_NOTE.md, stimuli/ (neutral IDs),
                stimulus_manifest.json + scoring_key.csv (internal),
                inspection_worksheet_BLANK.csv, inspection_record.csv (AUTHORED)
report/         final report (.docx + .pdf) + assignment checklist
presentation/   slides (.pptx with speaker notes) + Q&A preparation document
```

## Key verified findings

- **E2 (interpretation instability).** The figure-eight's Mapper graph
  fragments into 2 components at the pre-specified reference cell (10, 0.35)
  and into 4 at (20, 0.20), while (20, 0.50) gives the construction-
  consistent reading (connected, two 20-node basis cycles). The annulus loop
  signal vanishes entirely at n_cubes=5 (tree graph) and fragments only at
  (20, 0.20). Node count equals 2 x n_cubes in all 24 cells — uninformative.
  The no-loop blob control shows 4 short noise-scale graph cycles while its
  H1 diagram correctly shows no dominant class: **Mapper graph cycles are
  not automatically topological loops.**
- **E3 (single-observer inspection).** 13/13 task records: 11 properties
  clearly apparent, 2 ambiguous (the figure-eight diagram's loop count
  hinges on the unlabeled H0/H1 color convention — the essential-class
  point is drawn farther from the diagonal than either loop point; and the
  no-loop blob's Mapper graph reads as "ring-like" because noise-scale
  cycles are visually indistinguishable from data-scale loops). Scatter
  reference views were uniformly clear. Mapper morphology readings are
  parameter-dependent (E2) and layout-dependent (native kk overlaps
  disconnected components; the inspected stimuli use the documented
  component-separated rendering).
- **Native static layout limitation (E1/T10).** `draw_matplotlib(layout='kk')`
  places disconnected components in one frame with no inter-component
  repulsion: measured bbox overlap IoU 0.23 on three-blobs, node
  interleaving on the figure-eight (`results/e1/layout_overlap.json`);
  visually confirmed. A custom component-separated layout (structure
  untouched) is provided and documented side-by-side.
- **The kmapper HTML export is not an offline artifact.** Verified by a
  genuine cold-cache offline browser test: D3 fails to load, the graph does
  not render (0 nodes / 0 edges). It loads D3 6.1.1 + FileSaver 2.0.2 +
  Google Fonts + an imgur favicon (rate-limited 429 even online) from CDNs
  at view time. Static PNGs are the presentation fallback.
- ripser 0.6.15 no longer exports `plot_dgms`; H1 barcodes require a custom
  renderer (quantified in the capability matrix and glue accounting).
- networkx — needed for component counts — is **not** a declared kmapper
  runtime dependency.
