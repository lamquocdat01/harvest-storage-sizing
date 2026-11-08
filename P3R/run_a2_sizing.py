"""Amendment A2 (prereg/AMENDMENT_LOG.md, tag prereg-40-a2): sandwich brackets and exact miss of the taut string.

Parts
  --part time3     time 3 combinations (all eps), print an estimate for the split; writes nothing
  --part sizing    every frontier combination of the split (same cells and eps as v2 eps_sizing); one checkpoint
                   per combination in $THS_DATASETS/_derived/40/a2_ckpt/<split>/; resumable
  --part boot      H4d under A2: the 6 bootstrap cells of sim40.bootstrap, the same 7-day block resamples (seed-42
                   generator of run_boot replayed in its original order), B_ts = 100, exact feasibility
  --part analyze   results/a2_sizing_<split>.json (+ registered H4a-H4d next to the A2 column)
Reads the v2 frontier checkpoints (grid_ckpt_v2/frontier/<split>/) and results/*.json read-only; writes nothing there.
Guards: one process; stops before a combination when free RAM < 7 GB, and stops inside the 23:00-08:00 window
before 13-11-2026 12:00 (reserved for another measurement on this machine). Rerun the same command to resume.
Usage: python P3R/run_a2_sizing.py --split test --part sizing
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import time

import numpy as np
import psutil

TOPIC = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOPIC / "code"))

from sim40 import config as cfg                                   # noqa: E402
from sim40 import energy as E                                     # noqa: E402
from sim40 import metrics as M                                    # noqa: E402
from sim40 import policies as P                                   # noqa: E402
from sim40 import traces as T                                     # noqa: E402
from sim40.bootstrap import TS_CELLS, boot_p_sign, ci, day_block_resample, holm   # noqa: E402
from sim40.events import law_for                                  # noqa: E402
from sim40.miss_exact import PHASE, exact_miss                    # noqa: E402
from sim40.run_grid import baselines, combos                      # noqa: E402
from sim40.score_prereg import GROUPS, frac, g4, med_by           # noqa: E402

A2CK = cfg.DS / "_derived" / "40" / "a2_ckpt"
V2_FRONTIER = cfg.CKPT / "frontier"                               # read only
RAM_MIN_GB = 7.0
TOL = 0.01
NO_OUTAGE = 1e-9
QUIET_END = dt.datetime(2026, 11, 13, 12, 0)


def guard():
    """None if a combination may start now, else the reason to stop."""
    now = dt.datetime.now()
    if now < QUIET_END and (now.hour >= 23 or now.hour < 8):
        return f"quiet window 23:00-08:00 (now {now:%H:%M})"
    free = psutil.virtual_memory().available / 2**30
    if free < RAM_MIN_GB:
        return f"free RAM {free:.1f} GB < {RAM_MIN_GB} GB"
    return None


def name(c):
    s, sea, r, l, m = c
    return f"{s}_{sea}_r{r}_l{l}_m{m}.json"


def fin(x):
    return x is not None and np.isfinite(x)


# ------------------------------------------------------------------ brackets
def lb_bounds(h, r, l, a_target, C_hi):
    """The bisection of energy.C_for_amax (same iterations), returning both ends."""
    if not (E.amax_of_C(h, P.N_SUB, r, l, C_hi) >= a_target):
        return np.inf, np.inf
    lo, hi = 0.0, C_hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if E.amax_of_C(h, P.N_SUB, r, l, mid) >= a_target:
            hi = mid
        else:
            lo = mid
        if hi - lo <= TOL * hi:
            break
    return lo, hi


def ts_eval(h, r, l, C, law):
    """Realised taut-string schedule at C: exact miss, surrogate miss, outage, realised rate."""
    x = P.taut(h, r, l, C)
    if x is None:
        return None
    on, rt = x
    ex, det = exact_miss(on, rt, law, n=P.N_SUB, phase=PHASE, return_detail=True)
    sur = M.miss_from_hist(*M.rate_histogram(on, rt), law)
    return {"miss_exact": ex, "miss_sur": sur, "outage": float(1.0 - np.mean(on)), "a_real": det.get("a_real", 0.0)}


def feasible(ev, eps):
    return ev is not None and ev["outage"] < NO_OUTAGE and ev["miss_exact"] <= eps


def ts_exact_hi(h, r, l, law, eps, start, C_hi0):
    """Upper end of a bisection whose upper end is always verified feasible (A2 sec. 2)."""
    n_eval = 0
    hi = start if fin(start) else None
    if hi is not None:
        ev = ts_eval(h, r, l, hi, law)
        n_eval += 1
        while not feasible(ev, eps):
            hi *= 1.25
            if hi > C_hi0:
                return np.inf, None, n_eval
            ev = ts_eval(h, r, l, hi, law)
            n_eval += 1
    else:
        return np.inf, None, n_eval
    ev_hi = ev
    lo = 0.0
    for _ in range(60):
        if hi - lo <= TOL * hi:
            break
        mid = 0.5 * (lo + hi)
        ev = ts_eval(h, r, l, mid, law)
        n_eval += 1
        if feasible(ev, eps):
            hi, ev_hi = mid, ev
        else:
            lo = mid
    return hi, ev_hi, n_eval


# ------------------------------------------------------------------ sizing part
def run_combo(c, split):
    site, sea, r, l, m = c
    v2 = json.loads((V2_FRONTIER / split / name(c)).read_text())
    law = law_for(split)
    g, _ = T.season_series(site, sea, split=split)
    h = T.scale_panel(g, r, l, m)
    b = baselines(h, r, l)["C_star"]
    C_hi0 = 50 * b if np.isfinite(b) else 1e12
    out = {"site": site, "season": sea, "r": r, "l": l, "m": m, "split": split, "a_bal": v2["a_bal"], "eps": {}}
    for e, rec in v2["eps_sizing"].items():
        eps = float(e)
        a_e = rec["a_eps"]
        row = {"a_eps": a_e, "C_per": rec.get("C_per"), "C_LB_v2": rec.get("C_LB"), "C_TS_sur_hi": rec.get("C_TS")}
        if rec.get("note") or not fin(a_e) or a_e > v2["a_bal"]:
            row.update({"C_LB_lo": None, "C_LB_hi": None, "C_TS_exact_hi": None, "note": "a_eps > energy balance"})
            out["eps"][e] = row
            continue
        lo, hi = lb_bounds(h, r, l, a_e, C_hi0)
        row["C_LB_lo"], row["C_LB_hi"] = (lo if fin(lo) else None), (hi if fin(hi) else None)
        row["C_LB_hi_equals_v2"] = bool(fin(hi) and fin(rec.get("C_LB")) and abs(hi - rec["C_LB"]) <= 1e-9 * hi)
        sur = rec.get("C_TS")
        if fin(sur):
            ev = ts_eval(h, r, l, sur, law)
            row["at_sur_hi"] = ev
            row["sur_hi_feasible_exact"] = feasible(ev, eps)
            start = sur
        else:
            row["at_sur_hi"], row["sur_hi_feasible_exact"] = None, None
            cp = rec.get("C_per")
            start = cp * 1.01 if fin(cp) else None
        Cx, evx, ne = ts_exact_hi(h, r, l, law, eps, start, C_hi0)
        row["C_TS_exact_hi"] = Cx if fin(Cx) else None
        row["at_exact_hi"] = evx
        row["outage_at_exact_hi"] = evx["outage"] if evx else None
        row["abs_exact_minus_sur"] = abs(evx["miss_exact"] - evx["miss_sur"]) if evx else None
        row["n_eval"] = ne
        out["eps"][e] = row
    return out


def part_sizing(split, limit=0, todo=None):
    d = A2CK / split
    d.mkdir(parents=True, exist_ok=True)
    todo = todo if todo is not None else [c for c in combos("frontier") if not (d / name(c)).exists()]
    if limit:
        todo = todo[:limit]
    print(f"A2 sizing/{split}: {len(todo)} combinations to run", flush=True)
    t0 = time.time()
    for i, c in enumerate(todo, 1):
        why = guard()
        if why:
            print(f"STOP before {name(c)}: {why}; {i - 1} done in this call; rerun to resume", flush=True)
            return 3
        t = time.time()
        res = run_combo(c, split)
        res["elapsed_s"] = time.time() - t
        (d / name(c)).write_text(json.dumps(res, default=lambda o: None if (isinstance(o, float) and not np.isfinite(o)) else float(o)))
        if i % 10 == 0 or i == len(todo):
            el = time.time() - t0
            print(f"  {i}/{len(todo)}  {el / 60:.1f} min  eta {el / i * (len(todo) - i) / 60:.1f} min", flush=True)
    return 0


def part_time3(split):
    cs = combos("frontier")
    pick = [cs[0], cs[len(cs) // 2], cs[-1]]
    ts = []
    for c in pick:
        t = time.time()
        run_combo(c, split)
        ts.append(time.time() - t)
        print(f"  {name(c)}: {ts[-1]:.1f} s", flush=True)
    est = np.mean(ts) * len(cs) / 3600
    print(f"mean {np.mean(ts):.1f} s per combination; {len(cs)} combinations -> about {est:.1f} h", flush=True)
    return {"combos": [name(c) for c in pick], "seconds": ts, "estimate_h": est, "n": len(cs)}


# ------------------------------------------------------------------ H4d under A2
def part_boot(split, r=15.0, l=0.04, m=0.25, K=8, B=cfg.B_BOOT, B_ts=100):
    law = law_for(split)
    a = 1.0 / K
    eps_a2 = float(law.eps_star(a)[0]) + 1e-4
    eps_reg = float(law.eps_star(a)[0]) + 1e-9
    rng = np.random.default_rng(cfg.SEED)                 # replays bootstrap.run_boot's generator
    cells = []
    for site, sea in T.cells():
        why = guard()
        if why:
            print(f"STOP in boot at {site} {sea}: {why}; rerun (boot restarts from the first cell)", flush=True)
            return 3
        g, _ = T.season_series(site, sea, split=split)
        h = T.scale_panel(g, r, l, m)
        for _ in range(B):                                 # the dC block bootstrap of run_boot (consumes rng only)
            day_block_resample(h, rng)
        if (site, sea) not in TS_CELLS:
            continue

        def ratio(hh):
            cp = E.C_periodic(hh, P.N_SUB, r, l, a)
            if not np.isfinite(cp):
                return np.nan, None
            C, ev, _ = ts_exact_hi(hh, r, l, law, eps_a2, cp * 1.01, cp * 1.01)
            return (C / cp if fin(C) else np.inf), ev
        x0, ev0 = ratio(h)
        tb, reg_ok = [], []
        for _ in range(B_ts):
            xb, evb = ratio(day_block_resample(h, rng))
            tb.append(xb)
            reg_ok.append(bool(evb is not None and evb["miss_exact"] <= eps_reg))
        cells.append({"site": site, "season": sea, "TS_over_per_A2": x0, "TS_over_per_A2_ci": ci(tb),
                      "p_TS_ge_per_A2": boot_p_sign([1 - x for x in tb], +1),
                      "share_feasible_at_eps_plus_1e-9": float(np.mean(reg_ok)),
                      "miss_exact_point": ev0["miss_exact"] if ev0 else None})
        print(site, sea, round(x0, 4), flush=True)
    b2 = json.loads((cfg.RES / f"boot_{split}.json").read_text())
    nc = len(b2["cells"])
    ps = [c["p_dmiss_le0"] for c in b2["cells"]] + [c["p_dC_ge0"] for c in b2["cells"]] + [c["p_TS_ge_per_A2"] for c in cells]
    rej = holm(ps)
    r_ts = rej[2 * nc:]
    out = {"split": split, "B": B, "B_ts": B_ts, "eps_target": eps_a2, "eps_target_note": "eps*(1/8) + 1e-4 (A2 sec. 4)",
           "cells": cells, "holm_n_tests": len(ps), "holm_ts_rejected": [bool(x) for x in r_ts],
           "H4d_A2": "PASS" if (len(cells) == 6 and bool(np.all(r_ts)) and all(c["TS_over_per_A2"] < 1 for c in cells)) else "FAIL"}
    d = A2CK / split
    d.mkdir(parents=True, exist_ok=True)
    (d / "_boot_H4d.json").write_text(json.dumps(out, indent=1, default=float))
    print(out["H4d_A2"], flush=True)
    return 0


# ------------------------------------------------------------------ analyze
def part_analyze(split):
    d = A2CK / split
    files = sorted(f for f in d.glob("*.json") if not f.name.startswith("_"))
    rows = []
    for f in files:
        R = json.loads(f.read_text())
        for e, v in R["eps"].items():
            rows.append({k: R[k] for k in ("site", "season", "r", "l", "m")} | {"eps": float(e)} | v)
    n_comb = len(files)
    fin_rows = [x for x in rows if fin(x.get("C_LB_lo")) and fin(x.get("C_TS_exact_hi"))]
    lbts = [x["C_LB_lo"] / x["C_TS_exact_hi"] for x in fin_rows]
    viol = [x for x in fin_rows if x["C_LB_lo"] > x["C_TS_exact_hi"]]
    absd = np.array([x["abs_exact_minus_sur"] for x in rows if x.get("abs_exact_minus_sur") is not None])
    sur_bad = [x for x in rows if x.get("sur_hi_feasible_exact") is False]
    outage_exact = [x for x in rows if x.get("outage_at_exact_hi") not in (None, 0.0) and x["outage_at_exact_hi"] >= NO_OUTAGE]
    for x in rows:
        cp = x.get("C_per")
        x["TS_over_per"] = x["C_TS_exact_hi"] / cp if fin(x.get("C_TS_exact_hi")) and fin(cp) else (np.inf if fin(cp) else None)
        x["LB_over_TS"] = x["C_LB_lo"] / x["C_TS_exact_hi"] if fin(x.get("C_LB_lo")) and fin(x.get("C_TS_exact_hi")) else None
    # H4a-H4c, A2 column (same thresholds as PREREG v1)
    f_a, n_a = frac([x["TS_over_per"] for x in rows], lambda v: v < 1)
    md = {str(e): med_by([x for x in rows if x["eps"] == e], "TS_over_per") for e in (0.5, 0.6)}
    H4a = {"verdict": "PASS" if (f_a >= 0.95 and all(0.2 <= v.get(g, np.nan) <= 0.7 for v in md.values() for g in GROUPS)) else "FAIL",
           "share_lt1": f_a, "n": n_a, "medians": md}
    f_b, n_b = frac([x["LB_over_TS"] for x in rows], lambda v: v <= 1.02)
    H4b = {"verdict": "PASS" if f_b == 1.0 else "FAIL", "share_le_1_02": f_b, "n": n_b,
           "max": float(np.max(lbts)) if lbts else None}
    eps_hi = sorted(e for e in set(x["eps"] for x in rows) if e >= 0.6 - 1e-9)
    hi = {str(e): med_by([x for x in rows if x["eps"] == e], "LB_over_TS") for e in eps_hi}
    lo = med_by([x for x in rows if abs(x["eps"] - 0.45) < 1e-9], "LB_over_TS")
    H4c = {"verdict": "PASS" if (all(v[g] >= 0.9 for v in hi.values() for g in v) and sum(lo.get(g, 1) < 0.9 for g in GROUPS) >= 3) else "FAIL",
           "medians_eps_ge_0_6": hi, "medians_eps_0_45": lo}
    bfile = d / "_boot_H4d.json"
    H4d = json.loads(bfile.read_text()) if bfile.exists() else None
    reg = json.loads((cfg.RES / f"prereg_score_{split}.json").read_text())
    q = lambda v, p: float(np.percentile(v, p)) if len(v) else None  # noqa: E731
    out = {"split": split, "amendment": "A2 (prereg/AMENDMENT_LOG.md, tag prereg-40-a2)", "phase": PHASE, "tol": TOL,
           "n_combinations": n_comb, "n_cells": len(rows), "n_cells_finite": len(fin_rows),
           "n_cells_infinite_a_eps_gt_a_bal": sum(1 for x in rows if x.get("note")),
           "PASS_no_cell_C_LB_lo_gt_C_TS_exact": len(viol) == 0, "n_violations": len(viol),
           "violations": [{k: x[k] for k in ("site", "season", "r", "l", "m", "eps", "C_LB_lo", "C_TS_exact_hi")} for x in viol],
           "max_LB_lo_over_TS_exact": float(np.max(lbts)) if lbts else None,
           "median_LB_lo_over_TS_exact": float(np.median(lbts)) if lbts else None,
           "abs_exact_minus_sur": {"n": int(absd.size), "median": q(absd, 50), "p90": q(absd, 90), "p99": q(absd, 99),
                                   "max": float(absd.max()) if absd.size else None},
           "n_sur_hi_infeasible_exact": len(sur_bad),
           "sur_hi_infeasible_reason": {"miss_exact_gt_eps": sum(1 for x in sur_bad if x["at_sur_hi"] and x["at_sur_hi"]["miss_exact"] > x["eps"]),
                                        "outage": sum(1 for x in sur_bad if x["at_sur_hi"] and x["at_sur_hi"]["outage"] >= NO_OUTAGE),
                                        "no_schedule": sum(1 for x in sur_bad if not x["at_sur_hi"])},
           "n_outage_at_exact_hi": len(outage_exact),
           "C_LB_hi_equals_v2_share": float(np.mean([x["C_LB_hi_equals_v2"] for x in rows if "C_LB_hi_equals_v2" in x])) if rows else None,
           "TS_exact_over_sur": {"median": q([x["C_TS_exact_hi"] / x["C_TS_sur_hi"] for x in rows if fin(x.get("C_TS_exact_hi")) and fin(x.get("C_TS_sur_hi"))], 50),
                                 "max": float(np.max([x["C_TS_exact_hi"] / x["C_TS_sur_hi"] for x in rows if fin(x.get("C_TS_exact_hi")) and fin(x.get("C_TS_sur_hi"))] or [np.nan]))},
           "H4_registered": {k: reg[k]["verdict"] for k in ("H4a", "H4b", "H4c", "H4d")},
           "H4_A2": {"H4a": H4a, "H4b": H4b, "H4c": H4c, "H4d": H4d}}
    out["H4_A2_verdicts"] = {"H4a": H4a["verdict"], "H4b": H4b["verdict"], "H4c": H4c["verdict"],
                             "H4d": H4d["H4d_A2"] if H4d else "NOT RUN"}
    keep = ("site", "season", "r", "l", "m", "eps", "a_eps", "C_per", "C_LB_lo", "C_LB_hi", "C_TS_sur_hi",
            "sur_hi_feasible_exact", "C_TS_exact_hi", "outage_at_exact_hi", "abs_exact_minus_sur", "n_eval", "note")
    out["cells"] = [{k: x.get(k) for k in keep} | {
        "miss_exact_at_sur_hi": (x.get("at_sur_hi") or {}).get("miss_exact"),
        "miss_exact_at_exact_hi": (x.get("at_exact_hi") or {}).get("miss_exact"),
        "miss_sur_at_exact_hi": (x.get("at_exact_hi") or {}).get("miss_sur")} for x in rows]
    (cfg.RES / f"a2_sizing_{split}.json").write_text(json.dumps(out, indent=1, default=lambda o: None if (isinstance(o, float) and not np.isfinite(o)) else float(o)))
    print(json.dumps({k: out[k] for k in ("n_combinations", "n_cells", "n_cells_finite", "PASS_no_cell_C_LB_lo_gt_C_TS_exact",
                                          "max_LB_lo_over_TS_exact", "abs_exact_minus_sur", "n_sur_hi_infeasible_exact",
                                          "H4_registered", "H4_A2_verdicts")}, indent=1, default=str))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["test", "train"])
    ap.add_argument("--part", required=True, choices=["time3", "sizing", "boot", "analyze"])
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if a.part != "analyze":
        why = guard()
        if why:
            print("not started:", why, flush=True)
            sys.exit(3)
    if a.part == "time3":
        print(json.dumps(part_time3(a.split), indent=1))
        return
    sys.exit({"sizing": lambda: part_sizing(a.split, a.limit), "boot": lambda: part_boot(a.split),
              "analyze": lambda: part_analyze(a.split)}[a.part]())


if __name__ == "__main__":
    main()
