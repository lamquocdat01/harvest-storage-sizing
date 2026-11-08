#!/usr/bin/env python3
"""build_v3.py (topic 40, P0R2 08-11-2026): generated inputs of the venue-independent manuscript v3
-> manuscript_v3/latex/ (repository: paper/v3/).

Same sources and generators as build_v2.py (no simulation is run); the differences are presentation changes
asked by the S6 review and decided in CP3 (P3R/CP3_DECISION_40_20261108.md, section 5):
  prereg_table.tex   H1, H2a, H6 grouped as consistency checks (M5); H4b observation carries the A2 maximum (M11);
                     "Class-A node" -> "Reference node" (m1)
  sizing_table.tex   the 7-day block-bootstrap column is replaced by C* from the other satellite product of the same
                     cell (the values of Table S8; M6); "class-A" -> "reference node" (m1)
  supp_tables.tex    Table S5 empty "Scalar details" cells filled from the Table III observations (M12);
                     floats placed [H] so that every supplement section holds its own tables and figures (M12)
  numbers_v3.tex     counts used by the v3 text: substantive/consistency tally (M5), grid structure and effective n
                     (M7), dropped Buchli combinations (m7), E3 outage shares (M8/M9), v1 E[D] (F1), Fig. 1 sample (m4)
Every value is read from results/*.json or from the files that build_v2.py already reads; provenance per macro:
latex/numbers_v3_provenance.json and latex/numbers_provenance_v3.json. Figures are copied from results/figs, except
Fig. 2 whose axis labels are typeset by code/paper/fig_f3_v3.py (same data as fig_f3_a2.py).
Usage: python code/paper/build_v3.py   then   latexmk -pdf main.tex supp.tex   in the latex folder.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LATEX = ROOT / "manuscript_v3" / "latex"
if not (ROOT / "manuscript_v3").exists():        # repository layout (code/sync_repo.py): paper/v3
    LATEX = ROOT / "paper" / "v3"
RES = ROOT / "results"
sys.path.insert(0, str(HERE))

import gen_numbers as G          # noqa: E402
import gen_numbers_p3r as GP     # noqa: E402
import gen_supp as GS            # noqa: E402
import prereg_table as PT        # noqa: E402

FIGS = ("F1_frontier_K_Cstar_test", "F2_miss_vs_floor_test", "F4_gate_map_test",
        "F6_throttle_vs_blackout_test", "F6p_throttle_kansal_amax_test", "F7_kansal_obs_vs_pred_test")
CONS = ("H1", "H2a", "H6")       # consistency checks (S6 M5): a proved statement or an identity against the simulator


def J(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


def thou(n):
    return f"{int(n):,}".replace(",", "{,}")


def pct(x, d=0):
    return f"{100 * x:.{d}f}\\,\\%"


# ---------------------------------------------------------------- Table III (pre-registered predictions)
def prereg_table_v3(SC):
    PT._check_thresholds()
    obs = PT.observed(SC)
    A2 = J("a2_sizing_test.json")
    obs["H4b"] += f" (A2: {A2['max_LB_lo_over_TS_exact']:.4f})"
    keys = [k for k in SC if re.fullmatch(r"H\d[a-e]?", k)]
    assert set(keys) == set(PT.CRIT), (sorted(keys), sorted(PT.CRIT))
    assert all(SC[k]["verdict"] == "PASS" for k in CONS)
    L = [r"\begin{table*}[!t]\centering\caption{Pre-registered predictions (PREREG v1, frozen before TEST) and "
         r"their outcome on TEST. Criteria are abridged from the frozen text with every threshold kept; theorem "
         r"numbers refer to this paper. The consistency checks compare a proved statement or an identity with a "
         r"simulator of the same model and could fail only through an error in the code. H4b: the registered "
         r"maximum, and in brackets the maximum under the exact brackets of amendment A2. Scalar details are in the "
         r"supplement" + PT.CAPTION_EXTRA + r"}\label{tab:prereg}",
         r"\footnotesize\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.05}",
         r"\providecommand{\preregCritW}{0.50\textwidth}\providecommand{\preregObsW}{0.335\textwidth}",
         r"\begin{tabular}{@{}lp{\preregCritW}p{\preregObsW}l@{}}\toprule",
         r"\# & Pass criterion (abridged) & Observed on TEST & Outcome\\\midrule"]

    def row(k):
        v = SC[k]["verdict"]
        out = "PASS" if v == "PASS" else f"FAIL-{PT.FAIL_KIND[k]}"
        return rf"{k} & \raggedright {PT.CRIT[k]} & \raggedright {obs[k]} & {out}\\"
    L.append(r"\multicolumn{4}{@{}l}{\emph{Consistency checks}}\\")
    L += [row(k) for k in keys if k in CONS]
    L.append(r"\midrule\multicolumn{4}{@{}l}{\emph{Substantive predictions}}\\")
    L += [row(k) for k in keys if k not in CONS]
    L += [r"\bottomrule\end{tabular}\end{table*}"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- Table IV (sizing, full year)
def sizing_table_v3(F5):
    rows = [x for x in F5["rows"] if abs(x["m"] - 0.25) < 1e-9]
    R = {(x["site"], x["season"]): x for x in rows}
    other = {"Madrid-MSG": "Madrid-SARAH3", "Madrid-SARAH3": "Madrid-MSG",
             "Uppsala-MSG": "Uppsala-SARAH3", "Uppsala-SARAH3": "Uppsala-MSG"}
    order = ["HCMC", "Madrid-MSG", "Madrid-SARAH3", "Uppsala-MSG", "Uppsala-SARAH3"]
    L = [r"\begin{table}[!t]\centering\caption{Storage for the reference node over the full year ($m=0.25$, $K=8$; "
         r"kJ). Other product: $C^*$ of the same site and season from the other satellite product (Table~S8); "
         r"-- where only one product exists. $C^*$ is set by the single worst spell, so block-bootstrap intervals "
         r"are not shown (supplement, Tables~S9--S10). Kansal's mean-rate condition is omitted (it oversizes by "
         r"\kmeanInvLo--\kmeanInvHi{} times). Descriptive, not pre-registered}\label{tab:sizing}",
         r"\footnotesize\setlength{\tabcolsep}{2pt}",
         r"\begin{tabular}{@{}llrrrrr@{}}\toprule",
         r"Site & & $C^*$ & Other product & Avg-day & Buchli & 3-day\\\midrule"]
    kj = lambda v: "--" if v is None else f"{v / 1e3:.2f}"  # noqa: E731

    def line(x, name, sea):
        b = x["baselines_J"]
        o = other.get(x["site"])
        oc = kj(R[(o, x["season"])]["Cstar_J"]) if o else "--"
        return (f"{name} & {sea} & {kj(x['Cstar_J'])} & {oc} & {kj(b['C_avgday'])} & "
                f"{kj(b['C_buchli_daily'])} & {kj(b['C_3day'])}\\\\")
    names = {"HCMC": "HCMC", "Madrid-MSG": r"Mad.\ MSG", "Madrid-SARAH3": r"Mad.\ SARAH",
             "Uppsala-MSG": r"Upp.\ MSG", "Uppsala-SARAH3": r"Upp.\ SARAH"}
    for site in order:
        for sea in ("DJF", "MAM", "JJA", "SON"):
            L.append(line(R[(site, sea)], names[site] if sea == "DJF" else "", sea))
    for x in [r for r in rows if r["site"].startswith("Setup")]:
        L.append(line(x, "Indoor", x["site"][-1]))
    L += [r"\bottomrule\end{tabular}\end{table}"]
    (G.LATEX / "sizing_table.tex").write_text("\n".join(L) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- Table S5 (scalar details)
def supp_prereg_v3():
    SC = J("prereg_score_test.json")
    obs = PT.observed(SC)
    rows = []
    for k, v in SC.items():
        if not isinstance(v, dict) or "verdict" not in v:
            continue
        det = {kk: vv for kk, vv in v.items() if kk != "verdict"}
        txt = GS.esc("; ".join(f"{kk}={GS.num(vv)}" for kk, vv in det.items() if not isinstance(vv, (dict, list))))
        if not txt.strip():                         # only dictionary-valued details: print the Table III observation
            txt = obs[k]
        rows.append([k, v["verdict"], r"\parbox[t]{0.68\textwidth}{\raggedright " + txt + "}"])
    return GS.table(r"Scoring of PREREG v1 (H1--H7) on TEST; dictionary-valued details are in "
                    r"\texttt{results/prereg\_score\_test.json}", "tab:s_prereg", ["", "Verdict", "Scalar details"],
                    rows, "@{}llp{0.7\\textwidth}@{}")


# ---------------------------------------------------------------- numbers_v3.tex
def numbers_v3():
    M, P = {}, {}

    def put(k, v, src):
        M[k], P[k] = v, {"value": v, "source": src}
    SC = J("prereg_score_test.json")
    keys = [k for k in SC if re.fullmatch(r"H\d[a-e]?", k)]
    subst = [k for k in keys if k not in CONS]
    sp = sum(SC[k]["verdict"] == "PASS" for k in subst)
    put("nCons", str(len(CONS)), "prereg_score_test.json: H1, H2a, H6 (consistency checks, CP3 M5)")
    put("nSubst", str(len(subst)), "prereg_score_test.json: H-keys other than H1, H2a, H6")
    put("nSubstPass", str(sp), "prereg_score_test.json: PASS among the substantive keys")
    put("nSubstFail", str(len(subst) - sp), "prereg_score_test.json: FAIL among the substantive keys")
    X = J("exploratory_q2_test.json")
    put("nExpl", str(sum(1 for k in X if re.fullmatch(r"E\d", k))), "exploratory_q2_test.json: keys E1-E3 (all FAIL, Table S6)")
    e3 = X["E3"]
    put("ExThreeOutZero", pct(e3["per_amax_d0"]["share_outage_gt0"]), "exploratory_q2_test.json:E3.per_amax_d0.share_outage_gt0")
    put("ExThreeOutTen", pct(e3["per_amax_d10"]["share_outage_gt0"]), "exploratory_q2_test.json:E3.per_amax_d10.share_outage_gt0")
    # grid structure and effective n (M7): counted from the 1,600 combinations of the sizing-rule comparison
    B = J("summary_test.json")["main"]["baselines"]
    cells = {(x["site"], x["season"]) for x in B}
    grp = lambda s: "indoor" if s.startswith("Setup") else s.split("-")[0]  # noqa: E731
    per = {g: sum(1 for c in cells if grp(c[0]) == g) for g in ("HCMC", "Madrid", "Uppsala", "indoor")}
    nr, nl, nm = (len({x[k] for x in B}) for k in ("r", "l", "m"))
    assert len(cells) * nr * nl * nm == len(B)
    put("nCombos", thou(len(B)), "summary_test.json:main.baselines (rows)")
    put("nCells", str(len(cells)), "summary_test.json:main.baselines (site, season) pairs")
    put("nRgrid", str(nr), "summary_test.json:main.baselines distinct r")
    put("nLgrid", str(nl), "summary_test.json:main.baselines distinct l")
    put("nMgrid", str(nm), "summary_test.json:main.baselines distinct m")
    for g, k in (("HCMC", "nCellHCMC"), ("Madrid", "nCellMad"), ("Uppsala", "nCellUpp"), ("indoor", "nCellIn")):
        put(k, str(per[g]), f"summary_test.json:main.baselines cells of group {g}")
    mp = SC["H2c"]["medians_product"]
    ins = [v for k, v in mp.items() if k.startswith("Setup")]
    put("avgInSetupLo", f"{min(ins):.1f}", "prereg_score_test.json:H2c.medians_product Setup* min")
    put("avgInSetupHi", f"{max(ins):.1f}", "prereg_score_test.json:H2c.medians_product Setup* max")
    # m7: combinations without a Buchli ratio
    bad = [x for x in B if x["C*/C_buchli_daily"] is None or not np.isfinite(x["C*/C_buchli_daily"])]
    where = {(grp(x["site"]), x["season"], x["m"]) for x in bad}
    assert where == {("Madrid", "JJA", 1.0)}, where      # the text names this group
    assert len(B) - len(bad) == SC["H2d"]["n"]
    put("nBuDrop", str(len(bad)), "summary_test.json:main.baselines rows with C*/C_buchli_daily undefined (Madrid JJA, m=1)")
    put("nBuN", thou(SC["H2d"]["n"]), "prereg_score_test.json:H2d.n")
    # F1 (supp S1): E[D] of the earlier corpus
    N1 = json.loads((RES / "_v1_corpus3713" / "numbers.json").read_text(encoding="utf-8"))
    put("VoneED", f"{N1['F_D_all']['E[D]']:.1f}", "results/_v1_corpus3713/numbers.json:F_D_all.E[D]")
    # m4: Fig. 1 sample size
    pts = J("summary_test.json")["main"]["F2_points"]
    put("FtwoN", thou(len(pts["floor"])), "summary_test.json:main.F2_points (seed 42, n_max)")
    A2 = J("a2_sizing_test.json")
    put("AiiMaxLBTSreg", f"{J('prereg_score_test.json')['H4b']['max']:.3f}", "prereg_score_test.json:H4b.max")
    assert A2["n_violations"] == 0
    out = ["% numbers_v3.tex: GENERATED by code/paper/build_v3.py. Do not hand-edit."]
    out += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()]
    (LATEX / "numbers_v3.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    (LATEX / "numbers_v3_provenance.json").write_text(json.dumps(P, indent=1), encoding="utf-8")
    return M


def _float_here(fn):
    p = LATEX / fn
    t = p.read_text(encoding="utf-8").replace(r"\begin{table}[!ht]", r"\begin{table}[H]")
    t = t.replace("class-A node", "reference node")
    p.write_text(t, encoding="utf-8")


def main():
    LATEX.mkdir(parents=True, exist_ok=True)
    (LATEX / "figures").mkdir(exist_ok=True)
    G.LATEX = LATEX
    G.PROV_OUT = LATEX / "numbers_provenance_v3.json"
    G.exploratory = lambda: None
    G.sizing_table = sizing_table_v3
    PT.H3A_DEC = 3
    PT.CAPTION_EXTRA = (r". TEST on the corrected corpus (amendment A1, 3{,}170 events); the same table before the "
                        r"correction is Table~S1 of the supplement")
    PT.CRIT["H7"] = PT.CRIT["H7"].replace("Class-A node", "Reference node")
    PT.table = prereg_table_v3
    G.main()
    GS.LATEX = LATEX
    GS.prereg = supp_prereg_v3
    GS.main()
    pend = GP.main(LATEX)
    for fn in ("supp_tables.tex", "supp_p3r_tables.tex"):
        _float_here(fn)
    M = numbers_v3()
    for f in FIGS:
        src = RES / "figs" / f"{f}.pdf"
        if src.exists():
            shutil.copy2(src, LATEX / "figures" / src.name)
    import fig_f3_v3                                   # Fig. 2 with typeset axis labels (m4)
    fig_f3_v3.main(LATEX / "figures")
    print("v3 inputs written to", LATEX, "; pending:", pend, "; numbers_v3 macros:", len(M))


if __name__ == "__main__":
    main()
