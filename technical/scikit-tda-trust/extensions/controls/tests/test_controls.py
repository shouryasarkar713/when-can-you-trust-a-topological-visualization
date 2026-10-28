"""Tests for Extension D (independent audit controls): saved results are internally consistent,
reproducible from config + seeds, and consistent with the baseline / Extension A outputs."""
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
RES = EXT / "results"
CFG = yaml.safe_load((EXT / "configs" / "controls.yaml").read_text())


def load(name):
    return json.loads((RES / name).read_text())


def test_d1_grid_completeness():
    d = load("mapper_clusterer_control.json")
    assert set(d["shapes"]) == {"annulus", "figure_eight", "blob"}
    for s in d["shapes"].values():
        assert set(s["eps"]) == {"c1.5", "c3.0"}
        for e in s["eps"].values():
            assert len(e["cells"]) == 12


def test_d1_eps_tied_to_data_scale_not_tuned():
    d = load("mapper_clusterer_control.json")
    for s in d["shapes"].values():
        for c, e in s["eps"].items():
            assert e["eps_value"] == pytest.approx(e["multiplier"] * s["median_5nn_distance"], rel=1e-3)


def test_d1_determinism_reference_cell():
    from sklearn.decomposition import PCA
    from run_mapper_clusterer_control import median_knn_distance, mapper_single_linkage
    from src.pipeline import mapper_structure_stats
    from src.shapes import make_shape
    shapes = yaml.safe_load((REPO / "configs" / "shapes.yaml").read_text())["shapes"]
    X = make_shape("annulus", shapes["annulus"])
    eps = 3.0 * median_knn_distance(X, 5)
    st = mapper_structure_stats(mapper_single_linkage(X, PCA(n_components=1).fit_transform(X), 10, 0.35, eps))
    saved = load("mapper_clusterer_control.json")["shapes"]["annulus"]["eps"]["c3.0"]["cells"]["nc10_po0.35"]
    for k in ("n_nodes", "n_edges", "n_components", "cyclomatic_number"):
        assert st[k] == saved[k]


def test_d1_node_count_not_locked_to_two_per_interval_for_adaptive_clusterer():
    d = load("mapper_clusterer_control.json")
    for shape, s in d["shapes"].items():
        for c, e in s["eps"].items():
            assert e["summary"]["node_count_equals_2x_n_cubes_cells"] < 12, (shape, c)


def test_d3_seed_rule_and_counts():
    d = load("mapper_resampling_control.json")
    for shape, blk in d["shapes"].items():
        for e in blk["eps"].values():
            assert len(e["replicates"]) == 30
            off = CFG["mapper_resampling_control"]["seed_offsets"][shape]
            seeds = [r["seed"] for r in e["replicates"]]
            assert seeds == [20261022 + off + i for i in range(30)]


def test_d3_subsample_indices_match_extension_c_saved_indices():
    c = json.loads((REPO / "extensions" / "stability" / "results" / "mapper_resampling.json").read_text())
    for shape in ("annulus", "figure_eight", "blob"):
        n = c["shapes"][shape]["n_full"]
        for rep in c["shapes"][shape]["replicates"][:5]:
            idx = np.sort(np.random.default_rng(rep["seed"]).choice(n, size=400, replace=False))
            assert list(idx) == rep["indices"]


def test_d3_reference_equals_d1_reference_cell():
    d1, d3 = load("mapper_clusterer_control.json"), load("mapper_resampling_control.json")
    for shape in d3["shapes"]:
        for c in d3["shapes"][shape]["eps"]:
            r3 = d3["shapes"][shape]["eps"][c]["reference"]
            r1 = d1["shapes"][shape]["eps"][c]["cells"]["nc10_po0.35"]
            assert (r3["n_nodes"], r3["n_components"], r3["cyclomatic_number"]) == (
                r1["n_nodes"], r1["n_components"], r1["cyclomatic_number"])


def test_d2_raw_series_reproduces_extension_a_sweep_exactly():
    d2 = load("weather_null_controls.json")
    a = json.loads((REPO / "extensions" / "meteorology" / "results" / "weather_analysis_results.json").read_text())
    assert d2["temp_z_matches_saved_array_max_abs"] == 0.0
    for key, v in a["seasonal_ph"]["sweep"].items():
        assert d2["raw"][key]["gap_ratio_r1"] == v["gap_ratio_r1"]
        assert d2["raw"][key]["dominant_H1_persistence"] == v["dominant_H1_persistence"]


def test_d2_controls_have_no_dominant_loop_under_stated_convention():
    d2 = load("weather_null_controls.json")
    for key, v in d2["anomaly"].items():
        assert v["gap_ratio_r1"] < 3, key
    assert d2["shuffle"]["summary"]["n_with_r1_ge_3"] == 0
    assert len(d2["shuffle"]["replicates"]) == CFG["weather_null_controls"]["shuffle"]["n_shuffles"]


def test_d2_harmonic_fit_explains_most_variance():
    assert 0.8 < load("weather_null_controls.json")["annual_harmonic_fit_R2"] < 0.9
