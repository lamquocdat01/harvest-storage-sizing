#!/usr/bin/env python3
"""gen_numbers_p3r.py (topic 40, P3R): numbers added by the v2 manuscript -> numbers_a2.tex and
supp_p3r_tables.tex in the given LaTeX folder. No number is typed in main.tex or supp.tex.

Macro groups (letters only):
  \\Aii...   Amendment A2 (results/a2_sizing_test.json): exact brackets of the sizing sandwich
  \\Kc...    per-case Kansal check (results/kansal_check_test.json; P3R/kansal_check.py)
  \\Ex...    exploratory E1-E3 (results/exploratory_q2_test.json, exploratory_q2_boot_test.json)
  \\Hthreea...  H3a medians at three decimals (prereg_score_test.json)
  \\Vone...  v1 corpus (results/_v1_corpus3713/) for the correction note
  \\Lfour... Lemma 4 check on 3 cells (P3R/lemma4_check.json)
A missing source prints [[PENDING ...]]; the P3R report lists every pending macro.
Supplementary tables: v1 vs v2 prereg verdicts, F_D before/after A1, registered vs A2 H4 column, Kansal check.
Usage: python code/paper/gen_numbers_p3r.py <latex_dir>
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
RES = ROOT / "results"
V1 = RES / "_v1_corpus3713"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

MAC: dict[str, str] = {}
PROV: dict[str, dict] = {}


def J(p):
    p = pathlib.Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def put(k, v, src):
    assert k.isalpha(), k
    MAC[k] = v
    PROV[k] = {"value": v, "source": src}


def f(x, d=2):
    return f"{x:.{d}f}"


def sg(x, d=3):
    return f"{x:+.{d}f}"


def pct(x, d=0):
    return f"{100 * x:.{d}f}\\,\\%"


def thou(n):
    return f"{int(n):,}".replace(",", "{,}")


def v1_counts():
    """Events per dataset of the frozen v1 corpus (numbers.json v1 has no per-dataset block)."""
    import csv
    from collections import Counter
    return Counter(r["dataset"] for r in csv.DictReader(open(V1 / "event_corpus_40.csv", encoding="utf-8")))


def pend(keys, why):
    for k in keys:
        put(k, f"[[PENDING {why}]]", "missing")


def a2():
    A = J(RES / "a2_sizing_test.json")
    keys = ("AiiNcells", "AiiNfinite", "AiiPass", "AiiNviol", "AiiMaxLBTS", "AiiMedLBTS", "AiiAbsMed", "AiiAbsPninety",
            "AiiAbsMax", "AiiNsurBad", "AiiNsurBadMiss", "AiiTSratioMed", "AiiTSratioMax", "AiiHfourA", "AiiHfourB",
            "AiiHfourC", "AiiHfourD", "AiiTsMedLo", "AiiTsMedHi", "AiiLbtsHi", "AiiLbtsLoMin", "AiiLbtsLoMax",
            "AiiNcomb", "AiiTsInvLo", "AiiTsInvHi", "AiiNsurBadOut", "AiiTSbadMed", "AiiTSbadMax")
    if not A:
        pend(keys, "A2")
        return None
    s = "a2_sizing_test.json"
    put("AiiNcomb", thou(A["n_combinations"]), s)
    put("AiiNcells", thou(A["n_cells"]), s)
    put("AiiNfinite", thou(A["n_cells_finite"]), s)
    put("AiiPass", "PASS" if A["PASS_no_cell_C_LB_lo_gt_C_TS_exact"] else "FAIL", s)
    put("AiiNviol", str(A["n_violations"]), s)
    put("AiiMaxLBTS", f(A["max_LB_lo_over_TS_exact"], 4), s)       # 4 decimals: 0.9998 must not print as 1.000
    put("AiiMedLBTS", f(A["median_LB_lo_over_TS_exact"], 3), s)
    ab = A["abs_exact_minus_sur"]
    sci = lambda v: (f"{v:.1e}".replace("e-0", r"\times10^{-").replace("e-", r"\times10^{-") + "}") if v and v < 1e-3 else f"{v:.4f}"  # noqa: E731
    put("AiiAbsMed", "$" + sci(ab["median"]) + "$", s + ":abs_exact_minus_sur.median")
    put("AiiAbsPninety", "$" + sci(ab["p90"]) + "$", s + ":abs_exact_minus_sur.p90")
    put("AiiAbsMax", "$" + sci(ab["max"]) + "$", s + ":abs_exact_minus_sur.max")
    put("AiiNsurBad", thou(A["n_sur_hi_infeasible_exact"]), s)
    put("AiiNsurBadMiss", thou(A["sur_hi_infeasible_reason"]["miss_exact_gt_eps"]), s)
    put("AiiNsurBadOut", thou(A["sur_hi_infeasible_reason"]["outage"]), s)
    bad = [c["C_TS_exact_hi"] / c["C_TS_sur_hi"] for c in A["cells"]
           if c.get("sur_hi_feasible_exact") is False and c.get("C_TS_exact_hi") and c.get("C_TS_sur_hi")]
    put("AiiTSbadMed", f(float(np.median(bad)), 3) if bad else "--", s + ":cells[sur_hi_feasible_exact=false]")
    put("AiiTSbadMax", f(max(bad), 3) if bad else "--", s + ":cells[sur_hi_feasible_exact=false]")
    put("AiiTSratioMed", f(A["TS_exact_over_sur"]["median"], 3), s)
    put("AiiTSratioMax", f(A["TS_exact_over_sur"]["max"], 3), s)
    V = A["H4_A2_verdicts"]
    for k, kk in (("AiiHfourA", "H4a"), ("AiiHfourB", "H4b"), ("AiiHfourC", "H4c"), ("AiiHfourD", "H4d")):
        put(k, V[kk], s + f":H4_A2_verdicts.{kk}")
    h4 = A["H4_A2"]["H4a"]["medians"]
    meds = [v for e in ("0.5", "0.6") for v in h4[e].values()]
    put("AiiTsMedLo", f(min(meds)), s)
    put("AiiTsMedHi", f(max(meds)), s)
    put("AiiTsInvLo", f(1 / max(meds), 1), s)
    put("AiiTsInvHi", f(1 / min(meds), 1), s)
    hi = A["H4_A2"]["H4c"]["medians_eps_ge_0_6"]
    put("AiiLbtsHi", f(min(v for e in hi.values() for v in e.values()), 3), s)
    lo = A["H4_A2"]["H4c"]["medians_eps_0_45"].values()
    put("AiiLbtsLoMin", f(min(lo)), s)
    put("AiiLbtsLoMax", f(max(lo)), s)
    return A


def kansal():
    K = J(RES / "kansal_check_test.json")
    s = "kansal_check_test.json"
    keys = ("KcNcases", "KcNall", "KcKoneFail", "KcMinMargin", "KcNwin", "KcWinPct", "KcWinOutPct", "KcRateRatio",
            "KcGapMed", "KcGapLo", "KcGapHi", "KcKmoreOutPct", "KcPiK", "KcPiPer", "KcNnoOut", "KcNoOutWinBeyond",
            "KcNoOutLosePct", "KcNoOutMed", "KcWinMed", "KcKtwoMaxRound")
    if not K:
        pend(keys, "Kansal check")
        return None
    put("KcNall", thou(K["n_cases_all"]), s)
    put("KcNcases", thou(K["n_cases_E1"]), s)
    put("KcKoneFail", str(K["K1"]["n_fail_all"]), s)
    put("KcMinMargin", f(K["K1"]["min_margin_in_SE"], 1), s)
    k3 = K["K3"]
    put("KcNwin", thou(k3["n_kansal_wins_gt_0.005"]), s)
    put("KcWinPct", pct(k3["n_kansal_wins_gt_0.005"] / K["n_cases_E1"]), s)
    put("KcWinOutPct", pct(k3["share_with_pi_per_gt0"]), s)
    put("KcWinMed", sg(k3["median_d_wins"]), s)
    g = k3["eps_gap_real_minus_aK_wins"]
    put("KcGapMed", f(g["median"], 3), s)
    put("KcGapLo", f(g["p25"], 3), s)
    put("KcGapHi", f(g["p75"], 3), s)
    put("KcKmoreOutPct", pct(K["outage"]["share_pi_K_gt_pi_per_E1"]), s)
    put("KcPiK", f(K["outage"]["median_pi_K_E1"]), s)
    put("KcPiPer", f(K["outage"]["median_pi_per_E1"]), s)
    put("KcNnoOut", str(K["K2"]["n_cases_pi_per_0"]), s)
    put("KcNoOutWinBeyond", str(K["K2"]["n_kansal_wins_beyond_3SE"]), s)
    put("KcKtwoMaxRound", "$" + f"{K['K2']['max_abs_floor_mismatch']:.1e}".replace("e-0", r"\times10^{-") + "}$", s)
    # extras computed from the per-case table (realised-rate ratio in the wins; no-outage cases)
    import csv
    R = list(csv.DictReader(open(ROOT / "P3R" / "KANSAL_CHECK_40.csv", encoding="utf-8")))
    fl = lambda r, k: float(r[k])  # noqa: E731
    win = [r for r in R if r["E1_population"] == "True" and fl(r, "d_replay") < -0.005]
    put("KcRateRatio", f(float(np.median([fl(r, "a_K") / fl(r, "a_per_real") for r in win])), 2),
        "KANSAL_CHECK_40.csv median a_K / a_per_real over the wins")
    nopi = [r for r in R if fl(r, "pi_per") < 1e-12]
    d = np.array([fl(r, "miss_K_replay") - fl(r, "miss_per_analytic") for r in nopi])
    put("KcNoOutLosePct", pct(float(np.mean(d > 0))), "KANSAL_CHECK_40.csv pi_per = 0: share miss_K > miss_per")
    put("KcNoOutMed", sg(float(np.median(d))), "KANSAL_CHECK_40.csv pi_per = 0: median miss_K - miss_per")
    return K


def exploratory():
    X, XB = J(RES / "exploratory_q2_test.json"), J(RES / "exploratory_q2_boot_test.json")
    s = "exploratory_q2_test.json / exploratory_q2_boot_test.json"
    E1, E2, E3 = X["E1"], X["E2"], X["E3"]
    p = E2["predictors"]["T1_both_abar (primary)"]
    a0 = E3["per_amax_d0"]
    hk = XB["holm_E1_K_minus_perabar"]
    put("ExKblk", sg(E2["d_obs_median"]), s)
    put("ExOneShare", pct(E1["share_ge_-0.005"], 1), s)
    put("ExOneMed", sg(E1["d_K_minus_perabar"]["median"], 4), s)
    put("ExOneWrong", str(hk["n_sig_wrong_sign"]), s)
    put("ExOneN", str(hk["n"]), s)
    put("ExTwoPred", sg(p["median_pred"]), s)
    put("ExTwoRsq", f(p["R2_45"], 1), s)
    put("ExRatioAct", f(E2["a_bar_K_over_blk_median"]), s)
    put("ExThreeBlk", sg(a0["median_minus_blk"], 2), s)
    put("ExThreeBoth", pct(a0["share_le_both"], 1), s)
    put("ExThreeN", thou(E3["n_feasible"]), s)
    put("ExOutDiff", sg(E1["outage_perabar_minus_K"]), s)


def h3a_and_v1():
    SC = J(RES / "prereg_score_test.json")
    m = SC["H3a"]["medians_K8"]
    put("HthreeaLo", f(min(m.values()), 3), "prereg_score_test.json:H3a.medians_K8 min")
    put("HthreeaHi", f(max(m.values()), 3), "prereg_score_test.json:H3a.medians_K8 max")
    put("nFail", str(len(SC["tally"]["FAIL"])), "prereg_score_test.json:tally.FAIL")
    N1, N2 = J(V1 / "numbers.json"), J(RES / "numbers.json")
    put("VoneNev", thou(N1["corpus"]["n_events"]), "_v1_corpus3713/numbers.json")
    put("VoneLas", thou(v1_counts()["LASIESTA"]), "_v1_corpus3713/event_corpus_40.csv")
    put("VtwoLas", thou(N2["corpus"]["per_dataset_events"]["LASIESTA"]), "numbers.json")
    put("VoneEpsEight", f(N1["F_D_all"]["eps_star"]["8"], 3), "_v1_corpus3713/numbers.json")
    S1 = J(V1 / "prereg_score_test.json")
    put("VonePass", str(S1["tally"]["PASS"]), "_v1_corpus3713/prereg_score_test.json")


def a1():
    """Amendment A1 checks (P2R; copied to results/a1_*.json) and the longest event of the corrected corpus."""
    A, G = J(RES / "a1_corpus_checks.json"), J(RES / "a1_gt_offset_diagnostic.json")
    s, sg_ = "a1_corpus_checks.json", "a1_gt_offset_diagnostic.json"
    a = A["a_gt_alignment"]
    put("AoneHit", f(a["pooled_hit_time_order"], 3), s)
    put("AoneHitIdx", f(a["pooled_hit_dump_index"], 3), s)
    put("AoneHitPm", f(max(a["pooled_hit_offset_minus1"], a["pooled_hit_offset_plus1"]), 3), s + " (max of -1, +1)")
    put("AoneNseq", str(a["n_sequences"]), s)
    b = G["by_offset"]
    put("AoneIoUz", f(b["0"]["mean_best_iou"], 3), sg_)
    put("AoneIoUm", f(b["-1"]["mean_best_iou"], 3), sg_)
    put("AoneIoUp", f(b["1"]["mean_best_iou"], 3), sg_)
    put("AoneSeqM", str(G["offset_-1_vs_0"]["n_seq_mean_iou_higher_at_0"]), sg_)
    put("AoneSeqP", str(G["offset_1_vs_0"]["n_seq_mean_iou_higher_at_0"]), sg_)
    import csv
    dmax = max(int(r["duration"]) for r in csv.DictReader(open(RES / "event_corpus_40.csv", encoding="utf-8")))
    put("Dmax", thou(dmax), "event_corpus_40.csv max duration")


def lemma4():
    L = J(ROOT / "P3R" / "lemma4_check.json")
    if not L:
        pend(("LfourN", "LfourOK"), "Lemma 4 check")
        return None
    put("LfourN", str(len(L)), "P3R/lemma4_check.json")
    ok = all(x["feasible"] and x["non_decreasing"] and x["increase_only_at_upper"] and x["decrease_only_at_lower"]
             and x["optimal_vs_alternatives"] for x in L)
    put("LfourOK", "all checks hold" if ok else "a check fails (see lemma4\\_check.json)", "P3R/lemma4_check.json")
    return L


# ------------------------------------------------------------------ supplementary tables
def tab(caption, label, head, rows, spec):
    L = [r"\begin{table}[!ht]\centering\footnotesize\caption{" + caption + r"}\label{" + label + "}",
         r"\begin{tabular}{" + spec + r"}\toprule", " & ".join(head) + r"\\\midrule"]
    L += [" & ".join(r) + r"\\" for r in rows]
    L += [r"\bottomrule\end{tabular}\end{table}"]
    return "\n".join(L)


def supp_tables(A, K, L):
    import prereg_table as PT
    out = []
    S1, S2 = J(V1 / "prereg_score_test.json"), J(RES / "prereg_score_test.json")
    PT.H3A_DEC = 3
    o1, o2 = PT.observed(S1), PT.observed(S2)
    rows = []
    for k in PT.CRIT:
        v1, v2 = S1[k]["verdict"], S2[k]["verdict"]
        ch = r"\textbf{" + v2 + "}" if v1 != v2 else v2
        rows.append([k, r"\raggedright " + o1[k], v1, r"\raggedright " + o2[k], ch])
    out.append(tab(r"Pre-registered predictions on TEST before (v1, 3{,}713 events, earlier LASIESTA frame index) and "
                   r"after (v2, 3{,}170 events) the frame-order correction of amendment A1. Same criteria, seeds and "
                   r"splits; a changed verdict is in bold", "tab:s_v1v2",
                   ["\\#", "Observed v1", "v1", "Observed v2 (main text)", "v2"], rows,
                   r"@{}lp{0.36\textwidth}lp{0.36\textwidth}l@{}"))
    N1, N2 = J(V1 / "numbers.json"), J(RES / "numbers.json")
    f1, f2 = N1["F_D_all"], N2["F_D_all"]
    c1 = v1_counts()
    rws = [["Events", thou(N1["corpus"]["n_events"]), thou(N2["corpus"]["n_events"])],
           ["LASIESTA events", thou(c1["LASIESTA"]), thou(N2["corpus"]["per_dataset_events"]["LASIESTA"])],
           ["CDnet 2014 / BMC events", f"{thou(c1['CDnet2014'])} / {thou(c1['BMC'])}",
            f"{thou(N2['corpus']['per_dataset_events']['CDnet2014'])} / {thou(N2['corpus']['per_dataset_events']['BMC'])}"],
           ["$\\E[D]$ [frames]", f(f1["E[D]"], 2), f(f2["E[D]"], 2)],
           ["$P(D=1)$", f(f1["P(D=1)"], 3), f(f2["P(D=1)"], 3)],
           ["$P(D<8)$", pct(f1["P(D<8)"], 1), pct(f2["P(D<8)"], 1)]]
    rws += [[f"$\\eps^*(1/{K})$", f(f1["eps_star"][K], 3), f(f2["eps_star"][K], 3)] for K in ("4", "8", "16", "64")]
    out.append(tab("Duration law before and after the LASIESTA frame-order correction (all 121 videos)", "tab:s_fd",
                   ["", "v1", "v2"], rws, "@{}lrr@{}"))
    if A:
        R = A["H4_registered"]
        V = A["H4_A2_verdicts"]
        rows = [[k, R[k], (r"\textbf{" + V[k] + "}") if V[k] != R[k] else V[k]] for k in ("H4a", "H4b", "H4c", "H4d")]
        out.append(tab(r"H4a--H4d: registered verdict (v2 brackets, block surrogate miss) and the A2 column "
                       r"($C_{\mathrm{LB}}$ lower bracket, $C_{\mathrm{TS}}$ verified feasible with the exact miss); "
                       r"a changed verdict is in bold. Details in \texttt{results/a2\_sizing\_test.json}",
                       "tab:s_a2", ["", "Registered", "A2"], rows, "@{}lll@{}"))
    if K:
        k3 = K["K3"]
        rows = [["K1: $\\mathrm{miss}_K\\ge\\eps^*(a_K)-3\\,$SE, all cases", f"{K['K1']['n_fail_all']} of {thou(K['n_cases_all'])} fail"],
                ["K2: $\\pi_{\\mathrm{per}}=0$, Kansal better by $>3\\,$SE", f"{K['K2']['n_kansal_wins_beyond_3SE']} of {K['K2']['n_cases_pi_per_0']}"],
                ["K2: analytic periodic miss $-\\eps^*(a_K)$", f"max {K['K2']['max_abs_floor_mismatch']:.1e} (rate rounded to $10^{{-6}}$); 0 after rounding"],
                ["K3: Kansal better by $>0.005$", f"{thou(k3['n_kansal_wins_gt_0.005'])} of {thou(K['n_cases_E1'])}"],
                ["K3: of these, periodic has outages", pct(k3["share_with_pi_per_gt0"])],
                ["$\\eps^*(a_{\\mathrm{per,real}})-\\eps^*(a_K)$ in these cases", f"median {f(k3['eps_gap_real_minus_aK_wins']['median'], 3)}"],
                ["Kansal has more outage than periodic", pct(K["outage"]["share_pi_K_gt_pi_per_E1"])]]
        out.append(tab("Per-case check of the Kansal-style controller against periodic operation at its measured mean "
                       "activation (exploratory, post hoc; TEST, $10^5$ replayed events per case)", "tab:s_kansal",
                       ["Check", "Result"], rows, r"@{}p{0.55\textwidth}l@{}"))
    return "\n\n".join(out)


def main(latex_dir):
    latex_dir = pathlib.Path(latex_dir)
    A = a2()
    K = kansal()
    exploratory()
    h3a_and_v1()
    a1()
    L = lemma4()
    out = ["% numbers_a2.tex: GENERATED by code/paper/gen_numbers_p3r.py. Do not hand-edit."]
    out += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in MAC.items()]
    (latex_dir / "numbers_a2.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    (latex_dir / "supp_p3r_tables.tex").write_text("% GENERATED by code/paper/gen_numbers_p3r.py\n" + supp_tables(A, K, L) + "\n",
                                                   encoding="utf-8")
    (latex_dir / "numbers_a2_provenance.json").write_text(json.dumps(PROV, indent=1), encoding="utf-8")
    pending = [k for k, v in MAC.items() if "PENDING" in v]
    print(f"{len(MAC)} macros in numbers_a2.tex; pending: {pending}")
    return pending


if __name__ == "__main__":
    main(sys.argv[1])
