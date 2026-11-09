#!/usr/bin/env python3
"""P3T (review item M10): every C* printed in Tables IV, S14, S17 and S18 comes from one source, numbers_tables.json.
Parses the generated LaTeX and compares cell by cell; also checks the supplement table numbers. Exit 1 on any mismatch
(the build stops). Usage: python P3T/assert_tables.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAT = ROOT / "submission_package" / "TGCN" / "latex"
if not LAT.exists():                               # repository layout: paper/tgcn, script in checks/tgcn
    ROOT = pathlib.Path(__file__).resolve().parents[2]
    LAT = ROOT / "paper" / "tgcn"
sys.path.insert(0, str(ROOT / "code" / "paper"))
SEAS = ("DJF", "MAM", "JJA", "SON")
fails, checks = [], 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def kj(v):
    return f"{v / 1e3:.2f}"


def rows_of(tex, label):
    i = tex.index(r"\label{" + label + "}")
    j = tex.index(r"\bottomrule", i)
    out = []
    for ln in tex[tex.index(r"\midrule", i):j].splitlines():
        if ln.strip().endswith(r"\\") and "&" in ln:
            out.append([c.strip() for c in ln.strip()[:-2].split("&")])
    return out


def main():
    N = json.loads((LAT / "numbers_tables.json").read_text(encoding="utf-8"))["cells"]
    order = [f"{s}|{se}" for s in ("HCMC", "Madrid-MSG", "Uppsala-MSG") for se in SEAS] + [f"Setup{x}|ALL" for x in "BCDEF"]
    second = [f"{s}|{se}" for s in ("Madrid-SARAH3", "Uppsala-SARAH3") for se in SEAS]
    t4 = (LAT / "sizing_table.tex").read_text(encoding="utf-8")
    body = t4[t4.index(r"\midrule"):t4.index(r"\bottomrule")]
    R4 = [[c.strip() for c in ln.strip()[:-2].split("&")] for ln in body.splitlines() if ln.strip().endswith(r"\\") and "&" in ln]
    check(len(R4) == 17, f"Table IV has {len(R4)} rows, not 17")
    for k, r in zip(order, R4):
        c = N[k]
        check(r[2] == kj(c["Cstar_J"]), f"Table IV C* {k}: {r[2]}")
        check(r[3] == kj(c["No7d_J"]), f"Table IV No-week {k}: {r[3]}")
        check(r[7] == kj(c["radio_J"]["6TiSCH"]), f"Table IV 6TiSCH {k}: {r[7]}")
        check(r[8] == kj(c["fixed_J"]["6TiSCH"]), f"Table IV 6TiSCH fixed {k}: {r[8]}")
    S = (LAT / "supp_a3_tables.tex").read_text(encoding="utf-8")
    keys = order + second
    W = rows_of(S, "tab:s_a3_worst")
    R = rows_of(S, "tab:s_a4_radio")
    check(len(W) == 25 and len(R) == 25, f"S14/S17 rows {len(W)}, {len(R)}")
    for k, a, b in zip(keys, W, R):
        c = N[k]
        check(a[2] == kj(c["Cstar_J"]), f"S14 C* {k}: {a[2]}")
        check(b[2] == kj(c["Cstar_J"]), f"S17 C* {k}: {b[2]}")
        for i, q in ((3, "BLE"), (4, "6TiSCH"), (5, "LoRaWAN")):
            check(b[i] == kj(c["radio_J"][q]), f"S17 {q} {k}: {b[i]}")
        for i, q in ((6, "BLE"), (7, "6TiSCH")):
            check(b[i] == kj(c["fixed_J"][q]), f"S17 fixed {q} {k}: {b[i]}")
    B = rows_of(S, "tab:s_a4b")
    for se, r in zip(SEAS, B[:4]):
        check(re.sub(r"\$.*\$", "", r[7]) == kj(N[f"HCMC|{se}"]["Cstar_J"]), f"S18 2025 {se}: {r[7]}")
    aux = (LAT / "supp.aux").read_text(encoding="utf-8")
    for lab, num in (("tab:s_a3_worst", "S14"), ("tab:s_a3_ranges", "S15"), ("tab:s_a3_margin", "S16"), ("tab:s_a4_radio", "S17"), ("tab:s_a4b", "S18"), ("tab:s_train", "S19")):
        check(re.search(r"\\newlabel\{" + lab + r"\}\{\{" + num + r"\}", aux) is not None, f"{lab} is not {num}")
    print(f"assert_tables: {checks} checks, {len(fails)} failures")
    for f in fails[:40]:
        print("  FAIL", f)
    (pathlib.Path(__file__).resolve().parent / "assert_tables.json").write_text(json.dumps({"checks": checks, "failures": fails}, indent=1), encoding="utf-8")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
