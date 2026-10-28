"""Extension A output-validity tests — schema and consistency checks on the
SAVED results (skips cleanly with a message if the real artifacts are absent,
following the baseline test_outputs.py convention)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

EXT = Path(__file__).resolve().parents[1]
RESULTS = EXT / "results"
FIGS = EXT / "figures"
PROC = EXT / "data_provenance" / "processed"

HAS_RESULTS = (RESULTS / "weather_analysis_results.json").exists()
reason = "weather extension results not generated yet — run the pipeline first"


@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestPreprocessingArtifacts:
    def test_report_schema_and_status(self):
        rep = json.loads((RESULTS / "weather_preprocessing_report.json").read_text())
        assert rep["status"] == "OK"
        assert rep["n_raw_rows"] == 2192
        assert rep["date_validation"]["ok"]
        assert rep["sentinel_crosscheck_vs_provenance"]["diffs"] == {
            "SLP": {"preprocessing_exact": 4, "provenance_string_match": 5},
            "STP": {"preprocessing_exact": 0, "provenance_string_match": 6}}
        # documented data-quality observations present
        assert "STP_excluded" in rep["data_quality_observations"]
        assert "SLP_ambiguous_2020_12_01" in rep["data_quality_observations"]

    def test_primary_cloud_counts(self):
        rep = json.loads((RESULTS / "weather_preprocessing_report.json").read_text())
        pc = rep["primary_cloud"]
        assert pc["features"] == ["TEMP", "DEWP", "SLP"]
        assert pc["n_days_kept"] + pc["n_days_dropped"] == 2192
        assert pc["fraction_dropped"] < 0.05   # pre-specified acceptability rule
        sc = rep["sensitivity_cloud"]
        assert sc["n_days_kept"] + sc["n_days_dropped"] == 2192
        assert sc["features"] == ["TEMP", "DEWP", "SLP", "WDSP"]

    def test_npz_contents(self):
        d = np.load(PROC / "weather_analysis.npz", allow_pickle=True)
        for key in ("dates", "seasons", "X_primary", "temp_c", "temp_z",
                    "primary_dates", "oni_phase"):
            assert key in d
        assert d["X_primary"].shape == (2188, 3)
        assert d["temp_z"].shape == (2192,)
        # z-scored clouds really are standardized
        assert np.allclose(d["X_primary"].mean(0), 0, atol=1e-9)
        assert np.allclose(d["X_primary"].std(0), 1, atol=1e-6)
        # TEMP series complete
        assert np.isfinite(d["temp_c"]).all()

    def test_raw_immutable_inputs_exist_with_checksums(self):
        prov = json.loads((EXT / "data_provenance" / "provenance.json").read_text())
        for fname, rec in prov["files"].items():
            p = EXT / "data_provenance" / "raw" / fname
            assert p.exists(), fname
            import hashlib
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            assert h == rec["sha256"], f"{fname} changed after provenance was written"


@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestAnalysisArtifacts:
    def test_pca_results(self):
        a = json.loads((RESULTS / "weather_analysis_results.json").read_text())
        coords = np.load(RESULTS / "weather_pca_coords.npy")
        assert coords.shape == (2188, 2)
        evr = a["pca"]["explained_variance_ratio"]
        assert 0 < evr[0] <= 1 and 0 < evr[1] <= 1
        assert a["pca"]["cumulative_explained_variance"] == pytest.approx(sum(evr), abs=1e-4)

    def test_mapper_results_schema(self):
        m = json.loads((RESULTS / "weather_mapper_results.json").read_text())
        assert m["reference_cell"] == "nc10_po0.35"
        assert len(m["cells"]) == 8    # 4 resolutions x 2 overlaps
        for key, cell in m["cells"].items():
            s = cell["structure"]
            assert s["n_nodes"] == 2 * cell["n_cubes"]          # observed pattern
            assert s["cyclomatic_number"] == s["n_edges"] - s["n_nodes"] + s["n_components"]
            assert "membership_jaccard_S_vs_reference" in cell
            assert cell["lens"] == "PCA-1"
        assert m["cells"]["nc10_po0.35"]["membership_jaccard_S_vs_reference"] == 1.0
        assert "day_of_year" in m and "note" in m["day_of_year"]

    def test_seasonal_ph_results(self):
        a = json.loads((RESULTS / "weather_analysis_results.json").read_text())
        sweep = a["seasonal_ph"]["sweep"]
        assert len(sweep) == 6
        for key, c in sweep.items():
            assert c["status"] == "OK"
            assert c["span_days"] == (c["d"] - 1) * c["tau"]
            assert c["n_points"] > 1500
            assert c["dominant_H1_persistence"] > 0
            assert c["gap_ratio_r1"] > 1
        # reference config present
        assert a["seasonal_ph"]["reference"] == "tau60_d8"
        # interpretation guard present
        assert "NOT proof" in a["seasonal_ph"]["interpretation_guard"]

    def test_diagram_npz_matches_diagnostics(self):
        a = json.loads((RESULTS / "weather_analysis_results.json").read_text())
        dgms = np.load(RESULTS / "weather_seasonal_ph_dgms.npz")
        for key, c in a["seasonal_ph"]["sweep"].items():
            d1 = dgms[f"{key}_dgm1"]
            assert len(d1) == c["H1_classes"], key
            pers = np.sort((d1[:, 1] - d1[:, 0]))[::-1]
            assert pers[0] == pytest.approx(c["dominant_H1_persistence"], abs=1e-3), key

    def test_state_space_null_contrast(self):
        a = json.loads((RESULTS / "weather_analysis_results.json").read_text())
        ss = a["state_space_ph"]
        # the state-space cloud shows NO dominant loop (measured finding)
        assert ss["gap_ratio_r1"] < 3
        assert ss["dominant_H1_persistence"] < 1.0

    def test_oni_descriptive_only(self):
        a = json.loads((RESULTS / "weather_preprocessing_report.json").read_text())
        oni = a["oni"]
        assert oni["enabled"] is True
        assert "DESCRIPTIVE" in oni["role"]
        assert "power" in oni["power_statement"].lower()


@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestSeasonalityCheck:
    """Post-hoc periodogram/ACF sanity check (Stage 3): schema, values, and
    the scope guard — it must be labelled post-hoc and must NOT claim to have
    been used for embedding-parameter selection."""

    def _load(self):
        return json.loads((RESULTS / "weather_seasonality_check.json").read_text())

    def test_schema_and_status(self):
        s = self._load()
        assert s["status"] == "OK"
        assert s["step"] == "seasonality_check"
        for key in ("periodogram", "autocorrelation", "interpretation", "purpose"):
            assert key in s
        assert s["periodogram"]["n_samples"] == 2192
        assert len(s["autocorrelation"]["lags_days"]) == len(s["autocorrelation"]["acf"])
        assert s["autocorrelation"]["acf_at_lag_0"] == 1.0

    def test_dominant_scale_is_near_annual(self):
        s = self._load()
        dom = s["periodogram"]["dominant_period_days"]
        peak = s["autocorrelation"]["peak_lag_days"]
        lo, hi = s["autocorrelation"]["peak_search_window_days"]
        assert 350 <= dom <= 380, dom          # dominant FFT period near one year
        assert lo <= peak <= hi                 # ACF peak inside the search window
        assert 350 <= peak <= 380, peak         # ... and itself near one year
        assert s["autocorrelation"]["acf_at_lag_365"] > 0.5
        assert s["autocorrelation"]["acf_at_lag_182_half_year"] < 0  # anti-phase half-year

    def test_post_hoc_scope_guard(self):
        s = self._load()
        purpose = s["purpose"].lower()
        assert "post-hoc" in purpose
        assert "not used to select or retune" in purpose
        assert "not a hypothesis test" in purpose


@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestFigures:
    def test_all_figures_exist_nonempty(self):
        expected = [
            "weather_temp_series.png", "weather_pca_panels.png",
            "weather_mapper_reference.png", "weather_mapper_lens_comparison.png",
            "weather_mapper_grid.png", "weather_seasonal_ph_reference_diagram.png",
            "weather_seasonal_ph_reference_barcode.png",
            "weather_seasonal_ph_sweep.png", "weather_state_space_ph.png",
            "weather_state_space_ph_barcode.png", "weather_embedding_pca.png",
            "weather_seasonality_check.png",
        ]
        for name in expected:
            p = FIGS / name
            assert p.exists() and p.stat().st_size > 5000, name

    def test_captions_cover_all_figures(self):
        caps = json.loads((FIGS / "captions.json").read_text())
        for p in FIGS.glob("weather_*.png"):
            assert p.name in caps, p.name
        # honesty statements embedded where required
        assert "DESCRIPTIVE" in caps["weather_pca_panels.png"]
        assert "encodes calendar" in caps["weather_mapper_lens_comparison.png"].lower()
        assert "not automatically topological loops" in caps["weather_mapper_reference.png"]
        assert "NOT proof" in caps["weather_seasonal_ph_reference_diagram.png"]
        # Stage-3 honesty requirements on the revised captions
        assert "NOT connected" in caps["weather_seasonal_ph_sweep.png"]
        assert "does not by itself prove" in caps["weather_seasonal_ph_sweep.png"]
        assert "negative representation contrast" in caps["weather_state_space_ph_barcode.png"].lower()
        assert "POST-HOC" in caps["weather_seasonality_check.png"]
        assert "not a hypothesis test" in caps["weather_seasonality_check.png"].lower()


@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestSweepLabelPlacement:
    """Stage-4 regression: the sweep-figure labels must not overlap.

    A VLM inspection of the Stage-3 weather_seasonal_ph_sweep.png found
    overlapping labels near the three near-annual configurations (spans
    360/364/365 d) and labels covering markers / the annual-period note.
    The Stage-4 figure uses leader lines with hand-placed anchors; this
    test verifies, from the saved analysis results, that (a) no two label
    bounding boxes intersect in either panel, (b) no label box covers any
    data marker, and (c) all six configurations are labelled.
    """

    def _render(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from render_weather_figures import render_sweep_figure
        analysis = json.loads((RESULTS / "weather_analysis_results.json").read_text())
        fig, axes, texts, points = render_sweep_figure(analysis)
        return fig, axes, texts, points

    @staticmethod
    def _text_boxes(fig, arts):
        """Text-only bounding boxes (Annotation.get_window_extent would also
        include the leader-line arrow, which legitimately crosses other
        annotations' boxes)."""
        from matplotlib.text import Text
        fig.canvas.draw()
        ren = fig.canvas.get_renderer()
        return [Text.get_window_extent(t, ren) for t in arts]

    def test_no_label_bbox_overlaps(self):
        fig, _axes, texts, _points = self._render()
        try:
            for pi, arts in texts.items():
                boxes = self._text_boxes(fig, arts)
                names = [t.get_text() for t in arts]
                for i in range(len(boxes)):
                    for j in range(i + 1, len(boxes)):
                        assert not boxes[i].overlaps(boxes[j]), (
                            f"panel {pi}: labels {names[i]!r} and {names[j]!r} "
                            f"overlap (Stage-3 regression)")
        finally:
            import matplotlib.pyplot as plt
            plt.close(fig)

    def test_no_label_covers_a_marker(self):
        fig, axes, texts, points = self._render()
        try:
            fig.canvas.draw()
            for pi, arts in texts.items():
                boxes = self._text_boxes(fig, arts)
                names = [t.get_text() for t in arts]
                marker_px = [axes[pi].transData.transform((x, y))
                             for x, y in points[pi]]
                for b, nm in zip(boxes, names):
                    for (px, py) in marker_px:
                        assert not (b.x0 <= px <= b.x1 and b.y0 <= py <= b.y1), (
                            f"panel {pi}: label {nm!r} covers a data marker")
        finally:
            import matplotlib.pyplot as plt
            plt.close(fig)

    def test_all_six_configs_labelled_with_annual_line(self):
        fig, _axes, texts, _points = self._render()
        try:
            for pi, arts in texts.items():
                joined = " | ".join(t.get_text() for t in arts)
                for tau, d in [(30, 8), (45, 9), (52, 8), (73, 6), (60, 8), (90, 8)]:
                    assert f"={tau}, d={d}" in joined, f"panel {pi}: config tau={tau} missing"
                assert any("365.25" in t.get_text() for t in arts), \
                    f"panel {pi}: annual-period annotation missing"
                assert any("(ref)" in t.get_text() for t in arts), \
                    f"panel {pi}: reference marker label missing"
        finally:
            import matplotlib.pyplot as plt
            plt.close(fig)


@pytest.mark.skipif(not HAS_RESULTS, reason=reason)
class TestClaimsEvidenceTable:
    def test_table_rows_reference_existing_artifacts(self):
        claims = json.loads((RESULTS / "claims_evidence.json").read_text())
        repo_root = EXT.parents[1]
        assert len(claims["rows"]) >= 8
        for row in claims["rows"]:
            assert {"id", "claim", "evidence_file", "figure"} <= set(row)
            for ref in (row["evidence_file"], row["figure"]):
                if ref:
                    p = repo_root / ref
                    assert p.exists(), f"missing evidence artifact {ref}"
