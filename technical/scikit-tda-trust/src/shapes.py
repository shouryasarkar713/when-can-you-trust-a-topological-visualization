"""Deterministic synthetic point-cloud generators for the Scikit-TDA evaluation.

Four generators with known structural ground truth (blueprint Section 5.2):

  annulus       one prominent loop          -> H1 ground-truth rank k = 1
  figure_eight  two co-dominant loops       -> H1 ground-truth rank k = 2
  blob          no loop (control)           -> no meaningful H1 rank
  three_blobs   three separated components  -> component structure read from H0

All stochastic steps use numpy.random.Generator with explicit seeds, so arrays
are reproducible bit-for-bit on the pinned numpy version (stream compatibility
policy, NEP 19). Generators match the implementations verified on 2026-10-21
(scripts/smoke_test_final.py in the planning workspace).

IMPORTANT (R-1 in IMPLEMENTATION_NOTES.md): the ground-truth rank of each
dataset is known from its synthetic CONSTRUCTION. The persistence-gap ratio
evaluated at that rank is a validity check for these datasets only; it is NOT
a universal automatic loop-counting rule.
"""
from __future__ import annotations

import numpy as np

#: Ground-truth H1 rank per shape (None = no meaningful rank; calibration only).
GROUND_TRUTH_H1_RANK = {
    "annulus": 1,
    "figure_eight": 2,
    "blob": None,
    "three_blobs": None,
}

#: Config keys that describe a shape but are NOT generator parameters.
_META_KEYS = {"ground_truth_h1_rank", "role"}


def annulus(n: int = 500, r_in: float = 1.0, r_out: float = 1.4,
            noise: float = 0.05, seed: int = 42) -> np.ndarray:
    """Uniform points on a circular band [r_in, r_out] + Gaussian noise.

    Construction implies ONE prominent H1 class (the loop around the hole).
    """
    rng = np.random.default_rng(seed)
    t = rng.uniform(0, 2 * np.pi, n)
    rad = rng.uniform(r_in, r_out, n)
    X = np.column_stack([rad * np.cos(t), rad * np.sin(t)])
    return X + rng.normal(0, noise, X.shape)


def figure_eight(n: int = 500, noise: float = 0.05, seed: int = 42) -> np.ndarray:
    """Lemniscate of Gerono: x = cos t, y = sin(2t)/2, t ~ U[0, 2pi).

    Construction implies TWO approximately equal H1 classes (the two lobes),
    so the correct gap statistic is r_2 = p_2 / p_3; r_1 is expected to be
    close to 1 and is NOT a failure signal.
    """
    rng = np.random.default_rng(seed)
    t = rng.uniform(0, 2 * np.pi, n)
    X = np.column_stack([np.cos(t), np.sin(2 * t) / 2])
    return X + rng.normal(0, noise, X.shape)


def blob(n: int = 500, spread: float = 0.45, seed: int = 42) -> np.ndarray:
    """Isotropic Gaussian cloud — the no-loop control.

    Construction implies NO dominant H1 class; any gap ratio is calibration
    only. Its Mapper graph may still show short noise-scale cycles (a finding
    about reading Mapper graphs, not about the data).
    """
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, spread, (n, 2))


def three_blobs(n: int = 450, spread: float = 0.25, seed: int = 42,
                centers: tuple[tuple[float, float], ...] = (
                    (-2.0, 0.0), (2.0, 0.0), (0.0, 2.5))) -> np.ndarray:
    """Three well-separated Gaussian blobs — the component-counting control.

    Construction implies three connected components (read from H0: two late
    merges plus the essential class) and no prominent H1 class.
    """
    rng = np.random.default_rng(seed)
    centers = tuple(centers)
    per = n // len(centers)
    pts = [rng.normal(c, spread, (per, 2)) for c in centers]
    return np.vstack(pts)


_GENERATORS = {
    "annulus": annulus,
    "figure_eight": figure_eight,
    "blob": blob,
    "three_blobs": three_blobs,
}


def make_shape(name: str, params: dict) -> np.ndarray:
    """Build a shape by name from a config dict (seed included).

    Raises ValueError with an actionable message on unknown names or
    non-positive n.
    """
    if name not in _GENERATORS:
        raise ValueError(
            f"Unknown shape '{name}'. Available: {sorted(_GENERATORS)}. "
            "Check configs/shapes.yaml.")
    params = {k: v for k, v in params.items() if k not in _META_KEYS}
    n = int(params.get("n", 500))
    if n <= 0:
        raise ValueError(f"n must be positive, got {n} (shape '{name}').")
    if "seed" not in params:
        raise ValueError(
            f"Missing 'seed' for shape '{name}' — seeds are mandatory "
            "(blueprint Section 9: every stochastic step is seeded).")
    if name == "three_blobs" and "centers" in params:
        params["centers"] = tuple(tuple(c) for c in params["centers"])
    return _GENERATORS[name](**params)
