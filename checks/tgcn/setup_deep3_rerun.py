#!/usr/bin/env python3
"""A5b: copy runs run_old and run_corr of the 27-09-2026 audit (topic 17) to $THS_DATASETS/_derived/40/deep3_rerun/. In the copy the absolute
paths of the audit are rewritten to the copy; nothing else changes; every rewritten file is logged. Old outputs are removed from the copy.
Also checks cfs/ and scripts/ against the published Deep3 folder. Sources are read only. Usage: python P3U/setup_deep3_rerun.py
"""
import filecmp
import json
import os
import pathlib
import shutil
import stat

SRC = pathlib.Path(r"D:\PhD Program\02. Working\17_Sim2Real_Certification\legacy\audit_B0_deep3_pa\deep3")
PUB = pathlib.Path(r"D:\PhD Program\03.Final Submission\09.05 Certifiable worst-case\certifiable-frame-skipping")
DST = pathlib.Path(os.environ.get("THS_DATASETS", r"D:\Datasets")) / "_derived" / "40" / "deep3_rerun"
OLD = "D:/PhD Program/02. Working/17_Sim2Real_Certification/code/b0_impact/deep3"
NEW = DST.as_posix()
OUT = pathlib.Path(__file__).resolve().parent / "deep3_rerun_setup.json"


def main():
    if DST.exists():
        shutil.rmtree(DST, onerror=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))
    DST.mkdir(parents=True)
    log = {"source": str(SRC), "destination": str(DST), "path_rewrites": [], "code_vs_published": {}}
    for run in ("run_old", "run_corr"):
        shutil.copytree(SRC / run, DST / run, ignore=shutil.ignore_patterns("__pycache__", "out", "results"))
        for sub in ("out/figures", "out/tables", "results/deep3", "results/figures", "results/tables"):
            (DST / run / sub).mkdir(parents=True, exist_ok=True)
        for f in sorted((DST / run).rglob("*")):
            if f.suffix in (".py", ".yaml", ".yml", ".sh") and f.is_file():
                t = f.read_text(encoding="utf-8", errors="surrogateescape")
                if OLD in t:
                    n = t.count(OLD)
                    f.write_text(t.replace(OLD, NEW), encoding="utf-8", errors="surrogateescape", newline="")
                    log["path_rewrites"].append({"file": f.relative_to(DST).as_posix(), "n": n})
                assert "17_Sim2Real_Certification" not in f.read_text(encoding="utf-8", errors="surrogateescape"), f
        for sub in ("cfs", "scripts"):
            cmp = filecmp.dircmp(SRC / run / sub, PUB / sub, ignore=["__pycache__"])
            log["code_vs_published"][f"{run}/{sub}"] = {"differ": cmp.diff_files, "only_audit": cmp.left_only, "only_published": cmp.right_only}
    OUT.write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(len(log["path_rewrites"]), "files rewritten;", json.dumps(log["code_vs_published"])[:600])


if __name__ == "__main__":
    main()
