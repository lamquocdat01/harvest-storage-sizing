"""Amendments A4 and A4b (prereg/AMENDMENT_LOG.md, tag prereg-40-a4): post-hoc, descriptive sensitivities.
  a4b     : C* per year x season for Ho Chi Minh City, 2020-2025        -> results/a4b_interannual.json
  radio   : C*, C_LB, C_TS with report energy in r (LoRaWAN, BLE, 6TiSCH) -> results/a4_radio.json
  count17 : read-only recount on 17 site-season cells                   -> results/a4_count17.json
  deep3   : earlier and corrected corpus, quantities defined as in [14] -> results/a4_deep3_impact.json
Changes no verdict and no earlier number. One process; 08:00-23:00; at least 7 GB free at the start of each step.
python -m sim40.a4_sensitivity --part a4b|radio|count17|deep3 [--m 0.25 1.0]
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
import psutil

from . import config as cfg
from . import energy as E
from . import traces as T
from .bootstrap import TS_CELLS, holm
from .events import DurationLaw, law_for

R_REG, L_A, K, EIDLE_J = 14.3, 0.036, 8, 0.248e-3   # reference node (sizing.py)
A = 1.0 / K
N_SUB = 600
PERIOD_S = K * cfg.TAU                               # activation period at K = 8
PRIMARY = ("HCMC", "Madrid-MSG", "Uppsala-MSG", "SetupB", "SetupC", "SetupD", "SetupE", "SetupF")
SECOND = {"Madrid-MSG": "Madrid-SARAH3", "Uppsala-MSG": "Uppsala-SARAH3"}
YEARS = tuple(range(2020, 2026))
STEM_2025 = "HCMC_jma_jaxa_himawari_2025"
CKPT = cfg.DS / "_derived" / "40" / "a4_ckpt"


def guard():
    """Reason to stop now, or None (A4 section 7)."""
    now = dt.datetime.now().time()
    if not (dt.time(8) <= now < dt.time(23)):
        return "outside the 08:00-23:00 window"
    free = psutil.virtual_memory().available / 2**30
    return f"only {free:.1f} GB free" if free < 7.0 else None


def fin(x):
    return None if x is None or not math.isfinite(x) else float(x)


def is_primary(site):
    return site in PRIMARY


def group(site):
    return "indoor" if site.startswith("Setup") else site.split("-")[0]


# ------------------------------------------------------------------ radios: reference [2], A4 section 2
def t_lora(pl=8, sf=7, bw=125e3, cr=1, npr=8, ih=0, de=0):
    """Time on air, Eq. (9)-(10) of [2]."""
    s = npr + 4.25 + 8 + max(math.ceil((8 * pl - 4 * sf + 44 - 20 * ih) / (4 * (sf - 2 * de))) * (cr + 4), 0)
    return s * 2 ** sf / bw, s


def radios(pl=8):
    t, s = t_lora(pl)
    ble_t = 8 * (pl + 18) / 1e6
    mpdu = 38 + pl
    rows = {
        "LoRaWAN": {"E_rep_mJ": 166.0 + 134.0 * t, "T_TX_s": t, "S_TX_symbols": s, "task_s": 2.2 + t,
                    "source": "[2] Eq. (9)-(11), Table VI (SODAQ ExpLoRer, 2.7 V, 14 dBm, Class A, sleep between tasks)",
                    "packet": f"PL = {pl} B, SF7, 125 kHz, CR 4/5, 8 preamble symbols, explicit header, no LDRO"},
        "BLE": {"E_rep_mJ": (6.2 + 16.4e3 * 3 * ble_t) / 1e3, "T_TX_s": ble_t, "task_s": 24.3e-3 + 3 * ble_t,
                "source": "[2] Eq. (15)-(16), (20), Table VII (nRF52840, 1.8 V, 4 dBm, BLE Mesh LPN)",
                "packet": f"PL = {pl} B, 18 B overhead, 1 Mbit/s, three advertising channels"},
        "6TiSCH": {"E_rep_mJ": (336.5 + 0.174 * mpdu) / 1e3, "S_TX_bytes": mpdu, "task_s": 15e-3,
                   "source": "[2] Eq. (22), Table VIII (OpenMote, CC2538 2.4 GHz, 3.3 V, unicast TX slot)",
                   "packet": f"PL = {pl} B, 38 B headers, one hop"},
    }
    for x in rows.values():
        x["r"] = R_REG + x["E_rep_mJ"] / (EIDLE_J * 1e3)
        x["fits_activation_period"] = bool(x["task_s"] <= PERIOD_S)
    return rows


def margin_mJ(m, r=R_REG, l=L_A):
    """Report energy per activation that the registered panel can pay at a = 1/8 (energy balance)."""
    harvest = (1.0 + m) * (1.0 + l + (r - 1.0) / K)
    r_max = 1.0 + K * (harvest - 1.0 - l)
    return (r_max - r) * EIDLE_J * 1e3


# ------------------------------------------------------------------ A2 functions, unchanged
def a2():
    for d in ("P3R", "checks"):
        p = cfg.TOPIC / d / "run_a2_sizing.py"
        if p.exists():
            spec = importlib.util.spec_from_file_location("run_a2_sizing", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    raise FileNotFoundError("run_a2_sizing.py")


def f5_map():
    F5 = json.loads((cfg.RES / "F5_sizing_all.json").read_text())
    return {(x["site"], x["season"], x["m"]): x for x in F5["rows"]}


def check_reg(c_j, ref_j, what):
    if abs(c_j - ref_j) > 1e-9 * abs(ref_j):
        sys.exit(f"STOP: {what}: {c_j} J differs from F5_sizing_all.json {ref_j} J (A4 section 4)")


# ------------------------------------------------------------------ part radio
def radio_row(site, sea, rname, r, m, law, A2M, F5):
    g, meta = T.season_series(site, sea, split="all")
    h = T.scale_panel(g, r, L_A, m)
    cs = E.C_periodic(h, N_SUB, r, L_A, A)
    if rname == "reg":
        check_reg(cs * EIDLE_J, F5[(site, sea, m)]["Cstar_J"], f"{site} {sea} m={m}")
    eps = float(law.eps_star(A)[0]) + 1e-9
    a_eps = float(law.a_eps(eps))
    c_hi = 50 * cs if math.isfinite(cs) else 1e12
    lo, hi = A2M.lb_bounds(h, r, L_A, a_eps, c_hi)
    cx, ev, _ = A2M.ts_exact_hi(h, r, L_A, law, eps, cs * 1.01, c_hi) if math.isfinite(cs) else (math.inf, None, 0)
    e_ref = 1.0 + L_A + (r - 1.0) / cfg.K_REF
    p_mean_w = (1.0 + m) * e_ref * EIDLE_J / cfg.TAU
    outdoor = site in cfg.SITES_OUT
    ghi = float(g.mean()) if outdoor else None
    return {"site": site, "season": sea, "group": group(site), "primary": is_primary(site), "radio": rname, "r": r, "m": m,
            "days": meta["days"], "eps": eps, "a_eps": a_eps, "Cstar": fin(cs), "Cstar_J": fin(cs * EIDLE_J),
            "C_LB_lo": fin(lo), "C_LB_hi": fin(hi), "C_TS_exact_hi": fin(cx),
            "outage_at_TS": None if ev is None else ev["outage"], "miss_exact_at_TS": None if ev is None else ev["miss_exact"],
            "P_mean_mW": p_mean_w * 1e3, "mean_input": float(g.mean()), "input_unit": meta["unit"],
            "W_p": None if not outdoor else p_mean_w * 1000.0 / ghi}


def part_radio(ms):
    A2M, F5, law = a2(), f5_map(), law_for("all")
    R = radios()
    cases = [("reg", R_REG)] + [(k, v["r"]) for k, v in R.items()]
    (CKPT / "radio").mkdir(parents=True, exist_ok=True)
    rows = []
    for m in ms:
        for site, sea in T.cells():
            for rname, r in cases:
                f = CKPT / "radio" / f"{site}_{sea}_{rname}_m{m}.json"
                if f.exists():
                    rows.append(json.loads(f.read_text()))
                    continue
                why = guard()
                if why:
                    sys.exit(f"STOP before {f.name}: {why}; rerun to resume")
                x = radio_row(site, sea, rname, r, m, law, A2M, F5)
                f.write_text(json.dumps(x))
                rows.append(x)
            print(site, sea, "m", m, "done", flush=True)
    base = {(x["site"], x["season"], x["m"]): x["Cstar"] for x in rows if x["radio"] == "reg"}
    for x in rows:
        c0 = base[(x["site"], x["season"], x["m"])]
        x["ratio_to_reg"] = fin(x["Cstar"] / c0) if x["Cstar"] is not None and c0 else None
    summ = {}
    for m in ms:
        for rname, _ in cases:
            for lab, sel in (("primary17", True), ("second8", False)):
                v = [x["ratio_to_reg"] for x in rows if x["m"] == m and x["radio"] == rname and x["primary"] is sel and x["ratio_to_reg"] is not None]
                cj = [x["Cstar_J"] for x in rows if x["m"] == m and x["radio"] == rname and x["primary"] is sel and x["Cstar_J"] is not None]
                summ[f"m{m}_{rname}_{lab}"] = {"n": len(v), "ratio_median": float(np.median(v)), "ratio_min": float(np.min(v)),
                                               "ratio_max": float(np.max(v)), "Cstar_J_min": float(np.min(cj)), "Cstar_J_max": float(np.max(cj))}
    ok = [x for x in rows if x["C_LB_lo"] is not None and x["C_TS_exact_hi"] is not None]
    viol = [x for x in ok if x["C_LB_lo"] > x["C_TS_exact_hi"]]
    out = {"amendment": "A4 sections 2-4", "node": {"r_reg": R_REG, "l": L_A, "K": K, "e_idle_J": EIDLE_J, "slot_s": cfg.TAU,
                                                    "E_det_mJ": R_REG * EIDLE_J * 1e3, "activation_period_s": PERIOD_S},
           "r_reg_absorbs_mJ": 0.0, "panel_margin_mJ": {f"m{m}": margin_mJ(m) for m in (0.25, 1.0)}, "radios": R, "ms_run": list(ms),
           "primary_cells": len({(x['site'], x['season']) for x in rows if x['primary']}),
           "n_LB_gt_TS": len(viol), "max_LB_lo_over_TS": max(x["C_LB_lo"] / x["C_TS_exact_hi"] for x in ok), "n_with_bounds": len(ok),
           "max_outage_at_TS": max(x["outage_at_TS"] for x in rows if x["outage_at_TS"] is not None), "summary": summ, "rows": rows}
    (cfg.RES / "a4_radio.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("a4_radio.json written", flush=True)


# ------------------------------------------------------------------ part a4b
def part_a4b():
    why = guard()
    if why:
        sys.exit("STOP: " + why)
    F5 = f5_map()
    rel = "../OpenMeteo_HCMC_2020_2024/HCMC_jma_jaxa_himawari_{}"
    rows, missing, steps = [], [], {}
    for y in YEARS:
        name = "HCMC" if y == 2025 else f"HCMC_{y}"
        if y != 2025:
            cfg.SITES_OUT[name] = rel.format(y)
        try:
            s, step, n_nan = T.load_outdoor(name)
            steps[y] = {"step_s": step, "n_nan": n_nan, "rows": int(s.size)}
            for sea in cfg.SEASONS:
                g, meta = T.season_series(name, sea, split="all")
                if g.size < 1440 * 60 or not np.isfinite(g).all() or g.sum() <= 0:
                    missing.append({"year": y, "season": sea, "reason": f"{g.size} sub-steps"})
                    continue
                for m in cfg.M_LEVELS:
                    h = T.scale_panel(g, R_REG, L_A, m)
                    c = E.C_periodic(h, N_SUB, R_REG, L_A, A)
                    if y == 2025:
                        check_reg(c * EIDLE_J, F5[("HCMC", sea, m)]["Cstar_J"], f"HCMC {sea} m={m} (2025)")
                    rows.append({"year": y, "season": sea, "m": m, "days": meta["days"], "Cstar_J": fin(c * EIDLE_J),
                                 "mean_ghi_wm2": float(g.mean())})
        finally:
            if y != 2025:
                cfg.SITES_OUT.pop(name)
        print("year", y, "done", steps[y], flush=True)
    summ = {}
    for m in cfg.M_LEVELS:
        per = {}
        for sea in cfg.SEASONS:
            d = {x["year"]: x["Cstar_J"] for x in rows if x["m"] == m and x["season"] == sea and x["Cstar_J"] is not None}
            v = list(d.values())
            per[sea] = {"n_years": len(v), "min_J": min(v), "max_J": max(v), "max_over_min": max(v) / min(v),
                        "worst_year": max(d, key=d.get), "best_year": min(d, key=d.get), "value_2025_J": d.get(2025),
                        "max_over_2025": max(v) / d[2025] if 2025 in d else None}
        per["largest_max_over_min"] = max(per[s]["max_over_min"] for s in cfg.SEASONS)
        per["season_of_largest"] = max(cfg.SEASONS, key=lambda s: per[s]["max_over_min"])
        per["largest_max_over_2025"] = max(per[s]["max_over_2025"] for s in cfg.SEASONS)
        per["worst_season_cell_J"] = max(per[s]["max_J"] for s in cfg.SEASONS)
        per["worst_season_cell_2025_J"] = max(per[s]["value_2025_J"] for s in cfg.SEASONS)
        summ[f"m{m}"] = per
    out = {"amendment": "A4b", "site": "HCMC", "product": "jma_jaxa_himawari", "node": {"r": R_REG, "l": L_A, "K": K},
           "years": list(YEARS), "steps": {str(k): v for k, v in steps.items()}, "missing": missing, "summary": summ, "rows": rows}
    (cfg.RES / "a4b_interannual.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("a4b_interannual.json written", flush=True)


# ------------------------------------------------------------------ part count17 (read-only)
def part_count17():
    out = {"amendment": "A4 section 5", "primary_sites": list(PRIMARY)}
    B = json.loads((cfg.RES / "boot_test.json").read_text())
    C = [c for c in B["cells"] if is_primary(c["site"])]
    ps = [c["p_dmiss_le0"] for c in C] + [c["p_dC_ge0"] for c in C] + [c["p_TS_ge_per"] for c in C if "p_TS_ge_per" in c]
    rej = holm(ps)
    out["holm17"] = {"n_cells": len(C), "n_tests": len(ps), "n_rejected": int(rej.sum()), "all_rejected": bool(rej.all()),
                     "max_p": float(max(ps)), "ts_cells_primary": [c["site"] + " " + c["season"] for c in C if "p_TS_ge_per" in c]}
    out["hf17"] = {"dmiss_min": min(c["dmiss"] for c in C), "dmiss_max": max(c["dmiss"] for c in C),
                   "dC_rel_min": min(c["dC_rel"] for c in C), "dC_rel_max": max(c["dC_rel"] for c in C),
                   "ts_over_per": {c["site"] + " " + c["season"]: c["TS_over_per"] for c in C if "TS_over_per" in c}}
    S = json.loads((cfg.RES / "summary_test.json").read_text())["main"]["baselines"]
    keys = ("C*/C_avgday", "C*/C_buchli_daily", "C*/C_kansal_mean", "C*/C_3day")
    prod = defaultdict(lambda: defaultdict(list))
    for x in S:
        grp = group(x["site"])
        tag = "primary" if is_primary(x["site"]) else "second"
        for k in keys:
            if x[k] is not None and math.isfinite(x[k]):
                prod[(grp, tag)][k].append(float(x[k]))
                prod[(grp, "both")][k].append(float(x[k]))
    out["rule_medians"] = {f"{g}|{t}": {k: {"n": len(v), "median": float(np.median(v))} for k, v in d.items()} for (g, t), d in prod.items()}
    W = json.loads((cfg.RES / "a3_worst_spell.json").read_text())
    w = [x for x in W["rows"] if abs(x["m"] - 0.25) < 1e-9]
    v = [x["L7"]["ratio"] for x in w if is_primary(x["site"]) and x["L7"]["ratio"] is not None]
    out["worst17"] = {"n": len(v), "median": float(np.median(v)), "min": float(np.min(v)), "max": float(np.max(v)),
                      "n_unchanged": int(sum(1 for z in v if z > 1 - 1e-9))}
    Kd = json.loads((cfg.RES / "a3_margin_k.json").read_text())
    res_k = {}
    for m in cfg.M_LEVELS:
        kr = {(x["site"], x["season"]): x for x in Kd["rows"] if abs(x["m"] - m) < 1e-9}
        val = lambda s: math.inf if kr[s]["k_inf"] else kr[s]["k"]  # noqa: E731
        prim = [q for q in kr if is_primary(q[0])]
        ks = [val(q) for q in prim]
        ks_sorted = sorted(ks, key=lambda z: (not math.isfinite(z), z))
        med = ks_sorted[len(ks_sorted) // 2]
        n_gt2_finite_only, n_inf, cells_gt2, cells_inf = 0, 0, [], []
        for q in prim:
            vals = [val(q)]
            if q[0] in SECOND:
                vals.append(val((SECOND[q[0]], q[1])))
            if any(math.isinf(z) for z in vals):
                n_inf += 1
                cells_inf.append(f"{q[0]} {q[1]}")
            elif any(z > 2 for z in vals):
                n_gt2_finite_only += 1
                cells_gt2.append(f"{q[0]} {q[1]}")
        prim_gt2 = sum(1 for z in ks if z > 2)
        prim_inf = sum(1 for z in ks if math.isinf(z))
        res_k[f"m{m}"] = {"n": len(ks), "median_primary": None if math.isinf(med) else float(med),
                          "either_product": {"n_gt2_finite": n_gt2_finite_only, "n_inf": n_inf, "cells_gt2": cells_gt2, "cells_inf": cells_inf},
                          "primary_only": {"n_gt2_including_inf": prim_gt2, "n_inf": prim_inf},
                          "share_gt1_primary": float(np.mean([z > 1 for z in ks])), "largest_finite": float(max(z for z in ks if math.isfinite(z)))}
    out["k17"] = res_k
    Rg = json.loads((cfg.RES / "a3_per_cell_ranges.json").read_text())
    rr = {}
    for gg in ("HCMC", "Madrid", "Uppsala", "indoor"):
        v = [x["C*/C_avgday"]["median"] for x in Rg["rows"] if x["group"] == gg and is_primary(x["site"])]
        rr[gg] = {"n": len(v), "min": float(np.min(v)), "max": float(np.max(v))}
    out["avgday_per_cell_primary"] = rr
    F5 = f5_map()
    dif = []
    for x in W["rows"]:
        ref = F5[(x["site"], x["season"], x["m"])]["Cstar_J"]
        c = x["Cstar"] * EIDLE_J
        dif.append({"site": x["site"], "season": x["season"], "m": x["m"], "F5_J": ref, "A3_J": c, "rel_diff": c / ref - 1, "days": x["days"]})
    out["a3_vs_f5"] = {"n_differ_gt_1e-9": sum(1 for z in dif if abs(z["rel_diff"]) > 1e-9), "max_abs_rel": max(abs(z["rel_diff"]) for z in dif),
                       "cells_differ": [z for z in dif if abs(z["rel_diff"]) > 1e-9]}
    (cfg.RES / "a4_count17.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("a4_count17.json written", flush=True)


# ------------------------------------------------------------------ part deep3 (read-only)
def law_stats(d):
    d = np.asarray(d, float)
    law = DurationLaw(d.astype(int))
    a_list = (0.8, 0.5, 0.40, 1 / 3, 0.25, 0.2, 1 / 8, 1 / 16)
    return {"n": int(d.size), "mean": float(d.mean()), "median": float(np.median(d)), "max": int(d.max()),
            "cv": float(d.std(ddof=1) / d.mean()), "p_d1": float(np.mean(d == 1)),
            "eps_star": {f"{a:.4f}": float(law.eps_star(a)[0]) for a in a_list},
            "bernoulli_miss": {f"{a:.4f}": float(np.mean((1 - a) ** d)) for a in a_list}}


def part_deep3():
    v1 = pd.read_csv(cfg.RES / "_v1_corpus3713" / "event_corpus_40.csv")
    v2 = pd.read_csv(cfg.RES / "event_corpus_40.csv")
    out = {"amendment": "A4 section 6", "earlier_corpus": law_stats(v1.duration.values), "corrected_corpus": law_stats(v2.duration.values)}
    for name, c in (("earlier", v1), ("corrected", v2)):
        out[f"per_dataset_{name}"] = {k: {"n": int(g.shape[0]), "mean": float(g.duration.mean()), "median": float(g.duration.median()),
                                          "max": int(g.duration.max()), "cv": float(g.duration.std(ddof=1) / g.duration.mean())}
                                      for k, g in c.groupby("dataset")}
    for name in ("earlier_corpus", "corrected_corpus"):
        mu = out[name]["mean"]
        out[name]["exp_closed_form_R5"] = 1 - (mu / 5) * (1 - math.exp(-5 / mu))
    (cfg.RES / "a4_deep3_impact.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("a4_deep3_impact.json written", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["a4b", "radio", "count17", "deep3"])
    ap.add_argument("--m", type=float, nargs="+", default=[0.25])
    a = ap.parse_args()
    why = guard()
    if why:
        sys.exit("STOP: " + why)
    {"a4b": part_a4b, "radio": lambda: part_radio(tuple(a.m)), "count17": part_count17, "deep3": part_deep3}[a.part]()


if __name__ == "__main__":
    main()
