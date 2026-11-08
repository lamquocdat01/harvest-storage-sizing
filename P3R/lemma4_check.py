"""Numerical check of Lemma 4 (taut string) on 3 TEST cells, for the self-contained proof in the supplement.

For each cell (r = 15, l = 0.04, m = 0.25, C = C*_per8 / 2) the tube of energy.taut_schedule is rebuilt
(rotation to the anchor t*, margin r - 1, monotone hull) and the code's taut string Y* is checked for
  (1) feasibility: Lhull <= Y* <= Uhull, fixed end points, non-decreasing;
  (2) the contact property of the proof: the slope increases only where Y* touches the upper hull and decreases
      only where it touches the lower hull (relative tolerance 1e-9 of the tube width);
  (3) optimality against other feasible paths of the same tube: sum Psi(rate) and sum of convex test functions
      (x - c)^+ for 5 thresholds c, against convex mixtures lambda Lhull + (1 - lambda) Uhull (lambda in
      {0.1, 0.5, 0.9}) and a random monotone path inside the tube.
Usage: python P3R/lemma4_check.py -> P3R/lemma4_check.json
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

TOPIC = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOPIC / "code"))
from sim40 import energy as E            # noqa: E402
from sim40 import policies as P          # noqa: E402
from sim40 import traces as T            # noqa: E402
from sim40.events import law_for         # noqa: E402

CELLS = (("Madrid-MSG", "DJF"), ("Uppsala-MSG", "DJF"), ("HCMC", "SON"))
R, L, MM = 15.0, 0.04, 0.25


def tube(h, n, r, l, C):
    """Same construction as energy.taut_schedule (rotation, margin, hull)."""
    J = h.size
    S0 = np.cumsum(n * (h - 1.0 - l))
    rot = (int(np.argmax(S0)) + 1) % J
    hr = np.r_[h[rot:], h[:rot]]
    S = np.r_[0.0, np.cumsum(n * (hr - 1.0 - l))]
    U = C + S - (r - 1.0)
    U[-1] = S[-1]
    Up = np.minimum.accumulate(U[::-1])[::-1]
    Lp = np.minimum(np.maximum.accumulate(S.copy()), Up)
    Lp[0] = Up[0] = 0.0
    return Lp, Up


def main():
    law = law_for("test")
    n = float(P.N_SUB)
    out = []
    rng = np.random.default_rng(42)
    for site, sea in CELLS:
        g, _ = T.season_series(site, sea, split="test")
        h = T.scale_panel(g, R, L, MM)
        C = 0.5 * E.C_periodic(h, P.N_SUB, R, L, 1 / 8)
        Lp, Up = tube(h, n, R, L, C)
        Y = E.taut_string(Lp, Up)
        width = np.maximum(Up - Lp, 1e-12)
        tol = 1e-9 * max(1.0, float(np.max(width)))
        feas = bool(np.all(Y >= Lp - tol) and np.all(Y <= Up + tol) and abs(Y[0]) <= tol and abs(Y[-1] - Up[-1]) <= tol)
        d = np.diff(Y)
        mono = bool(np.all(d >= -tol))
        ds = np.diff(d)                                    # slope change at interior nodes 1..J-1
        scale = max(1.0, float(np.max(np.abs(d))))
        inc = np.flatnonzero(ds > 1e-9 * scale) + 1
        dec = np.flatnonzero(ds < -1e-9 * scale) + 1
        up_ok = bool(np.all(np.abs(Y[inc] - Up[inc]) <= 1e-6 * max(1.0, float(np.max(np.abs(Up))))))
        lo_ok = bool(np.all(np.abs(Y[dec] - Lp[dec]) <= 1e-6 * max(1.0, float(np.max(np.abs(Up))))))
        unit = n * (R - 1.0)
        psi = lambda Z: float(law.psi(np.clip(np.diff(Z) / unit, 0, 1)).sum())  # noqa: E731
        conv = lambda Z, c: float(np.maximum(np.diff(Z) / unit - c, 0).sum())    # noqa: E731
        alts = {f"mix{lam}": lam * Lp + (1 - lam) * Up for lam in (0.1, 0.5, 0.9)}
        w = rng.random(Lp.size)                           # random monotone path: running max of a random point in the tube
        Z = np.maximum.accumulate(Lp + w * (Up - Lp))
        Z = np.minimum(Z, Up)
        Z[0], Z[-1] = 0.0, Up[-1]
        alts["random_monotone"] = Z
        cs = (0.02, 0.05, 0.1, 0.2, 0.5)
        res = {"site": site, "season": sea, "C": C, "J": int(Lp.size - 1), "feasible": feas, "non_decreasing": mono,
               "n_slope_increases": int(inc.size), "n_slope_decreases": int(dec.size),
               "increase_only_at_upper": up_ok, "decrease_only_at_lower": lo_ok, "sum_psi_taut": psi(Y),
               "alternatives": {}}
        allok = True
        for k, Zk in alts.items():
            okz = bool(np.all(Zk >= Lp - tol) and np.all(Zk <= Up + tol))
            dpsi = psi(Y) - psi(Zk)
            dconv = [conv(Zk, c) - conv(Y, c) for c in cs]
            res["alternatives"][k] = {"feasible": okz, "sum_psi_taut_minus_alt": dpsi, "convex_alt_minus_taut": dconv}
            allok &= (not okz) or (dpsi >= -1e-9 * abs(psi(Y)) and min(dconv) >= -1e-9)
        res["optimal_vs_alternatives"] = bool(allok)
        out.append(res)
        print(site, sea, feas, mono, up_ok, lo_ok, allok, flush=True)
    (TOPIC / "P3R" / "lemma4_check.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
