# E3 Methods Note — Why the Single-Observer Fallback Was Used

## Decision and reason

Experiment 3 was designed (blueprint Section 4.3) as a small exploratory
classroom pilot: 3–6 classmates answering a five-task battery on neutral-ID
stimuli, with descriptive statistics only, behind an instructor-approval
gate. **That participant study was not conducted.** A project constraint
change (2026-10-22) made any volunteer or participant study impossible —
no recruitment, no participant contact, and no collection of participant
responses could occur. No participants were recruited, approached, or
observed; no participant data exist; no instructor approval was requested
or granted, and none is required for an artifact inspection that involves
no human subjects.

The blueprint pre-specified a fallback for exactly this situation
(Section 4.3, "Fallback"): the author performs the same task battery on
the same stimuli, recording answers and reasoning against the
pre-specified expected answers, and the report labels the result a
*structured task-based inspection by a single observer*. That fallback —
not a simulation or imitation of the abandoned study — is what was
executed, using the same 13 stimuli, the same five tasks, and the same
pre-specified expected properties prepared in Phase 2.

## What was actually done

- The 13 neutral-ID stimuli, the internal scoring key, and the blank
  worksheet were regenerated deterministically from saved results
  (`scripts/run_e3_readability.py`; identical seeds and sources as the
  Phase-2 pre-specification, so the ID mapping is unchanged).
- The author inspected the stimuli in one pass, in the fixed documented
  order S01–S13, completing the structured worksheet
  (`inspection_record.csv`) field by field: visible cues, the final interpretation,
  assessment category, match of the final interpretation to the expected
  property, misleading cues, evidence files, and limitations.
- Viewing was assisted by an AI vision model used as a
  viewing/description aid with neutral prompts (no dataset names, no
  method names, no expected answers). The unprimed first reading of each
  stimulus was recorded as evidence of what the rendering itself
  communicates; the final interpretation recorded is the author's
  judgment.
- The completed record was validated and summarized by
  `scripts/analyze_e3_inspection.py`
  (`results/e3/inspection_summary.{json,md}`), which fails loudly on any
  incomplete or inconsistent record and computes descriptive counts only.
- No participant order manifests, response sheets, or volunteer records
  were created for the inspection; the Phase-2 participant materials
  (six unused response sheets and the order manifest) were removed from
  the repository when the study was abandoned, and the analysis path that
  scored participant responses (`scripts/analyze_e3_responses.py`) was
  replaced by the inspection analyzer.

## What the evidence can and cannot support

**Can.** Statements about the produced artifacts: which structural
properties the renderings make visible, which are ambiguous or misleading,
how native and component-separated layouts differ, and how parameter
sensitivity (E2) and rendering choices (E1) create interpretation
ambiguities — all grounded in the recorded worksheet, the saved numerical
results, and the measured layout statistics.

**Cannot.** Statements about viewers in general: no measured human
accuracy, no population-level readability, no significance claims, no
confidence or timing distributions. The one recorded divergence between
an unprimed reading and the expected property (S08: the figure-eight
diagram count) is reported as a rendering-communication observation, not
as an error rate.

## Acknowledged limitations

1. **Single observer.** All interpretations are one reader's judgments;
   there is no inter-reader agreement and no dispersion estimate.
2. **Invested author.** The observer designed the datasets, wrote the
   pipeline, and had seen the E1/E2 computational results before the
   inspection; observer bias and retrospective interpretation are
   possible. The pre-specification of expected properties (before any
   inspection record existed) limits, but does not eliminate, this bias.
3. **No blinding claimed.** The author knew the constructions; the
   neutral-ID stimuli and neutral viewing prompts discipline the
   *recording* of unprimed readings but do not make the study blinded.
4. **AI viewing aid.** The images were viewed through an AI vision model;
   its descriptions are a viewing aid, not an independent observer, and
   its readings are treated as recorded evidence about the artifacts, not
   as human-response data.
5. **Task-specific judgments.** The five tasks expose different
   properties; no cross-task aggregate readability score is computed.

A larger human-readability study (multiple naive participants,
counterbalanced orders, preregistered analysis) remains a worthwhile
future extension; it is described in the report as future work only, not
as part of this completed project.
