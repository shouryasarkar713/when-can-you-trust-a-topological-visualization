#!/usr/bin/env python3
"""Reproducible glue-code accounting for the E1 capability audit.

COUNTING RULE (the single source of truth; run_e1_audit.py imports it):
  For each listed custom function, LOC = number of its source lines that are
    (a) not blank,
    (b) not comment-only (stripped line does not start with '#'),
    (c) not part of the function docstring (AST-detected).
  The def line, decorators, and local imports COUNT (they are code a user
  must write); inline trailing comments count as part of their code line.

SCOPE — what is counted as "glue" (code that exists because the evaluated
ecosystem lacks the capability):
  * data generation      — the four synthetic generators + config plumbing
  * custom rendering     — H1 barcode; component-separated graph layout
  * graph analysis       — node/edge/component/cycle-statistics wrapper
  * custom metrics       — persistence-gap ratio; membership-overlap S
  * conventional baselines — PCA scatter
EXCLUDED (with reasons):
  * tests/               — verification, not workflow glue
  * scripts/             — experiment harness & audit driver (they RUN the
                           evaluation; they are not needed to use the tools)
  * module docstrings, module-level constants, figure-caption plumbing,
    CLI/argparse code    — project infrastructure, not capability glue
  * generated code       — none exists; everything counted is hand-written

Output: audit/glue_code_accounting.json (+ console summary).
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import shapes as shapes_mod  # noqa: E402
import pipeline as pipeline_mod  # noqa: E402
import similarity as similarity_mod  # noqa: E402
import figures as figures_mod  # noqa: E402

RULE_TEXT = (
    "LOC per function = non-blank, non-comment-only, non-docstring source "
    "lines (AST docstring detection), including def/decorators/local "
    "imports. Scope: custom functions in src/ that fill a capability gap of "
    "the evaluated ecosystem (generators, custom renderers, graph-analysis "
    "wrapper, custom metrics, baseline, alternative layout). Excluded: "
    "tests/, scripts/ (experiment harness), module docstrings/constants, "
    "figure-caption plumbing, CLI code. No generated code is counted."
)

#: (module, function, task_id, category, why it is glue)
GLUE_INVENTORY = [
    ("shapes", "annulus", "T02", "data-generation",
     "ecosystem ships no data generators"),
    ("shapes", "figure_eight", "T02", "data-generation",
     "ecosystem ships no data generators"),
    ("shapes", "blob", "T02", "data-generation",
     "ecosystem ships no data generators"),
    ("shapes", "three_blobs", "T02", "data-generation",
     "ecosystem ships no data generators"),
    ("shapes", "make_shape", "T02", "data-generation",
     "config-to-generator plumbing"),
    ("pipeline", "render_barcode", "T05", "rendering",
     "persim ships diagrams, not barcodes (API inventory verified)"),
    ("pipeline", "gap_ratio", "E2-metric", "metric",
     "no gap-ratio statistic in ripser/persim"),
    ("pipeline", "h1_persistences", "E2-metric", "metric",
     "helper for the gap ratio"),
    ("pipeline", "h0_prominent_merges", "E2-metric", "metric",
     "component-structure check for the three-blob control"),
    ("pipeline", "mapper_structure_stats", "T09", "graph-analysis",
     "component/cycle counts need networkx (not a kmapper dependency)"),
    ("pipeline", "render_pca_baseline", "T13", "baseline",
     "conventional baseline assembled from sklearn + matplotlib"),
    ("similarity", "jaccard", "E2-metric", "metric",
     "membership-Jaccard helper for S"),
    ("similarity", "similarity", "E2-metric", "metric",
     "custom exploratory overlap indicator S (no canonical metric exists)"),
    ("similarity", "memberships_from_graph", "E2-metric", "metric",
     "graph-to-memberships extraction for S"),
    ("similarity", "memberships_equal", "E2-metric", "metric",
     "determinism-control equality"),
    ("figures", "component_separated_layout", "T10-alt", "rendering",
     "native kk layout can overlap disconnected components; alternative "
     "analytical layout (structure untouched)"),
]

_MODULES = {"shapes": shapes_mod, "pipeline": pipeline_mod,
            "similarity": similarity_mod, "figures": figures_mod}


def function_loc(func) -> int:
    """LOC of one function under the documented rule."""
    src = inspect.getsource(func)
    tree = ast.parse(src)
    fn = tree.body[0]
    doc_lines: set[int] = set()
    if (ast.get_docstring(fn) is not None
            and fn.body and isinstance(fn.body[0], ast.Expr)):
        doc = fn.body[0]
        doc_lines.update(range(doc.lineno, doc.end_lineno + 1))
    n = 0
    for i, line in enumerate(src.splitlines(), start=1):
        s = line.strip()
        if not s or s.startswith("#") or i in doc_lines:
            continue
        n += 1
    return n


def compute_accounting() -> dict:
    entries = []
    for mod_name, fn_name, task, category, why in GLUE_INVENTORY:
        func = getattr(_MODULES[mod_name], fn_name)
        entries.append({
            "module": mod_name, "function": fn_name, "task": task,
            "category": category, "why_glue": why,
            "loc": function_loc(func),
            "source": f"src/{mod_name}.py::{fn_name}",
        })
    by_task: dict[str, int] = {}
    for e in entries:
        by_task[e["task"]] = by_task.get(e["task"], 0) + e["loc"]
    return {
        "rule": RULE_TEXT,
        "inventory": entries,
        "total_loc": sum(e["loc"] for e in entries),
        "by_task": by_task,
        "by_category": {
            cat: sum(e["loc"] for e in entries if e["category"] == cat)
            for cat in sorted({e["category"] for e in entries})},
    }


def main() -> int:
    acc = compute_accounting()
    out = REPO / "audit" / "glue_code_accounting.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(acc, indent=2))
    print(f"Glue-code accounting (rule in JSON): {acc['total_loc']} LOC total")
    for task, loc in sorted(acc["by_task"].items()):
        print(f"  {task:>8}: {loc:3d} LOC")
    for cat, loc in acc["by_category"].items():
        print(f"  [category] {cat}: {loc} LOC")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
