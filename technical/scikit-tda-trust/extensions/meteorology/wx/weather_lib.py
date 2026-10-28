"""Extension A shared library — GSOD preprocessing, embeddings, ONI parsing.

Reuses the baseline project's modules (src.pipeline, src.figures) wherever
sensible; this module owns only what is weather-specific. It contains NO
expected-outcome assertions (results discipline carried over from the
baseline: generation code measures, tests assert).

Determinism: every function here is pure w.r.t. its inputs; the only
randomness in the extension lives in seeded KMeans inside kmapper runs and
is pinned by config.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.pipeline import (  # noqa: E402  (baseline reuse)
    GAP_RATIO_CONVENTION,
    gap_ratio,
    h1_persistences,
)

# ---------------------------------------------------------------- constants

SENTINELS = {
    "TEMP": 9999.9, "DEWP": 9999.9, "SLP": 9999.9, "STP": 9999.9,
    "VISIB": 999.9, "WDSP": 999.9, "MXSPD": 999.9, "GUST": 999.9, "SNDP": 999.9,
    "PRCP": 99.99,
}

# Unit conversion factors (applied AFTER sentinel->NaN replacement).
F_TO_C = lambda f: (f - 32.0) * 5.0 / 9.0      # noqa: E731
KNOTS_TO_MS = 0.514444
IN_TO_MM = 25.4
MB_TO_HPA = 1.0  # identity; documented

UNIT_CONVERSIONS = {
    "TEMP": ("degF->degC", F_TO_C),
    "DEWP": ("degF->degC", F_TO_C),
    "MAX": ("degF->degC", F_TO_C),
    "MIN": ("degF->degC", F_TO_C),
    "SLP": ("mb->hPa (identity)", lambda v: v * MB_TO_HPA),
    "STP": ("mb->hPa (identity)", lambda v: v * MB_TO_HPA),
    "WDSP": ("knots->m/s", lambda v: v * KNOTS_TO_MS),
    "MXSPD": ("knots->m/s", lambda v: v * KNOTS_TO_MS),
    "GUST": ("knots->m/s", lambda v: v * KNOTS_TO_MS),
    "VISIB": ("miles (kept)", lambda v: v),
    "PRCP": ("inches->mm", lambda v: v * IN_TO_MM),
    "SNDP": ("inches (kept)", lambda v: v),
}

CONVERTED_COLUMNS = [
    "STATION", "DATE", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME",
    "TEMP", "DEWP", "SLP", "STP", "VISIB", "WDSP", "MXSPD", "GUST",
    "MAX", "MIN", "PRCP", "SNDP",
]

METEOROLOGICAL_SEASON = {12: "DJF", 1: "DJF", 2: "DJF",
                          3: "MAM", 4: "MAM", 5: "MAM",
                          6: "JJA", 7: "JJA", 8: "JJA",
                          9: "SON", 10: "SON", 11: "SON"}

YEARDAY_NOTE = (
    "Day-of-year lens encodes calendar information directly into the filter "
    "function; any apparent seasonal separation under this lens is partially "
    "built in and must be read beside the unsupervised PCA-lens result."
)

SW_EMBEDDING_CONVENTION = (
    "Sliding-window (time-delay) embedding: point i is the vector "
    "(x[i], x[i+tau], ..., x[i+(d-1)*tau]) of the z-scored daily series; "
    "span = (d-1)*tau days; stride = days between consecutive window starts. "
    "The annual cycle period is T = 365.25 days; spans near one period are "
    "expected to resolve the seasonal loop if one is present."
)


# ---------------------------------------------------------------- parsing

def parse_gsod_value(raw: str, field: str) -> float:
    """Parse one GSOD numeric field: sentinel -> NaN, else float.

    Sentinels are matched exactly on the documented values (9999.9 / 999.9 /
    99.99 per field family). Whitespace is tolerated (the files are
    right-padded fixed-width-ish CSV).
    """
    v = float(raw)
    if not np.isfinite(v):
        return float("nan")
    if field in SENTINELS and abs(v - SENTINELS[field]) < 1e-9:
        return float("nan")
    return v


def convert_units(field: str, value: float) -> float:
    """Apply the documented unit conversion for one field (NaN passes through)."""
    conv = UNIT_CONVERSIONS.get(field)
    if conv is None:
        return value
    return conv[1](value) if np.isfinite(value) else value


# ---------------------------------------------------------------- validation

def validate_dates(dates: Sequence[str], expected_first: str, expected_last: str) -> dict:
    """Uniqueness + calendar-continuity + coverage checks for a date column.

    Returns a facts dict; 'ok' is True iff dates are unique, strictly
    increasing, and every calendar day between first and last is present.
    """
    import datetime as dt

    ds = [d.strip() for d in dates]
    unique = len(set(ds)) == len(ds)
    parsed = [dt.date.fromisoformat(d) for d in ds]
    increasing = all(a < b for a, b in zip(parsed, parsed[1:]))
    n_days = (parsed[-1] - parsed[0]).days + 1
    complete = len(parsed) == n_days
    return {
        "n_rows": len(ds),
        "n_unique": len(set(ds)),
        "strictly_increasing": bool(increasing),
        "unique": bool(unique),
        "calendar_complete": bool(complete),
        "first": ds[0], "last": ds[-1],
        "expected_first": expected_first, "expected_last": expected_last,
        "coverage_ok": ds[0] == expected_first and ds[-1] == expected_last,
        "ok": bool(unique and increasing and complete
                   and ds[0] == expected_first and ds[-1] == expected_last),
    }


# ---------------------------------------------------------------- missingness

def missingness_report(frame: Mapping[str, np.ndarray], fields: Sequence[str]) -> dict:
    """Per-field missing counts/fractions + longest consecutive NaN run."""
    n = len(frame["DATE"])
    out = {}
    for f in fields:
        vals = np.asarray(frame[f], dtype=float)
        isnan = ~np.isfinite(vals)
        # longest consecutive run
        longest = run = 0
        for flag in isnan:
            run = run + 1 if flag else 0
            longest = max(longest, run)
        out[f] = {
            "n_missing": int(isnan.sum()),
            "fraction_missing": round(float(isnan.mean()), 5),
            "longest_consecutive_missing_days": int(longest),
        }
    out["n_days_total"] = n
    return out


# ---------------------------------------------------------------- embeddings

def sliding_window_embedding(series: np.ndarray, tau: int, d: int, stride: int = 1) -> np.ndarray:
    """Time-delay embedding with EXPLICIT parameter semantics.

    Point i = (x[i], x[i+tau], ..., x[i+(d-1)*tau]); the returned array has
    ceil((n - (d-1)*tau) / stride) rows (empty if the series is shorter than
    the span). See SW_EMBEDDING_CONVENTION.
    """
    series = np.asarray(series, dtype=float)
    n = len(series)
    span = (d - 1) * tau
    if span >= n:
        return np.empty((0, d), dtype=float)
    last_start = n - 1 - span
    starts = np.arange(0, last_start + 1, stride)
    idx = starts[:, None] + tau * np.arange(d)[None, :]
    return series[idx]


def embedding_span_days(tau: int, d: int) -> int:
    return (d - 1) * tau


# ---------------------------------------------------------------- ONI

def parse_oni(text: str, sentinel: float = -99.90) -> dict:
    """Parse the PSL fixed-width ONI file into {(year, month): value}.

    Returns {'values': {...}, 'n_missing': int, 'years': [first, last]}.
    The ONI is the 3-month running mean of Nino-3.4 SST anomalies (degC);
    phase thresholds +/-0.5 follow the CPC convention (simplified here to
    the value itself, NOT the 5-consecutive-season episode definition).
    """
    values = {}
    n_missing = 0
    years = []
    for line in text.splitlines():
        tok = line.split()
        if not tok:
            continue
        try:
            year = int(tok[0])
        except ValueError:
            continue  # header/note lines
        years.append(year)
        for m, t in enumerate(tok[1:], start=1):
            if m > 12:
                break
            try:
                v = float(t)
            except ValueError:
                continue
            if abs(v - sentinel) < 1e-6:
                n_missing += 1
                continue
            values[(year, m)] = v
    return {
        "values": values,
        "n_missing": n_missing,
        "years": [min(years), max(years)] if years else [],
    }


def oni_phase(value: float, el: float = 0.5, la: float = -0.5) -> str:
    """Descriptive phase label from the ONI value (CPC thresholds)."""
    if value >= el:
        return "ElNino"
    if value <= la:
        return "LaNina"
    return "Neutral"


# ---------------------------------------------------------------- mapper

def mapper_run_with_lens(lens: np.ndarray, X: np.ndarray, n_cubes: int,
                         perc_overlap: float, seed: int = 42,
                         n_clusters: int = 2) -> dict:
    """Build one Mapper graph with an EXPLICIT lens array (baseline's
    mapper_run hard-codes the PCA-1 lens; the weather extension needs the
    day-of-year lens beside it). Same cover/clusterer discipline as baseline
    E2: CubicalCover + seeded KMeans."""
    import kmapper as km
    from sklearn.cluster import KMeans
    mapper = km.KeplerMapper()
    lens = np.asarray(lens, dtype=float).reshape(-1, 1)
    return mapper.map(
        lens, X,
        cover=km.CubicalCover(n_cubes=n_cubes, perc_overlap=perc_overlap),
        clusterer=KMeans(n_clusters=n_clusters, random_state=seed, n_init=10),
    )


def day_of_year_lens(dates: Sequence[str]) -> np.ndarray:
    """Day-of-year (1..366) as a 1-D lens, normalized to [0, 1].

    NOTE: this lens encodes calendar information directly (YEARDAY_NOTE);
    results under it are a descriptive comparison, always shown beside the
    unsupervised PCA-lens result.
    """
    import datetime as dt
    doy = np.array([dt.date.fromisoformat(d).timetuple().tm_yday for d in dates],
                   dtype=float)
    return (doy - 1.0) / 365.0


# ---------------------------------------------------------------- diagnostics

def seasonal_ph_diagnostics(dgms: Sequence[np.ndarray]) -> dict:
    """Dominant H1 persistence + gap ratio for one embedding run.

    Uses the baseline's generalized gap ratio r_1 = p1/p2 with its stated
    convention (GAP_RATIO_CONVENTION); r_1 >= 3 is a convention, not a
    theorem.
    """
    if len(dgms) < 2:
        return {"H1_classes": 0, "dominant_H1_persistence": None,
                "gap_ratio_r1": None, "convention": GAP_RATIO_CONVENTION}
    pers = h1_persistences(dgms[1])
    out = {
        "H1_classes": int(len(dgms[1])),
        "H0_classes": int(len(dgms[0])),
        "H1_top3_persistence": [round(float(x), 4) for x in pers[:3]],
        "dominant_H1_persistence": round(float(pers[0]), 4) if len(pers) else None,
    }
    r1 = gap_ratio(pers, 1)
    out["gap_ratio_r1"] = round(r1, 3) if r1 is not None else None
    out["gap_ratio_convention"] = GAP_RATIO_CONVENTION
    return out
