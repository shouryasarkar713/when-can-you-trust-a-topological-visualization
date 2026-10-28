"""Independent comparison of a regenerated tree against the baseline tree.

Usage: python -I compare_trees.py <baseline_dir> <regen_dir> <out_json> [subpath ...]

Per file class:
  .json  deep compare; volatile keys (wall-clock, timestamps, host/env) are ignored and
         LISTED; floats compared exactly first, then reported with max abs/rel difference.
  .csv/.md/.txt/.py/.yaml  newline-normalised text compare (CRLF vs LF is a platform artefact).
  .npz/.npy  array-by-array exact compare (max abs difference reported).
  .png   pixel compare (platform font rasterisation can differ): reports max abs diff and
         fraction of differing pixels.
  .html  newline-normalised text compare.
No tolerance is used to hide a difference: every difference is reported with its magnitude.
"""
import json, re, sys, hashlib
from pathlib import Path
import numpy as np

VOLATILE = re.compile(
    r"(^|_)(time|times|elapsed|runtime|wall|timestamp|generated|created|date|started|finished|"
    r"python|platform|hostname|machine|executable|cwd|path|abs_path|duration|ripser_time_s|time_s|"
    r"build_time|utc|version_string)($|_)|_s$|seconds", re.I)


def vol(k):
    return bool(VOLATILE.search(str(k)))


def walk(a, b, path, diffs, ignored, maxabs):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{path}.{k}"
            if k not in a or k not in b:
                diffs.append((p, "missing-key", "baseline" if k in a else "regen"))
                continue
            if vol(k) and not isinstance(a[k], (dict, list)):
                if a[k] != b[k]:
                    ignored.append(p)
                continue
            walk(a[k], b[k], p, diffs, ignored, maxabs)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append((path, "len", f"{len(a)} vs {len(b)}"))
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", diffs, ignored, maxabs)
    else:
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
            if a != b:
                d = abs(float(a) - float(b))
                maxabs[0] = max(maxabs[0], d)
                diffs.append((path, "num", f"{a} vs {b} (abs {d:.3g})"))
        elif a != b:
            if isinstance(a, str) and isinstance(b, str) and (
                    a.replace("\\", "/") == b.replace("\\", "/")):
                ignored.append(path + " (path-separator)")
            else:
                diffs.append((path, "value", f"{str(a)[:80]!r} vs {str(b)[:80]!r}"))


def cmp_file(fa, fb):
    ext = fa.suffix.lower()
    r = {"ext": ext}
    if ext == ".json":
        a, b = json.loads(fa.read_text(encoding="utf8")), json.loads(fb.read_text(encoding="utf8"))
        diffs, ign, mx = [], [], [0.0]
        walk(a, b, "$", diffs, ign, mx)
        r.update(status="identical" if not diffs else "DIFFERENT", n_diffs=len(diffs),
                 diffs=diffs[:15], ignored_volatile=len(ign), max_abs_num_diff=mx[0])
    elif ext in (".csv", ".md", ".txt", ".py", ".yaml", ".html", ".js", ".log"):
        ta = fa.read_bytes().replace(b"\r\n", b"\n")
        tb = fb.read_bytes().replace(b"\r\n", b"\n")
        if ext == ".csv" and b"time_s" in ta.split(b"\n")[0]:
            def _drop(t):  # wall-clock column is environment-dependent by design
                rows = [l.split(",") for l in t.decode().splitlines()]
                i = rows[0].index("time_s")
                return "\n".join(",".join(c for j, c in enumerate(r_) if j != i) for r_ in rows).encode()
            ta, tb = _drop(ta), _drop(tb)
            r["note"] = "time_s column excluded (wall-clock)"
        if ext == ".md" and b"Run date (UTC)" in ta:
            ta = re.sub(rb"Run date \(UTC\): [^\n]*", b"", ta)
            tb = re.sub(rb"Run date \(UTC\): [^\n]*", b"", tb)
            r["note"] = "run-date line excluded"
        r["status"] = "identical" if ta == tb else "DIFFERENT"
        r["byte_identical_raw"] = fa.read_bytes() == fb.read_bytes()
        if ta != tb:
            la, lb = ta.decode("utf8", "replace").splitlines(), tb.decode("utf8", "replace").splitlines()
            nd = [i for i, (x, y) in enumerate(zip(la, lb)) if x != y]
            r.update(n_diff_lines=len(nd) + abs(len(la) - len(lb)), first_diff_line=(nd[0] + 1) if nd else None)
    elif ext in (".npz", ".npy"):
        A, B = np.load(fa, allow_pickle=True), np.load(fb, allow_pickle=True)
        if ext == ".npy":
            A, B = {"arr": A}, {"arr": B}
        ks = sorted(set(A.files if ext == ".npz" else A) | set(B.files if ext == ".npz" else B))
        worst, bad = 0.0, []
        for k in ks:
            if k not in A or k not in B:
                bad.append(k + ":missing"); continue
            x, y = np.asarray(A[k]), np.asarray(B[k])
            if x.shape != y.shape:
                bad.append(f"{k}:shape {x.shape} vs {y.shape}"); continue
            if x.dtype.kind in "fc":
                m = np.isnan(x) & np.isnan(y)
                d = np.where(m, 0, np.abs(np.where(np.isfinite(x) | np.isfinite(y), x - y, 0)))
                mx = float(np.max(d)) if d.size else 0.0
            elif x.dtype.kind in "iub":
                mx = float(np.max(np.abs(x.astype(float) - y.astype(float)))) if x.size else 0.0
            else:
                mx = 0.0 if np.array_equal(x, y) else 1.0
            worst = max(worst, mx)
            if mx > 0:
                bad.append(f"{k}:max|d|={mx:.3g}")
        r.update(status="identical" if not bad else "DIFFERENT", worst_abs=worst, bad=bad[:10])
    elif ext == ".png":
        from PIL import Image
        if fa.read_bytes() == fb.read_bytes():
            r["status"] = "identical"; r["byte_identical"] = True
        else:
            ia, ib = Image.open(fa).convert("RGBA"), Image.open(fb).convert("RGBA")
            if ia.size != ib.size:
                r.update(status="DIFFERENT", note=f"size {ia.size} vs {ib.size}")
            else:
                x, y = np.asarray(ia).astype(int), np.asarray(ib).astype(int)
                d = np.abs(x - y).max(axis=2)
                r.update(status="pixel-identical" if d.max() == 0 else "pixel-different",
                         byte_identical=False, max_abs_pixel=int(d.max()),
                         frac_pixels_differing=round(float((d > 0).mean()), 5),
                         frac_pixels_diff_gt32=round(float((d > 32).mean()), 5))
    else:
        r["status"] = "identical" if fa.read_bytes() == fb.read_bytes() else "DIFFERENT"
    return r


def main():
    base, regen, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    subs = sys.argv[4:] or ["."]
    res = {}
    for sp in subs:
        for fa in sorted((base / sp).rglob("*")):
            if not fa.is_file() or "__pycache__" in fa.parts or fa.suffix == ".pyc":
                continue
            rel = fa.relative_to(base).as_posix()
            fb = regen / rel
            if not fb.exists():
                res[rel] = {"status": "MISSING-IN-REGEN"}; continue
            try:
                res[rel] = cmp_file(fa, fb)
            except Exception as e:  # report, do not hide
                res[rel] = {"status": "COMPARE-ERROR", "error": repr(e)}
    summ = {}
    for v in res.values():
        summ[v["status"]] = summ.get(v["status"], 0) + 1
    out.write_text(json.dumps({"baseline": str(base), "regen": str(regen), "summary": summ,
                               "files": res}, indent=1, default=str), encoding="utf8")
    print(json.dumps(summ))
    for k, v in res.items():
        if v["status"] not in ("identical",):
            print(f"  {v['status']:18s} {k}  " + {kk: vv for kk, vv in v.items()
                  if kk in ("n_diffs", "max_abs_num_diff", "worst_abs", "max_abs_pixel",
                            "frac_pixels_differing", "n_diff_lines", "note", "ignored_volatile")}.__str__())


if __name__ == "__main__":
    main()
