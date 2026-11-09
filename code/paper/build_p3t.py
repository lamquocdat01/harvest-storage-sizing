#!/usr/bin/env python3
"""build_p3t.py (topic 40, P3T): generated inputs of the TGCN build after amendments A4 and A4b. Run after build_tgcn.py.
  numbers_a4.tex        macros of A4 and A4b, recounts on 17 cells, physical units (+ numbers_a4_provenance.json)
  numbers_tables.json   the one source of every C* printed in Tables IV and S14-S18 (review item M10)
  sizing_table.tex      Table IV: 17 site-season cells, with report-energy columns
  supp_a3_tables.tex    Tables S14-S16 (A3), S17 (A4), S18 (A4b), S19 (TRAIN rerun against TEST)
  supp_deep3_table.tex  short table of Section S1 (no table number)
Reads only results/*.json and P0/energy_model_40.json. No simulation. Usage: python code/paper/build_p3t.py
"""
from __future__ import annotations

import json
import math
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LATEX = ROOT / "submission_package" / "TGCN" / "latex"
if not (ROOT / "submission_package").exists():
    LATEX = ROOT / "paper" / "tgcn"
RES = ROOT / "results"

SITES = [("HCMC", r"HCMC"), ("Madrid-MSG", r"Madrid"), ("Uppsala-MSG", r"Uppsala")]
SECOND = [("Madrid-SARAH3", r"Mad.\ SARAH"), ("Uppsala-SARAH3", r"Upp.\ SARAH")]
OTHER = {"Madrid-MSG": "Madrid-SARAH3", "Uppsala-MSG": "Uppsala-SARAH3", "Madrid-SARAH3": "Madrid-MSG", "Uppsala-SARAH3": "Uppsala-MSG"}
SEAS = ("DJF", "MAM", "JJA", "SON")
SETUPS = ("B", "C", "D", "E", "F")
EIDLE_J = 0.248e-3
SUPERCAP_J = 45.0


def J(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


def primary():
    for s, n in SITES:
        for i, se in enumerate(SEAS):
            yield s, se, n if i == 0 else "", se
    for x in SETUPS:
        yield f"Setup{x}", "ALL", "Indoor", x


def second():
    for s, n in SECOND:
        for i, se in enumerate(SEAS):
            yield s, se, n if i == 0 else "", se


def kj(v):
    return "--" if v is None else f"{v / 1e3:.2f}"


def table(caption, label, spec, head, rows, sep=None):
    L = [r"\begin{table}[H]\centering\footnotesize\caption{" + caption + r"}\label{" + label + "}",
         r"\begin{tabular}{" + spec + r"}\toprule", head + r"\\\midrule"]
    for i, r in enumerate(rows):
        if sep is not None and i == sep:
            L.append(r"\midrule")
        L.append(" & ".join(r) + r"\\")
    return "\n".join(L + [r"\bottomrule\end{tabular}\end{table}", ""])


def main():
    F5 = {(x["site"], x["season"]): x for x in J("F5_sizing_all.json")["rows"] if abs(x["m"] - 0.25) < 1e-9}
    W = {(x["site"], x["season"]): x for x in J("a3_worst_spell.json")["rows"] if abs(x["m"] - 0.25) < 1e-9}
    Rg = {(x["site"], x["season"]): x for x in J("a3_per_cell_ranges.json")["rows"]}
    Kd = {(x["site"], x["season"]): x for x in J("a3_margin_k.json")["rows"] if abs(x["m"] - 0.25) < 1e-9}
    RA = J("a4_radio.json")
    B = J("a4b_interannual.json")
    C17 = J("a4_count17.json")
    D3 = J("a4_deep3_impact.json")
    score = J("prereg_score_test.json")
    tr, te = J("prereg_score_train.json"), J("prereg_score_test.json")
    energy = json.loads((ROOT / "P0" / "energy_model_40.json").read_text(encoding="utf-8"))["node_classes"]["A_GAP9_HM0360"]
    rad = {(x["site"], x["season"], x["radio"]): x for x in RA["rows"] if abs(x["m"] - 0.25) < 1e-9}
    AV = J("a5_fixed_panel.json")
    fix = {(x["site"], x["season"], x["radio"]): x for x in AV["rows"]}
    GB = J("a5b_deep3_gate.json")
    gb = {r["quantity"]: r for r in GB["rows"]}
    M, P = {}, {}

    def put(k, v, src):
        assert re.fullmatch(r"[A-Za-z]+", k), k
        M[k], P[k] = str(v), {"value": str(v), "source": src}

    # one source of C* (M10)
    cells_all = list(primary()) + list(second())
    NT = {"source": "results/F5_sizing_all.json (m = 0.25); the only C* printed in Tables IV, S14, S17 and the 2025 row of S18", "cells": {}}
    for s, se, _, _ in cells_all:
        x = F5[(s, se)]
        NT["cells"][f"{s}|{se}"] = {"Cstar_J": x["Cstar_J"], "days": x["days"], "No7d_J": W[(s, se)]["L7"]["Cstar_drop"] * EIDLE_J,
                                    "radio_J": {r: rad[(s, se, r)]["Cstar_J"] for r in ("reg", "BLE", "6TiSCH", "LoRaWAN")},
                                    "fixed_J": {r: fix[(s, se, r)]["Cstar_fixed_J"] for r in ("BLE", "6TiSCH")}}
    (LATEX / "numbers_tables.json").write_text(json.dumps(NT, indent=1), encoding="utf-8")
    cj = lambda s, se: NT["cells"][f"{s}|{se}"]["Cstar_J"]  # noqa: E731

    # A4 radio
    R = RA["radios"]
    put("ErepLora", f"{R['LoRaWAN']['E_rep_mJ']:.0f}", "a4_radio.json:radios.LoRaWAN.E_rep_mJ")
    put("ErepBle", f"{R['BLE']['E_rep_mJ']:.3f}", "a4_radio.json:radios.BLE.E_rep_mJ")
    put("ErepSix", f"{R['6TiSCH']['E_rep_mJ']:.2f}", "a4_radio.json:radios.6TiSCH.E_rep_mJ")
    put("rLora", f"{R['LoRaWAN']['r']:.0f}", "a4_radio.json:radios.LoRaWAN.r")
    put("rBle", f"{R['BLE']['r']:.1f}", "a4_radio.json:radios.BLE.r")
    put("rSix", f"{R['6TiSCH']['r']:.1f}", "a4_radio.json:radios.6TiSCH.r")
    S = RA["summary"]
    for nm, k, d in (("kLora", "LoRaWAN", 1), ("kBle", "BLE", 3), ("kSix", "6TiSCH", 2)):
        q = S[f"m0.25_{k}_primary17"]
        assert q["ratio_max"] - q["ratio_min"] < 1e-3 * q["ratio_max"], k
        put(nm, f"{q['ratio_median']:.{d}f}", f"a4_radio.json:summary.m0.25_{k}_primary17.ratio_median")
    put("TaskLora", f"{R['LoRaWAN']['task_s']:.1f}", "a4_radio.json:radios.LoRaWAN.task_s")
    put("ActPeriod", f"{RA['node']['activation_period_s']:.1f}", "a4_radio.json:node.activation_period_s")
    put("PanelMarginQ", f"{RA['panel_margin_mJ']['m0.25']:.1f}", "a4_radio.json:panel_margin_mJ.m0.25")
    put("EdetmJ", f"{RA['node']['E_det_mJ']:.2f}", "a4_radio.json:node.E_det_mJ")
    put("AivNviol", str(RA["n_LB_gt_TS"]), "a4_radio.json:n_LB_gt_TS")
    put("AivNcases", str(RA["n_with_bounds"]), "a4_radio.json:n_with_bounds")
    put("AivMaxLB", f"{RA['max_LB_lo_over_TS']:.4f}", "a4_radio.json:max_LB_lo_over_TS")
    # physical units (M4)
    put("Pidle", f"{energy['P_idle_W'] * 1e3:.2f}", "P0/energy_model_40.json:P_idle_W")
    put("Pact", "62.9", "P0/ENERGY_MODEL_40.md: 62.9 mW, whole system during the detection loop")
    put("Tact", f"{energy['t_act_s'] * 1e3:.2f}", "P0/energy_model_40.json:t_act_s")
    for s, n in (("HCMC", "HCMC"), ("Madrid-MSG", "Mad"), ("Uppsala-MSG", "Upp")):
        v = [rad[(s, se, "reg")]["W_p"] * 1e3 for se in SEAS]
        put(f"Wp{n}Lo", f"{min(v):.0f}", f"a4_radio.json:rows {s} reg m=0.25 W_p min")
        put(f"Wp{n}Hi", f"{max(v):.0f}", f"a4_radio.json:rows {s} reg m=0.25 W_p max")
    idays = [F5[(f"Setup{x}", "ALL")]["days"] for x in SETUPS]
    put("InDaysLo", f"{min(idays):.0f}", "F5_sizing_all.json:indoor days min")
    put("InDaysHi", f"{max(idays):.0f}", "F5_sizing_all.json:indoor days max")
    ex = rad[("HCMC", "SON", "6TiSCH")]
    put("ExPmean", f"{ex['P_mean_mW']:.1f}", "a4_radio.json:rows HCMC SON 6TiSCH P_mean_mW")
    put("ExWp", f"{ex['W_p'] * 1e3:.0f}", "a4_radio.json:rows HCMC SON 6TiSCH W_p")
    put("ExCkJ", f"{ex['Cstar_J'] / 1e3:.2f}", "a4_radio.json:rows HCMC SON 6TiSCH Cstar_J")
    put("ExCaps", str(math.ceil(ex["Cstar_J"] / SUPERCAP_J)), "Cstar_J / 45 J, rounded up (10 F, 3 V supercapacitor)")
    hr = [round(F5[("HCMC", se)]["Cstar_J"] / 1e3, 2) / round(F5[("HCMC", se)]["baselines_J"]["C_avgday"] / 1e3, 2) for se in SEAS]
    put("FullRatioLo", f"{min(hr):.1f}", "F5_sizing_all.json: HCMC C*/C_avgday from the two decimals printed in Table IV, min")
    put("FullRatioHi", f"{max(hr):.1f}", "F5_sizing_all.json: HCMC C*/C_avgday from the two decimals printed in Table IV, max")
    bf = [round(F5[("HCMC", se)]["Cstar_J"] / 1e3, 2) / round(F5[("HCMC", se)]["baselines_J"]["C_buchli_daily"] / 1e3, 2) for se in SEAS]
    put("BuFullLo", f"{min(bf):.1f}", "F5_sizing_all.json: HCMC C*/C_buchli from the two decimals printed in Table IV, min")
    put("BuFullHi", f"{max(bf):.1f}", "F5_sizing_all.json: HCMC C*/C_buchli from the two decimals printed in Table IV, max")
    # A5: registered panel kept
    for r, n, d in (("6TiSCH", "Six", 2), ("BLE", "Ble", 3)):
        q = AV["summary"][f"{r}_primary17"]
        put(f"Av{n}Min", f"{q['ratio_min']:.{d}f}", f"a5_fixed_panel.json:summary.{r}_primary17.ratio_min")
        put(f"Av{n}Med", f"{q['ratio_median']:.{d}f}", f"a5_fixed_panel.json:summary.{r}_primary17.ratio_median")
        put(f"Av{n}Max", f"{q['ratio_max']:.{d}f}", f"a5_fixed_panel.json:summary.{r}_primary17.ratio_max")
        z = AV["summary"][f"{r}_second8"]
        put(f"Av{n}SecMin", f"{z['ratio_min']:.{d}f}", f"a5_fixed_panel.json:summary.{r}_second8.ratio_min")
        put(f"Av{n}SecMax", f"{z['ratio_max']:.{d}f}", f"a5_fixed_panel.json:summary.{r}_second8.ratio_max")
    s6 = AV["summary"]["6TiSCH_primary17"]
    assert s6["cell_max"] == "HCMC JJA" and s6["cell_min"] == "SetupF ALL" and not s6["cells_lost_balance"], "A5 text names these cells"
    assert not AV["summary"]["BLE_primary17"]["cells_lost_balance"]
    put("AvNviol", str(AV["n_LB_gt_TS"]), "a5_fixed_panel.json:n_LB_gt_TS")
    put("AvNcases", str(AV["n_with_bounds"]), "a5_fixed_panel.json:n_with_bounds")
    put("AvMaxLB", f"{AV['max_LB_lo_over_TS']:.4f}", "a5_fixed_panel.json:max_LB_lo_over_TS")
    # N3: maxima on the primary product; N10: largest difference between the A3 base and Table IV
    prim_rows = [x for x in Rg.values() if x["site"] in ("HCMC", "Madrid-MSG", "Uppsala-MSG")]
    put("MaxOutPrim", f"{max(x['C*/C_avgday']['max'] for x in prim_rows):.1f}", "a3_per_cell_ranges.json: C*/C_avgday max, primary outdoor cells")
    upp = [x for x in Rg.values() if x["site"] == "Uppsala-MSG"]
    put("MaxThreeUppPrim", f"{max(x['C*/C_3day']['max'] for x in upp):.1f}", "a3_per_cell_ranges.json: C*/C_3day max, Uppsala-MSG")
    put("PartialDayMax", f"{100 * C17['a3_vs_f5']['max_abs_rel']:.1f}", "a4_count17.json:a3_vs_f5.max_abs_rel (both m)")
    # N5: the Holm family on 17 cells
    put("nHolmHthree", str(2 * C17["holm17"]["n_cells"]), "a4_count17.json:holm17.n_cells x 2")
    put("nHolmHfourd", str(C17["holm17"]["n_tests"] - 2 * C17["holm17"]["n_cells"]), "a4_count17.json:holm17.n_tests minus 2 n_cells")
    put("FloorFiveOld", f"{D3['earlier_corpus']['eps_star']['0.2000']:.3f}", "a4_deep3_impact.json:earlier_corpus.eps_star[0.2]")
    put("FloorFiveNew", f"{D3['corrected_corpus']['eps_star']['0.2000']:.3f}", "a4_deep3_impact.json:corrected_corpus.eps_star[0.2]")
    put("ThreeDaykJ", f"{F5[('HCMC', 'DJF')]['baselines_J']['C_3day'] / 1e3:.2f}", "F5_sizing_all.json:baselines_J.C_3day")
    assert re.search(r"\\newcommand\{\\AiiMaxLBTSreg\}\{" + re.escape(f"{score['H4b']['max']:.3f}") + "}", "".join(f.read_text(encoding="utf-8") for d in (LATEX, LATEX.parent / "v3") if d.exists() for f in d.glob("numbers*.tex") if f.name != "numbers_a4.tex")), "AiiMaxLBTSreg"

    # recount on 17 cells
    put("nCellsSS", str(RA["primary_cells"]), "a4_radio.json:primary_cells")
    put("nCellMadS", "4", "A4 section 3: Madrid, MSG, 4 seasons")
    put("nCellUppS", "4", "A4 section 3: Uppsala, MSG, 4 seasons")
    H = C17["holm17"]
    assert H["all_rejected"]
    put("nHolmS", str(H["n_tests"]), "a4_count17.json:holm17.n_tests")
    put("pMaxBootS", f"{H['max_p']:.1e}".replace("e-0", r"\times10^{-").replace("e-", r"\times10^{-") + "}", "a4_count17.json:holm17.max_p")
    Hf = C17["hf17"]
    put("dmissMinS", f"{Hf['dmiss_min']:.2f}", "a4_count17.json:hf17.dmiss_min")
    put("dmissMaxS", f"{Hf['dmiss_max']:.2f}", "a4_count17.json:hf17.dmiss_max")
    put("dCMinS", f"{-100 * Hf['dC_rel_max']:.0f}", "a4_count17.json:hf17.dC_rel_max")
    put("dCMaxS", f"{-100 * Hf['dC_rel_min']:.0f}\\,\\%", "a4_count17.json:hf17.dC_rel_min")
    Wk = C17["worst17"]
    put("WorstMedS", f"{Wk['median']:.2f}", "a4_count17.json:worst17.median")
    put("WorstMinS", f"{Wk['min']:.2f}", "a4_count17.json:worst17.min")
    put("WorstMaxS", f"{Wk['max']:.2f}", "a4_count17.json:worst17.max")
    put("WorstOneS", str(Wk["n_unchanged"]), "a4_count17.json:worst17.n_unchanged")
    K5, K1 = C17["k17"]["m0.25"], C17["k17"]["m1.0"]
    put("KMedS", f"{K5['median_primary']:.2f}", "a4_count17.json:k17.m0.25.median_primary")
    put("KGtTwoS", str(K5["either_product"]["n_gt2_finite"]), "a4_count17.json:k17.m0.25.either_product.n_gt2_finite")
    put("KInfS", str(K5["either_product"]["n_inf"]), "a4_count17.json:k17.m0.25.either_product.n_inf")
    put("KMedMoneS", f"{K1['median_primary']:.2f}", "a4_count17.json:k17.m1.0.median_primary")
    put("KGtTwoMoneS", str(K1["either_product"]["n_gt2_finite"]), "a4_count17.json:k17.m1.0.either_product.n_gt2_finite")
    put("KInfMoneS", str(K1["either_product"]["n_inf"]), "a4_count17.json:k17.m1.0.either_product.n_inf")
    rm = C17["rule_medians"]
    put("avgMadS", f"{rm['Madrid|primary']['C*/C_avgday']['median']:.1f}", "a4_count17.json:rule_medians.Madrid|primary")
    put("avgMadSec", f"{rm['Madrid|second']['C*/C_avgday']['median']:.1f}", "a4_count17.json:rule_medians.Madrid|second")
    put("avgUppS", f"{rm['Uppsala|primary']['C*/C_avgday']['median']:.1f}", "a4_count17.json:rule_medians.Uppsala|primary")
    put("avgUppSec", f"{rm['Uppsala|second']['C*/C_avgday']['median']:.1f}", "a4_count17.json:rule_medians.Uppsala|second")
    bu = [rm[f"{g}|primary"]["C*/C_buchli_daily"]["median"] for g in ("Madrid", "Uppsala", "indoor")]
    put("buLoS", f"{min(bu):.1f}", "a4_count17.json:rule_medians, Buchli, min of Madrid, Uppsala, indoor")
    put("buHiS", f"{max(bu):.1f}", "a4_count17.json:rule_medians, Buchli, max of Madrid, Uppsala, indoor")
    pc = C17["avgday_per_cell_primary"]
    for g, n in (("HCMC", "HCMC"), ("Madrid", "Mad"), ("Uppsala", "Upp")):
        put(f"Cell{n}Lo", f"{pc[g]['min']:.1f}", f"a4_count17.json:avgday_per_cell_primary.{g}.min")
        put(f"Cell{n}Hi", f"{pc[g]['max']:.1f}", f"a4_count17.json:avgday_per_cell_primary.{g}.max")

    # A4b
    b5, b1 = B["summary"]["m0.25"], B["summary"]["m1.0"]
    mm = [b5[s]["max_over_min"] for s in SEAS]
    put("AivbLo", f"{min(mm):.1f}", "a4b_interannual.json:summary.m0.25 smallest max/min over seasons")
    put("AivbHi", f"{max(mm):.1f}", "a4b_interannual.json:summary.m0.25.largest_max_over_min")
    put("AivbHiMone", f"{b1['largest_max_over_min']:.1f}", "a4b_interannual.json:summary.m1.0.largest_max_over_min")
    put("AivbOverFive", f"{b5['largest_max_over_2025']:.1f}", "a4b_interannual.json:summary.m0.25.largest_max_over_2025")
    put("AivbWorstkJ", f"{b5['worst_season_cell_J'] / 1e3:.2f}", "a4b_interannual.json:summary.m0.25.worst_season_cell_J")
    put("AivbFivekJ", f"{b5['worst_season_cell_2025_J'] / 1e3:.2f}", "a4b_interannual.json:summary.m0.25.worst_season_cell_2025_J")

    # Deep3
    e, c = D3["earlier_corpus"], D3["corrected_corpus"]
    put("DthreeRatioOld", f"{e['eps_star']['0.2000'] / e['exp_closed_form_R5']:.1f}", "a4_deep3_impact.json: eps*(0.2)/exp closed form, earlier")
    put("DthreeRatioNew", f"{c['eps_star']['0.2000'] / c['exp_closed_form_R5']:.1f}", "a4_deep3_impact.json: eps*(0.2)/exp closed form, corrected")

    out = ["% numbers_a4.tex: GENERATED by code/paper/build_p3t.py. Do not hand-edit."] + [f"\\newcommand{{\\{a}}}{{{b}}}" for a, b in M.items()]
    (LATEX / "numbers_a4.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    (LATEX / "numbers_a4_provenance.json").write_text(json.dumps(P, indent=1), encoding="utf-8")

    # Table IV
    head = (r"Site & & $C^*$ & \shortstack{No worst-\\income week} & Other & Avg-day & Buchli & 6TiSCH & \shortstack{6TiSCH,\\fixed\\panel}\\\midrule")
    L = [r"\begin{table}[!t]\centering\caption{Storage for the reference node over the full trace ($m=0.25$, $K=8$; kJ; one slot = one frame period of "
         r"0.1\,s, 10\,fps). Seasons last \SeasonDays{} days; indoor rows give the trace length. No worst-income week: amendment A3 (Table~S14). Other: second "
         r"satellite product (Table~S8). 6TiSCH: one report per activation, panel rescaled (A4); fixed panel: registered panel kept (A5; Table~S17). The 3-day "
         r"rule needs \ThreeDaykJ{} kJ in every cell. Block-bootstrap intervals: Tables~S9--S10. Descriptive, not pre-registered}\label{tab:sizing}",
         r"\footnotesize\setlength{\tabcolsep}{1pt}", r"\begin{tabular}{@{}llrrrrrrr@{}}\toprule", head]
    for s, se, name, lab in primary():
        x = F5[(s, se)]
        b = x["baselines_J"]
        o = OTHER.get(s)
        ot = kj(cj(o, se)) if o else "--"
        lab2 = lab if s in dict(SITES) else f"{x['days']:.0f}\\,d"
        name = name if s in dict(SITES) else f"Indoor {lab}"
        L.append(f"{name} & {lab2} & {kj(cj(s, se))} & {kj(NT['cells'][f'{s}|{se}']['No7d_J'])} & {ot} & {kj(b['C_avgday'])} & {kj(b['C_buchli_daily'])} & "
                 f"{kj(rad[(s, se, '6TiSCH')]['Cstar_J'])} & {kj(fix[(s, se, '6TiSCH')]['Cstar_fixed_J'])}\\\\")
    L.append(r"\bottomrule\end{tabular}\end{table}")
    (LATEX / "sizing_table.tex").write_text("\n".join(L) + "\n", encoding="utf-8")
    days = [F5[(s, se)]["days"] for s, _ in SITES for se in SEAS]
    (LATEX / "numbers_a4.tex").open("a", encoding="utf-8").write(f"\\newcommand{{\\SeasonDays}}{{{min(days):.0f}--{max(days):.0f}}}\n")

    # Supplement tables
    prim = list(primary())
    sec = list(second())
    r2 = lambda x, d=2: r"$\infty$" if x is None else f"{x:.{d}f}"  # noqa: E731
    sepn = len(prim)
    second_note = r" Rows below the rule: second satellite product, a sensitivity, not counted among the \nCellsSS{} cells."
    rows = [[n, lab, kj(cj(s, se)), r2(W[(s, se)]["L1"]["ratio"]), r2(W[(s, se)]["L3"]["ratio"]), r2(W[(s, se)]["L7"]["ratio"]), str(W[(s, se)]["L7"]["start_day"])]
            for s, se, n, lab in prim + sec]
    o = [table(r"Worst-spell sensitivity (amendment A3, post hoc; reference node, $m=0.25$, full trace). $C^*$ in kJ, the value of Table~\ref{tab:s_a4_radio} and of Table~IV; the "
               r"ratios are $C^*$ with the worst window of 1, 3 or 7 days removed over $C^*$. A3 removes whole days, so for setups C and D its base drops a final partial day "
               r"(difference at most \PartialDayMax\,\% over both values of $m$). Last column: first day of the worst 7-day window." + second_note +
               r" Source: \texttt{results/a3\_worst\_spell.json}", "tab:s_a3_worst", "@{}llrrrrr@{}", r"Site & & $C^*$ & $-1$\,d & $-3$\,d & $-7$\,d & Start", rows, sepn)]
    cols = ("C*/C_avgday", "C*/C_buchli_daily", "C*/C_kansal_mean", "C*/C_3day")

    def cell(x, k):
        return "--" if k not in x else f"{x[k]['median']:.2f} [{x[k]['min']:.2f}, {x[k]['max']:.2f}]"
    rows = [[n, lab] + [cell(Rg[(s, se)], k) for k in cols] for s, se, n, lab in prim + sec]
    o.append(table(r"Ratio of $C^*$ to each sizing rule per cell (amendment A3, post hoc; TEST): median [min, max] over the $(r,\lt,m)$ combinations of the cell with a finite ratio."
                   + second_note + r" Source: \texttt{results/a3\_per\_cell\_ranges.json}", "tab:s_a3_ranges", "@{}llllll@{}",
                   r"Site & & $C^*$/Avg-day & $C^*$/Buchli & $C^*$/Kansal mean & $C^*$/3-day", rows, sepn))

    def mk(s, se, n, lab):
        x = Kd.get((s, se))
        if x is None:
            return [n, lab, "--", "--", "--"]
        return [n, lab, kj(x["C_TRAIN"] * EIDLE_J), kj(x["C_TEST"] * EIDLE_J) if x["C_TEST"] is not None else r"$\infty$", r"$\infty$" if x["k_inf"] else f"{x['k']:.2f}"]
    o.append(table(r"Train-to-test margin factor $k=C_{\mathrm{TEST}}/C_{\mathrm{TRAIN}}$ (amendment A3, post hoc; reference node, $m=0.25$; kJ). The panel is scaled on the TRAIN months only; "
                   r"$\infty$: that panel cannot sustain $a=1/8$ on the TEST months at any capacity. Adverse counts in the text count a site--season cell if either product shows the outcome (A4)."
                   + second_note + r" Source: \texttt{results/a3\_margin\_k.json}", "tab:s_a3_margin", "@{}llrrr@{}", r"Site & & $C_{\mathrm{TRAIN}}$ & $C_{\mathrm{TEST}}$ & $k$",
                   [mk(*c) for c in prim + sec], sepn))
    rows = []
    for s, se, n, lab in prim + sec:
        q = rad[(s, se, "reg")]
        lb, ts = q["C_LB_lo"], q["C_TS_exact_hi"]
        wp = "--" if q["W_p"] is None else f"{q['W_p'] * 1e3:.0f}"
        rows.append([n, lab, kj(cj(s, se)), kj(rad[(s, se, "BLE")]["Cstar_J"]), kj(rad[(s, se, "6TiSCH")]["Cstar_J"]), kj(rad[(s, se, "LoRaWAN")]["Cstar_J"]),
                     kj(fix[(s, se, "BLE")]["Cstar_fixed_J"]), kj(fix[(s, se, "6TiSCH")]["Cstar_fixed_J"]),
                     "--" if lb is None else f"{lb * EIDLE_J / 1e3:.2f}", "--" if ts is None else f"{ts * EIDLE_J / 1e3:.2f}", wp])
    o.append(table(r"Storage with report energy in $r$ (amendments A4 and A5, post hoc; reference node, $K=8$, $m=0.25$; kJ). $C^*$: registered $r$, as Table~IV. BLE, 6TiSCH, LoRaWAN: $C^*$ with one report per "
                   r"activation and the panel rescaled to the demand. BLE fix., 6T fix.: the registered panel is kept. $C_{\mathrm{LB}}$, $C_{\mathrm{TS}}$: lower bracket and verified feasible capacity at $\eps=\eps^*(1/8)$, registered $r$. "
                   r"$W_p$: implied panel in mW at the registered $r$ (horizontal, constant efficiency; no temperature, MPPT or regulator loss). LoRaWAN is an energy-only sensitivity (its "
                   r"Class~A task exceeds the activation period)." + second_note + r" Sources: \texttt{results/a4\_radio.json}, \texttt{results/a5\_fixed\_panel.json}", "tab:s_a4_radio", "@{}llrrrrrrrrr@{}",
                   r"Site & & $C^*$ & BLE & 6TiSCH & LoRaWAN & BLE fix. & 6T fix. & $C_{\mathrm{LB}}$ & $C_{\mathrm{TS}}$ & $W_p$", rows, sepn))
    rows = []
    br = {(x["year"], x["season"], x["m"]): x["Cstar_J"] for x in B["rows"]}
    for m, mm_lab, key in ((0.25, "0.25", "m0.25"), (1.0, "1", "m1.0")):
        for se in SEAS:
            vals = [br.get((y, se, m)) for y in B["years"]]
            cells_y = []
            for y, v in zip(B["years"], vals):
                t = kj(v)
                if y == 2023 and se == "JJA":
                    t += r"$^\ddagger$"
                cells_y.append(t)
            rows.append([mm_lab if se == "DJF" else "", se] + cells_y + [f"{B['summary'][key][se]['max_over_min']:.2f}"])
    o.append(table(r"Inter-annual range of $C^*$, Ho Chi Minh City (amendment A4b, post hoc; Himawari, reference node, $K=8$; kJ). The panel is rescaled for each year and season, so the table "
                   r"measures the worst spell at a matched mean harvest, not a fixed panel in a dark year. DJF is December, January and February of the same calendar year. The satellite changed from "
                   r"Himawari-8 to Himawari-9 within the period. $^\ddagger$: the archive has no data for one full day (6~June 2023); the registered pipeline fills it with zero harvest, so this value is "
                   r"inflated. Source: \texttt{results/a4b\_interannual.json}", "tab:s_a4b", "@{}ll" + "r" * (len(B["years"]) + 1) + "@{}",
                   r"$m$ & & " + " & ".join(str(y) for y in B["years"]) + r" & max/min", rows, 4))
    keys = [k for k in te if re.fullmatch(r"H\d[a-e]?", k)]
    o.append(table(r"Pre-registered predictions on the corrected corpus: TRAIN rerun (sensitivity only, amendment A1) against TEST (the scored split). Sources: "
                   r"\texttt{results/prereg\_score\_train.json}, \texttt{results/prereg\_score\_test.json}", "tab:s_train", "@{}lll@{}", r"\# & TRAIN & TEST",
                   [[k, tr[k]["verdict"], te[k]["verdict"]] for k in keys]))
    (LATEX / "supp_a3_tables.tex").write_text("\n".join(o), encoding="utf-8")

    # Short table of Section S1 (Deep3)
    E = e["eps_star"]
    Cn = c["eps_star"]
    rowsd = [("Events", "3,713", f"{e['n']:,}", f"{c['n']:,}", "--"),
             (r"$\E[D]$ (frames)", "34.0", f"{e['mean']:.1f}", f"{c['mean']:.1f}", "number changes"),
             (r"Median $D$; CV", r"2; $\approx$5.9", f"{e['median']:.0f}; {e['cv']:.2f}", f"{c['median']:.0f}; {c['cv']:.2f}", "yes"),
             (r"$\eps^*(0.8)$", "0.072", f"{E['0.8000']:.3f}", f"{Cn['0.8000']:.3f}", "number changes"),
             (r"$\eps^*(1/3)$", "0.289", f"{E['0.3333']:.3f}", f"{Cn['0.3333']:.3f}", "number changes"),
             (r"$\eps^*(1/5)$", "0.407", f"{E['0.2000']:.3f}", f"{Cn['0.2000']:.3f}", "number changes"),
             (r"$\eps^*(1/8)$", "not printed", f"{E['0.1250']:.3f}", f"{Cn['0.1250']:.3f}", "--"),
             (r"Floor / exponential form, $R=5$", r"$\approx$6", f"{e['eps_star']['0.2000'] / e['exp_closed_form_R5']:.1f}", f"{c['eps_star']['0.2000'] / c['exp_closed_form_R5']:.1f}", "yes"),
             ("Bernoulli minus floor, $a=1/5$", r"$\approx$0.06", f"{e['bernoulli_miss']['0.2000'] - E['0.2000']:.3f}", f"{c['bernoulli_miss']['0.2000'] - Cn['0.2000']:.3f}", "yes"),
             ]

    def g(prefix):
        m_ = [v for k, v in gb.items() if k.startswith(prefix)]
        assert len(m_) == 1, prefix
        return m_[0]
    c_ = g("Deployed gate")
    b_ = g("Lợi thế ε(a)/gated")
    t_ = g("TargetingGain")
    l_ = g("Leak-then-fix")
    p_ = g("Block-permutation test")
    x_ = g("Latency D≥R")
    m_ = g("Mô hình binary-channel")
    rowsd += [("Deployed gate: certified miss (\\%)", f"{c_['printed'][1]}", f"{c_['reproduced_old'][1]}", f"{c_['corrected'][1]:.2f}", "number changes"),
              (r"$\eps(a)$/gated, $a\in[0.2,0.8]$", f"{b_['printed'][0]}--{b_['printed'][1]:.2f}", f"{b_['reproduced_old'][0]}--{b_['reproduced_old'][1]:.2f}", f"{b_['corrected'][0]}--{b_['corrected'][1]:.2f}", "yes (marginal)"),
              ("Gain vs cost, deployed gate", f"{t_['printed'][0]} vs {t_['printed'][1]}", f"{t_['reproduced_old'][0]:.3f} vs {t_['reproduced_old'][1]:.3f}", f"{t_['corrected'][0]:.3f} vs {t_['corrected'][1]:.3f}", "yes (near break-even)"),
              ("Leak: misses with $D\\ge R$; share (\\%)", f"{l_['printed'][0]}; {l_['printed'][1]}", f"{l_['reproduced_old'][0]}; {l_['reproduced_old'][1]}", f"{l_['corrected'][0]}; {l_['corrected'][1]}", "yes"),
              ("Block-permutation $p$ at $L=R$", f"{p_['printed'][2]}", f"{p_['reproduced_old'][2]}", f"{p_['corrected'][2]}", "no: no longer rejected"),
              (r"Latency law, $\chi^2$ test", x_["printed"][1], x_["reproduced_old"][1], x_["corrected"][1], "no: now rejected"),
              ("Channel model, largest error", r"$\approx$" + str(m_["printed"]), f"{m_['reproduced_old']}", f"{m_['corrected']}", "no: above the printed bound")]
    Ld = [r"\begin{center}\footnotesize\begin{tabular}{@{}lllll@{}}\toprule", r"Quantity & Article & Earlier, recomputed & Corrected & Conclusion holds?\\\midrule"]
    Ld += [" & ".join(x) + r"\\" for x in rowsd]
    Ld.append(r"\bottomrule\end{tabular}\end{center}")
    (LATEX / "supp_deep3_table.tex").write_text("\n".join(Ld) + "\n", encoding="utf-8")
    print(len(M) + 1, "macros;", LATEX)


if __name__ == "__main__":
    main()
