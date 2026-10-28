#!/usr/bin/env python3
"""Extension A, Stage-3 addition — post-hoc seasonality sanity check.

Computes an FFT periodogram and a normalized autocorrelation of the z-scored
daily TEMP series (the same series the sliding-window PH sweep embeds) and
saves the results to results/weather_seasonality_check.json. The figure
(weather_seasonality_check.png) is rendered from the saved JSON by
render_weather_figures.py, preserving the "numerical outputs before figures"
discipline.

Scope guard (Stage-3 review instruction): this check is POST-HOC and
DESCRIPTIVE. It was computed only after the embedding sweep was pre-specified,
run, and saved; it is NOT used to select, retune, or re-rank any embedding
parameter, and it is not a hypothesis test. Its only role is to confirm that
the series itself carries near-annual periodicity, so the recurrent structure
recovered by the sliding-window PH is not attributable to an embedding
artefact acting on an aperiodic series.

Method (deliberately simple and reproducible, numpy only):
  - Periodogram: power spectrum of the mean-removed series via
    numpy.fft.rfft (no window function, no detrending beyond the mean).
    The dominant period is the argmax of power over periods in [30, 800] d.
  - Autocorrelation: normalized autocorrelation
    acf(k) = sum_i (x_i - m)(x_{i+k} - m) / sum_i (x_i - m)^2
    computed directly (no FFT). The peak lag is the argmax over the
    fixed analysis search window [180, 550] d (a pre-specified interval of
    the check itself; the check as a whole is post-hoc — see the scope
    guard above).

Determinism: pure numpy on a saved array; identical across re-runs.

Usage: python extensions/meteorology/scripts/seasonality_check.py
"""
from __future__ import annotations

import json
import sys
import datetime as dt
from pathlib import Path

import numpy as np

EXT_ROOT = Path(__file__).resolve().parents[1]
RESULTS = EXT_ROOT / "results"
DATA_NPZ = EXT_ROOT / "data_provenance" / "processed" / "weather_analysis.npz"

PERIOD_RANGE_DAYS = (30.0, 800.0)   # periodogram argmax search range
LAG_WINDOW_DAYS = (180, 550)        # autocorrelation peak search window
FIG_PERIOD_CAP_DAYS = 800           # arrays stored up to this period/lag


def main() -> int:
    data = np.load(DATA_NPZ, allow_pickle=True)
    dates = [str(d) for d in data["dates"]]
    temp_z = np.asarray(data["temp_z"], dtype=float)  # z-scored TEMP, full series
    n = len(temp_z)
    assert n == len(dates) == 2192, f"unexpected series length {n}"

    x = temp_z - temp_z.mean()

    # ---- FFT periodogram (mean-removed; no window) ----
    spec = np.fft.rfft(x)
    power = np.abs(spec) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0)              # cycles/day, freq[0] = DC
    with np.errstate(divide="ignore", invalid="ignore"):
        periods = np.where(freqs > 0, 1.0 / np.where(freqs > 0, freqs, 1.0), np.inf)
    band = (periods >= PERIOD_RANGE_DAYS[0]) & (periods <= PERIOD_RANGE_DAYS[1])
    idx = np.where(band)[0]
    dom_i = idx[np.argmax(power[idx])]
    dominant_period = float(periods[dom_i])
    total_power = float(power[1:].sum())            # exclude DC
    dom_fraction = float(power[dom_i] / total_power)

    # plottable arrays (periods within [30, 800] d, descending period order)
    keep = idx[::-1]
    periods_plot = [round(float(periods[i]), 4) for i in keep]
    power_plot = [round(float(power[i]), 4) for i in keep]

    # ---- normalized autocorrelation (direct sum; deterministic) ----
    denom = float((x * x).sum())
    acf = np.array([float((x[: n - k] * x[k:]).sum()) / denom
                    for k in range(0, min(n - 1, FIG_PERIOD_CAP_DAYS) + 1)])
    lags_plot = list(range(0, len(acf)))
    lo, hi = LAG_WINDOW_DAYS
    search = np.arange(lo, min(hi, len(acf) - 1) + 1)
    peak_lag = int(search[np.argmax(acf[search])])
    acf_365 = float(acf[365]) if len(acf) > 365 else None
    # strongest harmonic (half-year) for context
    acf_182 = float(acf[182]) if len(acf) > 182 else None

    out = {
        "step": "seasonality_check",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "purpose": (
            "POST-HOC descriptive sanity check on the daily TEMP series: does the "
            "series itself carry near-annual periodicity? Computed AFTER the "
            "sliding-window embedding sweep was pre-specified, run and saved; NOT "
            "used to select or retune any embedding parameter; not a hypothesis "
            "test and not an annual-specificity test."
        ),
        "series": "TEMP (z-scored), 2192 days, 2019-01-01..2024-12-31",
        "periodogram": {
            "method": "numpy.fft.rfft power spectrum of the mean-removed series; "
                      "no window function, no detrending beyond mean removal",
            "n_samples": n,
            "search_range_days": list(PERIOD_RANGE_DAYS),
            "dominant_period_days": round(dominant_period, 2),
            "dominant_power_fraction_of_total": round(dom_fraction, 5),
            "periods_days": periods_plot,
            "power": power_plot,
        },
        "autocorrelation": {
            "method": "normalized autocorrelation acf(k) = sum x_i x_{i+k} / sum x_i^2 "
                      "of the mean-removed series, direct sums (no FFT)",
            "peak_search_window_days": list(LAG_WINDOW_DAYS),
            "peak_lag_days": peak_lag,
            "acf_at_lag_365": round(acf_365, 4),
            "acf_at_lag_182_half_year": round(acf_182, 4),
            "acf_at_lag_0": 1.0,
            "lags_days": lags_plot,
            "acf": [round(float(a), 5) for a in acf],
        },
        "interpretation": (
            f"Both descriptors put the dominant scale near one year (dominant FFT "
            f"period {dominant_period:.1f} d; autocorrelation peak lag {peak_lag} d "
            f"in the pre-specified fixed analysis search window [{lo}, {hi}] d). "
            "The series itself is "
            "therefore near-annually recurrent, consistent with — but not a "
            "validation of — the recurrent structure the sliding-window PH "
            "recovers; no embedding parameter was chosen or adjusted using this "
            "check."
        ),
        "status": "OK",
    }
    (RESULTS / "weather_seasonality_check.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print(f"seasonality check saved: dominant period {dominant_period:.1f} d, "
          f"ACF peak lag {peak_lag} d (acf[365]={acf_365:.3f}, "
          f"acf[182]={acf_182:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
