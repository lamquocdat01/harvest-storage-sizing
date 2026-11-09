"""Amendment A4b (prereg/AMENDMENT_LOG.md, tag prereg-40-a4): satellite GHI of Ho Chi Minh City, 2020-2024.

Same request as code/p0_fetch_irradiance.py for 2025: Open-Meteo satellite archive, model jma_jaxa_himawari,
native temporal resolution, quarterly requests. No e-mail or key in any parameter.
Output: $THS_DATASETS/OpenMeteo_HCMC_2020_2024/HCMC_jma_jaxa_himawari_<year>.csv (time_utc, ghi_wm2), <...>.meta.json,
manifest.json. DATA_SOURCES.md is written by --write-sources after the download.
Usage: python code/a4b_fetch_hcmc.py [--write-sources]
"""
import csv
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("THS_DATASETS", "datasets")) / "OpenMeteo_HCMC_2020_2024"
YEARS = range(2020, 2025)
API = "https://satellite-api.open-meteo.com/v1/archive"
LAT, LON, MODEL = 10.80, 106.70, "jma_jaxa_himawari"
QUARTERS = [("01-01", "03-31"), ("04-01", "06-30"), ("07-01", "09-30"), ("10-01", "12-31")]


def fetch(start, end):
    url = (f"{API}?latitude={LAT}&longitude={LON}&start_date={start}&end_date={end}"
           f"&hourly=shortwave_radiation&models={MODEL}&temporal_resolution=native")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return url, json.load(r)
        except Exception as e:                      # network hiccup or rate limit
            print("  retry", attempt, e, file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(url)


def download():
    free = shutil.disk_usage(".").free / 2**30
    print(f"free space: {free:.1f} GB (rule: > 1.5 x size + 20 GB; expected size < 0.05 GB)")
    if free < 20.1:
        sys.exit("not enough free space")
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for y in YEARS:
        out = ROOT / f"HCMC_{MODEL}_{y}.csv"
        if not out.exists():
            rows, urls = [], []
            for q0, q1 in QUARTERS:
                url, d = fetch(f"{y}-{q0}", f"{y}-{q1}")
                urls.append(url)
                h = d["hourly"]
                rows += list(zip(h["time"], h["shortwave_radiation"]))
                meta = {k: d[k] for k in ("latitude", "longitude", "elevation")}
                time.sleep(2)
            with open(out, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["time_utc", "ghi_wm2"])
                w.writerows(rows)
            out.with_suffix(".meta.json").write_text(json.dumps({"site": "HCMC", "model": MODEL, "grid": meta, "urls": urls}, indent=1))
        sha = hashlib.sha256(out.read_bytes()).hexdigest()
        with open(out) as f:
            lines = f.read().splitlines()[1:]
        n_null = sum(1 for x in lines if x.endswith(","))
        manifest.append({"file": out.name, "year": y, "lat": LAT, "lon": LON, "model": MODEL, "rows": len(lines),
                         "n_null": n_null, "first": lines[0].split(",")[0], "last": lines[-1].split(",")[0], "sha256": sha})
        print(out.name, len(lines), "null", n_null, sha[:12], flush=True)
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=1))


def write_sources():
    m = json.loads((ROOT / "manifest.json").read_text())
    size = sum((ROOT / x["file"]).stat().st_size for x in m)
    L = ["# DATA_SOURCES: OpenMeteo_HCMC_2020_2024 (topic 40, amendment A4b)", "",
         "- **Source:** Open-Meteo Satellite Radiation API, https://satellite-api.open-meteo.com/v1/archive",
         f"- **Request:** latitude={LAT}, longitude={LON}, models={MODEL}, hourly=shortwave_radiation, temporal_resolution=native; "
         "quarterly requests; no e-mail or key.",
         "- **Same request as the 2025 file** in `$THS_DATASETS/OpenMeteo_SatRad/` (`code/p0_fetch_irradiance.py`).",
         "- **Licence:** CC BY 4.0 (Open-Meteo). Attribution: Open-Meteo; satellite data JMA/JAXA Himawari.",
         "- **Note:** the satellite changed from Himawari-8 to Himawari-9 within this period.",
         f"- **Downloaded:** {time.strftime('%Y-%m-%d %H:%M')} ICT by `code/a4b_fetch_hcmc.py`. Size {size / 2**20:.1f} MB.", "",
         "| File | Rows | Null values | First | Last | SHA-256 |", "|---|---|---|---|---|---|"]
    L += [f"| {x['file']} | {x['rows']} | {x['n_null']} | {x['first']} | {x['last']} | {x['sha256']} |" for x in m]
    (ROOT / "DATA_SOURCES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("DATA_SOURCES.md written")


if __name__ == "__main__":
    if "--write-sources" in sys.argv:
        write_sources()
    else:
        download()
