"""Amendment A3 (prereg/AMENDMENT_LOG.md, tag prereg-40-a3): post-hoc, descriptive sizing sensitivities.
  worst  : C* with the worst window of L days removed (split all)      -> results/a3_worst_spell.json
  ranges : per-cell ranges of the sizing-rule ratios (read-only, TEST) -> results/a3_per_cell_ranges.json
  margin : k = C_TEST / C_TRAIN with the panel scaled on TRAIN         -> results/a3_margin_k.json
Deterministic: no seed. Changes no verdict and no earlier number.
python -m sim40.a3_sensitivity --part all
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from collections import defaultdict

import numpy as np
import psutil

from . import config as cfg
from . import energy as E
from . import traces as T

R_A, L_A, K = 14.3, 0.036, 8       # reference node (sizing.py)
A = 1.0 / K
N_SUB, DAY = 600, 1440
LENGTHS = (7, 1, 3)                # primary first (A3 section 3)
RATIOS = ("C*/C_avgday", "C*/C_buchli_daily", "C*/C_kansal_mean", "C*/C_3day")
GROUPS = ("HCMC", "Madrid", "Uppsala", "indoor")


def g4(site):
    return "indoor" if site.startswith("Setup") else site.split("-")[0]


def guard():
    """One process; 08:00-23:00; at least 7 GB free (A3 section 6)."""
    now = dt.datetime.now().time()
    if not (dt.time(8) <= now < dt.time(23)):
        sys.exit("outside the compute window")
    free = psutil.virtual_memory().available / 2**30
    if free < 7.0:
        sys.exit(f"only {free:.1f} GB free")


def fin(x):
    return None if x is None or not math.isfinite(x) else float(x)


def whole_days(h):
    days = h.size // DAY
    return h[: days * DAY], days


def p90(values):
    """Smallest value with at least 90 % of the values at or below it; inf ranks last (A3 section 2)."""
    v = sorted(values, key=lambda x: (not math.isfinite(x), x))
    return v[math.ceil(0.9 * len(v)) - 1]


def median_inf(values):
    """Median with inf ranked last; the upper of the two middle values if one of them is inf."""
    v = sorted(values, key=lambda x: (not math.isfinite(x), x))
    n = len(v)
    if n % 2:
        return v[n // 2]
    a, b = v[n // 2 - 1], v[n // 2]
    return b if not math.isfinite(b) else 0.5 * (a + b)


def drop_worst(h, r, l, a, L):
    """Delete the L cyclic days with the smallest total net income; return remaining series and the window start."""
    h, days = whole_days(h)
    if days <= L:
        return None, None
    e = 1.0 + l + a * (r - 1.0)
    net = (h.reshape(days, DAY) - e).sum(1)
    w = [float(np.take(net, range(d, d + L), mode="wrap").sum()) for d in range(days)]
    start = int(np.argmin(w))           # first minimum on ties
    gone = {(start + i) % days for i in range(L)}
    keep = [d for d in range(days) if d not in gone]
    return h.reshape(days, DAY)[keep].ravel(), start


def part_worst():
    rows = []
    for site, sea in T.cells():
        g, meta = T.season_series(site, sea, split="all")
        for m in cfg.M_LEVELS:
            h = T.scale_panel(g, R_A, L_A, m)
            hw, days = whole_days(h)
            c0 = E.C_periodic(hw, N_SUB, R_A, L_A, A)
            rec = {"site": site, "season": sea, "group": g4(site), "m": m, "days": days, "Cstar": fin(c0)}
            for L in LENGTHS:
                hd, start = drop_worst(h, R_A, L_A, A, L)
                c1 = np.nan if hd is None else E.C_periodic(hd, N_SUB, R_A, L_A, A)
                rec[f"L{L}"] = {"start_day": start, "Cstar_drop": fin(c1),
                                "ratio": fin(c1 / c0) if hd is not None and math.isfinite(c0) and c0 > 0 else None}
            rows.append(rec)
    summ = {}
    for m in cfg.M_LEVELS:
        for L in LENGTHS:
            s = {}
            for grp in GROUPS + ("all",):
                v = [x[f"L{L}"]["ratio"] for x in rows if x["m"] == m and (grp == "all" or x["group"] == grp)
                     and x[f"L{L}"]["ratio"] is not None]
                s[grp] = {"n": len(v), "median": float(np.median(v)), "min": float(np.min(v)), "max": float(np.max(v))}
            summ[f"m{m}_L{L}"] = s
    return {"amendment": "A3 section 3", "node": {"r": R_A, "l": L_A, "K": K}, "split": "all", "summary": summ,
            "rows": rows}


def part_ranges():
    b = json.loads((cfg.RES / "summary_test.json").read_text())["main"]["baselines"]
    cell = defaultdict(lambda: defaultdict(list))
    for x in b:
        for k in RATIOS:
            if x[k] is not None and math.isfinite(x[k]):
                cell[(x["site"], x["season"])][k].append(float(x[k]))
    rows = []
    for (site, sea), d in cell.items():
        rows.append({"site": site, "season": sea, "group": g4(site),
                     **{k: {"n": len(d[k]), "median": float(np.median(d[k])), "min": float(np.min(d[k])),
                            "max": float(np.max(d[k]))} for k in RATIOS if d[k]}})
    groups = {}
    for grp in GROUPS:
        groups[grp] = {}
        for k in RATIOS:
            v = [x[k]["median"] for x in rows if x["group"] == grp and k in x]
            groups[grp][k] = {"n_cells": len(v), "median_of_cells_min": float(np.min(v)),
                              "median_of_cells_max": float(np.max(v))}
    return {"amendment": "A3 section 4", "source": "results/summary_test.json main.baselines", "split": "test",
            "groups": groups, "rows": rows}


def k_of(g_tr, g_te, r, l, m):
    h_tr = T.scale_panel(g_tr, r, l, m)
    scale = float(h_tr.sum() / g_tr.sum())
    c_tr = E.C_periodic(whole_days(h_tr)[0], N_SUB, r, l, A)
    c_te = E.C_periodic(whole_days(g_te * scale)[0], N_SUB, r, l, A)
    if not math.isfinite(c_tr):
        return None, c_tr, c_te
    return (c_te / c_tr if math.isfinite(c_te) else math.inf), c_tr, c_te


def stat(values):
    finite = [v for v in values if math.isfinite(v)]
    return {"n": len(values), "median": fin(median_inf(values)), "p90": fin(p90(values)),
            "max": fin(max(values)), "share_gt1": float(np.mean([v > 1 for v in values])),
            "n_inf": len(values) - len(finite), "median_is_inf": not math.isfinite(median_inf(values)),
            "p90_is_inf": not math.isfinite(p90(values))}


def part_margin():
    rows, excluded, grid = [], [], defaultdict(list)
    for site, sea in T.cells():
        try:
            g_tr, _ = T.season_series(site, sea, split="train")
            g_te, _ = T.season_series(site, sea, split="test")
        except ValueError as ex:
            excluded.append({"site": site, "season": sea, "reason": str(ex)})
            continue
        for m in cfg.M_LEVELS:
            k, c_tr, c_te = k_of(g_tr, g_te, R_A, L_A, m)
            if k is None:
                excluded.append({"site": site, "season": sea, "m": m, "reason": "C_TRAIN infinite"})
                continue
            rows.append({"site": site, "season": sea, "group": g4(site), "m": m, "C_TRAIN": fin(c_tr),
                         "C_TEST": fin(c_te), "k": fin(k), "k_inf": not math.isfinite(k)})
        for r in cfg.R_LEVELS:
            for l in cfg.L_LEVELS:
                for m in cfg.M_LEVELS:
                    k, _, _ = k_of(g_tr, g_te, r, l, m)
                    if k is not None:
                        grid[(site, sea)].append(k)
    val = lambda x: math.inf if x["k_inf"] else x["k"]  # noqa: E731
    summ = {f"m{m}": {grp: stat([val(x) for x in rows if x["m"] == m and (grp == "all" or x["group"] == grp)])
                      for grp in GROUPS + ("all",)} for m in cfg.M_LEVELS}
    per_cell = [median_inf(v) for v in grid.values()]
    return {"amendment": "A3 section 5", "node": {"r": R_A, "l": L_A, "K": K}, "panel": "scaled on TRAIN months only",
            "summary": summ, "grid_per_cell_median": stat(per_cell), "excluded": excluded, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="all", choices=["worst", "ranges", "margin", "all"])
    a = ap.parse_args()
    guard()
    todo = {"worst": ("a3_worst_spell.json", part_worst), "ranges": ("a3_per_cell_ranges.json", part_ranges),
            "margin": ("a3_margin_k.json", part_margin)}
    for k, (name, fn) in todo.items():
        if a.part in (k, "all"):
            out = fn()
            (cfg.RES / name).write_text(json.dumps(out, indent=1), encoding="utf-8")
            print(name, "written", flush=True)


if __name__ == "__main__":
    main()
