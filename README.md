# When Can You Trust a Topological Visualization?

A task-based evaluation of the Scikit-TDA ecosystem (ripser 0.6.15 · persim 0.4.1 · KeplerMapper 2.1.0) for the course
*Scientific Visualization — Evaluation of Visualization Systems*. Author: Shourya Sarkar. 28 October 2026.

Repository: <https://github.com/shouryasarkar713/when-can-you-trust-a-topological-visualization>

> **Provenance of this repository.** Contemporaneous version-control history was not maintained during the project. The
> submission repository is organized retrospectively for reproducibility and release; its commit history should not be
> interpreted as evidence of the original design or analysis chronology.

## What the project asks

A persistence diagram or a Mapper graph looks like a statement about the shape of data. The project asks when such a picture
can be trusted, keeping five things apart: the true topology of the data, the persistent-homology (PH) evidence under a given
metric and filtration, the Mapper graph under a given lens, cover, clusterer and parameters, the appearance of the drawing, and
the reader's interpretation.

- **RQ1 (workflow).** Which visualization-workflow tasks does the triad support natively, which need other packages, which need custom code? (E1)
- **RQ2 (sensitivity).** How sensitive are KeplerMapper visualizations to cover resolution, overlap and the clustering rule? (E2, controls D1/D3/D4, explorer)
- **RQ3 (what the artifacts communicate).** What structure do persistence diagrams and Mapper graphs make visible, and which ambiguities arise? (E3)
- **Extensions.** A weather case study (NOAA GSOD, one station, 2019–2024) with matched null controls; an offline Mapper explorer; resampling and leave-one-year-out analyses.

## Scientific limitations (read before citing any number)

- Mapper cycle behaviour depends on the clusterer. The default KMeans(k = 2) rule and single-linkage clustering give different
  answers on the same data. The two single-linkage scales were chosen **after** the KMeans result and only two were tried: an
  exploratory existence demonstration, not a pre-registered or exhaustive search and not a recommended setting.
- A Mapper graph cycle is not a proven topological loop; a missing cycle does not disprove one.
- The static-embedding contrast in the weather study is a constructed comparison, not temporal or topological evidence. The
  dominant-H1 cue (gap ratio r₁ ≥ 3, a convention) is absent in the matched null embeddings while H1 classes remain. The
  controls do not show that the annual cycle is the only possible source of the cue, and nothing here is a climate result.
- E3 is **one invested observer with an AI viewing aid**, not a participant study; it says nothing about how people read the figures.
- No cross-check against another persistent-homology implementation (ripser vs GUDHI) was made; one station, a limited set of
  lenses and covers; the order of design and analysis cannot be verified from artifacts.

Full discussion: report Sections 10 and 11.

## Deliverables

| Item | Files |
|---|---|
| Final report | [PDF](submission/report/Final_Report.pdf) · [DOCX](submission/report/Final_Report.docx) · [Markdown source](submission/report/Final_Report.md) (figures in `submission/report/figures/`) |
| Presentation | [PPTX, 14 slides, speaker notes embedded](submission/presentation/Final_Presentation.pptx) · [PDF](submission/presentation/Final_Presentation.pdf) · [speaker notes](submission/presentation/Speaker_Notes.md) |
| Q&A preparation | [DOCX](submission/presentation/QA_Preparation.docx) · [PDF](submission/presentation/QA_Preparation.pdf) |

## Directory guide

```
submission/report/                Final_Report.{md,docx,pdf} and figures/
submission/presentation/          slides, speaker notes, Q&A preparation
technical/scikit-tda-trust/       code, configs, data, results, figures, tests (has its own README)
  src/ scripts/ configs/          core experiments E1–E3
  extensions/meteorology/         weather case study (raw GSOD files included)
  extensions/mapper_explorer/     offline Mapper explorer (viewer/index.html is self-contained)
  extensions/stability/           resampling and leave-one-year-out analyses
  extensions/controls/            control experiments D1–D5
  tests/ extensions/*/tests/      pytest suites; conftest.py is the repository-wide side-effect guard
technical/verification/           evidence verifier, claims, environment record, reference evidence
technical/build/                  scripts that generate the DOCX/PDF, slides and Q&A from their sources
SHA256SUMS.txt                    checksums of every file in the repository except itself
DATA_AND_LICENSING.md             data sources and licence status
```

## Set up

Python 3.12 (verified with 3.12.13 on Windows 11). On Windows set `PYTHONUTF8=1`.

```bash
cd technical/scikit-tda-trust
python3.12 -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt -r requirements-verify.txt
```

The exact package list and installation record of the verified run: `technical/verification/env/`.

A note on older documents: `technical/scikit-tda-trust/README.md`, `IMPLEMENTATION_NOTES.md` and `extensions/README.md` are project
records written before the final deliverables were assembled. They are kept as written (the first two are protected by the baseline
manifest) and refer to folders such as `report/`, `presentation/` and `extensions/final/` that are not part of this repository, and to
test counts of their time. This README, `submission/` and `technical/verification/` are authoritative.

## Reproduce the experiments

All commands run from `technical/scikit-tda-trust`; seeds and parameters are in `configs/` and `extensions/*/configs/`. These
commands **overwrite** the stored results in the working tree; use a scratch clone if you want to compare against the shipped
results (`technical/verification/compare_trees.py`).

```bash
python scripts/verify_env.py                 # pinned versions and API surface (rewrites results/env/*)
python scripts/run_e1_audit.py               # E1 capability audit
python scripts/run_e2_sensitivity.py         # E2 Mapper grid
python scripts/run_e3_readability.py && python scripts/analyze_e3_inspection.py
python src/figures.py --all
python extensions/meteorology/scripts/preprocess_weather.py        # raw GSOD files included; fetch_gsod.py re-downloads (network)
python extensions/meteorology/scripts/run_weather_analysis.py      # about 2.5 min
python extensions/meteorology/scripts/seasonality_check.py
python extensions/meteorology/scripts/render_weather_figures.py
python extensions/stability/scripts/run_mapper_resampling.py
python extensions/stability/scripts/run_ph_resampling.py           # about 30 min, resumable
python extensions/stability/scripts/run_weather_loyo.py            # about 4 min
python extensions/stability/scripts/summarize_stability.py && python extensions/stability/scripts/render_stability_figures.py
python extensions/mapper_explorer/scripts/build_viewer.py          # --out-dir DIR builds somewhere else
for s in run_mapper_clusterer_control run_mapper_resampling_control run_caveat_checks run_independent_draws run_weather_null_controls render_control_figures; do
  python extensions/controls/scripts/$s.py; done
```

## Verify

```bash
cd technical/scikit-tda-trust
python scripts/run_all_tests.py --package-root ../.. --browser
```

The runner executes each pytest suite in its own process, the baseline-manifest check, `verify_env.py` in a temporary copy, the
evidence verifier and (with `--browser`; needs Playwright and Chrome in the interpreter given by `--browser-python`, default the current one) the offline explorer test. Properties:

- It writes logs to a fresh temporary directory (or `--log-dir`, which must be empty and outside the repository). A routine run
  never modifies tracked files, the baseline, or the reference evidence; the whole tree is hashed before and after and any
  difference fails the run.
- Each suite gets one outcome: PASS, FAIL, INTENTIONAL SKIP, DEPENDENCY MISSING, COULD NOT EXECUTE or MISSING SUITE. The exit
  status is 0 only if every required stage passed.
- `technical/verification/reference/` holds the immutable results of the recorded run; the runner compares fresh counts with it
  without writing to it.
- `conftest.py` also guards every test: a test that changes, creates or deletes a repository file is failed and the change reverted.

Verify the checksum manifests:

```bash
python technical/verification/check_manifest.py       # SHA256SUMS.txt
cd technical/scikit-tda-trust && python extensions/scripts/verify_baseline_unchanged.py
```

`BASELINE_MANIFEST.json` records 145 files of the preserved core results. Seventeen of them (sixteen original course report and
presentation files with their generators, and the original `.gitignore`) are intentionally not distributed; they are listed with hashes and reasons in
`extensions/BASELINE_RELEASE_EXCLUSIONS.json`, and the verifier reports them separately instead of hiding them.

## Regenerate the report and presentation

```bash
python technical/build/report/build_report_docx.py submission/report/Final_Report.md submission/report/Final_Report.docx
python technical/build/presentation/build_slides.py technical/build/presentation/figures submission/presentation/Final_Presentation.pptx submission/presentation/Speaker_Notes.md
python technical/build/report/build_report_docx.py technical/build/presentation/QA_Preparation.md submission/presentation/QA_Preparation.docx
```

PDF export and slide rendering use Microsoft Word and PowerPoint automation on Windows
(`technical/build/report/export_pdf.ps1`, `technical/build/presentation/render_pptx.ps1`); the generated PDFs are included.

## Licence and data

No licence has been granted for this repository: all rights are reserved by the author, and nothing here should be read as
permission for reuse beyond viewing and running the code for evaluation. Third-party data and software keep their own terms. See
[DATA_AND_LICENSING.md](DATA_AND_LICENSING.md).
