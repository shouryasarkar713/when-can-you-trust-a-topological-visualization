#!/usr/bin/env python3
"""Re-fetch bibliographic records from Crossref for every DOI in the report's reference list and compare
author list (family names, order), year, container, volume, issue and pages with the reference entry.
Usage: python check_references.py <Final_Report.md> <out.json>   (needs network; polite 1.5 s delay)"""
import json, re, sys, time, urllib.request, urllib.error
md = open(sys.argv[1], encoding="utf8").read()
refs = md.split("## 13. References", 1)[1].split("## Appendix A", 1)[0]
entries = [l[2:] for l in refs.splitlines() if l.startswith("- ")]
out = []
for e in entries:
    m = re.search(r"https://doi\.org/(\S+)", e)
    if not m:
        out.append({"entry": e[:80], "doi": None, "status": "no DOI (checked elsewhere)"}); continue
    doi = m.group(1).rstrip(").")
    rec = None
    for attempt in range(4):
        try:
            req = urllib.request.Request("https://api.crossref.org/works/" + doi, headers={"User-Agent": "scikit-tda-submission-check/1.0 (mailto:none@example.org)"})
            rec = json.load(urllib.request.urlopen(req, timeout=30))["message"]; break
        except urllib.error.HTTPError as ex:
            time.sleep(5 * (attempt + 1))
        except Exception as ex:
            time.sleep(3)
    if rec is None:
        out.append({"entry": e[:80], "doi": doi, "status": "FETCH FAILED"}); continue
    fam = [a.get("family", a.get("name", "")) for a in rec.get("author", [])]
    year = (rec.get("issued", {}).get("date-parts") or [[None]])[0][0]
    cont = (rec.get("container-title") or [""])[0]
    entry_fams = re.findall(r"([A-ZÀ-Ý][\w'’\-À-ÿ]+(?: [A-Z][\w\-]+)?),\s(?:[A-Z]\.|[A-Z]\.-)", e.split("(")[0])
    ok_auth = all(any(f.lower().split()[-1] in x.lower() for x in fam) for f in [t.split()[-1] for t in entry_fams]) if entry_fams else None
    pages = rec.get("page", "")
    out.append({"entry": e[:90], "doi": doi, "crossref": {"title": (rec.get("title") or [""])[0][:100], "authors": fam, "year": year,
                "container": cont, "volume": rec.get("volume"), "issue": rec.get("issue"), "pages": pages},
                "authors_in_entry_found_in_record": ok_auth,
                "year_in_entry": bool(re.search(r"\(%s\)" % year, e)) if year else None,
                "pages_in_entry": (pages.replace("-", "–") in e) if pages else None,
                "volume_in_entry": (str(rec.get("volume")) in e) if rec.get("volume") else None})
    time.sleep(1.5)
json.dump(out, open(sys.argv[2], "w", encoding="utf8"), indent=1, ensure_ascii=False)
for o in out:
    c = o.get("crossref")
    flag = "" if not c else ("" if all(o.get(k) in (True, None) for k in ("authors_in_entry_found_in_record", "year_in_entry", "pages_in_entry", "volume_in_entry")) else "  <-- CHECK")
    print(o["doi"], "|", (c or {}).get("year"), (c or {}).get("container", "")[:40], (c or {}).get("volume"), (c or {}).get("issue"), (c or {}).get("pages"), o.get("status", ""), flag)
