"""Output-validity tests for the result machinery.

Part 1 exercises the SAME code path as scripts/run_e2_sensitivity.py on a
miniature grid (fast; structure-independent validity checks), plus the figure
renderers, all inside a temp directory.

Part 2 validates the real results/ artifacts when they exist and skips with
a clear message otherwise (run the experiments first).
"""
import csv
import json
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run_e2_sensitivity import CSV_COLUMNS, run_shape  # noqa: E402
from figures import (  # noqa: E402
    e2_readability_comparison, e2_representative_panels, e2_summary_figure,
    component_separated_layout)

REPO = Path(__file__).resolve().parent.parent


def _mini_cfg():
    return {
        "grid": {"n_cubes": [5, 10], "perc_overlap": [0.35, 0.5]},
        "reference_cell": {"n_cubes": 5, "perc_overlap": 0.35},
        "constants": {"data_seed": 42, "kmeans_seed": 42,
                      "kmeans_n_clusters": 2, "lens": "PCA(n_components=1)"},
        "controls": {"determinism": True},
    }


def _mini_shape_params():
    return {"n": 150, "r_in": 1.0, "r_out": 1.4, "noise": 0.05, "seed": 42,
            "ground_truth_h1_rank": 1, "role": "mini test"}


def test_mini_grid_outputs_valid(tmp_path):
    res = run_shape("annulus", _mini_shape_params(), _mini_cfg())

    # expected number of cells = product of grid sizes
    assert len(res["cells"]) == 2 * 2
    required = {"n_cubes", "perc_overlap", "n_nodes", "n_edges", "n_components",
                "cyclomatic_number", "max_basis_cycle_length",
                "mean_basis_cycle_length", "similarity_to_reference", "time_s",
                "graph", "is_reference"}
    for cell in res["cells"]:
        assert required <= set(cell), f"missing: {required - set(cell)}"
        assert cell["n_nodes"] > 0 and cell["n_edges"] >= 0
        assert 0.0 <= cell["similarity_to_reference"] <= 1.0

    # reference cell flags and scores 1.0 against itself
    ref_cells = [c for c in res["cells"] if c["is_reference"]]
    assert len(ref_cells) == 1
    assert ref_cells[0]["similarity_to_reference"] == 1.0

    # determinism control must pass
    ctrl = res["determinism_control"]
    assert ctrl["memberships_identical"] is True
    assert ctrl["similarity_rerun"] == 1.0

    # JSON round-trip (memberships are plain ints)
    packed = json.loads(json.dumps(res))
    assert packed["cells"][0]["graph"]["nodes"]
    some = next(iter(packed["cells"][0]["graph"]["nodes"].values()))
    assert all(isinstance(i, int) for i in some)


def test_mini_figures_render_from_results(tmp_path):
    res = {"meta": {"contrast_cell_pre_specified": None},
           "shapes": [run_shape("annulus", _mini_shape_params(), _mini_cfg())]}
    p = tmp_path / "e2_sensitivity.json"
    p.write_text(json.dumps(res))
    written = e2_summary_figure(p, tmp_path)
    assert any(w.suffix == ".png" and w.stat().st_size > 5000 for w in written)
    written = e2_representative_panels(p, tmp_path)
    pngs = [w for w in written if w.suffix == ".png"]
    assert pngs and all(w.stat().st_size > 5000 for w in pngs)
    caps = [w for w in written if w.name.endswith(".caption.txt")]
    assert caps and all("not automatically equivalent" in w.read_text()
                        for w in caps)
    # readability comparison (native vs component-separated) also renders
    written = e2_readability_comparison(p, tmp_path)
    pngs = [w for w in written if w.suffix == ".png"]
    assert pngs and all(w.stat().st_size > 5000 for w in pngs)
    caps = [w for w in written if w.name.endswith(".caption.txt")]
    assert caps and all("graph structure" in w.read_text().lower()
                        for w in caps)


def test_component_separated_layout_separates_components():
    """The custom layout puts components in disjoint bands (structure kept)."""
    G = nx.Graph()
    G.add_nodes_from(range(6))
    G.add_edges_from([(0, 1), (1, 2), (3, 4), (4, 5)])  # two components
    pos = component_separated_layout(G, seed=42)
    assert set(pos) == set(range(6))
    y_a = [pos[n][1] for n in (0, 1, 2)]
    y_b = [pos[n][1] for n in (3, 4, 5)]
    # disjoint horizontal bands: component A strictly below component B
    assert max(y_a) < min(y_b) or max(y_b) < min(y_a)
    # edge set unchanged (the layout must not alter structure)
    assert G.number_of_edges() == 4 and G.number_of_nodes() == 6


def test_component_layout_process_deterministic():
    """Regression test: the custom layout must not depend on hash seeding.

    Defect (found by the clean-copy test 2026-10-22): networkx's subgraph
    view iterates its node filter SET for small components, and a set of
    string node names has process-dependent order under hash randomization,
    which made the layout differ ACROSS PROCESSES. The fix sorts nodes and
    components explicitly. This test runs the layout in two subprocesses
    with DIFFERENT PYTHONHASHSEED values and requires identical output.
    """
    import subprocess
    import sys as _sys
    code = (
        "import json, sys, hashlib\n"
        "sys.path.insert(0, 'src')\n"
        "from figures import component_separated_layout, _graph_from_json\n"
        "gj = json.load(open('results/e1/figure_eight_mapper_memberships.json'))\n"
        "G = _graph_from_json(gj)\n"
        "pos = component_separated_layout(G, seed=42)\n"
        "rep = sorted((n, round(p[0], 9), round(p[1], 9)) for n, p in pos.items())\n"
        "print(hashlib.sha256(str(rep).encode()).hexdigest())\n"
    )
    digests = set()
    for hashseed in ("1", "2"):
        env = {**__import__("os").environ, "PYTHONHASHSEED": hashseed}
        out = subprocess.run([_sys.executable, "-c", code], cwd=str(REPO),
                             capture_output=True, text=True, env=env,
                             timeout=120)
        assert out.returncode == 0, out.stderr
        digests.add(out.stdout.strip().splitlines()[-1])
    assert len(digests) == 1, (
        f"layout differs across PYTHONHASHSEED values: {digests} — "
        "the per-component node order is not deterministic")


def test_per_shape_contrast_resolution():
    """Per-shape pre-specified contrast entries are honoured; None auto-selects."""
    from figures import _contrast_for_shape
    cells = [{"n_cubes": nc, "perc_overlap": po, "n_components": 1,
              "cyclomatic_number": 1, "similarity_to_reference": 0.5}
             for nc in (5, 10) for po in (0.35, 0.5)]
    shape_res = {"shape": "x", "cells": cells,
                 "reference_cell": {"n_cubes": 5, "perc_overlap": 0.35}}
    ref, contrast = _contrast_for_shape(
        shape_res, {"x": {"n_cubes": 10, "perc_overlap": 0.5}})
    assert ref == (5, 0.35) and contrast == (10, 0.5)
    ref, contrast = _contrast_for_shape(shape_res, None)
    assert ref == (5, 0.35) and contrast != ref
    assert contrast in {(c["n_cubes"], c["perc_overlap"]) for c in cells}


def test_csv_columns_contract():
    """The CSV schema is part of the results contract (Phase 2 tests rely on it)."""
    assert CSV_COLUMNS[:3] == ["shape", "n_cubes", "perc_overlap"]
    assert "similarity_to_reference" in CSV_COLUMNS


@pytest.mark.skipif(not (REPO / "results" / "e2" / "e2_sensitivity.json").exists(),
                    reason="run scripts/run_e2_sensitivity.py first "
                           "(make e2) — output-validity checks then apply to "
                           "the real artifacts")
def test_real_e2_results_valid():
    R = json.loads((REPO / "results" / "e2" / "e2_sensitivity.json").read_text())
    assert R["meta"]["mapper_cycles_caveat"]
    assert R["meta"]["similarity_caveat"]
    assert R["meta"]["cyclomatic_number_definition"]
    assert "environment" in R["meta"]  # package versions recorded (Phase 2)
    shape_names = {s["shape"] for s in R["shapes"]}
    assert shape_names == {"annulus", "figure_eight"}  # both primary shapes
    for shape_res in R["shapes"]:
        assert len(shape_res["cells"]) == \
            R["meta"]["expected_cells_per_shape"] == 12
        assert shape_res["determinism_control"]["memberships_identical"] is True
        cells = {(c["n_cubes"], c["perc_overlap"]) for c in shape_res["cells"]}
        ref = shape_res["reference_cell"]
        assert (ref["n_cubes"], ref["perc_overlap"]) in cells
        # every cell stores its graph (memberships + links) for re-rendering
        assert all("graph" in c and c["graph"]["nodes"] for c in shape_res["cells"])
    csv_path = REPO / "results" / "e2" / "e2_sensitivity.csv"
    with open(csv_path) as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 24  # 12 cells x 2 shapes (Phase-2 full grid)
    assert set(CSV_COLUMNS) <= set(rows[0])


@pytest.mark.skipif(not (REPO / "results" / "e2" / "e2_blob_sanity.json").exists(),
                    reason="run scripts/run_e2_sensitivity.py first (make e2)")
def test_real_e2_sanity_control_valid():
    S = json.loads((REPO / "results" / "e2" / "e2_blob_sanity.json").read_text())
    assert S["shape"] == "blob"
    assert "not a full sweep" in S["purpose"].lower() or "diagnostic" in S["purpose"].lower()
    assert 1 <= len(S["cells"]) <= 3  # diagnostic settings only, NOT 12
    cal = S["h1_calibration"]
    assert cal["gap_ratio_r1_calibration"] is not None
    assert cal["H1_diagram"]  # diagram stored for figure re-rendering
    for c in S["cells"]:
        assert {"n_nodes", "n_edges", "n_components", "cyclomatic_number",
                "graph"} <= set(c)


@pytest.mark.skipif(not (REPO / "results" / "e1" / "layout_overlap.json").exists(),
                    reason="run scripts/run_e1_audit.py first (make e1)")
def test_real_layout_overlap_valid():
    """Readability measurement: native kk overlap vs custom layout stats."""
    LO = json.loads((REPO / "results" / "e1" / "layout_overlap.json").read_text())
    assert set(LO) >= {"annulus", "figure_eight", "blob", "three_blobs"}
    for name, entry in LO.items():
        for layout in ("native_kk", "component_separated"):
            st = entry[layout]
            assert 0.0 <= st["max_component_bbox_iou"] <= 1.0
            assert 0.0 <= st["inter_close_fraction"] <= 1.0
            assert st["n_components"] >= 1
        # custom layout must separate components by construction
        assert entry["component_separated"]["max_component_bbox_iou"] == 0.0
    # the multi-component shapes must report nonzero interleaving natively
    assert LO["figure_eight"]["native_kk"]["n_components"] == 2
    assert LO["three_blobs"]["native_kk"]["n_components"] == 3


@pytest.mark.skipif(not (REPO / "audit" / "glue_code_accounting.json").exists(),
                    reason="run scripts/run_e1_audit.py first (make e1)")
def test_glue_code_accounting_reproducible():
    """The accounting is recomputable from source and matches the saved file."""
    from count_glue_code import compute_accounting
    saved = json.loads(
        (REPO / "audit" / "glue_code_accounting.json").read_text())
    fresh = compute_accounting()
    assert saved == fresh
    assert "rule" in saved and "LOC" in saved["rule"]
    assert saved["total_loc"] > 0
    assert sum(saved["by_task"].values()) == saved["total_loc"]


@pytest.mark.skipif(not (REPO / "results" / "e1" / "e1_audit.json").exists(),
                    reason="run scripts/run_e1_audit.py first (make e1)")
def test_real_e1_results_valid():
    R = json.loads((REPO / "results" / "e1" / "e1_audit.json").read_text())
    for name in ("annulus", "figure_eight", "blob", "three_blobs"):
        assert name in R["shapes"]
        s = R["shapes"][name]
        assert s["ph_summary"]["H1_top3_persistence"]
        assert s["mapper_stats"]["n_nodes"] > 0
        for key in ("scatter", "diagram", "barcode", "mapper_static",
                    "mapper_html"):
            path = REPO / s["artifacts"][key]
            assert path.exists() and path.stat().st_size > 1000, f"{name}/{key}"
        assert s["mapper_html"]["external_urls"], "CDN finding must be recorded"
    assert R["determinism_check"]["mapper_memberships_identical"] is True
    assert "layout_overlap" in R and "figure_eight" in R["layout_overlap"]
    matrix = REPO / "audit" / "capability_matrix.csv"
    with open(matrix) as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 13 and {r["task_id"] for r in rows} == \
        {f"T{i:02d}" for i in range(1, 14)}
    assert all(r["evidence"] for r in rows)
    # Phase-2 columns: honest status + limitations for every task
    for r in rows:
        assert r["status"] in {"demonstrated", "failed", "pending", "untested"}
        assert r["limitations"].strip()
        assert r["packages_and_code_paths"].strip()
    # T12 must not claim demonstration without the clean-clone comparison
    t12 = next(r for r in rows if r["task_id"] == "T12")
    repro = REPO / "results" / "repro" / "comparison_report.json"
    if t12["status"] == "demonstrated":
        assert repro.exists()
