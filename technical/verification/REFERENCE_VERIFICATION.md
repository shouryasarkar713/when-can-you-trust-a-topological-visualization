# Reference verification notes

Reference list of `submission/report/Final_Report.md`, Section 13. Checked on 28 October 2026.

## Re-verified directly in this final pass

| Check | Method | Result |
|---|---|---|
| 20 entries with a Crossref DOI (Bauer; Brehmer & Munzner; Brown et al.; Carrière & Oudot; Cohen-Steiner et al.; Edelsbrunner et al.; Isenberg et al.; Lam et al.; Maria et al.; Munzner; Muszynski et al.; Nielsen; Perea et al. (SW1PerS); Perea & Harer; Sedlmair et al.; Strommen et al.; Tralie et al.; van Veen et al.; Zhou et al.; Zomorodian & Carlsson) | `check_references.py` fetches the Crossref record for each DOI and compares title, author surnames and order, year, container, volume, issue and pages with the entry (`reference_check_crossref.json`) | All titles, authors, volumes, issues and pages agree. Differences are only in the year field where Crossref records the online-first date and the entry uses the volume year: Brown et al. (Crossref 2020, volume 5 = 2021), Carrière & Oudot (2017, volume 18 = 2018), Cohen-Steiner et al. (2006, volume 37 = 2007), Perea & Harer (2014, volume 15 = 2015), Strommen et al. (2022, volume 60 = 2023), Zomorodian & Carlsson (2004, volume 33 = 2005). Crossref transliterates "Möller" as "Moller"; the entries keep the umlaut. |
| Sen, Singh & Tiwari (2026) | arXiv abstract page fetched | Title, author order and submission date (19 June 2026) confirmed; the abstract lists stability, cluster quality and topological shape preservation as the three axes. The full text was not read. |
| Perea & Harer (2015) | Crossref | Volume 15, issue 3, pages 799–838 (not issue 5) |
| Gudhi paper | Crossref | Authors Maria, Boissonnat, Glisse, Yvinec M.; pages 167–174; Crossref gives no LNCS volume |
| Non-Crossref URLs: JMLR (Belchí et al.; Carrière, Michel & Oudot; Tauzin et al.), GitHub (tda-mapper), IEEE VIS program page (LoCoMapper), NOAA GSOD directory, NOAA PSL ONI file, SPBG DOI | HTTP GET (`reference_url_check.json`) | All returned 200. `doi.org/10.5281/zenodo.2533369` returned 403 to a script (bot protection); it resolves in a browser according to the earlier research ledger. |

## Inherited from the earlier research ledger (`research_ledger.md`), not re-fetched in this pass

- Belchí et al. (2020), JMLR 21(202), 1–45; Carrière, Michel & Oudot (2018), JMLR 19(12), 1–39; Tauzin et al. (2021), JMLR 22(39), 1–6: volumes and pages come from the ledger (the JMLR pages exist).
- Springer LNCS volume 8592 for the Gudhi paper; the SPBG 2007 pages 91–100 and Zenodo record for Scikit-TDA.
- tda-mapper version 0.12.0 and first-release date; LoCoMapper authors, title, workshop and honorable mention (program page only; the full paper is behind a sign-in); the workshop date.
- GSOD terms of use and station identity; the ONI series derivation (ERSST v6 as of 7 September 2026).
- Sen et al. (2026) beyond the abstract; Nielsen's single-inspector result (secondary summary).

Citations marked † in the report were consulted at abstract or program-page level only. No bibliographic detail was invented: where a field could not be confirmed it is listed above.
