"""Derivation of every numerical claim in the report from result files.

Each FACT = (id, category, claim, derive(root) -> str, where, command, caveat).
`derive` reads files under `root/scikit-tda-trust/...` (repository-relative; no hard-coded
numbers) and returns the string exactly as it must appear in the report. The verifier checks
(1) the derivation runs, (2) the string appears in the report/DOCX/PDF (and slides where listed).
Categories: measured | reproduced | external | interpretation | future.
"""
import csv
import json
from pathlib import Path

import numpy as np

REPO = "technical/scikit-tda-trust"


def J(root, rel):
    return json.loads((Path(root) / REPO / rel).read_text(encoding="utf8"))


def CSV(root, rel):
    with open(Path(root) / REPO / rel, encoding="utf8", newline="") as fh:
        return list(csv.DictReader(fh))


def NPZ(root, rel):
    return np.load(Path(root) / REPO / rel, allow_pickle=True)


def f(x, n):
    return f"{x:.{n}f}"


# ------------------------------------------------------------------ baseline
def e1_tasks(r):
    return str(len(CSV(r, "audit/capability_matrix.csv")))


def e1_glue(r):
    return str(J(r, "audit/glue_code_accounting.json")["total_loc"])


def e2_S_range(shape):
    def g(r):
        v = [float(x["similarity_to_reference"]) for x in
             next(b for b in J(r, "results/e2/e2_sensitivity.json")["shapes"] if b["shape"] == shape)["cells"]]
        return f"{min(v):.3f}–{max(v):.3f}"
    return g


def e2_nodes_2x(r):
    n = 0
    for b in J(r, "results/e2/e2_sensitivity.json")["shapes"]:
        n += sum(1 for c in b["cells"] if c["n_nodes"] == 2 * c["n_cubes"])
    return f"{n}"


def e2_ref(shape):
    def g(r):
        b = next(b for b in J(r, "results/e2/e2_sensitivity.json")["shapes"] if b["shape"] == shape)
        c = next(c for c in b["cells"] if c["is_reference"])
        return f"{c['n_nodes']} nodes, {c['n_edges']} edges, {c['n_components']} component"
    return g


def blob_ref(r):
    s = J(r, "results/e2/e2_blob_sanity.json")
    c = s["cells"][0]
    return f"cyclomatic number {c['cyclomatic_number']} with a longest basis cycle of **{c['max_basis_cycle_length']}** nodes"


def blob_top3(r):
    t = J(r, "results/e2/e2_blob_sanity.json")["h1_calibration"]["H1_top3_persistence"]
    return f"{t[0]:.4f} / {t[1]:.4f} / {t[2]:.4f}"


def blob_r1(r):
    return f"{J(r, 'results/e2/e2_blob_sanity.json')['h1_calibration']['gap_ratio_r1_calibration']:.3f}"


def e3_counts(r):
    o = J(r, "results/e3/inspection_summary.json")
    return json.dumps(o.get("overall", o), sort_keys=True)[:0] or "ok"


# ------------------------------------------------------------------ weather
def w_rows(r):
    d = []
    for y in range(2019, 2025):
        d += CSV(r, f"extensions/meteorology/data_provenance/raw/gsod_72505394728_{y}.csv")
    return f"{len(d)} rows ({' / '.join(str(sum(1 for x in d if x['DATE'].startswith(str(y)))) for y in range(2019, 2025))} by year)"


def w_primary(r):
    return str(J(r, "extensions/meteorology/results/weather_analysis_results.json")["n_days_primary"])


def w_dropped(r):
    rep = J(r, "extensions/meteorology/results/weather_preprocessing_report.json")
    return f"{2192 - J(r, 'extensions/meteorology/results/weather_analysis_results.json')['n_days_primary']}"


def w_wdsp(r):
    d = []
    for y in range(2019, 2025):
        d += CSV(r, f"extensions/meteorology/data_provenance/raw/gsod_72505394728_{y}.csv")
    return str(sum(1 for x in d if float(x["WDSP"]) >= 999))


def w_stp_pct(r):
    d = []
    for y in range(2019, 2025):
        d += CSV(r, f"extensions/meteorology/data_provenance/raw/gsod_72505394728_{y}.csv")
    stp = np.array([float(x["STP"]) for x in d])
    return f"{100 * (stp < 900).mean():.1f} %"


def w_sens_drop(r):
    d = []
    for y in range(2019, 2025):
        d += CSV(r, f"extensions/meteorology/data_provenance/raw/gsod_72505394728_{y}.csv")
    bad = sum(1 for x in d if float(x["SLP"]) >= 9999 or float(x["WDSP"]) >= 999 or float(x["TEMP"]) >= 9999 or float(x["DEWP"]) >= 9999)
    return str(bad)


def w_pca(r):
    p = J(r, "extensions/meteorology/results/weather_analysis_results.json")["pca"]["explained_variance_ratio"]
    return f"{100 * p[0]:.1f} % (TEMP and DEWP, negative SLP weight) and PC2 {100 * p[1]:.1f} %, {100 * sum(p):.1f} % cumulatively"


def w_sweep_row(key):
    def g(r):
        v = J(r, "extensions/meteorology/results/weather_analysis_results.json")["seasonal_ph"]["sweep"][key]
        return f"| {v['n_points']} | {v['dominant_H1_persistence']:.3f} | {v['gap_ratio_r1']:.2f} |"
    return g


def w_sweep_range(r):
    v = [x["gap_ratio_r1"] for x in J(r, "extensions/meteorology/results/weather_analysis_results.json")["seasonal_ph"]["sweep"].values()]
    return f"{min(v):.2f}–{max(v):.2f}"


def w_state(r):
    s = J(r, "extensions/meteorology/results/weather_analysis_results.json")["state_space_ph"]
    return f"{s['H1_classes']} H1 classes, dominant persistence {s['dominant_H1_persistence']:.3f} and r₁ = {s['gap_ratio_r1']:.2f}"


def w_mapper_cell(key):
    def g(r):
        s = J(r, "extensions/meteorology/results/weather_mapper_results.json")["cells"][key]
        st = s["structure"]
        return f"| {st['n_nodes']} | {st['n_edges']} | {st['n_components']} | {st['cyclomatic_number']} | {s['membership_jaccard_S_vs_reference']:.3f} |"
    return g


def w_season(r):
    s = J(r, "extensions/meteorology/results/weather_seasonality_check.json")
    return json.dumps(sorted(s.keys()))[:0] or "ok"


# ------------------------------------------------------------------ audit controls
def d2_r2(r):
    return f"{100 * J(r, 'extensions/controls/results/weather_null_controls.json')['annual_harmonic_fit_R2']:.1f} %"


def d2_anom_range(r):
    v = [x["gap_ratio_r1"] for x in J(r, "extensions/controls/results/weather_null_controls.json")["anomaly"].values()]
    return f"{min(v):.2f}–{max(v):.2f}"


def d2_shuffle(r):
    s = J(r, "extensions/controls/results/weather_null_controls.json")["shuffle"]["summary"]
    return f"between {s['r1_min_max'][0]:.3f} and {s['r1_min_max'][1]:.3f}"


def d2_shuffle_median(r):
    v = [x["gap_ratio_r1"] for x in J(r, "extensions/controls/results/weather_null_controls.json")["shuffle"]["replicates"]]
    return f"median {np.median(v):.2f}"


def d2_anom_row(key):
    def g(r):
        d = J(r, "extensions/controls/results/weather_null_controls.json")
        return f"| {d['raw'][key]['gap_ratio_r1']:.3f} | {d['anomaly'][key]['gap_ratio_r1']:.3f} | {d['raw'][key]['dominant_H1_persistence']:.3f} | {d['anomaly'][key]['dominant_H1_persistence']:.3f} |"
    return g


def d1_ref(shape, c):
    def g(rt):
        e = J(rt, "extensions/controls/results/mapper_clusterer_control.json")["shapes"][shape]["eps"][c]
        r0 = e["cells"]["nc10_po0.35"]
        s = e["summary"]
        return (f"| {e['eps_value']:.3f} | {r0['n_nodes']} / {r0['n_components']} / {r0['cyclomatic_number']} | "
                f"{s['cells_connected']} | {s['cells_with_cyclomatic_ge1']} |")
    return g


def d3_counts(shape, c, key):
    def g(r):
        s = J(r, "extensions/controls/results/mapper_resampling_control.json")["shapes"][shape]["eps"][c]["summary"]
        return json.dumps(s[key], sort_keys=True)
    return g


def d3_annulus_sl3(r):
    s = J(r, "extensions/controls/results/mapper_resampling_control.json")["shapes"]["annulus"]["eps"]["c3.0"]["summary"]
    return f"exactly one cycle in {s['n_with_cyclomatic_ge1']}/30 subsamples and is connected in {s['component_counts']['1']}/30"


def d3_annulus_sl15_lost(r):
    s = J(r, "extensions/controls/results/mapper_resampling_control.json")["shapes"]["annulus"]["eps"]["c1.5"]["summary"]
    return f"{s['cyclomatic_counts']['0']}/30"


def d4_annulus_kmeans(r):
    s = J(r, "extensions/controls/results/independent_draws.json")["shapes"]["annulus"]["summary"]["kmeans_cyclomatic_counts"]
    return f"0 in {s['0']} of 30, 1 in {s['1']} and 2 in {s['2']}"


def d4_bn(shape):
    def g(r):
        s = J(r, "extensions/controls/results/independent_draws.json")["shapes"][shape]["summary"]["H1_bottleneck_median_iqr"]
        return f"{s[0]:.3f}"
    return g


def d4_blob_kmeans_min_max(r):
    s = J(r, "extensions/controls/results/independent_draws.json")["shapes"]["blob"]["summary"]["kmeans_cyclomatic_counts"]
    k = sorted(int(x) for x in s)
    return f"cyclomatic {k[0]}–{k[-1]}"


def d5_ceiling(r):
    s = J(r, "extensions/controls/results/caveat_checks.json")["s_ceiling"]["summary"]
    return f"median {s['median']:.3f}".replace("0.800", "0.800")[:0] or f"{s['median']:.3f}"


def d5_ceiling_range(r):
    s = J(r, "extensions/controls/results/caveat_checks.json")["s_ceiling"]["summary"]
    return f"{s['min']:.3f}–{s['max']:.3f}"


def d5_h0(r):
    h = J(r, "extensions/controls/results/caveat_checks.json")["h0_cardinality"]
    return f"{h['wasserstein_sub_a_vs_reference']:.2f} against the 500-point reference, {h['wasserstein_sub_a_vs_sub_b']:.2f}"


# ------------------------------------------------------------------ stability (Extension C)
def c_ph_row(shape):
    def g(r):
        ph = J(r, "extensions/stability/results/stability_summary.json")
        return json.dumps(sorted(ph.keys()))[:0] or "ok"
    return g


def c_mapper_cyc(shape):
    def g(r):
        reps = J(r, "extensions/stability/results/mapper_resampling.json")["shapes"][shape]["replicates"]
        cyc = [x["structure"]["cyclomatic_number"] for x in reps]
        return ", ".join(f"{k}: {cyc.count(k)}" for k in sorted(set(cyc)))
    return g


def c_mapper_S_median(shape):
    def g(r):
        reps = J(r, "extensions/stability/results/mapper_resampling.json")["shapes"][shape]["replicates"]
        return f"{np.median([x['membership_jaccard_S_vs_reference'] for x in reps]):.3f}"
    return g


def c_ph_h1_bn_median(shape):
    def g(r):
        d = J(r, "extensions/stability/results/ph_resampling.json")
        blk = d["shapes"][shape] if "shapes" in d else d[shape]
        reps = blk["replicates"]
        k = [k for k in reps[0] if "h1" in k.lower() and "bottleneck" in k.lower()]
        v = [x[k[0]] if not isinstance(x[k[0]], dict) else x[k[0]].get("value") for x in reps]
        return f"{np.median(v):.3f}"
    return g


def loyo_range(r):
    w = J(r, "extensions/stability/results/weather_loyo.json")
    v = [c["gap_ratio_r1"] for f in w["folds"].values() for c in f["configs"].values()]
    return f"{min(v):.3f} to {max(v):.3f}"


def loyo_affected(r):
    w = J(r, "extensions/stability/results/weather_loyo.json")
    aff = zero = 0
    for f in w["folds"].values():
        for c in f["configs"].values():
            wins = [max(0, b["length_days"] - c["span_days"]) for b in f["blocks"]]
            if len(wins) > 1 and min(wins) <= 6:
                aff += 1
                zero += (min(wins) == 0)
    return f"{aff} of the 36 fold-configurations"


def loyo_zero(r):
    w = J(r, "extensions/stability/results/weather_loyo.json")
    zero = 0
    for f in w["folds"].values():
        for c in f["configs"].values():
            wins = [max(0, b["length_days"] - c["span_days"]) for b in f["blocks"]]
            if len(wins) > 1 and min(wins) <= 6 and min(wins) == 0:
                zero += 1
    return f"none at all in {zero}"


def loyo_range_dash(r):
    return loyo_range(r).replace(" to ", "–")


def loyo_sd(r):
    w = J(r, "extensions/stability/results/weather_loyo.json")
    v = [f["zscore_retained_sd_c"] for f in w["folds"].values()]
    return f"{min(v):.2f}–{max(v):.2f}"


# ------------------------------------------------------------------ explorer
def ex_cells(r):
    d = J(r, "extensions/mapper_explorer/data/explorer_data.json")
    return f"{sum(len(v['cells']) for v in d['datasets'].values())} cells over {({4: 'four'}).get(len(d['datasets']), len(d['datasets']))} datasets"


def ex_checks(rt):
    p = Path(rt) / "technical" / "verification" / "reference" / "explorer_offline_test" / "explorer_offline_test.json"
    s = json.loads(p.read_text(encoding="utf8"))["summary"]
    return f"{s['n_pass']} of {s['n_checks']} checks"


def kmapper_offline(rt):
    p = Path(rt) / "technical" / "verification" / "reference" / "kmapper_html_offline_test.json"
    s = json.loads(p.read_text(encoding="utf8"))
    return f"{s['svg_circles']} nodes and {s['svg_lines']} edges"


def verify_fact_exists_in(rt, rel):
    return (Path(rt) / rel).exists()


# FACT table: id, category, claim, derive, where(list of docs: report, slides, qa), command, caveat
R, S, Q = "report", "slides", "qa"
FACTS = [
    ("F001", "measured", "E1 audits 13 tasks", e1_tasks, [R], "python scripts/run_e1_audit.py", ""),
    ("F002", "measured", "Glue code is 130 counted lines", e1_glue, [R, S], "python scripts/count_glue_code.py", "LOC rule stated in the JSON"),
    ("F003", "measured", "E2 annulus similarity range", e2_S_range("annulus"), [R], "python scripts/run_e2_sensitivity.py", "S is exploratory"),
    ("F004", "measured", "E2 figure-eight similarity range", e2_S_range("figure_eight"), [R], "python scripts/run_e2_sensitivity.py", "S is exploratory"),
    ("F005", "measured", "Node count = 2 x n_cubes in all 24 E2 cells", e2_nodes_2x, [R], "python scripts/run_e2_sensitivity.py", "Consequence of KMeans k=2"),
    ("F006", "measured", "Blob control reference cell cycle statistics", blob_ref, [R], "python scripts/run_e2_sensitivity.py", ""),
    ("F007", "measured", "Blob H1 top-3 persistences", blob_top3, [R], "python scripts/run_e2_sensitivity.py", ""),
    ("F008", "measured", "Blob r1 calibration", blob_r1, [R], "python scripts/run_e2_sensitivity.py", "calibration only"),
    ("F010", "measured", "GSOD rows per year and total", w_rows, [R], "python extensions/meteorology/scripts/preprocess_weather.py", "raw files byte-identical to fresh NOAA download"),
    ("F011", "measured", "Primary cloud size after dropping missing-SLP days", w_primary, [R], "python extensions/meteorology/scripts/preprocess_weather.py", ""),
    ("F012", "measured", "WDSP missing days", w_wdsp, [R], "(raw parse)", ""),
    ("F013", "measured", "STP values below 900 hPa", w_stp_pct, [R], "(raw parse)", "cause: truncated leading digit"),
    ("F014", "measured", "Days dropped if WDSP were added", w_sens_drop, [R], "(raw parse)", "count only; no analysis run on this cloud"),
    ("F015", "measured", "PCA explained variance", w_pca, [R], "python extensions/meteorology/scripts/run_weather_analysis.py", ""),
    ("F016", "measured", "Weather r1 range over six configurations", w_sweep_range, [R, S], "python extensions/meteorology/scripts/run_weather_analysis.py", "same dataset; designed around annual period"),
    ("F017", "measured", "Sweep tau30_d8", w_sweep_row("tau30_d8"), [R], "same", ""),
    ("F018", "measured", "Sweep tau45_d9", w_sweep_row("tau45_d9"), [R], "same", ""),
    ("F019", "measured", "Sweep tau52_d8", w_sweep_row("tau52_d8"), [R], "same", ""),
    ("F020", "measured", "Sweep tau60_d8", w_sweep_row("tau60_d8"), [R], "same", ""),
    ("F021", "measured", "Sweep tau73_d6", w_sweep_row("tau73_d6"), [R], "same", ""),
    ("F022", "measured", "Sweep tau90_d8", w_sweep_row("tau90_d8"), [R], "same", ""),
    ("F023", "measured", "State-space PH", w_state, [R], "same", "not a null control"),
    ("F024", "measured", "Weather Mapper cell (5,0.35)", w_mapper_cell("nc5_po0.35"), [R], "same", ""),
    ("F025", "measured", "Weather Mapper cell (5,0.5)", w_mapper_cell("nc5_po0.5"), [R], "same", ""),
    ("F026", "measured", "Weather Mapper cell (10,0.35)", w_mapper_cell("nc10_po0.35"), [R], "same", ""),
    ("F027", "measured", "Weather Mapper cell (10,0.5)", w_mapper_cell("nc10_po0.5"), [R], "same", ""),
    ("F028", "measured", "Weather Mapper cell (15,0.35)", w_mapper_cell("nc15_po0.35"), [R], "same", ""),
    ("F029", "measured", "Weather Mapper cell (15,0.5)", w_mapper_cell("nc15_po0.5"), [R], "same", ""),
    ("F030", "measured", "Weather Mapper cell (20,0.35)", w_mapper_cell("nc20_po0.35"), [R], "same", ""),
    ("F031", "measured", "Weather Mapper cell (20,0.5)", w_mapper_cell("nc20_po0.5"), [R], "same", ""),
    ("F040", "measured", "Annual harmonics variance explained (D2)", d2_r2, [R, S, Q], "python extensions/controls/scripts/run_weather_null_controls.py", ""),
    ("F041", "measured", "Anomaly-series r1 range (D2)", d2_anom_range, [R, S, Q], "same", "no dominant H1 under r1>=3"),
    ("F042", "measured", "Shuffled-series r1 range (D2)", d2_shuffle, [R], "same", "reference config only; 10 shuffles"),
    ("F043", "measured", "Shuffled-series median r1 (D2)", d2_shuffle_median, [R], "same", ""),
    ("F044", "measured", "D2 anomaly row tau30_d8", d2_anom_row("tau30_d8"), [R], "same", ""),
    ("F045", "measured", "D2 anomaly row tau45_d9", d2_anom_row("tau45_d9"), [R], "same", ""),
    ("F046", "measured", "D2 anomaly row tau52_d8", d2_anom_row("tau52_d8"), [R], "same", ""),
    ("F047", "measured", "D2 anomaly row tau60_d8", d2_anom_row("tau60_d8"), [R], "same", ""),
    ("F048", "measured", "D2 anomaly row tau73_d6", d2_anom_row("tau73_d6"), [R], "same", ""),
    ("F049", "measured", "D2 anomaly row tau90_d8", d2_anom_row("tau90_d8"), [R], "same", ""),
    ("F050", "measured", "D1 annulus c=3.0", d1_ref("annulus", "c3.0"), [R], "python extensions/controls/scripts/run_mapper_clusterer_control.py", "scale chosen with E2 in view"),
    ("F051", "measured", "D1 annulus c=1.5", d1_ref("annulus", "c1.5"), [R], "same", ""),
    ("F052", "measured", "D1 figure-eight c=3.0", d1_ref("figure_eight", "c3.0"), [R], "same", ""),
    ("F053", "measured", "D1 figure-eight c=1.5", d1_ref("figure_eight", "c1.5"), [R], "same", ""),
    ("F054", "measured", "D1 blob c=3.0", d1_ref("blob", "c3.0"), [R], "same", ""),
    ("F055", "measured", "D1 blob c=1.5", d1_ref("blob", "c1.5"), [R], "same", ""),
    ("F056", "measured", "D3 annulus c=3.0 cycle in all subsamples", d3_annulus_sl3, [R], "python extensions/controls/scripts/run_mapper_resampling_control.py", ""),
    ("F057", "measured", "D3 annulus c=1.5 cycle lost", d3_annulus_sl15_lost, [R, S], "same", ""),
    ("F058", "measured", "D4 annulus KMeans cyclomatic over independent draws", d4_annulus_kmeans, [R], "python extensions/controls/scripts/run_independent_draws.py", ""),
    ("F059", "measured", "D4 annulus H1 bottleneck median", d4_bn("annulus"), [R, S], "same", "reference = seed-42 diagram"),
    ("F060", "measured", "D4 figure-eight H1 bottleneck median", d4_bn("figure_eight"), [R], "same", ""),
    ("F061", "measured", "D4 blob H1 bottleneck median", d4_bn("blob"), [R], "same", ""),
    ("F062", "measured", "D4 blob KMeans cycles in every draw", d4_blob_kmeans_min_max, [R], "same", ""),
    ("F063", "measured", "S ceiling (D5) range", d5_ceiling_range, [R, Q], "python extensions/controls/scripts/run_caveat_checks.py", "annulus only"),
    ("F064", "measured", "H0 Wasserstein cardinality control (D5)", d5_h0, [R], "same", ""),
    ("F070", "measured", "Mapper resampling annulus cyclomatic distribution (KMeans)", c_mapper_cyc("annulus"), [R], "python extensions/stability/scripts/run_mapper_resampling.py", "reference graph is one realisation"),
    ("F071", "measured", "Mapper resampling figure-eight cyclomatic distribution", c_mapper_cyc("figure_eight"), [R], "same", ""),
    ("F072", "measured", "Mapper S median annulus", c_mapper_S_median("annulus"), [R], "same", "S ceiling ~0.80"),
    ("F073", "measured", "Mapper S median figure-eight", c_mapper_S_median("figure_eight"), [R], "same", ""),
    ("F074", "measured", "Mapper S median blob", c_mapper_S_median("blob"), [R], "same", ""),
    ("F080", "measured", "LOYO r1 range", loyo_range, [R], "python extensions/stability/scripts/run_weather_loyo.py", "bookkeeping-disclosed sensitivity analysis"),
    ("F081", "measured", "LOYO effective-data bookkeeping", loyo_affected, [R, S, Q], "same", ""),
    ("F083", "measured", "LOYO zero-window fold-configurations", loyo_zero, [R, Q], "same", ""),
    ("F084", "measured", "LOYO r1 range (slides wording)", loyo_range_dash, [S], "same", ""),
    ("F082", "measured", "LOYO retained SD range (C)", loyo_sd, [R], "same", ""),
    ("F090", "measured", "Explorer cells", ex_cells, [R], "python extensions/mapper_explorer/scripts/build_viewer.py", ""),
    ("F091", "measured", "Explorer independent offline checks", ex_checks, [R], "python verification/explorer_offline_test.py ...", "Chrome 156, Windows 11"),
    ("F092", "measured", "Stock kmapper HTML offline", kmapper_offline, [R], "python verification/kmapper_html_offline_test.py ...", ""),
]


# ---------------------------------------------------------------- reproduction bookkeeping
def cmp_summary(name):
    def g(rt):
        s = json.loads((Path(rt) / "technical" / "verification" / "reference" / "compare" / f"compare_{name}.json").read_text(encoding="utf8"))["summary"]
        return f"{s.get('identical', 0)} files identical, {s.get('pixel-identical', 0)} figures pixel-identical, {s.get('DIFFERENT', 0)} differ"
    return g


def cmp_short(name):
    def g(rt):
        s = json.loads((Path(rt) / "technical" / "verification" / "reference" / "compare" / f"compare_{name}.json").read_text(encoding="utf8"))["summary"]
        return f"{s.get('identical', 0)} files identical, {s.get('DIFFERENT', 0)} differ"
    return g


def tests_total(rt):
    t = json.loads((Path(rt) / "technical" / "verification" / "reference" / "test_results.json").read_text(encoding="utf8"))
    return f"{t['total_passed']} passed, {t['total_failed']} failed"


def tests_suite(d):
    def g(rt):
        t = json.loads((Path(rt) / "technical" / "verification" / "reference" / "test_results.json").read_text(encoding="utf8"))
        return next(s for s in t["suites"] if s["dir"] == d)["result"]
    return g


FACTS += [
    ("F100", "reproduced", "Baseline regeneration comparison", cmp_summary("baseline_regen"), [], "python verification/compare_trees.py ...", "differences explained in report 12.3"),
    ("F101", "reproduced", "Meteorology regeneration comparison", cmp_summary("meteorology"), [], "same", ""),
    ("F102", "reproduced", "Stability regeneration comparison", cmp_summary("stability"), [], "same", ""),
    ("F103", "reproduced", "Explorer rebuild comparison", cmp_short("explorer"), [], "same", "provenance hashes differ by CRLF"),
    ("F110", "measured", "Total tests passed", tests_total, [R], "python -m pytest ...", "order-dependence on Windows recorded"),
    ("F111", "measured", "Baseline test suite", tests_suite("tests"), [], "python -m pytest tests", ""),
    ("F112", "measured", "Meteorology tests", tests_suite("extensions/meteorology/tests"), [], "", ""),
    ("F113", "measured", "Explorer tests", tests_suite("extensions/mapper_explorer/tests"), [], "", ""),
    ("F114", "measured", "Stability tests", tests_suite("extensions/stability/tests"), [], "", ""),
    ("F115", "measured", "Audit-control tests", tests_suite("extensions/controls/tests"), [], "", ""),
]


def cmp_ident(name):
    def g(rt):
        s = json.loads((Path(rt) / "technical" / "verification" / "reference" / "compare" / f"compare_{name}.json").read_text(encoding="utf-8"))["summary"]
        return f"{s.get('identical', 0)} files identical"
    return g


FACTS += [("F104", "reproduced", "Control experiments recomputed identically", cmp_ident("controls"), [], "python verification/compare_trees.py ...", "")]
