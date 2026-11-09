"""P3U Viec 2: one process at a time; each step starts only inside 08:00-23:00 with at least 7 GB free (A5/A5b section 4).
Order: A5, then the batch of the audit on run_old and run_corr in the copy. Stops at 22:45. Usage: python P3U/run_a5_chain.py
"""
import datetime as dt
import os
import pathlib
import subprocess
import sys
import time

import psutil

TOPIC = pathlib.Path(__file__).resolve().parents[1]
LOG = TOPIC / "P3U" / "run_a5_chain.log"
RERUN = pathlib.Path(os.environ.get("THS_DATASETS", r"D:\Datasets")) / "_derived" / "40" / "deep3_rerun"
LAST = dt.time(22, 45)
STEPS = [("run_all", ["-m", "cfs.run_all", "--phase", "1", "2"]), ("a1", ["revision/sim_phase.py"]), ("a5", ["revision/analyze_mdep.py"]),
         ("a6", ["revision/analyze_relcorr.py"]), ("a4", ["revision/analyze_detector.py"]), ("sweep_tau", ["scripts/sweep_tau.py"]),
         ("a2", ["revision/analyze_alignment.py"]), ("activation", ["scripts/analyze_activation.py"]), ("thm4", ["scripts/check_thm4_and_integrity.py"]),
         ("b1", ["revision/b1_ablation_sota.py"]), ("b2", ["revision/b2_dilution.py"])]


def log(s):
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {s}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wait():
    said = False
    while True:
        now = dt.datetime.now().time()
        if now >= LAST:
            return False
        free = psutil.virtual_memory().available / 2**30
        if free >= 7.05 and now >= dt.time(8):
            return True
        if not said:
            log(f"waiting: {free:.2f} GB free")
            said = True
        time.sleep(30)


def main():
    env = dict(os.environ, PYTHONIOENCODING="utf-8", MPLBACKEND="Agg")
    if not wait():
        log("STOP before A5")
        return 3
    r = subprocess.run([sys.executable, "-m", "sim40.a5_sensitivity"], cwd=TOPIC / "code", env=env, capture_output=True, text=True)
    log(f"A5 rc={r.returncode} {(r.stdout + r.stderr).strip().splitlines()[-1][:300]}")
    if r.returncode:
        log("FAILED: " + (r.stdout + r.stderr)[-1500:])
        return 1
    bad = 0
    for run in ("run_old", "run_corr"):
        for name, args in STEPS:
            if not wait():
                log(f"STOP before {run}/{name}; rerun needed")
                return 3
            t0 = time.time()
            r = subprocess.run([sys.executable] + args, cwd=RERUN / run, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
            (RERUN / run / "out" / f"log_{name}.txt").write_text(r.stdout + r.stderr, encoding="utf-8")
            log(f"{run}/{name} rc={r.returncode} {time.time() - t0:.0f}s")
            if r.returncode:
                bad += 1
                log(f"NOT REPRODUCIBLE step {run}/{name}: " + (r.stdout + r.stderr)[-500:].replace("\n", " | "))
    log(f"ALL STEPS DONE, failed steps: {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
