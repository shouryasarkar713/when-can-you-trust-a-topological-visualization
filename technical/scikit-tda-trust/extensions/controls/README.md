# Extension D — control experiments

Supplementary control experiments for the Mapper and weather analyses. All parameters are in
`configs/controls.yaml`, written before the corresponding script's first run but after the results of the
default configuration (forced two-cluster KMeans) were known; the two clusterer scales are exploratory choices
(only these two were tried), not preregistered ones. No independent time stamp exists.

| Control | Script | Question | Output |
|---|---|---|---|
| D1 | `scripts/run_mapper_clusterer_control.py` | Is the E2 pattern a property of the forced KMeans k=2 rule? Same data, lens, grid; single-linkage at eps = c × median 5-NN distance, c ∈ {1.5, 3.0} | `results/mapper_clusterer_control.json` |
| D2 | `scripts/run_weather_null_controls.py` | Matched nulls for the weather embedding: anomaly series (two annual harmonics removed) and 10 shuffled series, same six configurations | `results/weather_null_controls.json` |
| D3 | `scripts/run_mapper_resampling_control.py` | Extension C's 30 × 80 % subsamples with the D1 clusterer | `results/mapper_resampling_control.json` |
| D4 | `scripts/run_independent_draws.py` | 30 independent 500-point redraws per shape: H1 bottleneck noise floor and Mapper cycle cue (KMeans and single-linkage) | `results/independent_draws.json` |
| D5 | `scripts/run_caveat_checks.py` | S ceiling at 400/500 points; H0 Wasserstein cardinality control | `results/caveat_checks.json` |

Figures: `scripts/render_control_figures.py` → `figures/`. Tests: `tests/test_controls.py` (10). Run order: D1, D2, D3, D4, D5,
then figures. Interpretation and limits: report §5.3, §6.4, §8.2–8.3.
