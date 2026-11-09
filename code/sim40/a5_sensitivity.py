"""Amendment A5 (prereg/AMENDMENT_LOG.md, tag prereg-40-a5): storage need with the report energy at the registered panel.
The panel stays at the size registered for r = 14.3, m = 0.25 and is not rescaled; the node pays r_BLE or r_6TiSCH of A4.
Output results/a5_fixed_panel.json. Changes no verdict and no earlier number. One process; 08:00-23:00; at least 7 GB free.
python -m sim40.a5_sensitivity
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np

from . import a4_sensitivity as A4
from . import config as cfg
from . import energy as E
from . import traces as T
from .events import law_for

M = 0.25
RADIOS = ("BLE", "6TiSCH")


def fixed_row(site, sea, rname, r, law, A2M, F5, rescaled):
    g, meta = T.season_series(site, sea, split="all")
    h = T.scale_panel(g, A4.R_REG, A4.L_A, M)                      # registered panel, not rescaled
    c_reg = E.C_periodic(h, A4.N_SUB, A4.R_REG, A4.L_A, A4.A)
    A4.check_reg(c_reg * A4.EIDLE_J, F5[(site, sea, M)]["Cstar_J"], f"{site} {sea} m={M}")
    cs = E.C_periodic(h, A4.N_SUB, r, A4.L_A, A4.A)
    eps = float(law.eps_star(A4.A)[0]) + 1e-9
    a_eps = float(law.a_eps(eps))
    demand = 1.0 + A4.L_A + A4.A * (r - 1.0)
    margin = float(h.mean() - demand)
    lo, hi, cx, ev = None, None, None, None
    if math.isfinite(cs):
        c_hi = 50 * cs
        lo, hi = A2M.lb_bounds(h, r, A4.L_A, a_eps, c_hi)
        cx, ev, _ = A2M.ts_exact_hi(h, r, A4.L_A, law, eps, cs * 1.01, c_hi)
    return {"site": site, "season": sea, "group": A4.group(site), "primary": A4.is_primary(site), "radio": rname, "r": r, "m": M, "days": meta["days"],
            "Cstar_reg_J": A4.fin(c_reg * A4.EIDLE_J), "Cstar_fixed_J": A4.fin(cs * A4.EIDLE_J), "ratio_to_reg": A4.fin(cs / c_reg),
            "ratio_to_rescaled": A4.fin(cs * A4.EIDLE_J / rescaled[(site, sea, rname)]), "mean_income_minus_demand": margin, "lost_balance": bool(margin <= 0 or not math.isfinite(cs)),
            "C_LB_lo": A4.fin(lo), "C_LB_hi": A4.fin(hi), "C_TS_exact_hi": A4.fin(cx), "outage_at_TS": None if ev is None else ev["outage"]}


def main():
    why = A4.guard()
    if why:
        sys.exit("STOP: " + why)
    A2M, F5, law = A4.a2(), A4.f5_map(), law_for("all")
    RA = json.loads((cfg.RES / "a4_radio.json").read_text(encoding="utf-8"))
    rescaled = {(x["site"], x["season"], x["radio"]): x["Cstar_J"] for x in RA["rows"] if abs(x["m"] - M) < 1e-9}
    rows = []
    for site, sea in T.cells():
        for rname in RADIOS:
            rows.append(fixed_row(site, sea, rname, RA["radios"][rname]["r"], law, A2M, F5, rescaled))
        print(site, sea, "done", flush=True)
    summ = {}
    for rname in RADIOS:
        for lab, sel in (("primary17", True), ("second8", False)):
            S = [x for x in rows if x["radio"] == rname and x["primary"] is sel]
            v = [x["ratio_to_reg"] for x in S if x["ratio_to_reg"] is not None]
            w = [x["ratio_to_rescaled"] for x in S if x["ratio_to_rescaled"] is not None]
            imin = int(np.argmin(v))
            imax = int(np.argmax(v))
            fin = [x for x in S if x["ratio_to_reg"] is not None]
            summ[f"{rname}_{lab}"] = {"n": len(S), "n_finite": len(v), "ratio_min": float(np.min(v)), "ratio_median": float(np.median(v)), "ratio_max": float(np.max(v)),
                                      "cell_min": f"{fin[imin]['site']} {fin[imin]['season']}", "cell_max": f"{fin[imax]['site']} {fin[imax]['season']}",
                                      "ratio_to_rescaled_min": float(np.min(w)), "ratio_to_rescaled_median": float(np.median(w)), "ratio_to_rescaled_max": float(np.max(w)),
                                      "cells_lost_balance": [f"{x['site']} {x['season']}" for x in S if x["lost_balance"]],
                                      "min_margin": float(min(x["mean_income_minus_demand"] for x in S))}
    ok = [x for x in rows if x["C_LB_lo"] is not None and x["C_TS_exact_hi"] is not None]
    out = {"amendment": "A5", "panel": "registered size at r = 14.3, m = 0.25, not rescaled", "node": {"r_reg": A4.R_REG, "l": A4.L_A, "K": A4.K, "e_idle_J": A4.EIDLE_J},
           "summary": summ, "n_with_bounds": len(ok), "n_LB_gt_TS": sum(1 for x in ok if x["C_LB_lo"] > x["C_TS_exact_hi"]),
           "max_LB_lo_over_TS": max(x["C_LB_lo"] / x["C_TS_exact_hi"] for x in ok), "max_outage_at_TS": max(x["outage_at_TS"] for x in ok), "rows": rows}
    (cfg.RES / "a5_fixed_panel.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("a5_fixed_panel.json written", flush=True)


if __name__ == "__main__":
    main()
