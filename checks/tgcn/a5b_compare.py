#!/usr/bin/env python3
"""A5b: compare the rerun of the Deep3 batch with the outputs of the 27-09-2026 audit, adopt the 67 audit rows if they agree, check the printed values
against the FINAL PDFs of [14]. Reads the audit (topic 17), writes results/a5b_deep3_gate.json. Usage: python P3U/a5b_compare.py <folder with m2.txt, s.txt>
"""
import json
import math
import os
import pathlib
import re
import sys

T = pathlib.Path(__file__).resolve().parents[1]
A17 = pathlib.Path(r"D:\PhD Program\02. Working\17_Sim2Real_Certification")
SRC = A17 / "legacy" / "audit_B0_deep3_pa" / "deep3"
DST = pathlib.Path(os.environ.get("THS_DATASETS", r"D:\Datasets")) / "_derived" / "40" / "deep3_rerun"
TOL = 1e-9
GATE_WORDS = ("Gate", "gate", "TargetingGain", "BMC", "q_in", "P_g", "D≥R", "Leak", "ε(a)/gated", "Family", "Đỉnh", "ρ_ev", "Reducto", "Refresh R=3", "Closed runs", "Table S5", "Table S2", "Dilution", "kênh", "miss D")


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((path + "/" + str(k), "missing key"))
            else:
                walk(a[k], b[k], path + "/" + str(k), out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path, f"len {len(a)} vs {len(b)}"))
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        if not (a == b or (math.isnan(a) and math.isnan(b)) or abs(a - b) <= TOL):
            out.append((path, f"{a} vs {b}"))
    elif a != b:
        out.append((path, f"{a!r} vs {b!r}"))


def n_leaves(x):
    if isinstance(x, dict):
        return sum(n_leaves(v) for v in x.values())
    if isinstance(x, list):
        return sum(n_leaves(v) for v in x)
    return 1


def fmt(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    s = {f"{v}", f"{v:g}"}
    if isinstance(v, int) and v >= 1000:
        s.add(f"{v:,}")
    return s


def main():
    folder = pathlib.Path(sys.argv[1])
    final = (folder / "m2.txt").read_text(encoding="utf-8", errors="replace") + "\n" + (folder / "s.txt").read_text(encoding="utf-8", errors="replace")
    flat = re.sub(r"\s+", " ", final)
    cmp_ = {}
    for run in ("run_old", "run_corr"):
        res = {"files": {}, "n_values": 0, "n_diff": 0, "not_produced": []}
        for f in sorted((SRC / run / "out").glob("*_results.json")):
            g = DST / run / "out" / f.name
            if not g.exists():
                res["not_produced"].append(f.name)
                continue
            a, b = json.loads(f.read_text(encoding="utf-8")), json.loads(g.read_text(encoding="utf-8"))
            d = []
            walk(a, b, "", d)
            res["files"][f.name] = {"values": n_leaves(a), "differ": len(d), "first": d[:6]}
            res["n_values"] += n_leaves(a)
            res["n_diff"] += len(d)
        cmp_[run] = res
    B0 = json.loads((A17 / "results" / "b0_deep3_impact.json").read_text(encoding="utf-8"))
    rows = []
    for r in B0["rows"]:
        q = r["quantity"]
        x = {k: r.get(k) for k in ("quantity", "printed", "reproduced_old", "corrected", "claim_changes", "note")}
        x["is_gate_row"] = any(w in q for w in GATE_WORDS)
        s = fmt(r.get("printed"))
        x["printed_found_in_FINAL_pdf"] = None if s is None else any(z in flat for z in s)
        rows.append(x)
    out = {"amendment": "A5b", "note": "Rows adopted from the 27-09-2026 audit after the rerun comparison below; hardware energy measurements of [14] are not corpus-dependent and were not rerun.",
           "rerun_vs_audit": cmp_, "n_rows": len(rows), "n_claim_changes": sum(1 for r in rows if r["claim_changes"]), "rows": rows}
    (T / "results" / "a5b_deep3_gate.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, v in cmp_.items():
        print(k, "values", v["n_values"], "differ", v["n_diff"], "not produced", v["not_produced"], {n: f["differ"] for n, f in v["files"].items()})
    print("rows", len(rows), "claim changes", out["n_claim_changes"], "gate rows", sum(r["is_gate_row"] for r in rows))
    print("numeric printed not found in FINAL:", [r["quantity"][:50] for r in rows if r["printed_found_in_FINAL_pdf"] is False][:30])


if __name__ == "__main__":
    main()
