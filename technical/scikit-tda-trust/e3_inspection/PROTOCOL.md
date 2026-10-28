# E3 Inspection Protocol — Structured Task-Based Inspection of Visualization Readability

**Status: EXECUTED on 2026-10-22.** This is the protocol of the experiment
that was actually run. The participant study originally planned for E3 was
**not conducted** (see `METHODS_NOTE.md`); this inspection is the blueprint's
pre-specified fallback, executed exactly as described here.

## 1. Research question

*For a predefined set of scientific exploration tasks, what structural
information is visible in Scikit-TDA's persistence diagrams and Mapper
visualizations, and what interpretation ambiguities arise from parameter
sensitivity and rendering choices?*

The question is deliberately answerable by the available evidence: it asks
what the produced artifacts communicate to an inspecting reader and where
interpretation becomes ambiguous — not what a population of viewers would
correctly identify.

## 2. Design

- **Method.** Structured, task-based inspection of rendered artifacts by a
  single observer (the project author), against pre-specified expected
  properties derived from the synthetic data constructions and saved
  computational results (E1/E2).
- **Stimuli.** 13 static PNG images with neutral IDs (S01–S13), rendered
  from SAVED RESULTS ONLY (no recomputation): scatter views from
  `results/e1/data/*.npy`, persistence diagrams from
  `results/e1/*_ph_dgms.npz`, Mapper graphs from
  `results/e1/*_mapper_memberships.json` (reference cover cell). Mapper
  stimuli use the documented component-separated custom layout; the native
  vs. component-separated rendering contrast is examined as a
  *rendering-choice* ambiguity using the E1/E2 side-by-side figures.
- **Task battery (T1–T5, retained from the original design).**
  - T1 (persistence diagram): Does this dataset contain a prominent loop?
  - T2 (persistence diagram): How many prominent loops?
  - T3 (scatter AND Mapper, matched comparison): How many well-separated
    components?
  - T4 (Mapper graph): Which best describes this graph — a large ring-like
    cycle / several disconnected pieces / a dense tangle?
  - T5 (scatter, matched questions): the same structural questions on the
    raw scatter view (known-answer reference view, not a competitor).
- **Expected properties.** Pre-specified from the data construction and
  measured anchors in `results/e1/e1_audit.json` and the E2 grid — never
  from inspection performance. Recorded in the internal
  `scoring_key.csv` / `stimulus_manifest.json` (carried over unchanged from
  the Phase-2 pre-specification).

## 3. Procedure (as actually followed)

1. Generate the materials: `python scripts/run_e3_readability.py`
   (stimuli, internal key, blank worksheet). Verify the completed-record
   path does not yet exist.
2. Inspect the stimuli **in one pass, in the fixed documented order
   S01 → S13**. No randomization is used (a single observer; the fixed
   order is the recorded procedure). For each stimulus, view the rendered
   PNG image and record, in the worksheet row for that stimulus:
   the visible cues, the observer's interpretation, the assessment
   category, whether the interpretation matches the expected property,
   any misleading cues or rendering problems, the supporting evidence
   files, and a concise explanation with limitations.
3. For Mapper stimuli, additionally consult (as context, recorded as
   evidence) the native-vs-component-separated side-by-side figures and
   the measured layout-overlap statistics, so that *graph structure*,
   *rendering*, and *parameter dependence* are kept distinct in the
   record.
4. Save the completed worksheet as `inspection_record.csv` (authored
   document; scripts never write it).
5. Validate and summarize:
   `python scripts/analyze_e3_inspection.py` — which fails loudly on any
   incomplete or inconsistent record and writes
   `results/e3/inspection_summary.{json,md}`.

**Viewing aid disclosure.** The stimuli were viewed as static PNG files
with the assistance of an AI vision model used as a viewing/description
aid; the recorded interpretation, cues, and category assignments are the
observer's own judgments. The viewing pass was conducted with neutral
prompts that contained no dataset names, no method names, and no expected
answers, so that the unprimed first reading of each stimulus is itself
recorded evidence of what the rendering communicates.

## 4. Recorded fields (one worksheet row per stimulus)

1. `task_id` and `stimulus_id`
2. `question` — the question being investigated
3. `expected_property` — from the synthetic construction or saved
   computational result (pre-specified)
4. `visible_cues` — the cues supporting the interpretation
5. `observer_interpretation` — the observer's recorded interpretation
6. `assessment` — one of the descriptive categories below
7. `matches_expected` — yes / no / partial (scores the final recorded
   interpretation, not the unprimed first reading)
8. `misleading_cues` — misleading cues or rendering problems (may be
   "none material")
9. `evidence_files` — repository paths supporting the assessment
10. `explanation_and_limitation` — concise explanation and limitation

## 5. Assessment categories (transparent descriptive categories — not metrics)

- **clearly_apparent** — the expected property is visible with ordinary
  care; the supporting cues dominate.
- **ambiguous** — cues point in more than one direction, or the property
  is visible only with substantial prior knowledge or inference; a
  different reasonable reader could disagree.
- **visually_obscured** — the property is present in the underlying
  computation but the rendering makes it hard or impossible to see.
- **not_represented** — the representation does not encode the property
  at all.

## 6. Standing interpretation rules

- **Keep the layers distinct.** The underlying dataset structure (the
  construction), the persistence-diagram evidence, the Mapper graph
  structure (a computational fact of its parameter cell), and the visual
  rendering are recorded separately and never conflated.
- **A Mapper graph cycle is not automatically a topological loop in the
  data.** The no-loop blob control produces short noise-scale graph
  cycles while its H1 diagram correctly shows no dominant class; cycle
  length and scale context distinguish the cases (E2 sanity finding).
- **No universal score across representations.** Persistence diagrams,
  Mapper graphs, and scatter plots expose different properties; judgments
  from different tasks are never merged into one readability score.
- **Counts are defined when reported.** Any count states exactly what was
  counted and whether it is a computational metric (from saved results)
  or a single-observer inspection result (a recorded judgment).

## 7. Honesty rules (binding)

- The inspection is **not** a blinded study and **not** a preregistered
  prospective experiment; it is a retrospective, single-observer,
  structured artifact inspection. Observer bias is acknowledged in every
  summary that uses its results.
- No participant accuracy, population-level readability, statistical
  significance, confidence-rating distributions, or response-time claims
  may be derived from this experiment.
- Subjective judgments are reported with the descriptive categories
  above, never as objective metrics.
- The output is labeled everywhere as a *structured task-based inspection
  by a single observer* — never as a human-participant study.
