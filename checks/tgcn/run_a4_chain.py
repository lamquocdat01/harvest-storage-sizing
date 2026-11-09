"""P3T Viec 2: one process at a time; each part starts only inside 08:00-23:00 with at least 7 GB free (A4 section 7).
Order: a4b, count17, deep3, radio m = 0.25, radio m = 1.0 (the last only if the window allows). Parts are resumable.
Stops at 22:45 and leaves the checkpoints; the log says what is left. Usage: python P3T/run_a4_chain.py
"""
import datetime as dt
import os
import pathlib
import subprocess
import sys
import time

import psutil

TOPIC = pathlib.Path(__file__).resolve().parents[1]
LOG = TOPIC / "P3T" / "run_a4_chain.log"
PARTS = [["--part", "a4b"], ["--part", "count17"], ["--part", "deep3"], ["--part", "radio", "--m", "0.25"],
         ["--part", "radio", "--m", "0.25", "1.0"]]
LAST = dt.time(22, 45)


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
            log(f"gate open, {free:.2f} GB free")
            return True
        if not said:
            log(f"waiting: {free:.2f} GB free")
            said = True
        time.sleep(30)


def main():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for p in PARTS:
        for attempt in range(40):
            if not wait():
                log(f"STOP: window closing before {p}; rerun to resume")
                return 3
            r = subprocess.run([sys.executable, "-m", "sim40.a4_sensitivity"] + p, cwd=TOPIC / "code", env=env, capture_output=True, text=True)
            tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
            log(f"{' '.join(p)} rc={r.returncode} {tail[0][:200]}")
            if r.returncode == 0:
                break
            if "STOP" not in (r.stdout + r.stderr):
                log("FAILED: " + (r.stdout + r.stderr)[-1500:])
                return 1
            time.sleep(60)
        else:
            log(f"STOP: too many attempts on {p}")
            return 2
    log("ALL PARTS DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
