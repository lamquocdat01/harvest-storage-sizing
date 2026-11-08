"""Viec 3 (P3R): per-case check of Kansal-EWMA against periodic at Kansal's measured mean activation (E1, TEST v2).

Exploratory and post hoc (PREREG v1.1 E1 stays FAIL as scored). No simulation: every field is read from the v2
checkpoints of the exploratory stage (grid_ckpt_v2/exploratory_q2/test, read only), written by sim40.explore_q2
with seed 42. A "case" is one (site, season, r, l, m, C) row; the E1 population is the H5 population
(0 < outage of blackout_K8 < 1), as in explore_q2.analyze.

Columns (per case): pi_per = outage of per_abarK, pi_K = outage of kansal_ewma; a_K = realised mean activation of
kansal_ewma (all slots, outages included); a_per_set = the rate periodic was set to (= a_K); a_per_real = realised
mean activation of per_abarK, also a_K (1 - pi_per); eps*(a_K), eps*(a_per_real); miss of both policies by
replay (1e5 real events) and analytic (rate histogram); SE of the replay, sqrt(m (1 - m) / 1e5).
Checks
  K1  miss_K(replay) >= eps*(a_K) - 3 SE_K in every case (Theorem 1 for an oblivious controller)
  K2  cases with pi_per = 0 (all cases, E1 population or not): analytic miss_per = eps*(a_K) within 1e-9, and miss_K(replay) - miss_per >= -3 SE
  K3  among cases with miss_K - miss_per < -0.005 (replay), the share with pi_per > 0; distribution of
      eps*(a_per_real) - eps*(a_K)
Usage: python P3R/kansal_check.py  -> P3R/KANSAL_CHECK_40.csv, P3R/kansal_check_summary.json,
       results/kansal_check_test.json (same summary, for the paper build)
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import numpy as np

TOPIC = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOPIC / "code"))
from sim40 import config as cfg          # noqa: E402
from sim40.events import law_for         # noqa: E402

N_EV = 100_000
SRC = cfg.CKPT / "exploratory_q2" / "test"
OUT = pathlib.Path(__file__).resolve().parent   # P3R/ in the topic folder, checks/ in the repository (P0R2 m6)


def se(m):
    return float(np.sqrt(max(m * (1 - m), 0.0) / N_EV))


def main():
    law = law_for("test")
    es = lambda a: float(law.eps_star(a)[0])  # noqa: E731
    rows = []
    for f in sorted(SRC.glob("*.json")):
        R = json.loads(f.read_text())
        for row in R["rows"]:
            p = row["policies"]
            k, q, b = p["kansal_ewma"], p["per_abarK"], p["blackout_K8"]
            aK = k["a_bar"]
            rec = {"site": R["site"], "season": R["season"], "r": R["r"], "l": R["l"], "m": R["m"], "C": row["C"],
                   "C_rel": row["C"] / R["C_per8"] if R["C_per8"] else None,
                   "E1_population": bool(0 < b["outage"] < 1),
                   "pi_per": q["outage"], "pi_K": k["outage"], "a_K": aK, "a_per_set": q.get("a_set"),
                   "a_per_real": q["a_bar"], "a_K_times_1_minus_pi_per": aK * (1 - q["outage"]),
                   "eps_aK": es(aK), "eps_a_per_real": es(q["a_bar"]),
                   "miss_K_replay": k["replay"], "miss_K_analytic": k["miss"],
                   "miss_per_replay": q["replay"], "miss_per_analytic": q["miss"],
                   "SE_K": se(k["replay"]), "SE_per": se(q["replay"])}
            rec["d_replay"] = rec["miss_K_replay"] - rec["miss_per_replay"]
            rec["d_analytic"] = rec["miss_K_analytic"] - rec["miss_per_analytic"]
            rec["SE_d"] = float(np.hypot(rec["SE_K"], rec["SE_per"]))
            rec["floor_P1_per"] = rec["pi_per"] + (1 - rec["pi_per"]) * rec["eps_aK"] if rec["pi_per"] < 1 else 1.0
            rec["K1_ok"] = rec["miss_K_replay"] >= rec["eps_aK"] - 3 * rec["SE_K"]
            rec["K1_analytic_ok"] = rec["miss_K_analytic"] >= rec["eps_aK"] - 1e-12
            rows.append(rec)
    E1 = [x for x in rows if x["E1_population"]]
    K1_all = [x for x in rows if not x["K1_ok"]]
    K1_E1 = [x for x in E1 if not x["K1_ok"]]
    nopi = [x for x in rows if x["pi_per"] < 1e-12]          # K2 over every case (the E1 population has none)
    K2_floor = [x for x in nopi if abs(x["miss_per_analytic"] - x["eps_aK"]) > 1e-9]           # literal (unrounded a_K)
    # metrics.rate_histogram rounds rates to 6 decimals before Psi; the stored analytic miss is eps*(round(a_K, 6))
    K2_floor_rnd = [x for x in nopi if abs(x["miss_per_analytic"] - es(round(x["a_K"], 6))) > 1e-9]
    K2_win = [x for x in nopi if x["miss_K_replay"] - x["miss_per_analytic"] < -3 * x["SE_K"]]
    win = [x for x in E1 if x["d_replay"] < -0.005]
    gap = np.array([x["eps_a_per_real"] - x["eps_aK"] for x in E1])
    gap_win = np.array([x["eps_a_per_real"] - x["eps_aK"] for x in win])
    q = lambda v: {"n": int(len(v)), "min": float(np.min(v)), "p25": float(np.percentile(v, 25)), "median": float(np.median(v)),  # noqa: E731
                   "p75": float(np.percentile(v, 75)), "max": float(np.max(v))} if len(v) else {"n": 0}
    # does the realised-rate gap explain the win?  d versus -(eps*(a_per_real) - eps*(a_K))
    d_w = np.array([x["d_replay"] for x in win])
    expl = np.array([x["miss_K_replay"] - x["floor_P1_per"] for x in win])
    beats_P1_floor = int(np.sum(np.array([x["miss_K_replay"] for x in win]) < np.array([x["miss_per_replay"] for x in win])))
    by_layer = {}
    for x in E1:
        by_layer.setdefault(f"{x['site']} {x['season']}", []).append(x)
    layers = {k: {"n": len(v), "median_d": float(np.median([y["d_replay"] for y in v])),
                  "median_pi_per": float(np.median([y["pi_per"] for y in v])),
                  "median_pi_K": float(np.median([y["pi_K"] for y in v])),
                  "share_win": float(np.mean([y["d_replay"] < -0.005 for y in v])),
                  "share_win_with_pi_per_gt0": (float(np.mean([y["pi_per"] > 0 for y in v if y["d_replay"] < -0.005]))
                                                 if any(y["d_replay"] < -0.005 for y in v) else None)} for k, v in sorted(by_layer.items())}
    summ = {"source": str(SRC), "n_cases_all": len(rows), "n_cases_E1": len(E1),
            "K1": {"pass": len(K1_all) == 0, "n_fail_all": len(K1_all), "n_fail_E1": len(K1_E1),
                   "analytic_fail": sum(not x["K1_analytic_ok"] for x in rows),
                   "min_margin_in_SE": float(min((x["miss_K_replay"] - x["eps_aK"]) / max(x["SE_K"], 1e-12) for x in rows))},
            "K2": {"n_cases_pi_per_0": len(nopi), "pass_literal": len(K2_floor) == 0 and len(K2_win) == 0,
                   "pass": len(K2_floor_rnd) == 0 and len(K2_win) == 0,
                   "pass_note": "pass = floor part checked against eps*(round(a_K, 6)), the rate the analytic miss is computed at "
                                "(metrics.rate_histogram rounds rates to 1e-6); pass_literal = against eps*(a_K) unrounded",
                   "n_floor_mismatch_literal": len(K2_floor), "n_floor_mismatch_rounding_aware": len(K2_floor_rnd),
                   "n_kansal_wins_beyond_3SE": len(K2_win),
                   "max_abs_floor_mismatch": float(max((abs(x["miss_per_analytic"] - x["eps_aK"]) for x in nopi), default=0.0))},
            "K3": {"n_kansal_wins_gt_0.005": len(win), "share_with_pi_per_gt0": float(np.mean([x["pi_per"] > 0 for x in win])) if win else None,
                   "eps_gap_real_minus_aK_all_E1": q(gap), "eps_gap_real_minus_aK_wins": q(gap_win),
                   "median_d_wins": float(np.median(d_w)) if win else None,
                   "kansal_minus_P1floor_per_wins": q(expl), "n_wins_kansal_below_per_replay": beats_P1_floor},
            "outage": {"median_pi_per_minus_pi_K_E1": float(np.median([x["pi_per"] - x["pi_K"] for x in E1])),
                       "share_pi_K_gt_pi_per_E1": float(np.mean([x["pi_K"] > x["pi_per"] for x in E1])),
                       "median_pi_per_E1": float(np.median([x["pi_per"] for x in E1])),
                       "median_pi_K_E1": float(np.median([x["pi_K"] for x in E1]))},
            "rates": {"median_a_K_over_a_per_real_E1": float(np.median([x["a_K"] / max(x["a_per_real"], 1e-12) for x in E1])),
                      "max_abs_a_per_real_minus_aK_1_minus_pi": float(max(abs(x["a_per_real"] - x["a_K_times_1_minus_pi_per"]) for x in E1))},
            "median_d_replay_E1": float(np.median([x["d_replay"] for x in E1])),
            "layers_25": layers}
    keys = list(rows[0].keys())
    with open(OUT / "KANSAL_CHECK_40.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, keys)
        w.writeheader()
        w.writerows(rows)
    (OUT / "kansal_check_summary.json").write_text(json.dumps(summ, indent=1, default=float), encoding="utf-8")
    (cfg.RES / "kansal_check_test.json").write_text(json.dumps(summ, indent=1, default=float), encoding="utf-8")   # new file (P3R)
    print(json.dumps({k: summ[k] for k in ("n_cases_all", "n_cases_E1", "K1", "K2", "K3", "outage", "rates", "median_d_replay_E1")},
                     indent=1, default=float))
    if not (summ["K1"]["pass"] and summ["K2"]["pass"]):
        print("STOP: K1 or K2 failed (Viec 3 stops; report verbatim)")
        sys.exit(2)


if __name__ == "__main__":
    main()
