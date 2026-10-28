# IMPLEMENTATION NOTES — Scikit-TDA Evaluation Project

Implementation-critical decisions, deviations, and completion tests for
*When Can You Trust a Topological Visualization? A Task-Based Evaluation of
the Scikit-TDA Ecosystem.* This file records ONLY what an implementer or
reviewer needs that is not already in the blueprint
(`../download/ScikitTDA_Final_Project_Blueprint.md`): methodological
corrections, deviations with justifications, and the tests that demonstrate
completion. It is not a restatement of the research plan.

---

## 1. Platform inspection (Phase 0, executed 2026-10-21)

| Item | Observed state |
|---|---|
| Host OS | Linux x86_64 (kernel 5.10) — same platform class as the blueprint's verification (Linux, Python 3.12.15) |
| Python | 3.12.15 at `python3.12` (matches the blueprint pin) |
| Git repo | `/home/z/my-project`, branch `main`, 3 commits |
| Uncommitted changes | 16 modified files under `assets/smoke/` (regenerated smoke-test artifacts from the 2026-10-21 blueprint verification). **Left untouched.** No commits, pushes, or history rewrites are performed (per instruction). |
| Project root | This directory, `scikit-tda-trust/`, created fresh; nothing outside it was modified except this file's parent workspace notes |
| Network | pip index reachable; fresh `.venv` installed from the pinned `requirements.txt` with all pins resolving exactly |
| Prior environment | `scripts/tda-venv` (workspace) holds the same pinned versions and was used only for Phase 0 probes; the project itself uses its own `.venv` |

---

## 2. Methodological resolutions (required before implementing)

### R-1. Generalized persistence-gap ratio

**Problem.** The blueprint's top-1/top-2 ratio describes the annulus (one
dominant loop) but is the *wrong statistic* for the figure-eight, whose two
leading H1 classes are approximately equal **by construction** (verified
top-3 persistences 0.481 / 0.481 / 0.049, so top1/top2 ≈ 1.00).

**Resolution.** The implemented metric is the general gap ratio

  r_k = p_k / p_{k+1},  with p_1 ≥ p_2 ≥ ... (persistences sorted descending),

evaluated at the **known ground-truth rank** of each synthetic dataset:

| Dataset | Ground-truth rank k | Reading | Why the rank is known |
|---|---|---|---|
| Annulus | 1 | r_1 ≫ 1 separates the single loop from noise | Construction: one circular band |
| Figure-eight | 2 | r_2 ≫ 1 separates the two loops from noise (r_1 ≈ 1 is expected, not a failure) | Construction: two loops of equal size |
| No-loop blob | none | no rank is meaningful; r_1 is reported only as a calibration value | Construction: isotropic Gaussian, no loop |
| Three-blob | none for H1 (component structure is read from H0 finite persistences) | | Construction: three separated Gaussians |

**Mandatory wording** (carried in code docstrings, configs, results JSON, and
report text): *the rank is known from the synthetic construction of each
dataset; r_k is not a universal automatic loop-counting rule.* The
"prominent loop" threshold (r_k ≥ 3) is a stated convention, not a theorem.

### R-2. Mapper similarity score → exploratory membership-overlap indicator

**Problem.** The blueprint defined S and asserted "S = 1 exactly when the two
node sets are identical." That assertion is **incorrect**: S = 1 whenever
every *distinct* node-membership set of one graph appears as a node-membership
set of the other, even when node counts differ (duplicated memberships) and
when edges differ. Verified counterexample: nodes [{1,2,3,4}, {1,2,3,4},
{5,6}] vs [{1,2,3,4}, {5,6}] score S = 1.0 with 3 vs 2 nodes.

**Resolution.** `src/similarity.py` implements S with the corrected
characterization and the following enforced properties (unit-tested):

1. **Corrected S = 1 condition.** S(G1, G2) = 1 if and only if the two graphs
   have the same *set of distinct node-membership sets*. Consequences: node
   multiplicities and edge structure are invisible to S; identical membership
   sets guarantee S = 1, but S = 1 does not imply identical graphs.
2. **Symmetric and bounded:** S(G1,G2) = S(G2,G1) ∈ [0, 1]; S(G,G) = 1.
3. **Not a metric.** 1 − S violates the triangle inequality. Verified
   counterexample (unit-tested with exact expected values):
   A = [{1,2,3}], B = [{1,2,3},{4,5,6}], C = [{4,5,6}] gives
   d(A,C) = 1.0 > d(A,B) + d(B,C) = 0.5. Never describe S as a distance.
4. **Edge-blind.** S is a function of node memberships only; edges,
   components, and representative graphs are always reported alongside.
5. **Greedy matching.** Best-match per node, not optimal assignment — S can
   understate similarity.
6. **No node-count normalization.** S must not be used to rank graphs across
   different cover resolutions (different n_cubes produce systematically
   different node granularities).

**Role in conclusions.** E2 sensitivity conclusions rest *primarily* on:
(a) saved per-cell numerical outputs (node/edge/component counts and the
clearly defined graph-structure statistics below), (b) connected-component
counts, (c) representative visual panels. S is reported as a *custom
exploratory overlap indicator* relative to the pre-specified reference cell,
with its limitations printed beside it.

**Graph-structure statistics** (clearly defined, per cell):
`n_nodes`, `n_edges`, `n_components` (networkx connected components),
`cyclomatic_number` = E − V + C (number of independent cycles),
`max_basis_cycle_length` / `mean_basis_cycle_length` (lengths of the cycles
in a cycle basis, `networkx.cycle_basis`).

**Mandatory wording** wherever cycles are discussed: *Mapper graph cycles are
not automatically equivalent to true topological loops in the data* — the
no-loop blob produces short noise-scale graph cycles while its H1 diagram
correctly shows no dominant class. Long, data-scale cycles (e.g., the annulus
reference cell's ~16-node basis cycle) are the loop-like signal; length and
context distinguish them.

### R-3. Readability experiment (E3) — design corrections; single-observer fallback ACTIVATED in Phase 3

1. **RQ/task agreement.** The research question and the task table must agree
   word-for-word on what is asked. Each task states whether it is
   *task-specific* (one representation, measuring that representation) or a
   *matched representation comparison* (same structural question, same data,
   multiple representations). Judgments from different tasks are never
   compared as if the tasks were equivalent.
2. **Order.** For the participant design, task/stimulus order was to be
   counterbalanced or randomized and recorded. **Superseded in Phase 3**
   (fallback activated): a single observer inspects in the FIXED documented
   order S01–S13; no randomization, no order manifest (nothing may imitate
   the abandoned study).
3. **Participant-facing / recorded materials** contain no dataset identities
   ("annulus", "figure-eight", …), no expected answers, and no method names
   that leak answers (neutral stimulus IDs S01…S13).
4. **Descriptive categories, not accuracy.** Single-observer judgments are
   recorded as transparent categories (clearly_apparent / ambiguous /
   visually_obscured / not_represented) plus a yes/no/partial match of the final
   interpretation to the pre-specified expected property. Any count states exactly what was
   counted and that it is a single-observer inspection result, never
   measured human accuracy. No significance claims, no confidence
   distributions, no timing.
5. **Participant study NOT conducted.** A project constraint change
   (2026-10-22) made any volunteer/participant study impossible. The
   classroom pilot was abandoned before any recruitment, contact, or data
   collection occurred; no participant data exist; no approval was
   requested or granted (none is needed for an artifact inspection). E3 is
   executed exclusively as the blueprint's pre-specified fallback:
   `e3_inspection/PROTOCOL.md` (executed protocol) and
   `e3_inspection/METHODS_NOTE.md` (why the fallback; observer-bias
   acknowledgment: the author designed the datasets and had seen E1/E2
   results — bias and retrospective interpretation are possible; expected
   properties were pre-specified in Phase 2, which limits but does not
   eliminate bias; no blinding is claimed; the AI viewing aid is
   disclosed).

### R-4. Day-3 MVP milestone — technical viability only

The MVP (this phase) is a **technical viability checkpoint**: pinned
environment, generators with tests, the E1 demonstration pipeline with an
initial capability matrix, and the E2 grid on at least one shape with a
stable-vs-unstable contrast. It does **not** by itself satisfy the final
submission requirements. Final acceptance additionally requires: the report,
evidence-linked findings, advantages/disadvantages, research gaps,
limitations, reproducibility instructions, and presentation + Q&A preparation.

---

## 3. Deviations from the blueprint (with justifications)

| ID | Deviation | Justification |
|---|---|---|
| D-1 | `requirements.txt` adds `pyyaml==6.0.3` | Blueprint Section 9 mandates YAML configs; no installed dependency provides a YAML parser. Minimal correction, pin kept exact. |
| D-2 | `requirements-dev.txt` adds `pytest==8.4.2` (dev-only) | Blueprint mandates `tests/` but names no runner; pytest is not imported by runtime code. |
| D-3 | Project lives at `/home/z/my-project/scikit-tda-trust/` inside the existing planning workspace | Keeps the blueprint's repository layout intact while not touching the workspace's unrelated tracked files. No git operations performed (per instruction, no commits without approval). |
| D-4 | This file (`IMPLEMENTATION_NOTES.md`) exists at the repo root | Explicitly requested by the implementation instruction; not in the blueprint's tree. |
| D-5 | `configs/e3_readability.yaml`, E3 materials, `report/`, `presentation/` deferred to Phase 3+ | Phase-1 scope is the MVP only; creating E3 participant materials before the approval gate and corrected design review would be premature. The corrected E3 design is pre-specified in R-3 above. (Phase 2 created the participant materials; Phase 3 replaced them with the inspection materials — see D-11/D-12 — and added `report/` and `presentation/`.) |
| D-6 | E2 results store per-cell node memberships and links in the results JSON | Required by the engineering rule "re-render figures from saved results" — representative Mapper panels must render without recomputation. |
| D-7 | `Makefile` target `e3` exits with an error message | The blueprint's target set includes e3, but the runner does not exist until Phase 3; failing loudly beats silently pretending. **Superseded in Phase 2** (materials generation) and **Phase 3** (single-observer inspection materials: stimuli, internal key, blank worksheet; `make e3-analysis` validates and summarizes the authored record). |
| D-8 | Phase 2: clean-copy test uses an rsync export, not `git clone` | Git commits are not permitted in this workspace, so a clone would only contain the last commit, not the current source state. The instruction explicitly allows "a clean clone or clean exported copy"; the export excludes only `.venv`, `__pycache__`, `.pytest_cache`, `*.pyc`, and the live test log. Recorded in `scripts/clean_clone_test.sh`. |
| D-9 | Phase 2: figure-eight E2 contrast cell (20, 0.50) selected after measuring the grid | Chosen to display the construction-consistent reading (connected, two 20-node basis cycles) against the fragmented reference cell. An honest post-hoc PRESENTATION choice, labeled as such in `configs/e2_sensitivity.yaml`; all 24 cells are reported in the summary figure and CSV. |
| D-10 | Phase 2: E3 mapper stimuli use the custom component-separated layout | The native kk layout overlaps disconnected components (measured; see R-6), which would confound graph-reading with layout-failure recovery. The rendering choice is recorded in `configs/e3_readability.yaml` and the stimulus manifest; E1 documents the native layout limits separately. In Phase 3 the native-vs-separated contrast is additionally examined inside the inspection as a *rendering-choice ambiguity* (recorded in the inspection record's misleading-cues fields). |
| D-11 | Phase 3: participant study abandoned; `pilot/` restructured to `e3_inspection/` | A project constraint change (2026-10-22) made any participant study impossible. The six unused response sheets, the order manifest, and the digitization template were REMOVED (nothing may remain that imitates the abandoned study); the directory now holds the inspection protocol, methods note, neutral-ID stimuli, internal key, blank worksheet, and the AUTHORED completed record `inspection_record.csv`. |
| D-12 | Phase 3: `scripts/analyze_e3_responses.py` (participant-response analyzer, approval-gated) replaced by `scripts/analyze_e3_inspection.py` | No participant responses exist or can exist; an accuracy-scoring analyzer for participant data would be dead code inviting misuse. The replacement validates the completed single-observer record (schema, completeness, evidence-path existence) and summarizes descriptive category counts — it computes no accuracy metrics and needs no approval gate. |

No other methodology changes were introduced. The gap-ratio and similarity
corrections (R-1, R-2) were mandated by the implementation instruction;
the E3 order rule evolved as documented in R-3 (participant-design
randomization pre-specified in Phase 2; fixed-order single-observer
inspection in Phase 3 after the participant study was abandoned).

---

## 3a. Phase-2 findings and fixes (executed 2026-10-22)

### R-5. Offline browser test — EXECUTED (no longer "untested")

A genuine browser-level offline test was performed with agent-browser 0.39.0
(headless Playwright Chromium): online baseline (graph renders: 20 node
groups + 21 edge lines; D3/FileSaver/fonts load; imgur favicon rate-limited
HTTP 429 even online), then a **cold-cache offline test** (fresh session,
offline enabled BEFORE navigation): D3 fails to load, **0 nodes / 0 edges
rendered** — only inline static text remains. A warm-cache reload still
renders (cache masks the dependency) — recorded as a caveat, not accepted
as the offline result. Evidence: `results/e1/offline_browser_test.json`,
screenshots `results/e1/browser_test/{online,offline_cold}.png`, inventory
`audit/html_resource_inventory.md`. The imgur URL is the FAVICON (the page
logo is inline base64 — a correction to the Phase-1 note that called it
"an imgur logo").

### R-6. Native static Mapper layout overlaps disconnected components (confirmed)

Hypothesis from another implementation, investigated here from our own
repository and CONFIRMED with quantitative and visual evidence:
* `km.draw_matplotlib(layout='kk')` computes ONE `nx.kamada_kawai_layout`
  for the whole graph — no inter-component repulsion — and draws uniform
  node sizes.
* Measured on the reference-cell graphs (`results/e1/layout_overlap.json`):
  figure-eight (2 components): bbox IoU 0.036, 6.7% of inter-component node
  pairs closer than the median intra-component nearest-neighbour distance;
  three-blobs (3 components): bbox IoU **0.233**, 14.4% interleaving.
  Single-component shapes (annulus, blob): 0 by definition.
* Visual confirmation (VLM check of the rendered figures): the figure-eight
  and three-blobs components are not clearly distinguishable natively and
  clearly separated in the custom rendering.
* **Alternative renderer provided** (smallest reasonable custom code):
  `figures.component_separated_layout` — per-component seeded spring
  layouts translated to disjoint horizontal bands, node area proportional
  to membership, per-component colors. **The graph structure is untouched**
  (nodes/edges/components identical); this is a rendering-capability
  finding, not a change to Mapper's mathematical output. Side-by-side
  figures: `figures/e1/*_readability_native_vs_separated.png` and
  `figures/e2/e2_readability_*.png`; the renderer used is documented in
  every caption and in `src/figures.py` (NATIVE_RENDERER / CUSTOM_RENDERER).

### R-7. Cross-process layout non-determinism — defect found by the clean-copy test, fixed

The first clean-copy comparison found 3 of 32 figures differing pixel-wise —
exactly those rendering multi-component graphs with the CUSTOM layout.
Root cause: `networkx`'s subgraph view iterates its node FILTER SET when
`2*len(component) < len(graph)`; a Python set of string node names has
process-dependent order (hash randomization), so the per-component
`spring_layout(sub, seed=42)` consumed its randomness in a different node
order per process. (The native kk layout and full-graph spring layouts are
unaffected — verified by digest probes.) Fix: rebuild each component
subgraph with an explicitly sorted node order and sort components by
(-size, sorted names). Regression test:
`tests/test_outputs.py::test_component_layout_process_deterministic` runs
the layout in two subprocesses with different `PYTHONHASHSEED` values and
requires identical output. After the fix, the clean-copy test reports
**32/32 figures pixel-identical**.

### R-8. Clean-copy / fresh-environment test — PASSED (re-run on the Phase-3 state)

`scripts/clean_clone_test.sh` (logged in
`results/repro/clean_clone_test.log`, report in
`results/repro/comparison_report.json`): rsync export of the current source
state (D-8 — a clean EXPORTED SOURCE COPY, not a git clone; the summary and
the log state this explicitly) → fresh Python 3.12.15 venv → pinned install
→ verify (38/38) → tests (60/60) → E1 → E2 (24 cells + sanity) → figures
→ E3 materials regeneration → E3 inspection-record analysis (the AUTHORED
record rides along verbatim; the analyzer only validates and summarizes it)
→ comparison against the reference run. Result: **26/26 structural
artifacts identical** (point clouds, ripser diagrams, memberships, e1/e2
JSONs with only whitelisted environment-dependent timing fields excluded,
E2 CSV except `time_s`, HTML byte-identical, glue accounting, E3 manifest
except `generated_utc`, E3 key/worksheet, E3 inspection summary) and
**45/45 PNG figures pixel-identical** (32 report figures + 13 E3 stimuli).
Wall-clock timings are the only environment-dependent outputs. Native
Windows remains untested (no claim made).

---

## 3b. Phase-3 execution (2026-10-22): E3 as the single-observer inspection

### R-9. E3 executed — participant study NOT conducted; fallback activated

Executed exactly as pre-specified (blueprint 4.3 fallback; R-3 above;
`e3_inspection/PROTOCOL.md`, `e3_inspection/METHODS_NOTE.md`):

- Materials regenerated deterministically from saved results (same seeds,
  same 13 neutral-ID stimuli and pre-specified expected properties as the
  Phase-2 pre-specification). Participant materials (6 unused response
  sheets, order manifest, digitization template) removed; participant-response
  analyzer replaced by the inspection analyzer (D-11, D-12).
- The inspection was performed in ONE pass, fixed order S01–S13, by the
  project author, with an AI vision model as a disclosed viewing aid using
  neutral prompts (no dataset/method names, no expected answers); the
  unprimed first reading of each stimulus is recorded evidence of what the
  rendering communicates.
- The completed record (`e3_inspection/inspection_record.csv`, AUTHORED,
  never script-written) passed validation: 13/13 rows complete, categories
  valid, every evidence path exists. Summary:
  `results/e3/inspection_summary.{json,md}`.
- **Recorded inspection results (single-observer judgments, not human
  accuracy):** 11 of 13 properties clearly_apparent, 2 ambiguous, 0
  visually_obscured, 0 not_represented; matches (scoring the final interpretations) to
  pre-specified expected properties: 12 yes, 1 partial (S11), 0 no. The two ambiguous cases are
  the substantive findings: (a) **S08** — the figure-eight diagram's loop
  count hinges on the unlabeled H0/H1 color convention; the essential-class
  point is drawn FARTHER from the diagonal than either co-dominant loop
  point, and the unprimed reading answered 1 instead of 2; (b) **S11** —
  the no-loop blob's Mapper graph reads as "a large ring-like cycle"
  because noise-scale cycles (basis length 6) are visually
  indistinguishable from data-scale loops (16), exactly the E2
  cycles-vs-loops trap. Scatter reference views (T5) were uniformly clear.
  Mapper morphology readings carry parameter-dependence (E2) and
  layout-dependence (native kk overlap; the inspected stimuli use the
  documented component-separated rendering) caveats in the record.
- Reporting discipline enforced everywhere: no participant data, no
  accuracy percentages, no significance claims, no confidence/timing
  distributions; counts are labeled single-observer inspection results;
  computational metrics and inspection judgments are kept distinct.

---

## 4. Tests that demonstrate completion

All under `tests/`, run with `make test` (or `.venv/bin/python -m pytest`):

| Test module | Demonstrates |
|---|---|
| `test_shapes.py` | Generator determinism (same seed → byte-identical arrays; different seed → different), array validity, parameter plumbing from config |
| `test_metrics.py` | Gap ratio r_k: correct values on known vectors, descending sort, tie behavior (figure-eight regime r_1 = 1), edge cases (empty, single class, zero persistence), None at insufficient rank |
| `test_similarity.py` | S: symmetry, bounds, identity; corrected S=1 condition incl. duplicate-membership counterexample (3 vs 2 nodes, S = 1); edge-blindness; triangle-inequality counterexample for 1−S with exact expected values; empty-graph conventions |
| `test_signatures.py` | Qualitative ground-truth checks on the four shapes at headline parameters, with tolerances (annulus r_1 > 5; figure-eight r_2 > 3 and r_1 < 2; blob r_1 < 3; three-blob H0 prominent merges = 2, small H1) — robust properties, not brittle exact floats; ripser determinism on fixed input |
| `test_outputs.py` | Output validity of the result machinery: mini-grid run through the same code path as `run_e2_sensitivity.py` into a temp dir, then schema/column/cell-count/JSON-validity checks; figure renderers incl. the readability comparison; component-separated layout separation + structure preservation; **cross-process layout determinism (PYTHONHASHSEED regression test, R-7)**; per-shape contrast resolution; real-artifact checks for E1/E2 (24 cells, both shapes), the blob sanity control, layout-overlap statistics, and glue-code reproducibility; capability-matrix schema with honest statuses and the T12 evidence consistency check. Skips cleanly with a clear message if real `results/` are absent |
| `test_e3_inspection.py` | The E3 single-observer pipeline: the analyzer's validation logic on synthetic records in a temp dir (accepts complete records; rejects incomplete, duplicate, illegal-category, and bad-evidence-path records; no accuracy-style metric fields in the summary; honest labeling); real-artifact checks (13/13 record validates, summary consistent with the record, PROTOCOL/METHODS_NOTE present with the not-conducted + bias statements) and **the no-participant-artifacts check** (`pilot/` gone; no response sheets, order manifest, digitization template, or participant-response analyzer remain) |

Ground truth (tests) and measured outputs (scripts) are strictly separated:
result-generation code contains no expected-outcome assertions; tests assert
robust properties with margins.

---

## 5. Phase status

- Phase 0 — complete (this file; platform inspection; probes of persim API,
  similarity properties, kmapper graph structure, HTML CDN dependency).
- Phase 1 (MVP) — complete and verified by execution (2026-10-21):
  `make all` runs verify (38/38 checks) → E1 (4 shapes, 13-task initial
  capability matrix, determinism + tadasets cross-check all green) → E2
  (12-cell annulus grid, determinism control identical) → figures (rendered
  from saved results) → tests (45/45 passed, 3.8 s). Real measured anchors:
  annulus r_1 = 19.345; figure-eight r_1 = 1.001 / r_2 = 9.747; blob
  r_1 = 1.451; three-blobs = 3 Mapper components; similarity range across
  the annulus grid 0.449–1.000; only cell (20, 0.20) fragments (2
  components). Bugs found and fixed during the run are recorded in the
  worklog (config-metadata leak into generator kwargs; persim 0.4.1
  matching-return shape; CDN regex quote handling; figure output path).
- Phase 2 — **complete and verified by execution (2026-10-22)**:
  - E2 full 24-cell grid (annulus + figure-eight, 12 cells each) + no-loop
    blob sanity control at two diagnostic settings; per-cell memberships
    stored; cyclomatic number defined in the results metadata;
    interpretation notes with stable/unstable readings
    (`results/e2/e2_interpretation_notes.md`). Headline measured findings:
    figure-eight fragments at the reference cell (2 components) and at
    (20, 0.20) (4 components) but is construction-consistent at (20, 0.50)
    (connected, two 20-node basis cycles); annulus loop signal vanishes at
    n_cubes=5 (tree) and fragments only at (20, 0.20); n_nodes = 2 x n_cubes
    in all 24 cells; blob shows 4 short noise cycles with H1 r_1 = 1.451
    (cycles-vs-loops distinction demonstrated).
  - E1 audit finalized: 13 tasks, all `demonstrated`, 7-column capability
    matrix with honest statuses/limitations, path-verified evidence log,
    reproducible glue-code accounting (130 LOC, documented rule — the mid-phase worklog figure of 127 predated the R-7 layout fix, which added three lines),
    layout-overlap measurement, HTML resource inventory, offline browser
    test EXECUTED (R-5).
  - Readability investigation (R-6): native kk overlap confirmed
    quantitatively + visually; custom component-separated alternative
    renderer provided and documented (structure untouched).
  - Clean-copy/fresh-environment test PASSED (R-8): 22/22 structural
    artifacts identical, 32/32 figures pixel-identical; one reproducibility
    defect found and fixed on the way (R-7).
  - E3 materials ready behind the approval gate (13 neutral-ID stimuli
    rendered from saved results, 6 randomized response sheets, scoring key
    with pre-specified answers + measured anchors, order manifest,
    digitization template, gate-enforcing analysis script). NO participant
    data collected; approval status: `not_requested`. **Historical note:
    all participant-specific materials were removed in Phase 3 when the
    study was abandoned (D-11); the Phase-2 gate design is recorded here
    only as the state of that phase.**
  - Tests: 51/51 pass (5 new Phase-2 tests).
- Phase 3 — **complete and verified by execution (2026-10-22)**:
  - E3 executed as the structured single-observer inspection (R-9, D-11,
    D-12): materials regenerated deterministically; genuine one-pass
    fixed-order inspection recorded and validated (13/13); summary written;
    protocol + methods note authored.
  - Full pipeline re-validated from the current source (verify, tests, E1,
    E2, E3 materials, figures) and the clean-copy / fresh-environment test
    re-run green on the Phase-3 state (see `results/repro/`).
  - Report (13 chapters, .docx + .pdf), presentation (.pptx with speaker
    notes), Q&A preparation document, and the updated assignment checklist
    produced in `report/` and `presentation/`, all consistent with the
    single-observer framing.
  - No git commits, pushes, or publishes were performed.
- Final editorial and consistency pass (2026-10-22, post-delivery cleanup;
  no experimental result changed):
  - Terminology: "pre-registered" -> "pre-specified" everywhere it referred
    to this project's expected properties (no formal, time-stamped
    preregistration occurred); the explicit negations ("not a preregistered
    prospective experiment") and the future-work recommendation ("a larger
    study ... preregistered analysis") were kept. "Committed" -> "saved" /
    "included in the project directory" wherever files were not actually
    committed to git ("commits are not permitted" statements kept).
  - Report precisifications: E3 Table 5's match column now states it scores
    the final recorded interpretation (S08 first-reading miscue preserved);
    the annulus claim is scoped to the Mapper graph's cycle cue (the
    underlying H1 loop persists in the persistence diagram); the E1 summary
    says all thirteen tasks were executed and documented with failures
    retained; cover label "Assignment component"; Appendix B freeze extract
    reformatted (3 aligned columns + platform line). Full re-render with a
    recreated `report/add_toc_placeholders.py` (TOC page numbers filled from
    a pass-1 render; the old PDF's dangling first TOC line is fixed).
  - Validation rerun note: the project `.venv` had been removed from the
    workspace and was rebuilt from the same pinned `requirements.txt` to
    run the final checks (60/60 tests; verify 38/38). The rebuilt
    environment resolved two newer transitive packages (python-dateutil
    3.0.0, tzdata) relative to the original experiment environment;
    `results/env/pip_freeze.txt` was restored to the original 32-entry
    experiment-environment record (E3 stimuli regenerated under the rebuilt
    environment were verified byte-identical, so no output was affected).
    `scripts/verify_report_consistency.py` (25 checks: TOC vs headings,
    report numbers vs saved outputs, terminology sweep, author placeholder)
    passes 25/25.
