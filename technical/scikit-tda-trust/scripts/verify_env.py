#!/usr/bin/env python3
"""Verify the pinned environment: version assertions + smoke checks.

Fails loudly (non-zero exit + explicit message) on ANY of:
  - a pinned package missing or at the wrong version (requirements.txt),
  - a core import failure,
  - an API-surface fact changing (ripser/persim/kmapper drift),
  - the end-to-end smoke computation not producing its known construction
    property (unit circle -> exactly one dominant H1 class).

Writes results/env/verification.json and results/env/pip_freeze.txt so every
later claim about the environment is traceable to a generated file.
"""
from __future__ import annotations

import importlib
import importlib.metadata as md
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

CHECKS: list[dict] = []


def record(name: str, ok: bool, detail: str) -> None:
    CHECKS.append({"check": name, "ok": bool(ok), "detail": detail})
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")


def require(name: str, ok: bool, detail: str) -> None:
    record(name, ok, detail)
    if not ok:
        print(f"\nENVIRONMENT VERIFICATION FAILED at: {name}\n{detail}\n"
              "Fix the environment (see README 'Setup') before running "
              "experiments. Do NOT silently change pins; diagnose, correct "
              "minimally, and record the change in IMPLEMENTATION_NOTES.md.",
              file=sys.stderr)
        sys.exit(1)


def main() -> int:
    print(f"Python : {sys.version.split()[0]}  ({sys.executable})")
    print(f"Platform: {platform.platform()}\n")

    # ---- 1. pinned versions -------------------------------------------
    req_path = REPO / "requirements.txt"
    pins = []
    for line in req_path.read_text().splitlines():
        line = line.split("#")[0].strip()
        if "==" in line:
            pkg, ver = [x.strip() for x in line.split("==", 1)]
            pins.append((pkg, ver))
    for pkg, want in pins:
        try:
            got = md.version(pkg)
        except md.PackageNotFoundError:
            require(f"pin:{pkg}", False, f"NOT INSTALLED (pin: {want})")
            continue
        require(f"pin:{pkg}", got == want,
                f"installed {got}, pinned {want}")

    # ---- 2. imports ----------------------------------------------------
    for mod in ["numpy", "scipy", "sklearn", "matplotlib", "networkx",
                "yaml", "ripser", "persim", "kmapper", "tadasets"]:
        try:
            importlib.import_module(mod)
            record(f"import:{mod}", True, "ok")
        except Exception as exc:  # noqa: BLE001
            require(f"import:{mod}", False, f"{type(exc).__name__}: {exc}")

    # ---- 3. API-surface facts (drift sentinels) ------------------------
    import ripser as ripser_mod
    import persim as persim_mod
    import kmapper as km

    public = [n for n in dir(ripser_mod) if not n.startswith("_")]
    require("api:ripser.no_plot_dgms", "plot_dgms" not in public,
            f"ripser exports {public} (diagram plotting lives in persim)")
    for fn in ["ripser", "Rips", "lower_star_img", "correlation_to_distance"]:
        require(f"api:ripser.{fn}", hasattr(ripser_mod, fn), "present")

    for fn in ["plot_diagrams", "bottleneck", "wasserstein",
               "bottleneck_matching", "wasserstein_matching"]:
        require(f"api:persim.{fn}", hasattr(persim_mod, fn), "present")
    record("api:persim.__version__", not hasattr(persim_mod, "__version__"),
           "absent (expected; use importlib.metadata)")

    for fn in ["KeplerMapper", "CubicalCover", "to_networkx", "draw_matplotlib"]:
        require(f"api:kmapper.{fn}", hasattr(km, fn),
                "module-level" if fn in ("to_networkx", "draw_matplotlib") else "present")

    # ---- 4. end-to-end smoke: construction property ---------------------
    import numpy as np
    from pipeline import gap_ratio, h1_persistences

    t = np.linspace(0, 2 * np.pi, 80, endpoint=False)
    circle = np.column_stack([np.cos(t), np.sin(t)])
    from ripser import ripser
    dgms = ripser(circle, maxdim=1)["dgms"]
    pers = h1_persistences(dgms[1])
    n_dominant = int(np.sum(pers > 0.5 * pers[0])) if len(pers) else 0
    r1 = gap_ratio(pers, 1)
    require("smoke:circle_H1_one_dominant_class", n_dominant == 1,
            f"H1 classes={len(pers)}, dominant(>0.5*top)={n_dominant}, "
            f"top persistence={pers[0]:.3f}, r_1={'n/a' if r1 is None else round(r1, 1)}")

    # ---- 5. mapper end-to-end (graph + HTML into a temp dir) ------------
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    rng = np.random.default_rng(0)
    X = np.column_stack([rng.uniform(1, 1.2, 60) * np.cos(rng.uniform(0, 2 * np.pi, 60)),
                         rng.uniform(1, 1.2, 60) * np.sin(rng.uniform(0, 2 * np.pi, 60))])
    mapper = km.KeplerMapper()
    lens = PCA(n_components=1).fit_transform(X)
    graph = mapper.map(lens, X, cover=km.CubicalCover(n_cubes=5, perc_overlap=0.35),
                       clusterer=KMeans(n_clusters=2, random_state=42, n_init=10))
    require("smoke:mapper_graph_built", len(graph["nodes"]) > 0,
            f"{len(graph['nodes'])} nodes, "
            f"{sum(len(v) for v in graph['links'].values()) // 2} edges")
    with tempfile.TemporaryDirectory() as td:
        html = Path(td) / "smoke.html"
        mapper.visualize(graph, path_html=str(html), title="verify_env smoke")
        ok = html.exists() and html.stat().st_size > 1000
        require("smoke:mapper_html_exported", ok,
                f"{html.stat().st_size if html.exists() else 0} bytes")

    # ---- 6. persist evidence -------------------------------------------
    out_dir = REPO / "results" / "env"
    out_dir.mkdir(parents=True, exist_ok=True)
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout
    (out_dir / "pip_freeze.txt").write_text(freeze)
    report = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "pins_checked": {p: v for p, v in pins},
        "checks": CHECKS,
        "all_passed": all(c["ok"] for c in CHECKS),
    }
    (out_dir / "verification.json").write_text(json.dumps(report, indent=2))

    n_fail = sum(not c["ok"] for c in CHECKS)
    print(f"\n{len(CHECKS) - n_fail}/{len(CHECKS)} checks passed. "
          f"Evidence: {out_dir / 'verification.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
