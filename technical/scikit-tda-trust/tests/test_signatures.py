"""Qualitative ground-truth signature checks at headline parameters.

These are GROUND-TRUTH checks (construction-known properties with margins),
kept strictly separate from measured experiment outputs:
  annulus       r_1 > 5        (verified single point: 19.3)
  figure-eight  r_2 > 3 and 0.5 < r_1 < 2   (9.7 and 1.00)
  blob          r_1 < 3        (1.45; no dominant loop by construction)
  three_blobs   2 prominent H0 merges (=> 3 components with essential class),
                small H1 (0.102 verified)
Tolerances are wide on purpose: robust properties, not brittle exact floats.
"""
import numpy as np

from pipeline import (compute_ph, gap_ratio, h0_prominent_merges, h1_persistences,
                      ph_summary)
from shapes import GROUND_TRUTH_H1_RANK, annulus, blob, figure_eight, three_blobs


def _h1_pers(X):
    return h1_persistences(compute_ph(X, maxdim=1)["dgms"][1])


def test_annulus_signature():
    p = _h1_pers(annulus(n=500, noise=0.05, seed=42))
    r1 = gap_ratio(p, 1)
    assert r1 is not None and r1 > 5.0
    assert p[0] > 1.0  # the loop persists at unit scale


def test_figure_eight_signature():
    p = _h1_pers(figure_eight(n=500, noise=0.05, seed=42))
    r1, r2 = gap_ratio(p, 1), gap_ratio(p, 2)
    # two co-dominant classes: r_1 ~ 1 is EXPECTED (not a failure);
    # r_2 at the ground-truth rank 2 separates the two loops from noise.
    assert r1 is not None and 0.5 < r1 < 2.0
    assert r2 is not None and r2 > 3.0


def test_blob_signature():
    p = _h1_pers(blob(n=500, spread=0.45, seed=42))
    r1 = gap_ratio(p, 1)
    assert r1 is not None and r1 < 3.0  # no dominant loop by construction
    assert p[0] < 0.5                    # noise-scale classes only


def test_three_blobs_signature():
    dgms = compute_ph(three_blobs(n=450, spread=0.25, seed=42), maxdim=1)["dgms"]
    assert h0_prominent_merges(dgms[0], fraction=0.5) == 2  # + essential = 3
    assert h1_persistences(dgms[1])[0] < 0.5                 # no prominent loop


def test_ripser_deterministic_on_fixed_input():
    X = annulus(n=300, noise=0.05, seed=11)
    d1 = compute_ph(X, maxdim=1)["dgms"]
    d2 = compute_ph(X, maxdim=1)["dgms"]
    for a, b in zip(d1, d2):
        np.testing.assert_array_equal(a, b)


def test_ph_summary_reports_rank_and_calibration():
    """ph_summary carries both r_1 (calibration) and r_k at the known rank."""
    X = annulus(n=300, noise=0.05, seed=42)
    s = ph_summary(X, maxdim=1, h1_rank=GROUND_TRUTH_H1_RANK["annulus"])
    assert s["gap_ratio_r1_calibration"] > 5.0
    assert s["gap_ratio_r1_at_ground_truth_rank"] > 5.0  # rank 1 for annulus
    s8 = ph_summary(figure_eight(n=300, noise=0.05, seed=42), maxdim=1,
                    h1_rank=GROUND_TRUTH_H1_RANK["figure_eight"])
    assert s8["gap_ratio_r2_at_ground_truth_rank"] > 3.0
    assert "NOT a universal" in s8["gap_ratio_convention"]
