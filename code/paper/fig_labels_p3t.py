#!/usr/bin/env python3
"""fig_labels_p3t.py (topic 40, P3T, review item m8): redraw Figs. S1, S3, S5 of the supplement with typeset axis labels.
Uses the plotting functions of sim40.make_figs and sim40.make_figs_q2 unchanged, on the same result files; only the text
strings are mapped. Output goes to the figures folder of the TGCN build; results/figs is not written.
Usage: python code/paper/fig_labels_p3t.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "code"))

import matplotlib.text as mtext  # noqa: E402

MAP = {
    "C / C*_per(8)": r"capacity relative to periodic: $C\,/\,C^*_{\mathrm{per}}(8)$",
    r"$C\,/\,C^*_{per}(8)$": r"capacity relative to periodic: $C\,/\,C^*_{\mathrm{per}}(8)$",
    "cue cost c [e_idle/slot]": r"cue cost $c$ ($e_{\mathrm{idle}}$ per slot)",
    "gate outage at C*_per (median)": r"median gate outage at $C^*_{\mathrm{per}}$",
    "c*(ρ) = (1−ρ) a_per (r−1)": r"$c^*(\rho)=(1-\rho)\,a_{\mathrm{per}}\,(r-1)$",
    "presence gate ρ≈6.1": r"presence gate, $\rho\approx6.1$",
    "ρ = a_gate / a_per": r"rate ratio $\rho=a_{\mathrm{gate}}/a_{\mathrm{per}}$",
    "miss − miss(blackout K=8)": r"miss minus miss of blackout ($K=8$)",
    "miss − miss(blackout)": "miss minus miss of blackout",
    "blackout K8": r"blackout, periodic $K=8$",
    "thr K16 5/10": r"throttle to $K=16$ (5/10 % thresholds)",
    "thr K64 20/50": r"throttle to $K=64$ (20/50 % thresholds)",
    "kansal ewma": "Kansal-style controller",
    "Kansal-EWMA": "Kansal-style controller",
    r"periodic at $\bar a_K$": r"periodic at the controller's rate $\bar a_K$",
    r"periodic at $a_{max}$ (TRAIN)": r"periodic at $a_{\max}$ (TRAIN)",
}
_orig = mtext.Text.set_text


def _set(self, s):
    return _orig(self, MAP.get(s, s) if isinstance(s, str) else s)


mtext.Text.set_text = _set

from sim40 import config as cfg  # noqa: E402
from sim40 import make_figs as F  # noqa: E402
from sim40 import make_figs_q2 as Q  # noqa: E402
from sim40.explore_q2 import load_rows  # noqa: E402


def main():
    dst = ROOT / "submission_package" / "TGCN" / "latex" / "figures"
    with tempfile.TemporaryDirectory() as tmp:
        cfg.FIGS = pathlib.Path(tmp)
        S = json.loads((cfg.RES / "summary_test.json").read_text())
        F.f4(S, "test")
        F.f6(S, "test")
        Q.f6p([x for x in load_rows() if 0 < x["blackout_K8"]["outage"] < 1])
        for n in ("F4_gate_map_test.pdf", "F6_throttle_vs_blackout_test.pdf", "F6p_throttle_kansal_amax_test.pdf"):
            shutil.copy2(pathlib.Path(tmp) / n, dst / n)
            print("written", n)


if __name__ == "__main__":
    main()
