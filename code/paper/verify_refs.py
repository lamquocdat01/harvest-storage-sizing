#!/usr/bin/env python3
"""verify_refs.py (topic 40): venue-independent reference check, no e-mail in any request.

Usage: python verify_refs.py --latex <dir with main.bbl, main.pdf, refs.bib> --out <csv>

For each entry of refs.bib:
  * resolve the DOI through doi.org (CSL JSON), or fetch the URL when there is no DOI;
  * compare title / year / container / first-author family with the registry record;
  * read the retraction flags: Crossref `update-to`, `updated-by`, `relation`; title containing "retract";
  * mark arXiv-only entries and preprints younger than 6 months.
For the rendered main.pdf: count entries of the References section that print no identifier.
Exit 1 if a DOI/URL fails, an identifier is missing on the page, or a retraction flag is set.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "topic40-verify-refs/1.1"}


def fetch(url, headers=None, tries=6):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as fh:
                return fh.status, fh.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or i == tries - 1:
                return e.code, b""
            time.sleep(5 * 2 ** i)
        except Exception:
            if i == tries - 1:
                return 0, b""
            time.sleep(5 * 2 ** i)
    return 0, b""


def parse_bib(path):
    txt = path.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", txt, flags=re.S):
        fields = {k.lower(): v.strip() for k, v in re.findall(r"^\s*(\w+)\s*=\s*\{(.*)\},?\s*$", m.group(3), flags=re.M)}
        out.append({"type": m.group(1), "key": m.group(2).strip(), **fields})
    return out


def norm(s):
    s = re.sub(r"\\[a-zA-Z]+|[{}\\'\"`~^]", "", s or "")
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 3]


def rendered_entries(pdf):
    t = subprocess.run(["pdftotext", "-raw", "-enc", "UTF-8", str(pdf), "-"], capture_output=True).stdout.decode("utf-8", "replace")
    t = t.replace("\r\n", "\n")
    i = t.rfind("\nReferences")
    t = t[i:] if i >= 0 else t
    j = t.rfind("Vitae")
    t = t[:j] if j > 0 else t
    starts = list(re.finditer(r"^\f?\[(\d+)\] ", t, flags=re.M))
    ents = {}
    for k, m in enumerate(starts):
        end = starts[k + 1].start() if k + 1 < len(starts) else len(t)
        ents[int(m.group(1))] = re.sub(r"\s+", " ", t[m.end():end]).replace("- ", "-")
    return ents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--latex", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    a = ap.parse_args()
    bib = parse_bib(a.latex / "refs.bib")
    today = dt.date.today()
    rows = []
    bbl_keys = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", (a.latex / "main.bbl").read_text(encoding="utf-8"))
    ents = rendered_entries(a.latex / "main.pdf")
    num = {k: i + 1 for i, k in enumerate(bbl_keys)}
    for e in bib:
        doi = e.get("doi", "")
        if not doi:                      # IEEEtran build (make_bib default/v2): DOI printed through `note`
            m_note = re.search(r"doi\.org/([^}\s]+)", e.get("note", ""))
            doi = m_note.group(1) if m_note else ""
        r = {"key": e["key"], "doi": doi, "url": e.get("url", ""), "resolves": "", "registry": "", "title_match": "", "year_bib": e.get("year", ""),
             "year_registry": "", "year_ok": "", "family_ok": "", "container_registry": "", "retraction_flag": "", "arxiv_only": "", "preprint_lt_6m": "",
             "cited": "yes" if e["key"] in num else "no", "render_no": num.get(e["key"], ""), "id_on_page": ""}
        if doi:
            st, b = fetch("https://doi.org/" + doi, {"Accept": "application/vnd.citationstyles.csl+json"})
            r["resolves"] = "yes" if st == 200 and b else f"FAIL {st}"
            if st == 200 and b:
                m = json.loads(b)
                title = m.get("title") if isinstance(m.get("title"), str) else ((m.get("title") or [""])[0])
                tb, tr = norm(e.get("title", "")), norm(title)
                r["title_match"] = f"{sum(w in tr for w in tb)}/{len(tb)}"
                y = ((m.get("published-print") or m.get("issued") or m.get("published") or {}).get("date-parts") or [[None]])[0][0]
                ys = {str(((m.get(f) or {}).get("date-parts") or [[None]])[0][0]) for f in ("published-print", "published-online", "issued", "published")}
                r["year_registry"] = y
                r["year_ok"] = "yes" if e.get("year") in ys else f"check {sorted(ys)}"
                au = m.get("author") or [{}]
                fam = au[0].get("family") or au[0].get("literal") or ""
                first = re.split(r"\s+and\s+", e.get("author", ""))[0]
                r["family_ok"] = "yes" if fam and re.sub(r"[^a-z]", "", fam.lower().split()[-1]) in re.sub(r"[^a-z]", "", first.lower()) else f"check ({fam})"
                ct = m.get("container-title") or ""
                r["container_registry"] = ct if isinstance(ct, str) else (ct[0] if ct else "")
                r["registry"] = m.get("source") or ("DataCite" if m.get("publisher") and "DataCite" in str(m.get("source")) else "")
                flags = []
                if "retract" in (title or "").lower():
                    flags.append("title")
                st2, b2 = fetch("https://api.crossref.org/works/" + doi, tries=3)
                if st2 == 200 and b2:
                    cr = json.loads(b2)["message"]
                    r["registry"] = "Crossref"
                    for f in ("update-to", "updated-by"):
                        if cr.get(f):
                            flags.append(f + ":" + ",".join(str(x.get("type")) for x in cr[f]))
                    rel = cr.get("relation") or {}
                    for kk in rel:
                        if re.search(r"retract|correct|erratum|withdraw", kk, re.I):
                            flags.append("relation:" + kk)
                elif st2 == 404:
                    r["registry"] = "DataCite/other (not in Crossref)"
                r["retraction_flag"] = ";".join(flags)
                arx = doi.lower().startswith("10.48550/arxiv")
                r["arxiv_only"] = "yes" if arx else "no"
                if arx:
                    d = (m.get("issued") or {}).get("date-parts", [[None]])[0]
                    if d and d[0]:
                        age = (today - dt.date(d[0], (d[1] if len(d) > 1 else 1), (d[2] if len(d) > 2 else 1))).days
                        r["preprint_lt_6m"] = "yes" if age < 183 else "no"
            time.sleep(0.5)
        elif e.get("url"):
            st, b = fetch(e["url"], tries=3)
            r["resolves"] = "yes (url)" if st == 200 else f"FAIL {st}"
            r["registry"] = "URL"
        else:
            r["resolves"] = "NO IDENTIFIER"
        txt = ents.get(num.get(e["key"], -1), "")
        flat = re.sub(r"\s", "", txt).lower()
        if e["key"] in num:
            r["id_on_page"] = "doi" if doi and doi.lower() in flat else ("url" if "http" in flat else "MISSING")
        rows.append(r)
        print(e["key"][:26].ljust(27), r["resolves"][:8].ljust(9), r["title_match"].ljust(7), str(r["year_ok"])[:14].ljust(15), r["family_ok"][:16].ljust(17), r["id_on_page"].ljust(8), r["retraction_flag"], flush=True)
    with a.out.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    ok = sum(1 for r in rows if r["resolves"].startswith("yes"))
    miss = [r["key"] for r in rows if r["id_on_page"] == "MISSING"]
    extra_on_page = [k for k in ents if k > len(bbl_keys)]
    flags = [(r["key"], r["retraction_flag"]) for r in rows if r["retraction_flag"]]
    print(f"SUMMARY entries={n} resolved={ok} rendered_entries={len(ents)} bbl={len(bbl_keys)} missing_id_on_page={len(miss)} {miss} "
          f"flags={flags} extra={extra_on_page} arxiv_only={sum(r['arxiv_only'] == 'yes' for r in rows)} preprint_lt6m={sum(r['preprint_lt_6m'] == 'yes' for r in rows)}")
    return 1 if ok != n or miss or flags else 0


if __name__ == "__main__":
    sys.exit(main())
