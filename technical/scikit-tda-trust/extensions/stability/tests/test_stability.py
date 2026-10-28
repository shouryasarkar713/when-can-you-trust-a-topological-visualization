"""Stage 4 — stability-extension tests.

Covers (per the Stage-4 authorization, Part E):
  * expected replicate counts and configuration values;
  * determinism with fixed seeds (index regeneration, replicate recompute,
    Mapper reference rebuild);
  * diagram and graph statistic calculations (cyclomatic definition, gap
    ratio, bottleneck/wasserstein sanity);
  * global point-identity handling across Mapper subsamples;
  * required output schemas and artifact existence;
  * reproducible figure generation;
  * preservation of the existing baseline manifest.

Skips cleanly (with a message) when the real artifacts are absent.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
RESULTS = EXT / "results"
FIGS = EXT / "figures"

HAS_RESULTS = (RESULTS / "ph_resampling.json").exists()
reason = "stability results not generated yet — run the Stage-4 scripts first"


# ---------------------------------------------------------------- helpers

def _load(name):
    return json.loads((RESULTS / name).read_text())


def _seed(shape: str, rep: int, cfg: dict) -> int:
    rs = cfg["resampling"]
    return int(rs["seed_base"]) + int(rs["seed_offsets"][shape]) + rep


# ---------------------------------------------------------------- config

@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestConfigAndReplicates:
    def test_replicate_counts_and_sizes(self):
        import yaml
        cfg = yaml.safe_load((EXT / "configs" / "stability.yaml").read_text())
        n_rep = int(cfg["resampling"]["n_replicates"])
        frac = float(cfg["resampling"]["fraction"])
        for name in ("ph_resampling.json", "mapper_resampling.json"):
            r = _load(name)
            assert len(r["shapes"]) == 3
            for shape, blk in r["shapes"].items():
                reps = blk["replicates"]
                assert len(reps) == n_rep == 30, (name, shape)
                assert blk["n_full"] == 500
                assert blk["subsample_size"] == int(round(frac * 500)) == 400
                for rep in reps:
                    assert rep["n_points"] == 400

    def test_indices_sorted_unique_in_range(self):
        for name in ("ph_resampling.json", "mapper_resampling.json"):
            r = _load(name)
            for shape, blk in r["shapes"].items():
                for rep in blk["replicates"]:
                    idx = rep["indices"]
                    assert idx == sorted(idx)
                    assert len(set(idx)) == len(idx) == 400
                    assert 0 <= min(idx) and max(idx) < 500

    def test_seeds_follow_config_rule_and_are_distinct(self):
        import yaml
        cfg = yaml.safe_load((EXT / "configs" / "stability.yaml").read_text())
        all_seeds = []
        for name in ("ph_resampling.json", "mapper_resampling.json"):
            r = _load(name)
            for shape, blk in r["shapes"].items():
                for rep in blk["replicates"]:
                    assert rep["seed"] == _seed(shape, rep["rep"], cfg)
                    all_seeds.append(rep["seed"])
        assert len(set(all_seeds)) == 90  # 3 shapes x 30 reps, all distinct

    def test_ph_and_mapper_use_identical_subsamples(self):
        ph = _load("ph_resampling.json")
        mp = _load("mapper_resampling.json")
        for shape in ph["shapes"]:
            for a, b in zip(ph["shapes"][shape]["replicates"],
                            mp["shapes"][shape]["replicates"]):
                assert a["seed"] == b["seed"] and a["indices"] == b["indices"]

    def test_configuration_values_echoed(self):
        ph = _load("ph_resampling.json")["config"]
        assert ph["ripser_maxdim"] == 1
        assert ph["metrics"] == ["bottleneck", "wasserstein"]
        assert ph["homology_dims"] == [0, 1]
        assert ph["n_replicates"] == 30 and ph["fraction"] == 0.8
        mp = _load("mapper_resampling.json")["config"]["mapper_fixed"]
        assert mp["n_cubes"] == 10 and mp["perc_overlap"] == 0.35
        assert mp["kmeans"] == {"n_clusters": 2, "random_state": 42, "n_init": 10}
        loyo = _load("weather_loyo.json")["config"]
        assert loyo["years"] == [2019, 2020, 2021, 2022, 2023, 2024]
        assert len(loyo["sweep"]) == 6
        assert loyo["reference_config"] == "tau60_d8"


# ---------------------------------------------------------------- determinism

@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestDeterminism:
    def test_subsample_indices_reproduce_from_seed_rule(self):
        import yaml
        from run_ph_resampling import subsample_indices
        cfg = yaml.safe_load((EXT / "configs" / "stability.yaml").read_text())
        r = _load("ph_resampling.json")
        for shape in ("annulus", "figure_eight", "blob"):
            for rep in (0, 15, 29):
                stored = r["shapes"][shape]["replicates"][rep]["indices"]
                regen = subsample_indices(500, 400, _seed(shape, rep, cfg))
                assert [int(v) for v in regen] == stored, (shape, rep)

    def test_one_replicate_recomputes_identically(self):
        from ripser import ripser
        from src.pipeline import h1_persistences
        r = _load("ph_resampling.json")
        blk = r["shapes"]["annulus"]
        rep = blk["replicates"][0]
        X = np.load(REPO / "results/e1/data/annulus.npy")
        dgms = ripser(X[np.asarray(rep["indices"])], maxdim=1)["dgms"]
        pers = [round(float(x), 4) for x in h1_persistences(dgms[1])[:3]]
        assert pers == rep["diagnostics"]["H1_top3_persistence"]
        assert len(dgms[1]) == rep["diagnostics"]["H1_classes"]
        assert (len(dgms[0]) - 1) == rep["diagnostics"]["H0_finite_classes"]

    def test_mapper_reference_rebuild_matches_saved(self):
        from src.pipeline import mapper_run, mapper_structure_stats
        mp = _load("mapper_resampling.json")
        for shape in ("annulus", "figure_eight", "blob"):
            ref = mp["shapes"][shape]["reference"]
            assert ref["verified_identical_to_e1_saved"] is True
            X = np.load(REPO / "results/e1/data" / f"{shape}.npy")
            g = mapper_run(X, 10, 0.35, seed=42, n_clusters=2)
            stats = mapper_structure_stats(g)
            for k in ("n_nodes", "n_edges", "n_components", "cyclomatic_number"):
                assert stats[k] == ref["structure"][k], (shape, k)


# ---------------------------------------------------------------- statistics

class TestStatisticCalculations:
    def test_cyclomatic_is_edges_minus_vertices_plus_components(self):
        import networkx as nx
        # triangle: 3 edges - 3 vertices + 1 component = 1 independent cycle
        g = nx.Graph([(0, 1), (1, 2), (2, 0)])
        assert (g.number_of_edges() - g.number_of_nodes()
                + nx.number_connected_components(g)) == 1
        # two disjoint triangles -> 2
        g2 = nx.Graph([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
        assert (g2.number_of_edges() - g2.number_of_nodes()
                + nx.number_connected_components(g2)) == 2
        # tree -> 0
        t = nx.Graph([(0, 1), (1, 2), (1, 3)])
        assert (t.number_of_edges() - t.number_of_nodes()
                + nx.number_connected_components(t)) == 0
        # isolated node added: V+1, C+1, E unchanged -> cyclomatic unchanged
        t.add_node(99)
        assert (t.number_of_edges() - t.number_of_nodes()
                + nx.number_connected_components(t)) == 0

    def test_cyclomatic_definition_recorded(self):
        if not HAS_RESULTS:
            pytest.skip(reason)
        mp = _load("mapper_resampling.json")
        assert "E - V + C" in mp["cyclomatic_number_definition"]

    def test_gap_ratio_matches_baseline_helper(self):
        from src.pipeline import gap_ratio
        pers = [5.0, 1.0, 0.5]
        assert gap_ratio(pers, 1) == 5.0
        assert gap_ratio(pers, 2) == 2.0
        assert gap_ratio([5.0], 1) is None  # no p2 -> undefined

    def test_bottleneck_of_diagram_with_itself_is_zero(self):
        from persim import bottleneck
        d = np.array([[0.0, 1.0], [0.5, 0.9], [0.2, 0.4]])
        assert bottleneck(d, d) == 0.0

    def test_wasserstein_symmetric(self):
        from persim import wasserstein
        a = np.array([[0.0, 1.0], [0.5, 0.9]])
        b = np.array([[0.1, 0.8], [0.4, 0.5], [0.0, 0.2]])
        assert abs(wasserstein(a, b) - wasserstein(b, a)) < 1e-9


# ------------------------------------------------------- global point identity

@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestGlobalPointIdentity:
    def test_memberships_use_global_ids_within_subsample(self):
        mp = _load("mapper_resampling.json")
        for shape, blk in mp["shapes"].items():
            for rep in blk["replicates"]:
                allowed = set(rep["indices"])
                for members in rep["memberships_global"].values():
                    assert members
                    assert set(members) <= allowed, (shape, rep["rep"])

    def test_reference_memberships_are_full_range(self):
        mp = _load("mapper_resampling.json")
        for shape, blk in mp["shapes"].items():
            ids = {i for m in blk["reference"]["memberships_global"].values()
                   for i in m}
            assert min(ids) >= 0 and max(ids) < 500

    def test_links_consistent_with_edge_counts(self):
        mp = _load("mapper_resampling.json")
        for shape, blk in mp["shapes"].items():
            pairs = set()
            for a, others in blk["reference"]["links"].items():
                for b in others:
                    pairs.add(tuple(sorted((a, b))))
            assert len(pairs) == blk["reference"]["structure"]["n_edges"]
            for rep in blk["replicates"]:
                pairs = set()
                for a, others in rep["links"].items():
                    for b in others:
                        pairs.add(tuple(sorted((a, b))))
                assert len(pairs) == rep["structure"]["n_edges"]

    def test_local_to_global_mapping_helper(self):
        from run_mapper_resampling import memberships_global
        # synthetic graph whose local rows map to non-trivial global ids
        graph = {"nodes": {"n0": [0, 2], "n1": [1]},
                 "links": {"n0": ["n1"], "n1": []}}
        sub_idx = np.array([50, 61, 72])
        out = memberships_global(graph, sub_idx)
        assert out == {"n0": [50, 72], "n1": [61]}

    def test_S_recomputed_on_global_ids_matches_stored(self):
        from src.similarity import similarity
        mp = _load("mapper_resampling.json")
        blk = mp["shapes"]["annulus"]
        rep = blk["replicates"][3]
        a = [frozenset(v) for v in rep["memberships_global"].values()]
        b = [frozenset(v) for v in blk["reference"]["memberships_global"].values()]
        assert round(similarity(a, b), 4) == rep["membership_jaccard_S_vs_reference"]


# ------------------------------------------------------- schemas and artifacts

@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestSchemasAndArtifacts:
    FIGURES = [
        "ph_resampling_dists.png", "ph_resampling_persistence.png",
        "ph_resampling_cross_shape.png", "mapper_resampling_structure.png",
        "mapper_resampling_graphs_annulus.png",
        "mapper_resampling_graphs_figure_eight.png",
        "mapper_resampling_graphs_blob.png", "mapper_resampling_layouts.png",
        "weather_loyo.png",
    ]

    def test_required_results_exist(self):
        for name in ("ph_resampling.json", "mapper_resampling.json",
                     "weather_loyo.json", "stability_summary.json",
                     "claims_evidence.json"):
            p = RESULTS / name
            assert p.exists() and p.stat().st_size > 500, name

    def test_figures_exist_nonempty_and_captioned(self):
        caps = json.loads((FIGS / "captions.json").read_text())
        for name in self.FIGURES:
            p = FIGS / name
            assert p.exists() and p.stat().st_size > 5000, name
            assert name in caps, name

    def test_ph_schema_and_guards(self):
        r = _load("ph_resampling.json")
        for key in ("reference_overlap_guard",
                    "methodology_note_metric_vs_test"):
            assert key in r and "not" in r[key].lower()
        assert "drop points with non-finite death" in r["essential_class_handling"]
        for shape, blk in r["shapes"].items():
            for rep in blk["replicates"]:
                for dim in ("H0", "H1"):
                    d = rep["distances"][dim]
                    assert {"n_finite_resample", "n_finite_reference",
                            "bottleneck", "wasserstein"} <= set(d)
                    assert d["bottleneck"]["value"] >= 0
                    assert d["wasserstein"]["value"] >= 0
                assert {"H1_classes", "H0_finite_classes",
                        "H1_top3_persistence", "gap_ratio_r1"} \
                    <= set(rep["diagnostics"])

    def test_mapper_schema_and_guards(self):
        mp = _load("mapper_resampling.json")
        for key in ("cyclomatic_number_definition", "similarity_caveat",
                    "global_identity_note"):
            assert key in mp
        assert "not a metric" in mp["similarity_caveat"]
        assert "GLOBAL" in mp["global_identity_note"]

    def test_loyo_windows_never_cross_gap(self):
        loyo = _load("weather_loyo.json")
        assert len(loyo["folds"]) == 6
        for year, f in loyo["folds"].items():
            lengths = [b["length_days"] for b in f["blocks"]]
            assert sum(lengths) == f["n_retained_days"]
            for key, c in f["configs"].items():
                span = c["span_days"]
                expected = sum(max(0, L - span) for L in lengths)
                assert c["n_points"] == expected, (year, key)
                # gap-loss bookkeeping: contiguous hypothetical minus actual
                assert (c["n_windows_lost_to_gap"]
                        == max(0, f["n_retained_days"] - span) - expected)

    def test_loyo_summary_consistency(self):
        loyo = _load("weather_loyo.json")
        s = _load("stability_summary.json")
        for cfg, agg in s["weather_loyo"].items():
            r1s = [loyo["folds"][y]["configs"][cfg]["gap_ratio_r1"]
                   for y in loyo["folds"]]
            assert agg["all_folds_r1_at_least_3"] == (min(r1s) >= 3)
            assert agg["min_fold_r1"] == round(min(r1s), 3)
        # the recorded headline finding, as a regression check on the artifact
        assert all(agg["all_folds_r1_at_least_3"] for agg in s["weather_loyo"].values())

    def test_summary_matches_ph_results(self):
        ph = _load("ph_resampling.json")
        s = _load("stability_summary.json")
        for shape in ph["shapes"]:
            reps = ph["shapes"][shape]["replicates"]
            bn = [r["distances"]["H1"]["bottleneck"]["value"] for r in reps]
            assert s["ph_resampling"][shape]["distances"]["H1_bottleneck"]["min"] \
                == round(min(bn), 5)


# ------------------------------------------------------- figure reproducibility

@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestFigureReproducibility:
    def test_cross_shape_figure_renders_identically_twice(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from render_stability_figures import fig_ph_cross_shape
        import io as _io

        def render_bytes():
            buf = _io.BytesIO()
            ph = _load("ph_resampling.json")
            import render_stability_figures as rsf
            orig = rsf._save
            # render without touching the saved figures dir
            rsf.CAPTIONS.clear()
            rsf._save = lambda fig, name, caption: (
                fig.savefig(buf, dpi=150, format="png"), plt.close(fig), buf)[2]
            try:
                fig_ph_cross_shape(ph)
            finally:
                rsf._save = orig
            return buf.getvalue()

        b1, b2 = render_bytes(), render_bytes()
        assert b1 == b2 and len(b1) > 5000
        # and the shipped figure regenerates deterministically from results
        import render_stability_figures as rsf
        ph = _load("ph_resampling.json")
        fig = plt.figure()
        plt.close(fig)
        rsf.CAPTIONS.clear()
        rsf._save_orig = rsf._save
        shipped = (FIGS / "ph_resampling_cross_shape.png").read_bytes()
        buf = _io.BytesIO()

        def save_to_buf(fig_, name, caption_):
            fig_.savefig(buf, dpi=150, format="png")
            plt.close(fig_)
        rsf._save = save_to_buf
        try:
            fig_ph_cross_shape(ph)
        finally:
            rsf._save = rsf._save_orig
        # independent-rebuild change: PNG *bytes* embed platform/library metadata (differ between
        # Linux and Windows); the rendered PIXELS must be identical.
        import matplotlib.image as _mimg
        px_new = _mimg.imread(_io.BytesIO(buf.getvalue()), format="png")
        px_old = _mimg.imread(_io.BytesIO(shipped), format="png")
        assert px_new.shape == px_old.shape and (px_new == px_old).all()


# ------------------------------------------------------- baseline preservation

class TestBaselinePreservation:
    def test_baseline_manifest_unchanged(self):
        script = REPO / "extensions" / "scripts" / "verify_baseline_unchanged.py"
        if not script.exists():
            pytest.skip("verify script not present")
        r = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(REPO))
        assert r.returncode == 0, r.stdout + r.stderr
        assert "BASELINE PRESERVATION VERIFIED" in r.stdout


# ------------------------------------------------------- claims table

@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestClaimsEvidenceTable:
    def test_rows_reference_existing_artifacts(self):
        claims = _load("claims_evidence.json")
        assert len(claims["rows"]) >= 10
        for row in claims["rows"]:
            assert {"id", "claim", "evidence_file", "figure"} <= set(row)
            p = REPO / row["evidence_file"]
            assert p.exists(), f"missing evidence artifact {row['evidence_file']}"
            if row["figure"]:
                assert (REPO / row["figure"]).exists(), f"missing {row['figure']}"

    def test_guards_present(self):
        claims = _load("claims_evidence.json")
        g = " ".join(claims["global_guards"]).lower()
        for phrase in ("not independent validation", "not a metric",
                       "not a hypothesis test", "no human-participant study"):
            assert phrase in g
