#!/usr/bin/env python3
"""Report where each registered fact's derived value actually appears.

    python technical/verification/audit_coverage.py --root . [--out FILE]

For every fact in facts.py the value is re-derived from the saved results and searched (whitespace,
table bars, asterisks and underscores ignored, as in verify_evidence.py) in the report, the slide text,
the embedded speaker notes and the Q&A. The output lists

  * `registered_but_absent`: documents named in the fact's `where` list that do not contain the value
    (verify_evidence.py fails on these);
  * `present_but_unregistered`: documents that contain the value but are not named, i.e. text that the
    verifier does not check against that fact.

Presence of a short value such as "0.041" is a text match, not proof that the number is used in the same
sense; the unregistered list is therefore a prompt for manual review, not an automatic registration.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import facts as F  # noqa: E402


def squash(s):
    return re.sub(r"[\s|*`_]+", "", s).replace(" ", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(HERE.parent.parent))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    root = Path(a.root).resolve()
    from pptx import Presentation

    P = Presentation(str(root / "submission" / "presentation" / "Final_Presentation.pptx"))
    slides, notes = [], []
    for s in P.slides:
        for sh in s.shapes:
            if sh.has_text_frame:
                slides.append(sh.text_frame.text)
            elif getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    slides.append(" | ".join(c.text_frame.text for c in row.cells))
        if s.has_notes_slide:
            notes.append(s.notes_slide.notes_text_frame.text)
    docs = {
        "report": (root / "submission" / "report" / "Final_Report.md").read_text(encoding="utf8"),
        "slides": "\n".join(slides),
        "notes": "\n".join(notes),
        "qa": (root / "technical" / "build" / "presentation" / "QA_Preparation.md").read_text(encoding="utf8"),
    }
    sq = {k: squash(v) for k, v in docs.items()}
    rows = []
    for fid, cat, claim, fn, where, cmd, cav in F.FACTS:
        try:
            val = fn(str(root))
        except Exception as e:  # reported, never skipped
            rows.append({"id": fid, "claim": claim, "error": repr(e)})
            continue
        v = squash(val)
        present = [k for k in docs if v and v in sq[k]]
        reg = list(where)
        absent = [k for k in reg if k not in present and not (k == "slides" and "notes" in present and False)]
        unreg = [k for k in present if k not in reg and k != "notes"]
        rows.append({"id": fid, "claim": claim, "value": val[:80], "registered": reg, "present": present,
                     "registered_but_absent": absent, "present_but_unregistered": unreg})
    out = {"facts": len(rows), "with_errors": [r["id"] for r in rows if "error" in r],
           "registered_but_absent": {r["id"]: r["registered_but_absent"] for r in rows if r.get("registered_but_absent")},
           "present_but_unregistered": {r["id"]: r["present_but_unregistered"] for r in rows if r.get("present_but_unregistered")},
           "rows": rows}
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
