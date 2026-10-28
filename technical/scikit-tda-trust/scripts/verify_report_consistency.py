#!/usr/bin/env python3
"""verify_report_consistency.py — final editorial-pass validation.

Checks (no experiment data is touched):
  A. TOC page numbers in the final PDF match the pages where the headings
     actually appear (displayed Arabic numbers).
  B. Report claims vs saved experimental outputs:
     - E2 24-cell grid numbers in Table 4 vs results/e2/e2_sensitivity.json
     - headline E2 claims (2*n_cubes node counts; fig-eight ref cell 2 comp;
       (20,0.20) 4 comp; (20,0.50) connected cyclo 2; annulus n_cubes=5 tree)
     - E3 counts (11 clearly apparent, 2 ambiguous; 12 yes, 1 partial) vs
       results/e3/inspection_summary.json and inspection_record.csv
     - E1 glue LOC 130 vs audit/glue_code_accounting.json
     - env checks 38/38 vs results/env/verification.json
     - repro 26/26 structural + 45/45 figures vs results/repro/comparison_report.json
     - freeze extract entries vs results/env/pip_freeze.txt (all present)
  C. Terminology sweep of the final PDF text: no residual
     "pre-registered"/"preregistered" except the two allowed uses
     (future-work "preregistered analysis"; "not a preregistered
     prospective experiment"), and no "committed" outside the
     "commits are not permitted" phrasing.
  D. Author placeholder unchanged on the cover.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/scikit-tda-trust")
PDF = REPO / "report" / "When_Can_You_Trust_a_Topological_Visualization_Report.pdf"
DOCX = REPO / "report" / "When_Can_You_Trust_a_Topological_Visualization_Report.docx"

fails: list[str] = []
oks = 0


def check(cond: bool, label: str, detail: str = "") -> None:
    global oks
    if cond:
        oks += 1
        print(f"  [PASS] {label}")
    else:
        fails.append(f"{label} {detail}")
        print(f"  [FAIL] {label} {detail}")


def pdf_pages(pdf: Path) -> list[str]:
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    return [re.sub(r"\s+", " ", subprocess.run(
        ["pdftotext", "-f", str(p), "-l", str(p), str(pdf), "-"],
        capture_output=True, text=True).stdout) for p in range(1, n + 1)]


def docx_text() -> str:
    import zipfile
    with zipfile.ZipFile(DOCX) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", "", xml)


def main() -> int:
    pages = pdf_pages(PDF)
    full_pdf = " ".join(pages)
    norm = lambda s: re.sub(r"\s+", " ", s).strip()

    print("A. TOC page numbers vs actual heading pages")
    headings = [
        "1. Introduction and Research Questions", "1.1 Contribution statement",
        "2. The Scikit-TDA Ecosystem and System Boundary",
        "3. Related Work and Scientific Motivation",
        "4. Installation and Experimental Setup", "5. Methodology",
        "5.1 Attribution framework", "5.2 Metric definitions and corrections",
        "5.3 Experiment 3 methodology: the single-observer fallback",
        "5.4 Deviations from the original plan",
        "6. Capability and Workflow Audit (E1 Results)", "6.1 Assembly burden",
        "6.2 The HTML export is not an offline artifact",
        "6.3 Native static layout limitation",
        "7. Mapper Parameter Sensitivity Results (E2)",
        "7.1 Interpretation instability", "7.2 The cycles-versus-loops control",
        "7.3 Rendering changes what is visible",
        "8. Structured Task-Based Inspection of Visualization Readability (E3)",
        "8.1 Inspection results", "8.2 The two ambiguous cases",
        "8.3 Parameter and rendering dependence of the Mapper readings",
        "8.4 What this evidence does and does not establish",
        "9. Advantages and Disadvantages",
        "10. Research Gaps and Future Improvements",
        "10.1 Mapper parameter selection without guidance (established)",
        "10.2 No cross-parameter visualization of Mapper itself (established)",
        "10.3 Diagram statistics without inference (established)",
        "10.4 A static interaction grammar - and a fragile one (observed)",
        "10.5 Rendering defaults that under-communicate (observed; this project's contribution)",
        "10.6 Workflow integration and documentation drift (observed)",
        "11. Limitations and Threats to Validity",
        "11.1 The single-observer inspection (E3)",
        "11.2 Scope of the computational experiments",
        "11.3 Environment and platform", "11.4 What remains unverified",
        "12. Conclusion", "13. References and Reproduction Instructions",
        "13.1 References", "13.2 Reproduction instructions",
        "13.3 Assignment-requirement checklist",
        "Appendix A. The Three Representations",
        "Appendix B. Environment Freeze (extract)",
    ]
    body_start = next(i for i, t in enumerate(pages)
                      if norm(headings[0]) in t and "Table of Contents" not in t)
    cursor, bad = body_start, []
    for h in headings:
        hit = next((i for i in range(cursor, len(pages)) if norm(h) in pages[i]), None)
        if hit is None:
            bad.append(h)
            continue
        cursor = hit
        shown = hit - body_start + 1
        # TOC line for this heading must end with the same number (long
        # titles wrap: allow whitespace between title and the dot leader)
        m = re.search(re.escape(norm(h)) + r"\s*\.{2,}\s*(\d+)", full_pdf)
        if not m or int(m.group(1)) != shown:
            bad.append(f"{h} (heading@{shown}, toc={m.group(1) if m else '??'})")
    check(not bad, "all 43 TOC entries match actual heading pages", str(bad))

    print("B. Report numbers vs saved outputs")
    e2 = json.load(open(REPO / "results/e2/e2_sensitivity.json"))
    cells = {(sh["shape"], c["n_cubes"], round(c["perc_overlap"], 2)): c
             for sh in e2["shapes"] for c in sh["cells"]}
    # node count = 2 * n_cubes everywhere
    check(all(c["n_nodes"] == 2 * k for (s, k, o), c in cells.items()),
          "E2: n_nodes == 2*n_cubes in all 24 cells")
    fe_ref = cells[("figure_eight", 10, 0.35)]
    check(fe_ref["n_components"] == 2, "E2: figure-eight (10,0.35) has 2 components")
    fe_2020 = cells[("figure_eight", 20, 0.20)]
    check(fe_2020["n_components"] == 4, "E2: figure-eight (20,0.20) has 4 components")
    fe_2050 = cells[("figure_eight", 20, 0.50)]
    check(fe_2050["n_components"] == 1 and fe_2050["cyclomatic_number"] == 2,
          "E2: figure-eight (20,0.50) connected, cyclomatic 2")
    ann5 = [cells[("annulus", 5, o)] for o in (0.20, 0.35, 0.50)]
    check(all(c["cyclomatic_number"] == 0 for c in ann5),
          "E2: annulus n_cubes=5 tree (cyclomatic 0) in all 3 overlaps")
    ann_ref = cells[("annulus", 10, 0.35)]
    check(ann_ref["n_components"] == 1 and ann_ref["cyclomatic_number"] == 2
          and ann_ref["max_basis_cycle_length"] == 16,
          "E2: annulus reference cell: 16-node basis cycle")
    # Table 4 in PDF matches the saved grid numbers
    check(len(cells) == 24, "E2: 24 cells loaded", str(len(cells)))
    tbl_ok, tbl_bad = True, []
    for (s, k, o), c in cells.items():
        row = (f"{s.replace('_', '-')} {k} {o:.2f} {c['n_nodes']} {c['n_edges']} "
               f"{c['n_components']} {c['cyclomatic_number']}")
        if norm(row) not in full_pdf:
            tbl_ok = False
            tbl_bad.append(row)
    check(tbl_ok, "Table 4: all 24 rows' shape/n_cubes/overlap/nodes/edges/comp/cyclo match saved grid", str(tbl_bad[:3]))

    e3 = json.load(open(REPO / "results/e3/inspection_summary.json"))
    check(e3["assessment_counts_overall"] == {"clearly_apparent": 11, "ambiguous": 2},
          "E3: 11 clearly apparent + 2 ambiguous (summary file)")
    check(e3["matches_expected_counts_overall"] == {"yes": 12, "partial": 1},
          "E3: 12 yes + 1 partial (summary file)")
    with open(REPO / "e3_inspection/inspection_record.csv") as f:
        rows = [r for r in csv.DictReader(l for l in f if not l.startswith("#"))]
    check(len(rows) == 13 and sum(1 for r in rows if r["matches_expected"] == "partial") == 1
          and sum(1 for r in rows if r["assessment"] == "ambiguous") == 2,
          "E3: record has 13 rows, 1 partial, 2 ambiguous")
    s08 = next(r for r in rows if r["stimulus_id"] == "S08")
    check("answered 1" in s08["misleading_cues"] and s08["matches_expected"] == "yes",
          "E3: S08 first-reading miscue preserved; final match = yes")

    glue = json.load(open(REPO / "audit/glue_code_accounting.json"))
    total = sum(f["loc"] for f in glue["inventory"])
    check(total == 130, "E1: glue LOC == 130", f"got {total}")

    ver = json.load(open(REPO / "results/env/verification.json"))
    check(all(c["ok"] for c in ver["checks"]) and len(ver["checks"]) == 38,
          "env verification: 38/38 checks pass")

    rep = json.load(open(REPO / "results/repro/comparison_report.json"))
    check(len(rep["comparisons"]) == 26
          and all(c["identical"] for c in rep["comparisons"])
          and rep["all_structural_outputs_identical"] is True,
          "repro test: 26/26 structural outputs identical recorded")
    fpc = rep["figure_pixel_comparison"]
    check(fpc["n_figures"] == 45 and fpc["n_pixel_identical"] == 45,
          "repro test: 45/45 figures pixel-identical recorded")

    freeze = [l.strip() for l in open(REPO / "results/env/pip_freeze.txt") if l.strip()]
    missing = [p for p in freeze if p.split("==")[0] not in full_pdf]
    check(not missing, "Appendix B freeze extract contains all 32 pinned packages", str(missing))

    print("C. Terminology sweep of the final PDF")
    for m in re.finditer(r"preregistered|pre-registered|pre-register", full_pdf, re.I):
        ctx = full_pdf[max(0, m.start() - 70):m.end() + 70]
        allowed = ("preregistered analysis" in ctx and "counterbalanced" in ctx) or \
                  "not a preregistered prospective experiment" in ctx
        check(allowed, f"residual preregistration term is an allowed use: ...{ctx[:90]}...")
    for m in re.finditer(r"\bcommit", full_pdf, re.I):
        ctx = full_pdf[max(0, m.start() - 60):m.end() + 60]
        check("commits are not permitted" in ctx or "commit" not in ctx.lower().replace("commits are not permitted", ""),
              f"residual 'commit' use: ...{ctx[:90]}...")

    print("D. Cover author placeholder")
    check("【Student name】" in pages[0], "author placeholder unchanged on cover")

    print(f"\n==== {oks} checks passed, {len(fails)} failed ====")
    for f in fails:
        print("FAILED:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
