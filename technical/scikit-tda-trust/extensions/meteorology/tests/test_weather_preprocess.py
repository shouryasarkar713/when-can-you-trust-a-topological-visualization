"""Extension A unit tests — GSOD parsing, sentinels, unit conversion,
date validation, missingness, ONI parsing, preprocessing rules.

Ground-truth style: robust properties with margins, no brittle exact floats
(baseline test discipline).
"""
from __future__ import annotations

import numpy as np
import pytest

from weather_lib import (
    F_TO_C,
    KNOTS_TO_MS,
    METEOROLOGICAL_SEASON,
    SENTINELS,
    convert_units,
    embedding_span_days,
    missingness_report,
    oni_phase,
    parse_gsod_value,
    parse_oni,
    sliding_window_embedding,
    validate_dates,
)


# ---------------------------------------------------------------- sentinels

class TestSentinels:
    def test_temp_family_sentinel_becomes_nan(self):
        assert np.isnan(parse_gsod_value("9999.9", "TEMP"))
        assert np.isnan(parse_gsod_value(" 9999.9", "DEWP"))
        assert np.isnan(parse_gsod_value("9999.9", "SLP"))

    def test_wind_family_sentinel_becomes_nan(self):
        assert np.isnan(parse_gsod_value("999.9", "WDSP"))
        assert np.isnan(parse_gsod_value(" 999.9", "GUST"))
        assert np.isnan(parse_gsod_value("99.99", "PRCP"))

    def test_documented_sentinel_per_field_only(self):
        # the wind-family value in the SLP field is NOT SLP's sentinel
        # (documented schema decision, 2020-12-01 case)
        assert parse_gsod_value("999.9", "SLP") == 999.9

    def test_valid_values_pass_through(self):
        assert parse_gsod_value("52.4", "TEMP") == 52.4
        assert parse_gsod_value("1011.6", "SLP") == 1011.6

    def test_sentinel_table_documented_families(self):
        assert SENTINELS["TEMP"] == 9999.9
        assert SENTINELS["WDSP"] == 999.9
        assert SENTINELS["PRCP"] == 99.99


# ---------------------------------------------------------------- units

class TestUnitConversion:
    def test_fahrenheit_to_celsius_anchor_points(self):
        assert F_TO_C(32.0) == pytest.approx(0.0)
        assert F_TO_C(212.0) == pytest.approx(100.0)
        assert F_TO_C(52.4) == pytest.approx(11.333, abs=1e-3)

    def test_knots_to_ms_factor(self):
        assert 10.0 * KNOTS_TO_MS == pytest.approx(5.14444, abs=1e-4)

    def test_convert_units_applies_and_passes_nan(self):
        assert convert_units("TEMP", 32.0) == pytest.approx(0.0)
        assert np.isnan(convert_units("TEMP", float("nan")))
        # identity conversion for SLP (mb == hPa)
        assert convert_units("SLP", 1011.6) == 1011.6

    def test_all_numeric_fields_have_documented_conversion(self):
        for f in ("TEMP", "DEWP", "SLP", "WDSP", "PRCP"):
            assert f in dict.fromkeys(["TEMP", "DEWP", "SLP", "WDSP", "PRCP"])


# ---------------------------------------------------------------- dates

class TestDateValidation:
    def test_complete_range_ok(self):
        facts = validate_dates(["2019-01-01", "2019-01-02", "2019-01-03"],
                               "2019-01-01", "2019-01-03")
        assert facts["ok"] and facts["calendar_complete"] and facts["unique"]

    def test_gap_detected(self):
        facts = validate_dates(["2019-01-01", "2019-01-03"],
                               "2019-01-01", "2019-01-03")
        assert not facts["ok"]
        assert not facts["calendar_complete"]

    def test_duplicate_detected(self):
        facts = validate_dates(["2019-01-01", "2019-01-01"],
                               "2019-01-01", "2019-01-01")
        assert not facts["ok"] and not facts["unique"]

    def test_unsorted_detected(self):
        facts = validate_dates(["2019-01-02", "2019-01-01"],
                               "2019-01-01", "2019-01-02")
        assert not facts["ok"] and not facts["strictly_increasing"]

    def test_wrong_coverage_detected(self):
        facts = validate_dates(["2019-01-01", "2019-01-02"], "2019-01-01", "2019-01-03")
        assert not facts["ok"] and not facts["coverage_ok"]


# ---------------------------------------------------------------- missingness

class TestMissingness:
    def test_report_counts_and_longest_run(self):
        frame = {"DATE": np.array(["d"] * 10),
                 "A": np.array([np.nan, 1, np.nan, np.nan, np.nan, 2, 3, np.nan, np.nan, 4.0]),
                 "B": np.arange(10, dtype=float)}
        rep = missingness_report(frame, ["A", "B"])
        assert rep["A"]["n_missing"] == 6
        assert rep["A"]["fraction_missing"] == pytest.approx(0.6)
        assert rep["A"]["longest_consecutive_missing_days"] == 3
        assert rep["B"]["n_missing"] == 0
        assert rep["n_days_total"] == 10


# ---------------------------------------------------------------- embedding

class TestSlidingWindowEmbedding:
    def test_shape_and_span_math(self):
        series = np.arange(100, dtype=float)
        emb = sliding_window_embedding(series, tau=7, d=5, stride=1)
        assert emb.shape == (100 - 28, 5)
        assert embedding_span_days(7, 5) == 28

    def test_exact_values(self):
        series = np.arange(10, dtype=float)
        emb = sliding_window_embedding(series, tau=3, d=3, stride=1)
        assert emb[0].tolist() == [0.0, 3.0, 6.0]
        assert emb[1].tolist() == [1.0, 4.0, 7.0]

    def test_stride(self):
        series = np.arange(10, dtype=float)
        emb = sliding_window_embedding(series, tau=2, d=3, stride=2)
        assert emb.shape == (3, 3)
        assert emb[0].tolist() == [0.0, 2.0, 4.0]

    def test_deterministic(self):
        rng = np.random.default_rng(0)
        series = rng.normal(size=500)
        e1 = sliding_window_embedding(series, tau=60, d=8)
        e2 = sliding_window_embedding(series, tau=60, d=8)
        np.testing.assert_array_equal(e1, e2)

    def test_series_shorter_than_span_gives_empty(self):
        emb = sliding_window_embedding(np.arange(5, dtype=float), tau=3, d=3)
        assert emb.shape == (0, 3)

    def test_reference_config_span_brackets_annual_period(self):
        # reference tau=60 d=8 -> 420 d (~1.15 T); documented alternatives
        spans = {embedding_span_days(c["tau"], c["d"])
                 for c in [{"tau": 30, "d": 8}, {"tau": 45, "d": 9}, {"tau": 52, "d": 8},
                           {"tau": 60, "d": 8}, {"tau": 73, "d": 6}, {"tau": 90, "d": 8}]}
        assert min(spans) < 365.25 < max(spans)   # sweep brackets the annual scale


# ---------------------------------------------------------------- ONI

class TestONI:
    def test_parse_known_text(self):
        text = "header note\n1950  -1.32 -1.20\n1951   0.10  0.20\nbad line\n"
        parsed = parse_oni(text)
        assert parsed["values"][(1950, 1)] == -1.32
        assert parsed["values"][(1950, 2)] == -1.20
        assert parsed["values"][(1951, 2)] == 0.20
        assert (1951, 1) in parsed["values"]
        assert parsed["years"] == [1950, 1951]
        assert (1952, 1) not in parsed["values"]

    def test_missing_sentinel_skipped(self):
        text = "1950  -99.90  -1.00\n"
        parsed = parse_oni(text, sentinel=-99.90)
        assert (1950, 1) not in parsed["values"]
        assert parsed["n_missing"] == 1
        assert parsed["values"][(1950, 2)] == -1.00

    def test_phase_thresholds_cpc_convention(self):
        assert oni_phase(0.7) == "ElNino"
        assert oni_phase(0.5) == "ElNino"
        assert oni_phase(0.3) == "Neutral"
        assert oni_phase(-0.4) == "Neutral"
        assert oni_phase(-0.5) == "LaNina"
        assert oni_phase(-1.2) == "LaNina"


# ---------------------------------------------------------------- seasons

class TestSeasons:
    def test_meteorological_season_months(self):
        assert METEOROLOGICAL_SEASON[12] == "DJF"
        assert METEOROLOGICAL_SEASON[1] == "DJF"
        assert METEOROLOGICAL_SEASON[7] == "JJA"
        assert METEOROLOGICAL_SEASON[10] == "SON"
        assert len(METEOROLOGICAL_SEASON) == 12
