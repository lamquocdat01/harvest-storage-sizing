"""Interpolation sensitivity of the satellite traces (supplementary table; macro interpMax).

For 6 TEST cells, the satellite steps (10-30 min) are held on 1-min sub-steps by zero-order hold (the main
analysis) or by linear interpolation between interval midpoints with the daily integral preserved
(traces._to_substeps). On each version, at the design point r = 15, l = 0.04, m = 0.25, K = 8:
  Cstar_per8         storage need of periodic K = 8 (Corollary of Lemma 2)
  miss_per8_at_half  analytic miss of periodic K = 8 run at C = Cstar_per8 / 2 of the same version (outages)
  outage_at_half     its outage fraction
  rel_diff_Cstar     Cstar(linear) / Cstar(zoh) - 1  (energy only; does not depend on F_D)
Only miss_per8_at_half depends on the duration law (TEST videos).

This generator was written in P3R (07-11-2026): the file of 09-10-2026 had no generator in the repository. It is
validated by reproducing that file from the frozen v1 corpus (--law-csv results/_v1_corpus3713/event_corpus_40.csv
--out <tmp>), then run on the corrected corpus (default).
Usage: python -m sim40.interp_sensitivity [--law-csv CSV] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
import pandas as pd

from . import config as cfg
from . import energy as E
from . import metrics as M
from . import policies as P
from . import traces as T
from .events import DurationLaw, law_for, video_split

CELLS = (("HCMC", "SON"), ("Madrid-MSG", "DJF"), ("Madrid-SARAH3", "JJA"), ("Uppsala-MSG", "DJF"),
         ("Uppsala-SARAH3", "JJA"), ("HCMC", "MAM"))
R, L, MM, K = 15.0, 0.04, 0.25, 8


def test_law(csv=None):
    if csv is None:
        return law_for("test")
    ev = pd.read_csv(csv)
    tr = video_split(ev)
    key = ev.dataset + "/" + ev.video
    return DurationLaw(ev.duration.values[(~key.isin(tr)).values])


def one(site, season, interp, law):
    g, _ = T.season_series(site, season, interp=interp, split="test")
    h = T.scale_panel(g, R, L, MM)
    C = E.C_periodic(h, P.N_SUB, R, L, 1.0 / K)
    s = M.summarize(*P.periodic(h, R, L, 0.5 * C, K), law)
    return {"Cstar_per8": C, "miss_per8_at_half": s["miss"], "outage_at_half": s["outage_frac"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--law-csv", default=None)
    ap.add_argument("--out", default=str(cfg.RES / "interp_sensitivity_test.json"))
    a = ap.parse_args()
    law = test_law(a.law_csv)
    out = []
    for site, sea in CELLS:
        z, li = one(site, sea, "zoh", law), one(site, sea, "linear", law)
        out.append({"site": site, "season": sea, "zoh": z, "linear": li,
                    "rel_diff_Cstar": li["Cstar_per8"] / z["Cstar_per8"] - 1.0})
    pathlib.Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps([[x["site"], x["season"], round(x["zoh"]["miss_per8_at_half"], 4), round(x["rel_diff_Cstar"], 6)]
                      for x in out]))


if __name__ == "__main__":
    main()
