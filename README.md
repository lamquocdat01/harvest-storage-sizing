# harvest-storage-sizing

Code, pre-registration and derived results for the paper
**"Miss Floors and Storage Sizing for Energy-Harvesting Sensing Nodes with Events of Random Duration"** (Dat Lam Quoc).

The paper proves a miss floor for event-independent duty-cycle schedules, an energy-induced floor for finite storage and a sizing sandwich for the smallest storage meeting a miss target. It checks them on satellite and indoor-light harvest traces with a pre-registered train/test protocol. This repository rebuilds every number and table of the paper from the released results, and the results from public data.

## Layout

| Path | Content |
|---|---|
| `code/sim40/` | trace loaders, storage dynamics, policies, event replay, grid stages, bootstrap, analysis, figures, amendments A3–A5 |
| `code/sim40/tests/` | machine checks of the theorems and amendments (`python -m pytest code/sim40/tests`) |
| `code/paper/` | generation of macros, tables and figures of the manuscript |
| `paper/tgcn/` | manuscript sources (`body.tex`, `main_review.tex`, `main_2col.tex`, `supp.tex`) |
| `paper/v3/` | base sources from which part of the generated inputs are built |
| `code/reproduce.sh` | one-command reproduction of all TEST results |
| `code/compare_results.py` | key-by-key comparison of a reproduced `results/` folder with the released one |
| `prereg/` | `PREREG_40.md` (H1–H7, frozen before TEST; tag `prereg-40-v1`), `PREREG_40_v1.1_exploratory.md` (E1–E3), `AMENDMENT_LOG.md` (amendments A1–A5b; tags `prereg-40-a1` … `prereg-40-a5`), hashes |
| `results/` | released derived results (JSON, the event-duration corpus CSV, figures) |
| `checks/` | post-registration checks and their outputs |

`RELEASE_FILES.txt` lists every released file with its size and SHA-256.

## Reproduce

```bash
pip install -r requirements.txt            # Python 3.11.9
python -m pytest code/sim40/tests
export THS_DATASETS=/path/to/datasets      # folder described under "Data"
bash code/reproduce.sh 3                   # about 4-5 h on a 4-core laptop, needs at least 6 GB free RAM
python code/compare_results.py results /path/to/clean/clone/results
```

Generated manuscript inputs, from the released results and without simulation:

```bash
python code/paper/build_v3.py
python code/paper/build_tgcn.py
python code/paper/build_p3t.py
```

All randomness is seeded (seed 42). TRAIN is the odd months and half of the videos (seeded permutation); TEST is the even months and the other videos. Grid checkpoints are written to `$THS_DATASETS/_derived/40/grid_ckpt_v2`; delete that folder for a run from scratch.

## Licenses

| What | Licence | File |
|---|---|---|
| Code (`code/`) | MIT | `LICENSE` |
| Derived data and figures (`results/`) | CC BY 4.0 | `LICENSE-DATA` |

Third-party input data keep their own terms and are not redistributed here.

## Data (third-party; not redistributed)

| Data | Source | Licence | Expected location |
|---|---|---|---|
| Satellite global horizontal irradiance 2025: Ho Chi Minh City (JMA/JAXA Himawari-9), Madrid and Uppsala (EUMETSAT LSA SAF MSG; EUMETSAT CM SAF SARAH-3); Ho Chi Minh City 2020–2024 for amendment A4b | Open-Meteo satellite API, `https://satellite-api.open-meteo.com/v1/archive` (DOI 10.5281/zenodo.7970649; SARAH-3 DOI 10.5676/EUM_SAF_CM/SARAH/V003) | CC BY 4.0 | `$THS_DATASETS/OpenMeteo_SatRad/`, `$THS_DATASETS/OpenMeteo_HCMC_2020_2024/` |
| Indoor irradiance, EnHANTS setups B–F | CRAWDAD columbia/enhants on IEEE DataPort, DOI 10.15783/C77P47 | CC BY 4.0 | `$THS_DATASETS/EnHANTS/extracted/` |
| Event durations | per-frame detections (Ultralytics YOLO26s, CPU) on CDnet 2014, LASIESTA and BMC videos | videos and ground truth stay under their providers' terms; no frame is re-hosted | derived corpus `results/event_corpus_40.csv` (121 videos, 3,170 events) |

## LASIESTA frame order

LASIESTA file names are not zero-padded (`1.bmp`, `10.bmp`, `100.bmp`, …). `code/sim40/events.py` maps each index of the detection dump to the number in the file name before cutting events, which is checked on all 48 sequences (`code/sim40/tests/test_events_order.py`). An earlier build cut events on the text order: 3,713 events instead of 3,170, LASIESTA 936 instead of 393; CDnet 2014 and BMC are identical in both. The correction is amendment A1 (`prereg/AMENDMENT_LOG.md`); the three files of the earlier build used by Tables S1–S2 are in `results/_v1_corpus3713/`.

## Tags

`prereg-40-v1`, `prereg-40-a1` … `prereg-40-a5` freeze the pre-registration and its amendments before the runs they govern. `v3.0.1-tgcn` is the state accompanying the manuscript.
