#!/usr/bin/env python3
"""Experiment 3 — structured single-observer inspection MATERIALS generation.

The participant study was NOT conducted (project constraint change,
2026-10-22); E3 is executed exclusively as the blueprint's pre-specified
fallback: a structured task-based inspection by a single observer. This
script generates, from SAVED RESULTS ONLY (no recomputation):

  e3_inspection/stimuli/S01.png ...          — static stimuli, NEUTRAL IDs
  e3_inspection/stimulus_manifest.json       — INTERNAL: ID -> source/property/basis
  e3_inspection/scoring_key.csv              — INTERNAL: expected properties + basis
  e3_inspection/inspection_worksheet_BLANK.csv — structured worksheet
                                                (observer fields left blank)

Authored (NOT generated) companion documents, maintained by hand:
  e3_inspection/PROTOCOL.md        — the explicit inspection protocol
  e3_inspection/METHODS_NOTE.md    — why the single-observer fallback was used
  e3_inspection/inspection_record.csv — the COMPLETED record of the actual
                                        single-observer inspection

This script NEVER collects, simulates, or fabricates observations. It refuses
to overwrite a completed inspection record (it does not write that file at
all). Validation and summarization of the completed record is
scripts/analyze_e3_inspection.py.

Expected properties are PRE-REGISTERED from the data construction and cite
measured anchors from saved results (results/e1/e1_audit.json, E2 grid) —
never from inspection performance.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from figures import _draw_mapper_component_separated  # noqa: E402

# ---------------------------------------------------------------- ground truth
# PRE-REGISTERED expected properties, from the CONSTRUCTION of each dataset
# (blueprint Table 4.3; R-1/R-3 in IMPLEMENTATION_NOTES.md). The 'basis'
# strings cite measured anchors that are filled in from saved results at
# generation time. These properties are NOT derived from inspection data.
EXPECTED = {
    ("T1", "annulus"): ("Yes", "construction: one circular band; "
                        "anchor: annulus H1 top persistence + r_1 from "
                        "results/e1/e1_audit.json"),
    ("T1", "blob"): ("No", "construction: isotropic Gaussian; "
                     "anchor: blob r_1 calibration from e1_audit.json"),
    ("T2", "annulus"): ("1", "construction: one loop; anchor: H1 gap at rank 1"),
    ("T2", "figure_eight"): ("2", "construction: two co-dominant loops; "
                             "anchor: top two persistences ~equal, r_2 gap"),
    ("T3", "three_blobs"): ("3", "construction: three separated Gaussians; "
                            "anchor: H0 two late merges + essential class; "
                            "Mapper reference cell components from "
                            "e1_audit.json"),
    ("T4", "annulus"): ("a large ring-like cycle",
                        "E2 reference cell: connected, long basis cycle; "
                        "PARAMETER-DEPENDENT caveat from E2 grid"),
    ("T4", "figure_eight"): ("several disconnected pieces",
                             "E2 reference cell: 2 components — the expected "
                             "label is EXPLICITLY parameter-dependent (E2 "
                             "finding: other cells are connected)"),
    ("T4", "blob"): ("a dense tangle", "E1: noise-scale short cycles"),
    ("T5", "annulus"): ("Yes", "T1 question on the scatter; scatter IS the "
                        "2-D data (known-answer reference view)"),
    ("T5", "figure_eight"): ("2", "T2 question on the scatter"),
    ("T5", "blob"): ("No", "T1 question on the scatter"),
    ("T5", "three_blobs"): ("3", "T3 question on the scatter"),
}

T5_QUESTION_BY_SHAPE = {
    "annulus": "Does this dataset contain a prominent loop? Yes / No.",
    "figure_eight": "How many prominent loops does this dataset contain?",
    "blob": "Does this dataset contain a prominent loop? Yes / No.",
    "three_blobs": "How many well-separated components does this dataset "
                   "contain?",
}

TASK_STATEMENTS = {
    "T1": "Does this dataset contain a prominent loop? Yes / No.",
    "T2": "How many prominent loops does this dataset contain?",
    "T3": "How many well-separated components does this dataset contain?",
    "T4": "Which best describes this graph: a large ring-like cycle / "
          "several disconnected pieces / a dense tangle?",
    "T5": "(matched question — see worksheet)",
}

RECORD_COLUMNS = [
    "task_id", "stimulus_id", "question", "expected_property", "visible_cues",
    "observer_interpretation", "assessment", "matches_expected",
    "misleading_cues", "evidence_files", "explanation_and_limitation",
]


def die(msg: str) -> None:
    print(f"ERROR [run_e3_readability]: {msg}", file=sys.stderr)
    sys.exit(1)


def load_yaml(path: Path) -> dict:
    if not path.exists():
        die(f"config not found: {path}")
    with open(path) as fh:
        return yaml.safe_load(fh)


def render_scatter_stimulus(X: np.ndarray, path: Path, dpi: int,
                            figsize: tuple) -> None:
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    ax.scatter(X[:, 0], X[:, 1], s=8, alpha=0.8, c="tab:blue")
    ax.set_aspect("equal")
    ax.set_xticks([]), ax.set_yticks([])
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def render_diagram_stimulus(npz_path: Path, path: Path, dpi: int,
                            figsize: tuple) -> None:
    from persim import plot_diagrams
    data = np.load(npz_path)
    dgms = [data[k] for k in data.files]
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    plot_diagrams(dgms, ax=ax, legend=False, size=22)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def render_mapper_stimulus(graph_json: dict, path: Path, dpi: int,
                           figsize: tuple) -> None:
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    _draw_mapper_component_separated(graph_json, ax, title="")
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config",
                    default=str(REPO / "configs" / "e3_readability.yaml"))
    args = ap.parse_args()

    cfg = load_yaml(Path(args.config))
    scfg = cfg["stimuli"]
    e3_dir = REPO / cfg["paths"]["e3_dir"]
    stim_dir = e3_dir / "stimuli"
    stim_dir.mkdir(parents=True, exist_ok=True)
    e1 = REPO / cfg["paths"]["results_e1"]

    # ------------------------------------------------ anchors from saved results
    audit = json.loads((e1 / "e1_audit.json").read_text())
    anchors = {}
    for shape, entry in audit["shapes"].items():
        ps = entry["ph_summary"]
        anchors[shape] = {
            "H1_top3": ps.get("H1_top3_persistence"),
            "r1": ps.get("gap_ratio_r1_calibration"),
            "r_at_rank": next((v for k, v in ps.items()
                               if k.startswith("gap_ratio_r")
                               and k.endswith("_at_ground_truth_rank")), None),
            "mapper_components": entry["mapper_stats"]["n_components"],
            "mapper_max_basis_cycle": entry["mapper_stats"]["max_basis_cycle_length"],
        }

    # ------------------------------------------------ neutral stimulus IDs
    items = scfg["items"]
    rng = random.Random(scfg["shuffle_seed"])
    order = list(range(len(items)))
    rng.shuffle(order)
    ids = {}
    for slot, idx in enumerate(order, start=1):
        ids[idx] = f"{scfg['id_prefix']}{slot:02d}"

    # ------------------------------------------------ render stimuli
    dpi, figsize = scfg["dpi"], tuple(scfg["figsize"])
    manifest = []
    for idx, item in enumerate(items):
        shape, view, task = item["shape"], item["view"], item["task"]
        sid = ids[idx]
        out = stim_dir / f"{sid}.png"
        if view == "scatter":
            X = np.load(e1 / "data" / f"{shape}.npy")
            render_scatter_stimulus(X, out, dpi, figsize)
        elif view == "diagram":
            render_diagram_stimulus(e1 / f"{shape}_ph_dgms.npz", out,
                                    dpi, figsize)
        elif view == "mapper":
            graph_json = json.loads(
                (e1 / f"{shape}_mapper_memberships.json").read_text())
            render_mapper_stimulus(graph_json, out, dpi, figsize)
        else:
            die(f"unknown view {view!r} for item {item}")

        question = (T5_QUESTION_BY_SHAPE[shape] if task == "T5"
                    else TASK_STATEMENTS[task])
        exp, basis = EXPECTED[(task, shape)]
        a = anchors[shape]
        basis_full = (f"{basis}. Measured anchors: top3 H1 persistence "
                      f"{a['H1_top3']}, r_1 {a['r1']}"
                      + (f", r_at_ground_truth_rank {a['r_at_rank']}"
                         if a["r_at_rank"] is not None else "")
                      + f"; Mapper reference cell: {a['mapper_components']} "
                        f"component(s), longest basis cycle "
                        f"{a['mapper_max_basis_cycle']}.")
        src = {"scatter": f"results/e1/data/{shape}.npy",
               "diagram": f"results/e1/{shape}_ph_dgms.npz",
               "mapper": f"results/e1/{shape}_mapper_memberships.json"}[view]
        manifest.append({
            "stimulus_id": sid, "task_id": task, "shape": shape,
            "view": view, "question": question,
            "expected_property": exp, "basis": basis_full,
            "source_files": [src],
            "rendering": {
                "mapper_layout": scfg["mapper_layout"] if view == "mapper"
                                else None,
                "dpi": dpi, "figsize": list(figsize)},
        })
        print(f"stimulus {sid}: {task} / {shape} / {view} -> {out}")

    manifest.sort(key=lambda m: m["stimulus_id"])
    (e3_dir / "stimulus_manifest.json").write_text(json.dumps({
        "generated_utc": time.strftime("%Y-%m-%d %H:%M"),
        "shuffle_seed": scfg["shuffle_seed"],
        "note": "INTERNAL — neutral IDs; expected properties pre-specified "
                "from construction and saved numerical results (never from "
                "inspection performance). Companion of PROTOCOL.md / "
                "METHODS_NOTE.md; the completed record is the authored "
                "inspection_record.csv.",
        "record_columns": RECORD_COLUMNS,
        "items": manifest}, indent=2))

    with open(e3_dir / "scoring_key.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stimulus_id", "task_id", "shape", "view", "question",
                    "expected_property", "basis"])
        for m in manifest:
            w.writerow([m["stimulus_id"], m["task_id"], m["shape"],
                        m["view"], m["question"], m["expected_property"],
                        m["basis"]])

    # ------------------------------------------------ blank inspection worksheet
    # Pre-fills the fixed fields (task/stimulus/question/expected property).
    # The observer-authored fields are left blank; they are completed in
    # inspection_record.csv — never by this script. Blinding of the expected
    # properties is NOT claimed (single invested observer; see PROTOCOL.md).
    with open(e3_dir / "inspection_worksheet_BLANK.csv", "w",
              newline="") as fh:
        fh.write("# E3 structured single-observer inspection worksheet "
                 "(BLANK).\n"
                 "# One row per stimulus, fixed order S01..S13 (PROTOCOL.md).\n"
                 "# assessment in {clearly_apparent, ambiguous, "
                 "visually_obscured, not_represented}; matches_expected in "
                 "{yes, no, partial}.\n"
                 "# evidence_files: semicolon-separated repo-relative paths.\n"
                 "# The completed copy of this worksheet is the AUTHORED file "
                 "e3_inspection/inspection_record.csv.\n")
        w = csv.writer(fh)
        w.writerow(RECORD_COLUMNS)
        for m in manifest:
            w.writerow([m["task_id"], m["stimulus_id"], m["question"],
                        m["expected_property"], "", "", "", "", "", "", ""])

    record = e3_dir / "inspection_record.csv"
    if record.exists():
        n = sum(1 for _ in record.open())
        print(f"NOTE: completed inspection record already exists "
              f"({record}, {n} lines) — this script does NOT touch it.")

    for doc in ("PROTOCOL.md", "METHODS_NOTE.md"):
        if not (e3_dir / doc).exists():
            print(f"WARNING: authored document e3_inspection/{doc} is "
                  f"missing — it is maintained by hand, not generated.")

    print(f"\nWrote {stim_dir} ({len(manifest)} stimuli), scoring key, "
          f"manifest, blank inspection worksheet -> {e3_dir}")
    print("E3 is a STRUCTURED SINGLE-OBSERVER INSPECTION: the participant "
          "study was NOT conducted (constraint change 2026-10-22); no "
          "participant data exist or may be implied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
