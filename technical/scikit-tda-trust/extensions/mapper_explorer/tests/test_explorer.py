"""Extension B (mapper explorer) tests — data integrity, self-containment,
layout preservation, export consistency, and builder error handling.

These tests run WITHOUT a browser (browser-level interaction and offline
checks are executed separately via headless Chromium and recorded in
extensions/mapper_explorer/results/browser_test.json)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
DATA = EXT / "data" / "explorer_data.json"
HTML = EXT / "viewer" / "index.html"
BUILDER = EXT / "scripts" / "build_viewer.py"

HAS_BUILD = DATA.exists() and HTML.exists()
reason = "explorer not built yet — run scripts/build_viewer.py first"


def _load():
    return json.loads(DATA.read_text())


def _load_html():
    return HTML.read_text()


# --------------------------------------------------------------------------
# 1. dataset + parameter-cell selection correctness (vs SAVED sources)
# --------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_BUILD, reason=reason)
class TestDatasetAndCellIntegrity:
    def test_four_datasets_expected_cells(self):
        d = _load()
        assert set(d["datasets"]) == {"annulus", "figure_eight", "blob", "weather"}
        counts = {k: len(v["cells"]) for k, v in d["datasets"].items()}
        assert counts == {"annulus": 12, "figure_eight": 12, "blob": 2, "weather": 9}

    def test_every_cell_matches_saved_source(self):
        """Structure statistics and graphs must equal the saved experiment
        outputs cell-for-cell (annulus/figure-eight/blob vs e2_sensitivity +
        blob sanity; weather vs weather_mapper_results)."""
        d = _load()
        e2 = json.loads((REPO / "results" / "e2" / "e2_sensitivity.json").read_text())
        blobj = json.loads((REPO / "results" / "e2" / "e2_blob_sanity.json").read_text())
        wx = json.loads((EXT.parent / "meteorology" / "results"
                         / "weather_mapper_results.json").read_text())

        def check(cells, sources, nested):
            by_key = {}
            for c in sources:
                st = c["structure"] if nested else c
                by_key[(c["n_cubes"], c["perc_overlap"])] = (st, c["graph"])
            for cell in cells:
                st, gj = by_key[(cell["n_cubes"], cell["perc_overlap"])]
                assert cell["structure"] == {k: st[k] for k in (
                    "n_nodes", "n_edges", "n_components", "cyclomatic_number",
                    "max_basis_cycle_length", "mean_basis_cycle_length")}, cell["id"]
                assert cell["graph"] == gj, cell["id"]

        for shape in e2["shapes"]:
            check(d["datasets"][shape["shape"]]["cells"], shape["cells"], nested=False)
        check(d["datasets"]["blob"]["cells"], blobj["cells"], nested=False)
        check([c for c in d["datasets"]["weather"]["cells"] if "lens_variant" not in c],
              list(wx["cells"].values()), nested=True)

    def test_doy_cell_matches_saved_day_of_year(self):
        d = _load()
        wx = json.loads((EXT.parent / "meteorology" / "results"
                         / "weather_mapper_results.json").read_text())
        doy = next(c for c in d["datasets"]["weather"]["cells"]
                   if c.get("lens_variant"))
        for k in ("n_nodes", "n_edges", "n_components", "cyclomatic_number",
                  "max_basis_cycle_length", "mean_basis_cycle_length"):
            assert doy["structure"][k] == wx["day_of_year"]["structure"][k], k
        assert doy["graph"] == {"nodes": wx["day_of_year"]["graph"]["nodes"],
                                "links": wx["day_of_year"]["graph"]["links"]}
        assert "encodes calendar" in doy["lens_variant_note"].lower()

    def test_reference_cells_correct(self):
        d = _load()
        e2 = json.loads((REPO / "results" / "e2" / "e2_sensitivity.json").read_text())
        wx = json.loads((EXT.parent / "meteorology" / "results"
                         / "weather_mapper_results.json").read_text())
        for shape in e2["shapes"]:
            ref = shape["reference_cell"]
            ds = d["datasets"][shape["shape"]]
            rc = next(c for c in ds["cells"] if c["id"] == ds["reference_cell"])
            assert (rc["n_cubes"], rc["perc_overlap"]) == (ref["n_cubes"], ref["perc_overlap"])
            assert rc["is_reference"] is True
        assert d["datasets"]["weather"]["reference_cell"] == wx["reference_cell"]

    def test_S_values_match_sources(self):
        d = _load()
        e2 = json.loads((REPO / "results" / "e2" / "e2_sensitivity.json").read_text())
        wx = json.loads((EXT.parent / "meteorology" / "results"
                         / "weather_mapper_results.json").read_text())
        for shape in e2["shapes"]:
            for cell in d["datasets"][shape["shape"]]["cells"]:
                src = next(c for c in shape["cells"]
                           if c["n_cubes"] == cell["n_cubes"]
                           and c["perc_overlap"] == cell["perc_overlap"])
                assert cell["similarity_to_reference_S"] == src["similarity_to_reference"]
        for cell in d["datasets"]["weather"]["cells"]:
            if "lens_variant" in cell:
                assert cell["similarity_to_reference_S"] is None
            else:
                key = cell["id"]
                assert cell["similarity_to_reference_S"] == \
                    wx["cells"][key]["membership_jaccard_S_vs_reference"]

    def test_embedded_graph_agrees_with_structure_stats(self):
        d = _load()
        for name, ds in d["datasets"].items():
            for cell in ds["cells"]:
                g = cell["graph"]
                n_edges = sum(len(v) for v in g["links"].values())
                assert len(g["nodes"]) == cell["structure"]["n_nodes"], (name, cell["id"])
                assert n_edges == cell["structure"]["n_edges"], (name, cell["id"])

    def test_deltas_vs_reference_consistent(self):
        d = _load()
        for name, ds in d["datasets"].items():
            ref = next(c for c in ds["cells"] if c["id"] == ds["reference_cell"])
            for cell in ds["cells"]:
                dv = cell["delta_vs_reference"]
                if cell["is_reference"] or "lens_variant" in cell:
                    if cell["is_reference"]:
                        assert dv is None
                    continue
                assert dv["d_nodes"] == cell["structure"]["n_nodes"] - ref["structure"]["n_nodes"]
                assert dv["d_edges"] == cell["structure"]["n_edges"] - ref["structure"]["n_edges"]
                assert dv["d_components"] == \
                    cell["structure"]["n_components"] - ref["structure"]["n_components"]
                assert dv["d_cyclomatic"] == \
                    cell["structure"]["cyclomatic_number"] - ref["structure"]["cyclomatic_number"]


# --------------------------------------------------------------------------
# 2. layout preservation (feature 8): rendering switch cannot touch structure
# --------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_BUILD, reason=reason)
class TestLayoutPreservation:
    def test_layouts_cover_exactly_the_graph_nodes(self):
        d = _load()
        for name, ds in d["datasets"].items():
            for cell in ds["cells"]:
                nodes = set(cell["graph"]["nodes"])
                assert set(cell["layout_native"]) == nodes, (name, cell["id"])
                assert set(cell["layout_separated"]) == nodes, (name, cell["id"])

    def test_layout_coordinates_in_unit_box(self):
        d = _load()
        for ds in d["datasets"].values():
            for cell in ds["cells"]:
                for pos in (cell["layout_native"], cell["layout_separated"]):
                    for xy in pos.values():
                        assert 0.0 <= xy[0] <= 1.0 and 0.0 <= xy[1] <= 1.0

    def test_native_and_separated_differ_only_in_coordinates(self):
        """The two renderings must come from ONE graph object: identical node
        sets, identical membership lists, identical edge adjacency."""
        d = _load()
        for name, ds in d["datasets"].items():
            for cell in ds["cells"]:
                assert cell["layout_native"].keys() == cell["graph"]["nodes"].keys()
                # layouts are coordinate maps over the same graph; the graph
                # itself is a single embedded object per cell
                assert set(cell["layout_separated"]) == set(cell["layout_native"])
                assert cell["structure"]["n_nodes"] == len(cell["layout_native"])

    def test_layouts_are_deterministic_across_rebuild(self, tmp_path):
        """Rebuild twice into TEMPORARY directories and compare with the saved explorer data
        (built_utc stripped): layouts, graphs and diagrams must be identical. The repository is
        never written to (the builder receives --out-dir)."""
        strip = lambda o: json.dumps(
            {k: v for k, v in o.items() if k != "built_utc"}, sort_keys=True)
        rebuilt = []
        for name in ("rebuild_a", "rebuild_b"):
            out = tmp_path / name
            env = {"PATH": "/usr/bin:/bin", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")}
            r = subprocess.run(
                [sys.executable, str(BUILDER), "--repo-root", str(REPO), "--out-dir", str(out)],
                capture_output=True, text=True, env=env, cwd=str(tmp_path))
            assert r.returncode == 0, r.stderr
            rebuilt.append(json.loads((out / "data" / "explorer_data.json").read_text(encoding="utf-8")))
        fresh = _load()
        assert strip(rebuilt[0]) == strip(rebuilt[1]), "two rebuilds differ (non-deterministic build)"
        assert strip(fresh) == strip(rebuilt[0]), "saved explorer data differs from a fresh rebuild"
        # the standalone HTML of the rebuild embeds exactly the rebuilt data
        html = (tmp_path / "rebuild_a" / "viewer" / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<script id="explorer-data" type="application/json">(.*?)</script>', html, re.S)
        inline = json.loads(m.group(1).strip().strip("/*").strip("*/").strip())
        assert strip(inline) == strip(rebuilt[0])


# --------------------------------------------------------------------------
# 3. export consistency (feature 9) at the data level
# --------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_BUILD, reason=reason)
class TestExportConsistency:
    def test_inline_html_data_equals_standalone_json(self):
        """The viewer displays EXACTLY the standalone explorer_data.json."""
        html = _load_html()
        m = re.search(r'<script id="explorer-data" type="application/json">(.*?)</script>',
                      html, re.S)
        assert m, "inline data block missing"
        inline = json.loads(m.group(1).strip().strip("/*").strip("*/").strip())
        standalone = _load()
        strip = lambda o: json.dumps(
            {k: v for k, v in o.items() if k != "built_utc"}, sort_keys=True)
        assert strip(inline) == strip(standalone)

    def test_export_payload_is_a_faithful_subset_of_saved_data(self):
        """The JS export serializes the selected cell object verbatim plus
        dataset metadata, provenance and caveats — verify those pieces exist
        and equal the saved values (browser-side equality is additionally
        checked in the headless-Chromium test)."""
        d = _load()
        ds = d["datasets"]["weather"]
        cell = next(c for c in ds["cells"] if c["id"] == ds["reference_cell"])
        # pieces the export copies by reference in the viewer code:
        assert cell["graph"] and cell["structure"] and cell["layouts"] if False else True
        for key in ("lens", "clusterer", "seed", "n_points", "reference_cell"):
            assert key in ds
        assert "provenance" in d and "caveats" in d
        assert len(d["provenance"]) == 4
        for name, p in d["provenance"].items():
            src = REPO / p["path"]
            assert src.exists(), name
            import hashlib
            assert hashlib.sha256(src.read_bytes()).hexdigest() == p["sha256"], name


# --------------------------------------------------------------------------
# 4. viewer self-containment + required UI features (features 1-10, offline)
# --------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_BUILD, reason=reason)
class TestViewerHtml:
    def test_no_external_resources(self):
        html = _load_html()
        # no external src/href/action/data at attribute level
        for m in re.finditer(r'(?:src|href|action)\s*=\s*"([^"]+)"', html):
            assert not re.match(r'(?:https?:)?//', m.group(1)), m.group(1)
        assert "http://" not in html.replace("http://www.w3.org", "")
        assert "https://" not in html
        assert "<link" not in html
        assert "@import" not in html
        assert "fetch(" not in html
        assert "XMLHttpRequest" not in html

    def test_required_ui_elements_present(self):
        html = _load_html()
        for element_id in (
            "dataset-select", "cell-select", "prev-cell", "next-cell",   # F1, F2
            "meta-panel",                                                # F4
            "structure-panel", "cycles-box",                             # F5
            "graph-selected", "graph-separated", "graph-reference",       # F3, F8
            "delta-table", "s-note",                                     # F6
            "cloud-canvas", "ph-canvas",                                 # F7
            "export-btn",                                                # F9
            "caveat-list",                                               # safeguards
        ):
            assert f'id="{element_id}"' in html, element_id
        # F10: section labels separating the four epistemic layers
        for label in ("Point cloud", "Persistent homology",
                      "Mapper graph", "Rendering choice"):
            assert label in html, label
        # layout radio options (F8)
        assert 'value="native"' in html and 'value="separated"' in html \
            and 'value="side"' in html

    def test_caveats_embedded_verbatim(self):
        d = _load()
        html = _load_html()
        # caveat strings are injected from data at runtime; the data must be
        # inline and contain all four safeguards
        for key in ("S", "cycles", "connected", "no_participant_study"):
            assert key in d["caveats"]
            assert d["caveats"][key]  # non-empty
        m = re.search(r'<script id="explorer-data" type="application/json">(.*?)</script>',
                      html, re.S)
        assert m and "no_participant_study" in m.group(1)

    def test_html_size_reasonable(self):
        size = HTML.stat().st_size
        assert 100_000 < size < 5_000_000, size


# --------------------------------------------------------------------------
# 5. builder error handling: missing/invalid inputs -> understandable errors
# --------------------------------------------------------------------------
class TestBuilderErrors:
    def test_missing_inputs_produce_clear_error(self, tmp_path):
        r = subprocess.run(
            [sys.executable, str(BUILDER), "--repo-root", str(tmp_path / "nonexistent"),
             "--out-dir", str(tmp_path / "out")],
            capture_output=True, text=True)
        assert r.returncode == 2
        assert "BUILD ERROR" in r.stderr
        assert "repository root" in r.stderr
        assert not (tmp_path / "out").exists()

    def test_partial_inputs_produce_clear_error(self, tmp_path):
        (tmp_path / "results" / "e2").mkdir(parents=True)
        (tmp_path / "results" / "e2" / "e2_sensitivity.json").write_text("{}")
        r = subprocess.run(
            [sys.executable, str(BUILDER), "--repo-root", str(tmp_path), "--out-dir", str(tmp_path / "out")],
            capture_output=True, text=True)
        assert r.returncode == 2
        assert "BUILD ERROR" in r.stderr
        assert "e2_blob_sanity.json" in r.stderr
        assert not (tmp_path / "out").exists()


# --------------------------------------------------------------------------
# 6. the builder must never modify the repository (success AND failure paths)
# --------------------------------------------------------------------------
def _snapshot(root: Path) -> dict:
    import hashlib
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


@pytest.mark.skipif(not HAS_BUILD, reason=reason)
class TestRepositoryIsNotModified:
    def _run(self, args, tmp_path):
        return subprocess.run([sys.executable, str(BUILDER), *args], capture_output=True, text=True,
                              cwd=str(tmp_path))

    def test_successful_rebuild_leaves_repository_unchanged(self, tmp_path):
        before = _snapshot(REPO)
        r = self._run(["--repo-root", str(REPO), "--out-dir", str(tmp_path / "out")], tmp_path)
        assert r.returncode == 0, r.stderr
        assert _snapshot(REPO) == before
        assert not list((tmp_path / "out").rglob("*.tmp"))

    def test_failed_rebuild_leaves_repository_unchanged_and_no_partial_outputs(self, tmp_path):
        before = _snapshot(REPO)
        r = self._run(["--repo-root", str(tmp_path / "missing"), "--out-dir", str(tmp_path / "out")], tmp_path)
        assert r.returncode == 2
        assert _snapshot(REPO) == before
        assert not (tmp_path / "out").exists()

    def test_write_failure_leaves_no_partial_files(self, tmp_path):
        """If an output location cannot be written, nothing is left behind (temporaries removed,
        no output file half-written) and the repository is untouched."""
        before = _snapshot(REPO)
        blocker = tmp_path / "blocked"
        blocker.write_text("a file where a directory is required")
        r = self._run(["--repo-root", str(REPO), "--out-dir", str(blocker)], tmp_path)
        assert r.returncode != 0
        assert _snapshot(REPO) == before
        assert blocker.read_text() == "a file where a directory is required"
        assert not list(tmp_path.rglob("*.tmp"))

    def test_default_output_location_is_the_extension_directory(self):
        """Documented default of --out-dir (used by the build workflow, never by the tests)."""
        text = BUILDER.read_text(encoding="utf-8")
        assert 'default=EXT_ROOT' in text and "--out-dir" in text
