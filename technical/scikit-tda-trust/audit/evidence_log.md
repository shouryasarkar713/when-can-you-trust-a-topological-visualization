# E1 Evidence Log (Phase 2 — every path existence-tested at write time)

- Run date (UTC): 2026-10-21 17:16
- Environment: results/env/verification.json  [all paths verified on disk] (38 checks) + results/env/pip_freeze.txt
- T01 install: requirements.txt pins; clean-clone re-verification in results/repro/comparison_report.json  [all paths verified on disk]
- T02 data: results/e1/data/annulus.npy  [all paths verified on disk] (also figure_eight, blob, three_blobs .npy); params in configs/shapes.yaml
- T03 diagrams: results/e1/annulus_ph_dgms.npz  [all paths verified on disk] (all four shapes); determinism in e1_audit.json#determinism_check
- T04/T05 figures: figures/e1/annulus_diagram.png  [all paths verified on disk]; custom barcode: figures/e1/annulus_barcode.png  [all paths verified on disk]
- T06 stability (annulus): bottleneck=0.05261, wasserstein=0.71316 (full table: results/e1/e1_audit.json#stability_check)
- T07 matching: figures/e1/annulus_matching.png  [all paths verified on disk]
- T08/T09/T10/T11 per-shape artifacts: figures/e1/annulus_mapper_static.png  [all paths verified on disk]; memberships: results/e1/annulus_mapper_memberships.json  [all paths verified on disk]; HTML exports: figures/e1/annulus_mapper.html  [all paths verified on disk]
- T10 readability: results/e1/layout_overlap.json  [all paths verified on disk] — native kk component-overlap statistics; side-by-side figures figures/e1/*_readability_native_vs_separated.png (rendered by src/figures.py from saved memberships)
- T11 offline browser test (EXECUTED): results/e1/offline_browser_test.json  [all paths verified on disk]; inventory: audit/html_resource_inventory.md  [all paths verified on disk]; screenshots: results/e1/browser_test/online.png, offline_cold.png
- T12 determinism (annulus): arrays=True, diagrams=True, memberships=True; clean-clone comparison PASSED: results/repro/comparison_report.json
- T13 baselines: figures/e1/annulus_pca_baseline.png  [all paths verified on disk]
- Glue-code accounting (reproducible rule): audit/glue_code_accounting.json  [all paths verified on disk] — 130 LOC total; method: scripts/count_glue_code.py
- tadasets cross-check: {"source": "tadasets.infty_sign(n=500, noise=0.05, seed=7)", "H1_top3_persistence": [0.673, 0.6339, 0.054], "gap_ratio_r2": 11.736, "purpose": "external-generator agreement with the custom figure-eight two-loop signature (correctness check, blueprint Table 5.2)"}
- E2 companion evidence: results/e2/e2_sensitivity.csv  [all paths verified on disk] (24-cell grid) and results/e2/e2_blob_sanity.json  [all paths verified on disk]
