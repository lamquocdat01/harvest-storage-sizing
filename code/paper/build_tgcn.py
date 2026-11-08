#!/usr/bin/env python3
"""build_tgcn.py (topic 40, P3S): generated inputs specific to the TGCN build, on top of the v3 inputs.
  numbers_a3.tex        macros of amendment A3 and of the TRAIN rerun, with numbers_a3_provenance.json
  sizing_table.tex      Table IV with the worst-spell column of A3 (review item M6)
  supp_a3_tables.tex    Tables S14-S16 (A3, 25 cells each) and Table S17 (TRAIN rerun against TEST)
Reads only results/*.json. No simulation. Usage: python code/paper/build_tgcn.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LATEX = ROOT / "submission_package" / "TGCN" / "latex"
if not (ROOT / "submission_package").exists():    # repository layout (code/sync_repo.py): paper/tgcn
    LATEX = ROOT / "paper" / "tgcn"
RES = ROOT / "results"
sys.path.insert(0, str(HERE))

import prereg_table as PT                        # noqa: E402

EIDLE_J = 0.248e-3                                # reference node (sim40/sizing.py)
NAMES = {"HCMC": "HCMC", "Madrid-MSG": r"Mad.\ MSG", "Madrid-SARAH3": r"Mad.\ SARAH", "Uppsala-MSG": r"Upp.\ MSG",
         "Uppsala-SARAH3": r"Upp.\ SARAH"}
ORDER = ["HCMC", "Madrid-MSG", "Madrid-SARAH3", "Uppsala-MSG", "Uppsala-SARAH3"]
SEAS = ("DJF", "MAM", "JJA", "SON")
SETUPS = ("B", "C", "D", "E", "F")
OTHER = {"Madrid-MSG": "Madrid-SARAH3", "Madrid-SARAH3": "Madrid-MSG", "Uppsala-MSG": "Uppsala-SARAH3",
         "Uppsala-SARAH3": "Uppsala-MSG"}


def J(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


def cells():
    for s in ORDER:
        for i, sea in enumerate(SEAS):
            yield s, sea, NAMES[s] if i == 0 else "", sea
    for x in SETUPS:
        yield f"Setup{x}", "ALL", "Indoor", x


def kj(c):
    return "--" if c is None else f"{c * EIDLE_J / 1e3:.2f}"


def r2(x, d=2):
    return r"$\infty$" if x is None else f"{x:.{d}f}"


def table(caption, label, spec, head, rows):
    return "\n".join([r"\begin{table}[H]\centering\footnotesize\caption{" + caption + r"}\label{" + label + "}",
                      r"\begin{tabular}{" + spec + r"}\toprule", head + r"\\\midrule"] + [" & ".join(r) + r"\\" for r in rows] +
                     [r"\bottomrule\end{tabular}\end{table}", ""])


def sizing_table(F5, W):
    R = {(x["site"], x["season"]): x for x in F5["rows"] if abs(x["m"] - 0.25) < 1e-9}
    D = {(x["site"], x["season"]): x for x in W["rows"] if abs(x["m"] - 0.25) < 1e-9}
    L = [r"\begin{table}[!t]\centering\caption{Storage for the reference node over the full year ($m=0.25$, $K=8$; "
         r"kJ). No 7 d: $C^*$ with the worst 7-day window removed (amendment A3, post hoc; Table~S14). Other product: "
         r"$C^*$ of the same site and season from the other satellite product (Table~S8); -- where only one product "
         r"exists. Block-bootstrap intervals are not shown because they break the worst spell (supplement, "
         r"Tables~S9--S10). Kansal's mean-rate condition is omitted (it oversizes by \kmeanInvLo--\kmeanInvHi{} times). "
         r"Descriptive, not pre-registered}\label{tab:sizing}",
         r"\footnotesize\setlength{\tabcolsep}{2pt}", r"\begin{tabular}{@{}llrrrrrr@{}}\toprule",
         r"Site & & $C^*$ & No 7\,d & Other & Avg-day & Buchli & 3-day\\\midrule"]
    fj = lambda v: "--" if v is None else f"{v / 1e3:.2f}"  # noqa: E731
    for site, sea, name, lab in cells():
        x = R[(site, sea)]
        b = x["baselines_J"]
        o = OTHER.get(site)
        oc = fj(R[(o, sea)]["Cstar_J"]) if o else "--"
        L.append(f"{name} & {lab} & {fj(x['Cstar_J'])} & {kj(D[(site, sea)]['L7']['Cstar_drop'])} & {oc} & "
                 f"{fj(b['C_avgday'])} & {fj(b['C_buchli_daily'])} & {fj(b['C_3day'])}\\\\")
    L.append(r"\bottomrule\end{tabular}\end{table}")
    (LATEX / "sizing_table.tex").write_text("\n".join(L) + "\n", encoding="utf-8")


def supp_tables(W, Rg, K, score_tr, score_te):
    D = {(x["site"], x["season"]): x for x in W["rows"] if abs(x["m"] - 0.25) < 1e-9}
    rows = [[name, lab, kj(D[(s, se)]["Cstar"]), r2(D[(s, se)]["L1"]["ratio"]), r2(D[(s, se)]["L3"]["ratio"]),
             r2(D[(s, se)]["L7"]["ratio"]), str(D[(s, se)]["L7"]["start_day"])] for s, se, name, lab in cells()]
    out = [table(r"Worst-spell sensitivity (amendment A3, post hoc; reference node, $m=0.25$, full year). $C^*$ in kJ; "
                 r"the ratios are $C^*$ with the worst window of 1, 3 or 7 days removed over $C^*$. Last column: first day "
                 r"of the worst 7-day window on the cell's day index. Source: \texttt{results/a3\_worst\_spell.json}",
                 "tab:s_a3_worst", "@{}llrrrrr@{}", r"Site & & $C^*$ & $-1$\,d & $-3$\,d & $-7$\,d & Start", rows)]
    C = {(x["site"], x["season"]): x for x in Rg["rows"]}
    cols = ("C*/C_avgday", "C*/C_buchli_daily", "C*/C_kansal_mean", "C*/C_3day")

    def cell(x, k):
        return "--" if k not in x else f"{x[k]['median']:.2f} [{x[k]['min']:.2f}, {x[k]['max']:.2f}]"
    rows = [[name, lab] + [cell(C[(s, se)], k) for k in cols] for s, se, name, lab in cells()]
    out.append(table(r"Ratio of $C^*$ to each sizing rule per cell (amendment A3, post hoc; TEST): median [min, max] over "
                     r"the $(r,\lt,m)$ combinations of the cell with a finite ratio. Source: "
                     r"\texttt{results/a3\_per\_cell\_ranges.json}", "tab:s_a3_ranges", "@{}lllll l@{}".replace(" ", ""),
                     r"Site & & $C^*$/Avg-day & $C^*$/Buchli & $C^*$/Kansal mean & $C^*$/3-day", rows))
    M = {(x["site"], x["season"]): x for x in K["rows"] if abs(x["m"] - 0.25) < 1e-9}

    def mk(s, se, name, lab):
        x = M.get((s, se))
        if x is None:
            return [name, lab, "--", "--", "--"]
        return [name, lab, kj(x["C_TRAIN"]), kj(x["C_TEST"]) if x["C_TEST"] is not None else r"$\infty$",
                r"$\infty$" if x["k_inf"] else f"{x['k']:.2f}"]
    rows = [mk(*c) for c in cells()]
    out.append(table(r"Train-to-test margin factor $k=C_{\mathrm{TEST}}/C_{\mathrm{TRAIN}}$ (amendment A3, post hoc; "
                     r"reference node, $m=0.25$; kJ). The panel is scaled on the TRAIN months only; $\infty$: that panel "
                     r"cannot sustain $a=1/8$ on the TEST months at any capacity. Source: \texttt{results/a3\_margin\_k.json}",
                     "tab:s_a3_margin", "@{}llrrr@{}", r"Site & & $C_{\mathrm{TRAIN}}$ & $C_{\mathrm{TEST}}$ & $k$", rows))
    keys = [k for k in score_te if re.fullmatch(r"H\d[a-e]?", k)]
    rows = [[k, score_tr[k]["verdict"], score_te[k]["verdict"]] for k in keys]
    out.append(table(r"Pre-registered predictions on the corrected corpus: TRAIN rerun (sensitivity only, amendment A1) "
                     r"against TEST (the scored split). Sources: \texttt{results/prereg\_score\_train.json}, "
                     r"\texttt{results/prereg\_score\_test.json}", "tab:s_train", "@{}lll@{}", r"\# & TRAIN & TEST", rows))
    (LATEX / "supp_a3_tables.tex").write_text("\n".join(out), encoding="utf-8")


def main():
    W, Rg, K = J("a3_worst_spell.json"), J("a3_per_cell_ranges.json"), J("a3_margin_k.json")
    F5 = J("F5_sizing_all.json")
    tr, te = J("prereg_score_train.json"), J("prereg_score_test.json")
    A2tr = J("a2_sizing_train.json")
    M, P = {}, {}

    def put(k, v, src):
        assert re.fullmatch(r"[A-Za-z]+", k), k
        M[k], P[k] = v, {"value": v, "source": src}
    s7 = W["summary"]["m0.25_L7"]
    for g, n in (("all", "All"), ("HCMC", "HCMC"), ("Madrid", "Mad"), ("Uppsala", "Upp"), ("indoor", "In")):
        for st, sn in (("median", "Med"), ("min", "Min"), ("max", "Max")):
            put(f"AiiiW{n}{sn}", f"{s7[g][st]:.2f}", f"a3_worst_spell.json:summary.m0.25_L7.{g}.{st}")
    put("AiiiWn", str(s7["all"]["n"]), "a3_worst_spell.json:summary.m0.25_L7.all.n")
    one = sum(1 for x in W["rows"] if abs(x["m"] - 0.25) < 1e-9 and x["L7"]["ratio"] > 1 - 1e-9)
    put("AiiiWone", str(one), "a3_worst_spell.json:rows m=0.25 with L7 ratio = 1")
    k = "C*/C_avgday"
    for g, n in (("HCMC", "HCMC"), ("Madrid", "Mad"), ("Uppsala", "Upp"), ("indoor", "In")):
        x = Rg["groups"][g][k]
        put(f"AiiiAvg{n}Lo", f"{x['median_of_cells_min']:.1f}", f"a3_per_cell_ranges.json:groups.{g}.{k}.median_of_cells_min")
        put(f"AiiiAvg{n}Hi", f"{x['median_of_cells_max']:.1f}", f"a3_per_cell_ranges.json:groups.{g}.{k}.median_of_cells_max")
    x = K["summary"]["m0.25"]["all"]
    inf = r"$\infty$"
    put("AiiiKn", str(x["n"]), "a3_margin_k.json:summary.m0.25.all.n")
    put("AiiiKMed", inf if x["median_is_inf"] else f"{x['median']:.2f}", "a3_margin_k.json:summary.m0.25.all.median")
    put("AiiiKNinety", inf if x["p90_is_inf"] else f"{x['p90']:.1f}", "a3_margin_k.json:summary.m0.25.all.p90")
    put("AiiiKInf", str(x["n_inf"]), "a3_margin_k.json:summary.m0.25.all.n_inf")
    fin = [r["k"] for r in K["rows"] if abs(r["m"] - 0.25) < 1e-9 and not r["k_inf"]]
    put("AiiiKMaxFin", f"{max(fin):.1f}", "a3_margin_k.json:rows m=0.25, largest finite k")
    put("AiiiKGtOne", f"{100 * x['share_gt1']:.0f}\\,\\%", "a3_margin_k.json:summary.m0.25.all.share_gt1")
    y = K["summary"]["m1.0"]["all"]
    put("AiiiKMedMone", inf if y["median_is_inf"] else f"{y['median']:.2f}", "a3_margin_k.json:summary.m1.0.all.median")
    put("AiiiKNinetyMone", inf if y["p90_is_inf"] else f"{y['p90']:.1f}", "a3_margin_k.json:summary.m1.0.all.p90")
    put("AiiiKInfMone", str(y["n_inf"]), "a3_margin_k.json:summary.m1.0.all.n_inf")
    keys = [q for q in te if re.fullmatch(r"H\d[a-e]?", q)]
    same = sum(tr[q]["verdict"] == te[q]["verdict"] for q in keys)
    put("TrainNsame", str(same), "prereg_score_train.json vs prereg_score_test.json: equal verdicts")
    put("TrainNall", str(len(keys)), "prereg_score_test.json: H-keys")
    put("TrainPass", str(sum(tr[q]["verdict"] == "PASS" for q in keys)), "prereg_score_train.json: PASS")
    put("TrainDiff", ", ".join(q for q in keys if tr[q]["verdict"] != te[q]["verdict"]) or "none", "prereg_score_train.json vs test: differing keys")
    put("AiiTrainViol", str(A2tr["n_violations"]), "a2_sizing_train.json:n_violations")
    put("AiiTrainMax", f"{A2tr['max_LB_lo_over_TS_exact']:.4f}", "a2_sizing_train.json:max_LB_lo_over_TS_exact")
    out = ["% numbers_a3.tex: GENERATED by code/paper/build_tgcn.py. Do not hand-edit."]
    out += [f"\\newcommand{{\\{a}}}{{{b}}}" for a, b in M.items()]
    (LATEX / "numbers_a3.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    (LATEX / "numbers_a3_provenance.json").write_text(json.dumps(P, indent=1), encoding="utf-8")
    sizing_table(F5, W)
    supp_tables(W, Rg, K, tr, te)
    print(len(M), "macros written;", LATEX)


if __name__ == "__main__":
    main()
