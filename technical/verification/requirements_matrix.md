# Requirements → implementation → evidence matrix

Reconstructed 2026-10-28 from: `Scikit-TDA_Evaluation_Research_Plan.pdf` / `scikit_tda_evaluation_plan.md` (Revision 1, 20 Oct 2026), `ScikitTDA_Adversarial_Review_Report.pdf` (21 Oct), `ScikitTDA_Research_Plan_Rev2.pdf` / `scikit_tda_plan_v2_revision.md` (21 Oct), `ScikitTDA_Final_Project_Blueprint.pdf` (21 Oct), the repository `IMPLEMENTATION_NOTES.md` and `PROJECT_WORKLOG.md`, and the extension design documents. **The original assignment text and any grading rubric were not among the supplied files**; the course requirements are known only through the blueprint's Table 11. Later documents were not assumed correct: where a later document dropped an earlier element, the drop is listed as *cut* and its stated reason recorded.

Status vocabulary: **met** (implemented and evidenced), **met-narrowed** (implemented with a narrower claim than first written), **cut** (deliberately dropped by a documented decision; not claimed), **added** (new in the independent rebuild), **not met** (required, not delivered — none).

## A. Course requirements (Blueprint Table 11)

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| C1 | Install the selected tool(s) | `technical/scikit-tda-trust/requirements.txt` (pins), `README.md`, `scripts/verify_env.py` | `technical/verification/env/` freeze; 38/38 environment assertions in the rebuilt environment; install from pins into a fresh Python 3.12.13 venv on Windows 11 | met |
| C2 | Explore, experiment, demonstrate use cases with visualizations | E1–E3, Extensions A–C, controls D1–D5 | `technical/scikit-tda-trust/figures/`, `results/`, `extensions/*/figures/` | met |
| C3 | Scripts and instructions to reproduce | `scripts/`, `configs/`, `src/`, `tests/`, `README.md`, `Makefile` | full regeneration in a fresh copy; file-by-file comparison in `technical/verification/reference/compare/compare_*.json` | met |
| C4 | Comprehensive report with advantages and disadvantages | Report Sections 5–10 | `submission/report/Final_Report.{md,docx,pdf}` | met |
| C5 | Research gaps and future improvements | Report Sections 9.3, 10, 12 | gaps framed as limits/future work; no novelty claim | met-narrowed |
| C6 | Presentation and Q&A | `submission/presentation/Final_Presentation.pptx` (14 slides, about 10 min narration), `Speaker_Notes.md`, `QA_Preparation.{docx,pdf}` (25 questions) | rendered and inspected slide by slide | met |

## B. Research design commitments

| ID | Commitment | Source | Implementation | Evidence | Status |
|---|---|---|---|---|---|
| D1 | Central RQ + RQ1 workflow, RQ2 sensitivity, RQ3 readability | Blueprint §2 | Report §2.1 | — | met (RQ3 answered by single-observer inspection) |
| D2 | System boundary: ripser, persim, kmapper; others external | Blueprint §3 | Report §3.1; E1 glue accounting | `audit/glue_code_accounting.json` | met |
| D3 | E1: 13-task audit, each cell backed by a file path | Blueprint §4.1 | `scripts/run_e1_audit.py`, `audit/capability_matrix.csv`, `audit/evidence_log.md` | regenerated identically | met |
| D4 | E1 task 12: re-run from a clean clone, byte-identical numeric outputs | Blueprint §4.1(12) | clean exported-copy test (baseline); this rebuild's fresh-copy rerun on a second OS | `technical/verification/reference/compare/compare_baseline_regen.json` | met-narrowed (source-export copy, not a `git clone`; text/PNG bytes differ by platform, values identical) |
| D5 | E2: 24-cell grid, reference cell fixed before results, S with five stated limitations, determinism control | Blueprint §4.2 | `scripts/run_e2_sensitivity.py`, `configs/e2_sensitivity.yaml` | regenerated identically | met |
| D6 | E2 no-loop blob control at diagnostic cells | Blueprint §4.2 | `results/e2/e2_blob_sanity.json` | — | met |
| D7 | E3: five-task battery, pre-registered expected answers, static stimuli | Blueprint §4.3 | `e3_inspection/` (13 stimuli, scoring key) | stimuli regenerated pixel-identically | met |
| D8 | E3 participant pilot (3–6 classmates) with consent and instructor confirmation | Blueprint §4.3 | **not conducted** (constraint change 2026-10-22) | `e3_inspection/METHODS_NOTE.md` | cut — pre-specified fallback executed (single-observer inspection with AI viewing assistance); never described as a participant study |
| D9 | Metric rules: S never a distance; r_k threshold a convention; attribution levels | Blueprint §6 | `src/similarity.py`, `src/pipeline.py`, Report §4.2 | tests incl. 11 new edge-case tests | met |
| D10 | Real scientific dataset, verification-gated (Decision D) | Blueprint §1.1 | Extension A (NOAA GSOD, Central Park 2019–2024) | raw files byte-identical to fresh NOAA download | met |
| D11 | Optional: GUDHI cross-check of one distance | Blueprint §4.4 | — | — | cut (optional; ripser correctness rests on known-answer signatures and determinism) |
| D12 | Optional: UMAP/t-SNE/PCA comparison | Rev2 R5; Blueprint cut | PCA baseline only | — | cut (documented) |
| D13 | Optional: torus / higher-homology | Blueprint §4.4 | — | — | cut |
| D14 | Performance/scaling micro-benchmark (Rev2 E4) | Rev2 §10.6 | reduced to reported runtimes | per-run timings in results | cut (blueprint: "no scaling campaign") |
| D15 | Rev2 E2 "comparative structure visibility on benchmark data" (digits) | Rev2 §10.4 | — | — | cut (documented in blueprint Table 2) |
| D16 | ENSO as descriptive exhibit with power statement, no test | Rev2 | Extension A phase labels | `weather.yaml` power_statement | met (context only; ONI source stated) |
| D17 | Five-minute cut of the presentation | Blueprint §10.2 | Slides 1, 2, 5, 6, 9, 12, 14 | — | met |
| D18 | Twelve likely Q&A questions with evidence locations | Blueprint §14 | `QA_Preparation.*` (25 questions) | — | met |
| D19 | Report structure of 13 chapters following the assignment | Blueprint §10.1 | Report has 14 chapters + 2 appendices (merged baseline + extensions + audit) | — | met-narrowed (structure adapted because the extensions and audit are part of the project) |

## C. Extensions and rebuild-specific requirements

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| X1 | Extension A: provenance, preprocessing, six seasonal configurations, static cloud, post-hoc seasonality, LOYO | `extensions/meteorology/`, `extensions/stability/` | regenerated; independent parse of raw data; auditor's recomputation | met-narrowed (see Report §6, §8.4, §10.3 corrections) |
| X2 | Extension B: self-contained offline explorer; cold-cache offline test; metadata, exports | `extensions/mapper_explorer/` | `technical/verification/explorer_offline_test.py`: 222/222 (`reference/explorer_offline_test/`) | met; 3 defects fixed |
| X3 | Extension C: 30 × 80 % subsamples, PH + Mapper on the same indices, LOYO | `extensions/stability/` | seed rule verified for all 90 index sets | met-narrowed |
| X4 | Prior-art statements precise (no "first", "novel") | Report §3.2, §7.3 | `technical/verification/research_ledger.md` | met |
| X5 | Independent clean-environment rebuild, same pins, documented | `technical/verification/env/` | Python 3.12.13, pins from `requirements.txt`, freeze | added |
| X6 | Targeted tests for uncovered methods/edge cases | `tests/test_audit_edge_cases.py`, `extensions/controls/tests/` | pytest logs | added |
| X7 | Portable evidence verifier run from outside the repository | `technical/verification/verify_evidence.py` | `technical/verification/reference/evidence_verification.json` | added |
| X8 | Claims register with stable IDs | `technical/verification/claims_register.json` | — | added |
| X9 | Controls where the audit found a confound (clusterer; null; independent draws; ceilings) | `extensions/controls/` | D1–D5 results | added |
| X10 | Single canonical source for the report (no divergent "canonical" copies) | Markdown → DOCX by script → PDF by Word | `report/build_report_docx.py` | added |
| X11 | Baseline preservation: 145-file manifest | `technical/scikit-tda-trust/extensions/BASELINE_MANIFEST.json` (byte-identical to the original); `extensions/BASELINE_RELEASE_EXCLUSIONS.json`; `technical/verification/reference/test_run/baseline_manifest_after_tests.log` | original archive: 145/145 byte-identical under the original verifier. This repository: 128/145 present and byte-identical; 17 intentionally not distributed (16 original course report/slide files and generators, and the original `.gitignore`), each declared with hash and reason | met for the 128 distributed files; the 17 are not verifiable here by design |
