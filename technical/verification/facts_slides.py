"""Slide-specific facts of the expanded presentation (imported by facts.py).

Each derived string equals the wording or table row used on the slides, computed from the saved results.
Slide tables are checked as rows whose cells are joined by ' | ' (verify_evidence.py reads table cells)."""
import facts as _f

J, R, S = _f.J, _f.R, _f.S


def _e2cell(r, shape, nc, po):
    b = next(b for b in J(r, "results/e2/e2_sensitivity.json")["shapes"] if b["shape"] == shape)
    return next(c for c in b["cells"] if c["n_cubes"] == nc and abs(c["perc_overlap"] - po) < 1e-9)


def s_e2_phrase(shape):
    def g(r):
        b = next(b for b in J(r, "results/e2/e2_sensitivity.json")["shapes"] if b["shape"] == shape)
        c = next(c for c in b["cells"] if c["is_reference"])
        comp = "component" if c["n_components"] == 1 else "components"
        return f"{c['n_nodes']} nodes, {c['n_edges']} edges, {c['n_components']} {comp}, cyclomatic number {c['cyclomatic_number']}"
    return g


def s_e2_blob_ref(r):
    c = J(r, "results/e2/e2_blob_sanity.json")["cells"][0]
    return f"{c['n_nodes']} nodes, {c['n_edges']} edges, {c['n_components']} component, cyclomatic number {c['cyclomatic_number']}"


def s_e2_blob_frag(r):
    c = J(r, "results/e2/e2_blob_sanity.json")["cells"][1]
    return f"{c['n_components']} components, cyclomatic number {c['cyclomatic_number']}"


def s_layout(r):
    lo = J(r, "results/e1/layout_overlap.json")
    from decimal import ROUND_HALF_UP, Decimal
    q = lambda x, p: str(Decimal(repr(x)).quantize(Decimal(p), rounding=ROUND_HALF_UP))  # noqa: E731  (stored values have 4 decimals)
    return (f"{q(lo['three_blobs']['native_kk']['max_component_bbox_iou'], '0.01')} on three blobs, "
            f"{q(lo['figure_eight']['native_kk']['max_component_bbox_iou'], '0.001')} on the figure-eight")


def s_d1_row(shape, c, label):
    def g(rt):
        e = J(rt, "extensions/controls/results/mapper_clusterer_control.json")["shapes"][shape]["eps"][c]
        r0 = e["cells"]["nc10_po0.35"]
        s = e["summary"]
        return f"{label} | {r0['n_nodes']} / {r0['n_components']} / {r0['cyclomatic_number']} | {s['cells_connected']} | {s['cells_with_cyclomatic_ge1']}"
    return g


def s_sweep_row(key, ref=False):
    def g(r):
        d = J(r, "extensions/controls/results/weather_null_controls.json")["raw"][key]
        return f"({d['tau']}, {d['d']}){' reference' if ref else ''} | {d['gap_ratio_r1']:.3f} | {d['dominant_H1_persistence']:.3f}"
    return g


def s_window(r):
    res = J(r, "extensions/meteorology/results/weather_analysis_results.json")
    sw = res["seasonal_ph"]["sweep"]["tau60_d8"]
    return f"(60, 8): span {(8 - 1) * 60} days, {sw['n_points']:,} windows from {res['n_days_primary'] + 4:,} days"


def s_pca(r):
    p = J(r, "extensions/meteorology/results/weather_analysis_results.json")["pca"]["explained_variance_ratio"]
    return f"PC1 explains {100 * p[0]:.1f} %, PC2 {100 * p[1]:.1f} %, {100 * sum(p):.1f} % together"


def s_primary(r):
    return f"{J(r, 'extensions/meteorology/results/weather_analysis_results.json')['n_days_primary']:,} days"


def s_ph_persist(shape):
    def g(r):
        d = J(r, "extensions/stability/results/ph_resampling.json")["shapes"][shape]["replicates"]
        v = [x["diagnostics"]["H1_top3_persistence"][0] for x in d]
        return f"{min(v):.3f}–{max(v):.3f}"
    return g


def s_draws_persist(shape):
    def g(r):
        v = J(r, "extensions/controls/results/independent_draws.json")["shapes"][shape]["summary"]["dominant_H1_min_max"]
        return f"{v[0]:.3f}–{v[1]:.3f}"
    return g


def s_mapper_row(shape, label):
    def g(r):
        reps = J(r, "extensions/stability/results/mapper_resampling.json")["shapes"][shape]["replicates"]
        comp = [x["structure"]["n_components"] for x in reps]
        cyc = [x["structure"]["cyclomatic_number"] for x in reps]
        keys = sorted(set(comp)) if shape == "blob" else sorted(set(comp), key=lambda k: (-comp.count(k), k))
        cs = ", ".join(f"{k}: {comp.count(k)}" for k in keys)
        ys = f"{min(cyc)}–{max(cyc)}" if shape == "blob" else ", ".join(f"{k}: {cyc.count(k)}" for k in sorted(set(cyc)))
        return f"{label} | {cs} | {ys}"
    return g


def s_ph_gap_ranges(r):
    out = []
    for shape, name, dec in (("annulus", "annulus r₁", 1), ("figure_eight", "figure-eight r₂", 2), ("blob", "blob r₁", 2)):
        d = J(r, "extensions/stability/results/ph_resampling.json")["shapes"][shape]["replicates"]
        v = [x["diagnostics"].get("gap_ratio_r1_at_ground_truth_rank", x["diagnostics"]["gap_ratio_r1"]) for x in d]
        a, b = min(v), max(v)
        if shape == "figure_eight":
            out.append(f"{name} = {a:.2f}–{b:.1f}")
        else:
            out.append(f"{name} = {a:.{dec}f}–{b:.{dec}f}")
    return ", ".join(out)


def _h0_bn_times(r, shapes=("annulus", "figure_eight", "blob")):
    d = J(r, "extensions/stability/results/ph_resampling.json")["shapes"]
    return [x["distances"]["H0"]["bottleneck"]["time_s"] for s in shapes for x in d[s]["replicates"]]


def s_h0_range(r):
    a = _h0_bn_times(r)
    b = _h0_bn_times(r, ("blob",))
    return f"Individual H0 bottleneck calls took {min(a):.1f}–{max(a):.0f} s across the {len(a)} resamples ({min(b):.1f}–{max(b):.0f} s for the blob)"


def s_h0_share(r):
    d = J(r, "extensions/stability/results/ph_resampling.json")["shapes"]
    tot = sum(m["time_s"] for s in d.values() for x in s["replicates"] for dim in x["distances"].values() for k, m in dim.items() if isinstance(m, dict) and "time_s" in m)
    h0 = sum(_h0_bn_times(r))
    return f"{h0:.0f} of the {tot:.0f} s of recorded distance-computation time"


def s_loyo_runtime(r):
    w = J(r, "extensions/stability/results/weather_loyo.json")
    ts = [c["ripser_time_s"] for f in w["folds"].values() for c in f["configs"].values()]
    return f"about {round(sum(ts) / 60)} minutes ({len(ts)} embeddings, {sum(ts):.0f} s of recorded ripser time)"


FACTS_SLIDES = [
    ("F140", "measured", "E2 annulus reference cell (slide wording)", s_e2_phrase("annulus"), [S, R], "python scripts/run_e2_sensitivity.py", ""),
    ("F141", "measured", "E2 figure-eight reference cell (slide wording)", s_e2_phrase("figure_eight"), [S, R], "python scripts/run_e2_sensitivity.py", ""),
    ("F142", "measured", "E2 blob reference cell (slide wording)", s_e2_blob_ref, [S, R], "python scripts/run_e2_sensitivity.py", ""),
    ("F143", "measured", "E2 blob fragmented cell (20, 0.20) (slide wording)", s_e2_blob_frag, [S], "python scripts/run_e2_sensitivity.py", ""),
    ("F144", "measured", "E1 native-layout component overlap (slide wording)", s_layout, [S], "python scripts/run_e1_audit.py", "descriptive layout measure"),
    ("F145", "measured", "D1 annulus c=3.0 row (slide table)", s_d1_row("annulus", "c3.0", "Annulus, c = 3.0"), [S], "python extensions/controls/scripts/run_mapper_clusterer_control.py", "scale chosen post hoc"),
    ("F146", "measured", "D1 annulus c=1.5 row (slide table)", s_d1_row("annulus", "c1.5", "Annulus, c = 1.5"), [S], "same", "scale chosen post hoc"),
    ("F147", "measured", "D1 figure-eight c=3.0 row (slide table)", s_d1_row("figure_eight", "c3.0", "Figure-eight, c = 3.0"), [S], "same", "scale chosen post hoc"),
    ("F148", "measured", "D1 figure-eight c=1.5 row (slide table)", s_d1_row("figure_eight", "c1.5", "Figure-eight, c = 1.5"), [S], "same", "scale chosen post hoc"),
    ("F149", "measured", "D1 blob c=3.0 row (slide table)", s_d1_row("blob", "c3.0", "Blob, c = 3.0"), [S], "same", "scale chosen post hoc"),
    ("F150", "measured", "D1 blob c=1.5 row (slide table)", s_d1_row("blob", "c1.5", "Blob, c = 1.5"), [S], "same", "scale chosen post hoc"),
    ("F151", "measured", "Sweep (30, 8) row (slide table)", s_sweep_row("tau30_d8"), [S], "python extensions/meteorology/scripts/run_weather_analysis.py", "one dataset"),
    ("F152", "measured", "Sweep (45, 9) row (slide table)", s_sweep_row("tau45_d9"), [S], "same", "one dataset"),
    ("F153", "measured", "Sweep (52, 8) row (slide table)", s_sweep_row("tau52_d8"), [S], "same", "one dataset"),
    ("F154", "measured", "Sweep (60, 8) reference row (slide table)", s_sweep_row("tau60_d8", True), [S], "same", "one dataset"),
    ("F155", "measured", "Sweep (73, 6) row (slide table)", s_sweep_row("tau73_d6"), [S], "same", "one dataset"),
    ("F156", "measured", "Sweep (90, 8) row (slide table)", s_sweep_row("tau90_d8"), [S], "same", "one dataset"),
    ("F157", "measured", "Reference embedding span and window count (slide wording)", s_window, [S], "same", "stride 1"),
    ("F158", "measured", "Static-cloud PCA variance (slide wording)", s_pca, [S], "same", ""),
    ("F159", "measured", "Static-cloud day count (slide wording)", s_primary, [S], "same", "after dropping four SLP-missing days"),
    ("F160", "measured", "Resample dominant persistence, annulus (slide table)", s_ph_persist("annulus"), [S, R], "python extensions/stability/scripts/run_ph_resampling.py", "overlapping subsamples"),
    ("F161", "measured", "Resample dominant persistence, figure-eight (slide table)", s_ph_persist("figure_eight"), [S, R], "same", "overlapping subsamples"),
    ("F162", "measured", "Resample dominant persistence, blob (slide table)", s_ph_persist("blob"), [S, R], "same", "overlapping subsamples"),
    ("F163", "measured", "Independent-redraw dominant persistence, annulus (slide table)", s_draws_persist("annulus"), [S, R], "python extensions/controls/scripts/run_independent_draws.py", ""),
    ("F164", "measured", "Independent-redraw dominant persistence, figure-eight (slide table)", s_draws_persist("figure_eight"), [S, R], "same", ""),
    ("F165", "measured", "Independent-redraw dominant persistence, blob (slide table)", s_draws_persist("blob"), [S, R], "same", ""),
    ("F166", "measured", "KMeans resampled graph row, annulus (slide table)", s_mapper_row("annulus", "Annulus"), [S], "python extensions/stability/scripts/run_mapper_resampling.py", "KMeans k=2"),
    ("F167", "measured", "KMeans resampled graph row, figure-eight (slide table)", s_mapper_row("figure_eight", "Figure-eight"), [S], "same", "KMeans k=2"),
    ("F168", "measured", "KMeans resampled graph row, blob (slide table)", s_mapper_row("blob", "Blob"), [S], "same", "KMeans k=2"),
    ("F170", "measured", "H0 bottleneck call times (runtime slide)", s_h0_range, [S, R], "recorded in extensions/stability/results/ph_resampling.json", "observed on the reported workload and environment; not a benchmark"),
    ("F171", "measured", "H0 bottleneck share of recorded distance time (runtime slide)", s_h0_share, [S, R], "same", "observed runtimes"),
    ("F172", "measured", "Leave-one-year-out runtime (runtime slide)", s_loyo_runtime, [S, R], "recorded in extensions/stability/results/weather_loyo.json", "observed runtimes; wall-clock sums of per-configuration ripser timings"),
]
