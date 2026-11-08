#!/usr/bin/env python3
"""fig_f3_v3.py (P0R2, S6 m4): Fig. 2 of manuscript v3 = the A2 frontier figure of fig_f3_a2.py with typeset axis
labels. Same data and the same selection (results/summary_test.json, results/a2_sizing_test.json); nothing is
recomputed except medians for plotting. Writes only into the given figures folder (results/figs is not touched).
Usage: python code/paper/fig_f3_v3.py <figures folder>   (build_v3.py calls main())
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from sim40 import make_figs as MF          # noqa: E402  (style, palette, helpers)
import matplotlib.pyplot as plt            # noqa: E402

NAME = "F3_frontier_spread_vs_hf_test_a2_v3"


def main(dst):
    dst = pathlib.Path(dst)
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
    axs[0].set(xlabel=r"$C_{\mathrm{HF}}/C_{\mathrm{per}}$ at $a=1/8$",
               ylabel=r"$\mathrm{miss}_{\mathrm{HF}}-\mathrm{miss}_{\mathrm{per}}$")
    axs[1].set(xlabel=r"miss target $\varepsilon$", ylabel=r"$C_{\mathrm{TS}}(\varepsilon)/C_{\mathrm{per}}(\varepsilon)$",
               ylim=(0, 1.05))
    axs[1].axhline(1, color="#666", lw=0.8, ls=":")
    h_, l_ = axs[0].get_legend_handles_labels()
    fig.legend(h_, l_, frameon=False, fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3)
    dst.mkdir(parents=True, exist_ok=True)
    fig.savefig(dst / f"{NAME}.pdf", bbox_inches="tight")
    plt.close(fig)
    print("Fig. 2 (v3 labels) written to", dst / f"{NAME}.pdf")


if __name__ == "__main__":
    main(sys.argv[1])
