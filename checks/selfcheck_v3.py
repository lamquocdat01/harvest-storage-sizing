"""P0R2 Viec 2.4: self-checks of manuscript_v3 (P3R/selfcheck.py run on manuscript_v3/latex, plus the P0R2 patterns).

P0R2 patterns, counted on the sources (comments removed, number macros expanded) AND on the rendered PDFs
(pdftotext), main and supplement:
  heavy-tailed              0 in title and body, except a sentence that quotes our earlier article (Deep3)
  miss-optimal              0
  abstract only             0
  IoT-7                     0 (manuscript IDs of papers under review)
  holds without tolerance   0
  15 of 18                  0
Also counts "X, not Y" constructions in main.tex (S6 m9: keep <= 2) and "certificate" in main.tex.
Writes P0R2/selfcheck_v3.json, P0R2/HANDNUM_CHECK_v3.txt, P0R2/selfcheck_v3_long_sentences.txt.
Usage: python P0R2/selfcheck_v3.py
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import subprocess

TOPIC = pathlib.Path(__file__).resolve().parents[1]
LAT = TOPIC / "manuscript_v3" / "latex"
CHK = TOPIC / "P3R"
if not LAT.exists():                      # repository layout (code/sync_repo.py): paper/v3, checks/
    LAT, CHK = TOPIC / "paper" / "v3", TOPIC / "checks"
OUT = pathlib.Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("sc", CHK / "selfcheck.py")
SC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SC)
SC.LAT, SC.OUT = LAT, OUT
SC.PARAM_HINTS += ["Table~S12", "10^{-12}", "10\\,\\%", "10 %", "0.005", "two tolerances", "1/8", "1/16"]

P0R2_RULES = [
    ("heavy-tailed", r"heavy[- ]tailed", r"earlier article|deep3_jiot2026|Deep3"),
    ("miss-optimal", r"miss[- ]optimal", None),
    ("abstract only", r"abstract only|read from the abstract", None),
    ("IoT-7", r"IoT-7\d{4}", None),
    ("holds without tolerance", r"holds without tolerance", None),
    ("15 of 18", r"\b15 of 18\b", None),
]


def macros():
    m = {}
    for fn in ("numbers.tex", "numbers_a2.tex", "numbers_v3.tex"):
        for k, v in re.findall(r"\\newcommand\{\\([A-Za-z]+)\}\{((?:[^{}]|\{[^{}]*\})*)\}",
                               (LAT / fn).read_text(encoding="utf-8")):
            m[k] = v
    return m


def expand(t, M):
    for _ in range(2):
        t = re.sub(r"\\([A-Za-z]+)(\{\})?", lambda x: M.get(x.group(1), x.group(0)), t)
    return t


def pdftext(name):
    pdf = LAT / f"{name}.pdf"
    r = subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", str(pdf), "-"], capture_output=True)
    return re.sub(r"-\n\s*", "", r.stdout.decode("utf-8", "replace"))       # join hyphenated line breaks


def p0r2_checks():
    M = macros()
    out = {}
    srcs = {fn: expand(SC.strip_comments((LAT / fn).read_text(encoding="utf-8")), M)
            for fn in ("main.tex", "supp.tex", "related_work.tex", "prereg_table.tex", "sizing_table.tex",
                       "supp_tables.tex", "supp_p3r_tables.tex")}
    srcs["main.pdf"] = pdftext("main")
    srcs["supp.pdf"] = pdftext("supp")
    for name, pat, qual in P0R2_RULES:
        for fn, t in srcs.items():
            S = SC.sentences(t)
            hits = [s for s in S if re.search(pat, s, re.I)]
            bad = [s for s in hits if not (qual and re.search(qual, s, re.I))]
            out.setdefault(name, {})[fn] = {"hits": len(hits), "violations": len(bad), "text": [b[:240] for b in bad]}
    # S6 m9: "X, not Y" cadence in main.tex + related_work.tex (sources, comments removed)
    body = SC.strip_comments((LAT / "main.tex").read_text(encoding="utf-8")) + \
        SC.strip_comments((LAT / "related_work.tex").read_text(encoding="utf-8"))
    xny = re.findall(r"[A-Za-z\-]+,\s+not\s+[a-z][A-Za-z\- ]{0,30}", body)
    out["X, not Y (main+related, <= 2)"] = {"main.tex": {"hits": len(xny), "violations": max(0, len(xny) - 2),
                                                         "text": xny}}
    cert = re.findall(r"[^.]*certif[^.]*\.", SC.strip_comments((LAT / "main.tex").read_text(encoding="utf-8")) +
                      SC.strip_comments((LAT / "related_work.tex").read_text(encoding="utf-8")))
    out["certificate/certified (info)"] = {"main.tex": {"hits": len(cert), "violations": 0,
                                                        "text": [c.strip()[:200] for c in cert]}}
    return out


def main():
    # P3R rules, hand-typed digits and sentences > 35 words on manuscript_v3 (files written into P0R2/:
    # selfcheck_regex.json, HANDNUM_CHECK_40.txt, selfcheck_long_sentences.txt)
    SC.main()
    rx = SC.regex_checks()
    rx.update(p0r2_checks())
    (OUT / "selfcheck_v3.json").write_text(json.dumps(rx, indent=1, ensure_ascii=False), encoding="utf-8")
    tot = sum(v["violations"] for d in rx.values() for v in d.values())
    print("regex violations (P3R + P0R2 rules):", tot)
    for k, d in rx.items():
        print(f"  {k}: hits {sum(v['hits'] for v in d.values())}, violations {sum(v['violations'] for v in d.values())}")


if __name__ == "__main__":
    main()
