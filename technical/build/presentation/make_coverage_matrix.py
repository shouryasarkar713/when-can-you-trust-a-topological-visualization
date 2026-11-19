#!/usr/bin/env python3
"""Write PRESENTATION_COVERAGE_MATRIX.md: where each report section, result and numbered figure appears in the deck.

    python make_coverage_matrix.py <out.md>

Slide numbers and figure placement are read from slides_content.py (so they cannot drift); the
section-level judgments are written here."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slides_content import SLIDES  # noqa: E402

DIV = next(i for i, s in enumerate(SLIDES, 1) if s.get("kind") == "divider")
N = len(SLIDES)


def slides_with(img):
    return [i for i, s in enumerate(SLIDES, 1) for e in s.get("els", []) if e["type"] == "img" and e["name"] == img]


def title_of(i):
    return SLIDES[i - 1].get("title", "")


def tag(i):
    return f"{i}" + ("s" if i > DIV else "")


def fmt(lst):
    return ", ".join(tag(i) for i in lst) if lst else "none"


def find(substr):
    return [i for i, s in enumerate(SLIDES, 1) if substr.lower() in s.get("title", "").lower()]


# (report item, content, previous coverage, classification, action, final slides)
ROWS = [
    ("1 Summary; 2 Introduction (2.1–2.3)", "Problem, four layers between data and reader, RQ1–RQ3, contribution", "Slides 2, 4 (compressed)", "represented but too compressed", "Separate slides for the layers, the research questions and the contribution; positioning added", [find("not the topology")[0], find("Three questions")[0], find("Positioning")[0]]),
    ("2.4 Scope and exclusions", "No other TDA library, no GUDHI check", "limits slide only", "represented but too compressed", "Visible in limitations and future work", [find("Limitations,")[0], find("Takeaway")[0]]),
    ("3 Related work", "Persistent homology, Mapper, tools, periodic signals, evaluation, positioning", "not in the deck", "missing", "Positioning table and two reference slides (supplementary)", [find("Positioning")[0]] + find("References")),
    ("4 The evaluated software", "ripser, persim, kmapper, external packages, CDN property", "slide 5 (compressed)", "represented but too compressed", "Package row plus support-level table on one slide", [find("RQ1: the triad")[0]]),
    ("5.1 Persistent homology", "Filtration, H0/H1, birth/death, diagram, shapes, 1.496/0.481/0.140", "slide 3 schematic only", "represented only in speaker notes", "Method slide and a known-shapes slide with redrawn diagrams from saved results", [find("Persistent homology tracks")[0], find("Three known shapes")[0]]),
    ("5.3 Gap ratio r_k", "Definition, k per shape, r_k ≥ 3 convention", "slide 2 text", "represented but too compressed", "Own slide with a chart of the saved persistences", [find("gap ratio turns")[0]]),
    ("5.2 Mapper construction", "Six steps, default configuration, cyclomatic number", "slide 3 schematic only", "represented only in speaker notes", "Own slide: six-step schematic, default configuration, caveat on graph cycles", [find("Mapper builds")[0]]),
    ("5.3 Membership indicator S; diagram distances", "Jaccard matching, caveats, ceiling 0.80; bottleneck, Wasserstein, H0 cardinality", "notes and Q&A only", "represented only in speaker notes", "Supplementary method slide with a toy illustration; caveats also on the E2 slide and resampling slides", [find("Diagram distances and the overlap")[0]]),
    ("5.4–5.5 Conventions and caveats", "Seeds, thresholds, six methodological caveats", "partly on limits slide", "represented but too compressed", "Caveats are shown where they apply; collected on the limitations slide and configuration slide", [find("Limitations,")[0], find("Configurations and software")[0]]),
    ("6.1 E1 audit", "13 tasks, 130 lines, CDN failure, layout overlap 0.23 / 0.036", "slide 5 (compressed)", "represented but too compressed", "Support-level table in the talk; full 13-task matrix and layout figure in the supplement", [find("RQ1: the triad")[0], find("full 13-task")[0], find("native Mapper layout")[0]]),
    ("6.2 E2 sensitivity (Table 6.2; Figures 6.1–6.3)", "Annulus, figure-eight and blob results, S ranges", "one annulus slide", "represented but too compressed", "One slide per shape with the original figure", [find("E2, annulus")[0], find("E2, figure-eight")[0], find("E2, blob")[0]]),
    ("6.3 D1 clusterer control (Table 6.3; Figure 6.4)", "Six-row table, post hoc disclosure", "repeated-sampling chart only", "represented but too compressed", "Full table in the talk; figure and other-shape numbers in the supplement", [find("Clusterer control")[0], find("Cyclomatic number of the resampled")[0], find("Clusterer effect on the other")[0]]),
    ("6.4 E3 inspection", "Two judgments, protocol, stimuli", "one slide without stimuli", "represented but too compressed", "Slide with both judgments and two actual stimuli; more stimuli in the supplement", [find("RQ3, E3")[0], find("additional stimuli")[0]]),
    ("7.1 Weather data and preprocessing (Figures 7.1, 7.2)", "Source, variables, missing values, decisions, pipeline", "one bullet", "represented only in speaker notes", "Pipeline slide; variable and missing-value table with the series in the supplement", [find("Weather: one station")[0], find("Weather variables")[0]]),
    ("7.2 Static state-space cloud (Table 7.1; Figures 7.3, 7.6)", "PCA, eight Mapper cells, r₁ = 1.19, not a null", "one clause", "missing", "Slide with the eight graphs; cell table and diagram in the supplement", [find("static weather cloud")[0], find("Static weather cloud:")[0]]),
    ("7.3 Time-delay embedding (Table 7.2; Figures 7.4, 7.5, 7.7)", "Definition, 420-day span, 1,772 windows, six settings, seasonality", "one slide", "represented but too compressed", "Definition slide with an illustration, results slide, seasonality check in the supplement", [find("time-delay embedding turns")[0], find("All six embedding")[0], find("Seasonality check")[0]]),
    ("7.4 Matched null controls (Table 7.3; Figure 7.8)", "Anomaly and shuffled series, limits", "adequately represented", "adequately represented", "Kept; temperature-versus-anomaly table added to the supplement", [find("Matched null controls")[0], find("Weather nulls in detail")[0]]),
    ("8 Offline explorer (Figures 8.1–8.3)", "Design, 35 cells, 222/222 offline checks, limits", "one screenshot", "represented but too compressed", "Design slide with the annulus view; weather and blob views in the supplement", [find("offline explorer")[0], find("Explorer: the weather")[0]]),
    ("9.1–9.2 Persistence resampling (Table 9.1; Figures 9.1–9.3)", "Ranges, redraws, distances, H0 caveat", "ranges in text", "represented but too compressed", "Design and ranges in the talk; distance figures in the supplement", [find("Persistence evidence for constructed")[0], find("Diagram distances under resampling")[0]]),
    ("9.3 Mapper resampling (Tables 9.2, 9.3; Figures 9.4, 9.5)", "KMeans structure, single-linkage comparison, S ceiling", "one chart", "represented but too compressed", "Components and cycles in the talk; full figure, small multiples and tables in the supplement", [find("In the same samples")[0], find("Mapper graph statistics over all")[0], find("Annulus Mapper graphs under resampling")[0], find("Clusterer effect on the other")[0]]),
    ("9.4 Leave-one-year-out (Figure 9.6)", "36 embeddings, r₁ range, 10/36 caveat", "limits slide only", "represented only in speaker notes", "Own slide with the figure", [find("Leave-one-year-out")[0]]),
    ("9.5 Runtimes and determinism", "H0 bottleneck dominates; call times 0.2–75 s; leave-one-year-out about 4 minutes; determinism", "not in the deck", "missing", "One supplementary slide with the recorded runtimes and the caveat that they are not a benchmark", [find("Runtime and determinism")[0]]),
    ("10 Discussion", "Answers to RQ1–RQ3, three dependent variables", "one slide", "represented but too compressed", "Answer slide with boundaries; dependent-variable table", [find("Answers to RQ1")[0], find("Three dependent variables")[0]]),
    ("11 Limitations, threats, chronology, non-claims", "Scope, validity threats, order of design, non-claims", "one text slide", "represented but too compressed", "Three-column slide; full chronology table in the supplement", [find("Limitations,")[0], find("Order of design")[0]]),
    ("12 Reproducibility", "Environment, platforms, tests, verifier scope", "one slide", "adequately represented", "Kept and scoped; configuration table in the supplement", [find("Reproducibility checks")[0], find("Configurations and software")[0]]),
    ("13 Conclusions and future work", "Answers, trust follows construction, five directions", "takeaway only", "represented but too compressed", "Takeaway with the five future-work directions", [find("Takeaway")[0]]),
    ("14 References", "Bibliography", "not in the deck", "missing", "Two reference slides in the supplement", find("References")),
    ("Appendix A Configurations", "Experiment configuration table", "not in the deck", "suitable for supplementary slides rather than the main talk", "Condensed table with the software versions", [find("Configurations and software")[0]]),
]

FIGS = [
    ("6.1", ["e2_sensitivity_summary_annulus.png", "e2_annulus_heatmaps_slide.png"]), ("6.2", ["e2_sensitivity_summary_figure_eight.png", "e2_figure_eight_heatmaps_slide.png"]), ("6.3", ["e2_no_loop_blob_control.png", "e2_blob_control_slide.png"]),
    ("6.4", "d3_mapper_resampling_clusterer.png"), ("7.1", "weather_analysis_pipeline.png"), ("7.2", "weather_temp_series.png"),
    ("7.3", ["weather_grid_top.png", "weather_grid_bottom.png"]), ("7.4", "weather_seasonal_ph_sweep.png"), ("7.5", "weather_seasonality_check.png"),
    ("7.6", "weather_state_space_ph.png"), ("7.7", "weather_embedding_pca.png"), ("7.8", "d2_weather_null_controls.png"),
    ("8.1", "explorer_annulus_reference.png"), ("8.2", "explorer_weather_fragmentation.png"), ("8.3", "explorer_blob_control_fragmented.png"),
    ("9.1", "ph_resampling_persistence.png"), ("9.2", "ph_resampling_dists.png"), ("9.3", "ph_resampling_cross_shape.png"),
    ("9.4", ["mapper_resampling_cc.png", "mapper_resampling_structure.png"]), ("9.5", "mapper_resampling_graphs_annulus.png"), ("9.6", "weather_loyo.png"),
]

NEW = [
    ("e2_annulus_heatmaps_slide.png / e2_figure_eight_heatmaps_slide.png / e2_blob_control_slide.png", "Presentation copies of report Figures 6.1–6.3 with audience-facing titles (same saved results and plotting code)"),
    ("shapes_clouds_diagrams.png", "Known-answer shapes and their saved persistence diagrams (redrawn from saved results)"),
    ("gap_ratio_shapes.png", "Gap ratio at the known loop count (redrawn from saved diagrams)"),
    ("method_ph.png / method_mapper.png", "Schematic of persistence and Mapper (illustration on synthetic points, labelled as such)"),
    ("delay_window_illustration.png", "One delay window on the saved reference embedding"),
    ("s_indicator_toy.png", "Toy illustration of the membership-overlap indicator (labelled as not data)"),
    ("e3_stimulus_S02/S05/S06/S08/S11.png", "Original E3 stimuli"),
    ("three_blobs_readability_native_vs_separated.png", "E1 layout figure"),
    ("weather_grid_top/bottom.png, mapper_resampling_cc.png", "Crops of report Figures 7.3 and 9.4 (no data changed)"),
]


def main(out):
    L = []
    a = L.append
    a("# Presentation coverage matrix\n")
    a(f"Generated by `make_coverage_matrix.py` from `slides_content.py`. The deck has **{N} slides**: slides 1–{DIV - 1} are the timed main talk, slide {DIV} is the divider, and slides {DIV + 1}–{N} are supplementary (marked `s`).\n")
    a("## Report sections and results\n")
    a("| Report section / item | Important content | Previous deck | Classification of the previous coverage | Action | Final slides |")
    a("|---|---|---|---|---|---|")
    for r in ROWS:
        a(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {fmt(r[5])} |")
    a("\n## The 21 numbered report figures\n")
    a("| Report figure | File | Final slides |")
    a("|---|---|---|")
    for num, f in FIGS:
        fl = f if isinstance(f, list) else [f]
        sl = sorted({i for x in fl for i in slides_with(x)})
        a(f"| {num} | {', '.join(fl)} | {fmt(sl)} |")
        assert sl, f"figure {num} not on any slide"
    a("\n## Figures added for the presentation\n")
    a("| File | Content |")
    a("|---|---|")
    for f, c in NEW:
        a(f"| {f} | {c} |")
    a("\n## Slide outline\n")
    a("| Slide | Title |")
    a("|---|---|")
    for i, s in enumerate(SLIDES, 1):
        a(f"| {tag(i)} | {s.get('title', '')} |")
    Path(out).write_text("\n".join(L) + "\n", encoding="utf8")
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
