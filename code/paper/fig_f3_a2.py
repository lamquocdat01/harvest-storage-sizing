#!/usr/bin/env python3
"""fig_f3_a2.py (P3R): Fig. 3 of the v2 manuscript with the exact sizing brackets of amendment A2.

Left panel: harvest-following against periodic at a = 1/8 (summary_test.json, as in sim40.make_figs.f3).
Right panel: C_TS/C_per at equal miss target with C_TS = C_TS_exact_hi of A2 (results/a2_sizing_test.json, per-cell
records), median per site; the registered block-objective curve (v2) is drawn thin and dashed for comparison.
Output: results/figs/F3_frontier_spread_vs_hf_test_a2.{pdf,png} (new files; the v2 figure is not overwritten) and a
copy in the v2 figures folder. Usage: python code/paper/fig_f3_a2.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from sim40 import make_figs as MF          # noqa: E402  (style, palette, helpers)
import matplotlib.pyplot as plt            # noqa: E402


def main():
    S = json.loads((ROOT / "results" / "summary_test.json").read_text())
    A = json.loads((ROOT / "results" / "a2_sizing_test.json").read_text())
    eq = [x for x in S["frontier"]["equal_a"] if x["r"] == 15.0 and x["l"] == 0.04 and x["m"] == 0.25 and x["K"] == 8]
    v2 = [x for x in S["frontier"]["eps_sizing"] if x["r"] == 15.0 and x["l"] == 0.04 and x["m"] == 0.25]
    a2 = [x for x in A["cells"] if x["r"] == 15.0 and x["l"] == 0.04 and x["m"] == 0.25
          and x.get("C_TS_exact_hi") and x.get("C_per")]
    fig, axs = plt.subplots(1, 2, figsize=(MF.W, 2.3), gridspec_kw={"wspace": 0.5})
    for i, g in enumerate(MF.SITES):
        e = [x for x in eq if MF._grp(x["site"]) == g]
        if e:
            axs[0].scatter([x["C_hf"] / x["C_per"] for x in e], [x["dmiss_hf_minus_per"] for x in e], s=12,
                           color=MF.COL[i], marker=MF.MK[i], label=g)
        z = [x for x in a2 if MF._grp(x["site"]) == g]
        if z:
            es = sorted(set(x["eps"] for x in z))
            med = [np.median([x["C_TS_exact_hi"] / x["C_per"] for x in z if x["eps"] == ee]) for ee in es]
            axs[1].plot(es, med, color=MF.COL[i], marker=MF.MK[i], ms=3.5, label=g)
        zz = [x for x in v2 if MF._grp(x["site"]) == g and np.isfinite(x["TS_over_per"])]
        if zz:
            es = sorted(set(x["eps"] for x in zz))
            med = [np.median([x["TS_over_per"] for x in zz if x["eps"] == ee]) for ee in es]
            axs[1].plot(es, med, color=MF.COL[i], lw=0.6, ls="--", alpha=0.6)
    axs[0].set(xlabel="C_HF / C_per  (a = 1/8)", ylabel="miss_HF − miss_per")
    axs[1].set(xlabel="miss target ε", ylabel="C_TS(ε) / C_per(ε)", ylim=(0, 1.05))
    axs[1].axhline(1, color="#666", lw=0.8, ls=":")
    h_, l_ = axs[0].get_legend_handles_labels()
    fig.legend(h_, l_, frameon=False, fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3)
    out = ROOT / "results" / "figs"
    for ext in ("pdf", "png"):
        fig.savefig(out / f"F3_frontier_spread_vs_hf_test_a2.{ext}", bbox_inches="tight")
    plt.close(fig)
    dst = ROOT / "submission_package" / "v2" / "latex" / "figures"
    if not dst.exists():
        dst = ROOT / "paper" / "v2" / "figures"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out / "F3_frontier_spread_vs_hf_test_a2.pdf", dst / "F3_frontier_spread_vs_hf_test_a2.pdf")
    print("F3 (A2) written")


if __name__ == "__main__":
    main()
