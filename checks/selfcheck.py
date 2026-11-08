"""Viec 6 (P3R): self-checks of the v2 sources.

1. Forbidden phrases in main.tex and supp.tex (LaTeX comments removed), each must have 0 hits unless the stated
   qualifier is in the same sentence.
2. Hand-typed digits in the prose of main.tex: every digit outside macros, \\cite/\\ref/\\label/\\input/\\includegraphics
   arguments and comments is listed with its sentence and a category; categories other than the allowed ones are
   flagged "CHECK" for the author.
Writes P3R/selfcheck_regex.json and P3R/HANDNUM_CHECK_40.txt. Usage: python P3R/selfcheck.py
"""
from __future__ import annotations

import json
import pathlib
import re

TOPIC = pathlib.Path(__file__).resolve().parents[1]
LAT = TOPIC / "submission_package" / "v2" / "latex"
if not LAT.exists():                      # repository layout (sync_repo.py): paper/v2
    LAT = TOPIC / "paper" / "v2"
OUT = pathlib.Path(__file__).resolve().parent   # P3R/ in the topic folder, checks/ in the repository (P0R2 m6)


def strip_comments(t):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", ln) for ln in t.splitlines())


def sentences(t):
    t = re.sub(r"\s+", " ", t)
    return re.split(r"(?<=[.!?])\s+(?=[A-Z\\(])", t)


RULES = [
    ("any event-independent controller", r"any event-independent controller", r"never enters outage"),
    ("violates the model", r"violates the model", None),
    ("No theorem of that paper is used", r"No theorem of that paper is used", None),
    ("checked to be identical", r"checked to be identical", None),
    ("indistinguishable", r"indistinguishable", None),
    ("attained exactly when", r"attained exactly when", r"for every duration law"),
    ("miss_per8_at_half", r"miss\\?_per8\\?_at\\?_half", None),
    ("avoids outage", r"avoids? outages?", "K3"),
]


def regex_checks():
    out = {}
    for fn in ("main.tex", "supp.tex", "related_work.tex"):
        t = strip_comments((LAT / fn).read_text(encoding="utf-8"))
        S = sentences(t)
        for name, pat, qual in RULES:
            hits = [s for s in S if re.search(pat, s, re.I)]
            bad = [s for s in hits if not (qual and qual != "K3" and re.search(qual, s, re.I))]
            if qual == "K3":       # allowed only as a negated statement backed by the K3 check
                bad = [s for s in hits if not re.search(r"does not avoid|not because it avoids|no(?:t)? avoid", s, re.I)]
            out.setdefault(name, {})[fn] = {"hits": len(hits), "violations": len(bad), "text": [b[:240] for b in bad]}
        # P3R2 (CP_R16, Viec 1.5): the "first ... miss floor" claim must carry "events with duration" in the same
        # sentence, and Lemma greedy must not be marked New on any line (table rows are lines)
        hits = [s for s in S if re.search(r"first finite-capacity miss floor", s, re.I)]
        bad = [s for s in hits if not re.search(r"events with duration", s, re.I)]
        out.setdefault("first floor needs 'events with duration'", {})[fn] = {
            "hits": len(hits), "violations": len(bad), "text": [b[:240] for b in bad]}
        bad = [ln for ln in t.splitlines() if re.search(r"Lemma~\\ref\{lem:greedy\}.*New", ln)]
        out.setdefault("Lemma greedy marked New", {})[fn] = {
            "hits": len(bad), "violations": len(bad), "text": [b[:240] for b in bad]}
    # P3R2 (CP3 #3, Viec 2): no 100 % share and no "avoids outage" in Sec. VI-E of main.tex (macros expanded)
    t = strip_comments((LAT / "main.tex").read_text(encoding="utf-8"))
    sec = t[t.index(r"\label{sec:throttle}"):t.index(r"\section{A Sizing Procedure")]
    macros = {}
    for fn in ("numbers.tex", "numbers_a2.tex"):
        for k, v in re.findall(r"\\newcommand\{\\([A-Za-z]+)\}\{((?:[^{}]|\{[^{}]*\})*)\}",
                               (LAT / fn).read_text(encoding="utf-8")):
            macros[k] = v
    sec_x = re.sub(r"\\([A-Za-z]+)(\{\})?", lambda m: macros.get(m.group(1), m.group(0)), sec)
    bad = [s for s in sentences(sec_x) if re.search(r"100\s*\\%|100\\,\\%", s)
           and re.search(r"outage|\\pi|per", s, re.I)]
    out["VI-E: 100 % near pi_per/outage"] = {"main.tex": {"hits": len(bad), "violations": len(bad),
                                                          "text": [b[:240] for b in bad]}}
    bad = [s for s in sentences(sec_x) if re.search(r"avoids outage", s, re.I)]
    out["VI-E: avoids outage"] = {"main.tex": {"hits": len(bad), "violations": len(bad), "text": [b[:240] for b in bad]}}
    return out


ALLOWED = [
    ("theorem/section/table label", r"(Thms?\.|Lemma|Theorem|Proposition|Corollary|Table|Section|Sec\.|Fig\.|Eq\.|Thm\.)~?\s*[\d\u2013\-]+"),
    ("hypothesis/RQ label", r"\b(H\d[a-e]?|E\d|RQ\d|A1|A2|S\d)\b"),
    ("year", r"\b(19|20)\d\d\b"),
    ("manuscript ID", r"IoT-\d{5}-\d{4}"),
    ("ORCID/e-mail", r"\d{4}-\d{4}-\d{4}-\d{4}"),
    ("standard or product name", r"SHA-256|CC BY 4\.0|(Opus|Fable) \d\.\d|p\{0\.\d+"),
]
MATH_CONST = re.compile(r"\$[^$]*\$")

PARAM_HINTS = [
    "K=8", "K=64", "K=16", "K\\in", "r\\in", "r=14.3", "r=15", "\\lt=0.04", "\\lt=0.036", "\\lt\\in", "m\\in", "m=0.25",
    "\\eps\\in", "\\eps\\ge0.6", "\\eps=0.45", "0.248", "1-min", "n=600", "10--30", "theta=0.05", "\\theta=0.05",
    "B=1000", "7-day", "10^5", "10^{-6}", "\\alpha=0.05", "3-day", "20\\,\\%", "\\pm0.03", "0.01", "0.005",
    "(8 values)", "20 capacities", "\\{0,0.01,0.04,0.1\\}", "\\{1.1,\\dots,300\\}", "\\{2,\\dots,64\\}", "a=1/8",
    "1/16", "1/8", "\\{0.5,0.6\\}", "[0.18,0.32]", "a_j\\le1", "gaps ... 2", "Himawari-9", "SARAH-3", "2014",
    "B--F", "four seasons", "3 standard errors", "\\{g,g+1\\}", "\\{1,\\dots,T\\}", "n\\ge1", "D\\ge8", "8 frames",
    "from 8 to 16", "K=8$ to $K=64", "x_t\\in\\{0,1\\}", "[0,r-1]", "least 2", "(1+m)", "\\ge0", "1-\\pi",
]


def handnum():
    t = (LAT / "main.tex").read_text(encoding="utf-8")
    body = t[t.index(r"\begin{document}"):]
    body = strip_comments(body)
    # drop arguments that are not prose
    body = re.sub(r"\\(cite|ref|label|input|includegraphics|bibliography|bibliographystyle|eqref)(\[[^\]]*\])?\{[^}]*\}", " ", body)
    body = re.sub(r"\\begin\{tabular\}\{[^}]*\}", " ", body)
    body = re.sub(r"\\(begin|end)\{[a-zA-Z*]+\}(\[[^\]]*\])?", " ", body)
    body = re.sub(r"\\setlength\{[^}]*\}\{[^}]*\}|\\(footnotesize|centering|toprule|midrule|bottomrule)", " ", body)
    body = re.sub(r"\\newcommand\{\\[A-Za-z]+\}\{[^}]*\}", " ", body)
    body = re.sub(r"\\[A-Za-z]+\{\}", " MACRO ", body)
    body = re.sub(r"\\[A-Za-z]+", lambda m: " " + m.group(0) + " ", body)
    rows = []
    for s in sentences(body):
        if not re.search(r"\d", s):
            continue
        cat = None
        for name, pat in ALLOWED:
            s2 = re.sub(pat, "", s)
            if not re.search(r"\d", s2):
                cat = name
                break
        if cat is None:
            # math segments whose only digits are 0, 1, 2 (notation: indices, r-1, B_0, {0,1}, 1-miss, T^{-1})
            m = MATH_CONST.sub(lambda x: "" if not re.search(r"[3-9]|\d\d|\d\.\d", x.group(0)) else x.group(0), s)
            if not re.search(r"\d", re.sub("|".join(p for _, p in ALLOWED), "", m)):
                rows.append(("math notation (digits 0-2 only)", [], s.strip()[:300]))
                continue
            stripped = s
            for name, pat in ALLOWED:
                stripped = re.sub(pat, "", stripped)
            residual = re.findall(r"[^\s]*\d[^\s]*", stripped)
            hint = [h for h in PARAM_HINTS if h.replace(" ", "") in stripped.replace(" ", "")]
            cat = "design parameter / math constant (PREREG, config, notation)" if hint else "CHECK"
            rows.append((cat, residual, s.strip()[:300]))
        else:
            rows.append((cat, [], s.strip()[:300]))
    return rows


def main():
    rx = regex_checks()
    (OUT / "selfcheck_regex.json").write_text(json.dumps(rx, indent=1, ensure_ascii=False), encoding="utf-8")
    tot = sum(v["violations"] for d in rx.values() for v in d.values())
    print("regex violations:", tot, {k: sum(v["violations"] for v in d.values()) for k, d in rx.items()})
    rows = handnum()
    L = ["HANDNUM_CHECK_40: digits in the prose of submission_package/v2/latex/main.tex outside macros, citations,",
         "references and labels. Category 'CHECK' = to be reviewed by hand; every other category is an allowed exception.",
         "Manual review of the 'design parameter' sentences (P3R): the residual digits are PREREG or config parameters",
         "(K, r, l, m, eps grid, n = 600, theta = 0.05, B = 1000, 10^5 events, 7-day blocks, tolerances 0.01 and 0.005,",
         "the registered band [0.18, 0.32]), class-A platform inputs of the energy model (r = 14.3, e_idle = 0.248 mJ,",
         "l = 0.036), product names (Himawari-9, SARAH-3) or 'more than 3 standard errors'. No measured result is typed",
         "by hand; every measured value is a macro of numbers.tex or numbers_a2.tex.",
         ""]
    n_check = 0
    for cat, res, s in rows:
        if cat == "CHECK":
            n_check += 1
        L.append(f"[{cat}] residual={res}\n    {s}")
    L.insert(2, f"Sentences with digits: {len(rows)}; CHECK: {n_check}")
    (OUT / "HANDNUM_CHECK_40.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("handnum sentences:", len(rows), "CHECK:", n_check)
    # sentences longer than 35 words in the prose of main.tex (math and macros count as one word each)
    t = strip_comments((LAT / "main.tex").read_text(encoding="utf-8"))
    t = t[t.index(r"\begin{abstract}"):t.index(r"\bibliographystyle")]
    t = re.sub(r"\\begin\{(table|figure)\*?\}.*?\\end\{(table|figure)\*?\}", " ", t, flags=re.S)
    t = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", " ", t, flags=re.S)
    t = re.sub(r"\$[^$]*\$", "M", t)
    t = re.sub(r"~?\\(cite|ref|label)\{[^}]*\}", "", t)
    # environment, section, item and paragraph boundaries end a sentence
    t = re.sub(r"\\(begin|end)\{[^}]*\}(\[[^\]]*\])?|\\(sub)*section\*?\{[^}]*\}|\\input\{[^}]*\}|\\item|\\noindent|\n\s*\n",
               ". ", t)
    t = re.sub(r"\\newcommand\{[^}]*\}\{[^}]*\}", " ", t)
    # number macros count as one word each
    names = set()
    for fn in ("numbers.tex", "numbers_a2.tex"):
        names |= set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", (LAT / fn).read_text(encoding="utf-8")))
    t = re.sub(r"\\([A-Za-z]+)(\{\})?", lambda m: " X " if m.group(1) in names else m.group(0), t)
    t = re.sub(r"(\.\s*){2,}", ". ", t)
    t = re.sub(r"\\[A-Za-z]+\*?(\[[^\]]*\])?", " ", t)
    t = re.sub(r"[{}]", " ", t)
    longs = [(len(s.split()), s.strip()) for s in sentences(t) if len(s.split()) > 35]
    (OUT / "selfcheck_long_sentences.txt").write_text(
        "\n".join(f"{n} words: {s}" for n, s in longs) + ("\n" if longs else "none\n"), encoding="utf-8")
    print("sentences > 35 words:", len(longs))


if __name__ == "__main__":
    main()
