"""Generator determinism, validity, and error handling (MVP completion tests)."""
import numpy as np
import pytest

from shapes import annulus, blob, figure_eight, three_blobs, make_shape

ALL_SHAPES = [
    ("annulus", annulus), ("figure_eight", figure_eight),
    ("blob", blob), ("three_blobs", three_blobs),
]


@pytest.mark.parametrize("name,fn", ALL_SHAPES)
def test_same_seed_identical(name, fn):
    """Same seed must reproduce the array bit-for-bit (blueprint Section 9)."""
    a = fn(seed=42)
    b = fn(seed=42)
    assert isinstance(a, np.ndarray) and a.shape[1] == 2
    np.testing.assert_array_equal(a, b)


@pytest.mark.parametrize("name,fn", ALL_SHAPES)
def test_different_seed_different(name, fn):
    a, b = fn(seed=42), fn(seed=43)
    assert not np.array_equal(a, b)


def test_annulus_construction():
    """Radii concentrate in the band [r_in, r_out] up to noise tolerance."""
    X = annulus(n=2000, noise=0.05, seed=7)
    r = np.hypot(X[:, 0], X[:, 1])
    assert r.min() > 1.0 - 4 * 0.05
    assert r.max() < 1.4 + 4 * 0.05
    # not degenerate: the band is populated around its middle
    assert np.mean((r > 1.1) & (r < 1.3)) > 0.4


def test_figure_eight_construction():
    """Points track the lemniscate x=cos t, y=sin(2t)/2 up to noise."""
    X = figure_eight(n=2000, noise=0.05, seed=7)
    assert X[:, 0].min() > -1 - 0.3 and X[:, 0].max() < 1 + 0.3
    assert X[:, 1].min() > -0.5 - 0.3 and X[:, 1].max() < 0.5 + 0.3
    assert abs(X[:, 0].mean()) < 0.1  # symmetric lobes


def test_three_blobs_construction():
    """450 points split evenly across the three configured centers."""
    X = three_blobs(n=450, seed=7)
    assert X.shape == (450, 2)
    # nearest-center assignment recovers three balanced groups
    centers = np.array([(-2, 0), (2, 0), (0, 2.5)])
    d = np.linalg.norm(X[:, None, :] - centers[None, :, :], axis=2)
    assign = d.argmin(axis=1)
    counts = np.bincount(assign, minlength=3)
    assert (counts == 150).all()
    # centers are recovered within tolerance
    for k in range(3):
        assert np.allclose(X[assign == k].mean(axis=0), centers[k], atol=0.1)


def test_make_shape_plumbs_params():
    X = make_shape("annulus", {"n": 100, "seed": 5, "noise": 0.0})
    r = np.hypot(X[:, 0], X[:, 1])
    assert ((r >= 1.0) & (r <= 1.4)).all()  # zero noise: exact band


def test_make_shape_errors():
    with pytest.raises(ValueError, match="Unknown shape"):
        make_shape("torus_knot", {"seed": 1})
    with pytest.raises(ValueError, match="seed"):
        make_shape("annulus", {"n": 10})
    with pytest.raises(ValueError, match="positive"):
        make_shape("annulus", {"n": -5, "seed": 1})


def test_headline_shapes_match_config_defaults():
    """The headline artifacts use n=500 / seed=42 (README + configs)."""
    assert annulus().shape == (500, 2)
    assert figure_eight().shape == (500, 2)
    assert blob().shape == (500, 2)
    assert three_blobs().shape == (450, 2)
