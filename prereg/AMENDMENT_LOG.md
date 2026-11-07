# AMENDMENT_LOG: amendments to PREREG_40 (topic 40)

*`PREREG_40.md` (v1, tag `prereg-40-v1`) and `PREREG_40_v1.1_exploratory.md` are not edited. Each amendment below is frozen by SHA-256 and by a local git tag before the run it governs.*

## A1 (07-11-2026): LASIESTA frame order

*Written and hashed before any rebuilt corpus or any v2 simulation exists. Tag: `prereg-40-a1`. Decision source: CP0R, approved by the author on 07-11-2026 (one-time unlock of `numbers.json`, `results/` and PREREG for this data correction only).*

### 1. Reason

The detection dump indexes frames by their position in the text-sorted file list. LASIESTA file names are not zero-padded (`I_BS_01-1.bmp`, `-10`, `-100`, `-101`, ...), so its `frame` column is text order, not time. `code/sim40/events.py` read that column as time, so LASIESTA events were cut and merged on a shuffled axis.

- Found on 27-09-2026 in the author's topic 17: ground-truth hit rate 0.949 with the file-name number as time, 0.220 with the index as time, over 48 of 48 sequences.
- Identified for this topic at the P0R audit on 07-11-2026. Topic 40 had reused the 3,713-event corpus without knowing this.
- CDnet 2014 (53 of 53 videos) and BMC (20 of 20) are unaffected: their text order equals their numeric order.
- Expected from topic 17: LASIESTA 936 to 393 events, corpus 3,713 to 3,170.

### 2. The only change

The time axis of LASIESTA: frames are ordered by the number parsed from the file name. The onset of a LASIESTA event becomes (true frame number − 1), the 0-based convention of the other datasets.

Everything that defines the study stays as frozen in v1 and v1.1:

- predictions H1–H7 and exploratory predictions E1–E3, with every pass criterion and threshold;
- seeds (42 throughout, and the seeded rule of each stage);
- the TRAIN/TEST rule for traces, and the video split (same 121 videos, same seeded permutation, same list);
- grids, policies, bootstrap settings and the event rule (a maximal run of consecutive frames with at least one box).

### 3. Parameters informed by TRAIN

These keep their old values in the primary analysis:

- the pass bands of H2c–H2e, H3a, H3b, H4a, H4c, H5a–H5c and H7, all set from the v1 TRAIN exploration;
- the grid choices made at that stage, including ε ∈ {0.45, 0.5, 0.55, 0.6, 0.66, 0.75}, K_REF = 8, the throttle variants and the E3 population rule (a_max(TRAIN) > 0).

No numeric policy parameter in `code/sim40/` was fitted to the TRAIN duration law. `a_max` in E3 is computed from TRAIN energy traces, which this amendment does not touch.

Choosing again on the corrected TRAIN is a sensitivity analysis only. TRAIN is re-run on the corrected corpus and reported next to its v1 basis; a band that TRAIN v2 would have moved is reported as such and never used for scoring.

### 4. What will be run

`code/reproduce.sh` in its order, for TEST and for TRAIN: `run_grid` (main, frontier, gate, throttle), `bootstrap`, then `analyze`, `numbers`, `score_prereg`. For TEST also `sizing` (test, all), `explore_q2`, `sizing_sens` and `make_figs`. For TRAIN also `sizing` (train).

- Checkpoints go to a new folder, `grid_ckpt_v2`. The old `grid_ckpt` is not read, and this is audited.
- The v1 TRAIN bootstrap was a smoke test (1 cell, B = 50). The v2 TRAIN bootstrap uses the full protocol (25 cells, B = 1000), so TRAIN H3c and H4d have no v1 comparator.

Planned code changes, and no others:

- `code/sim40/events.py`: frame order, corpus check;
- `code/sim40/config.py`: checkpoint folder;
- `code/sim40/tests/`: order tests;
- `code/reproduce.sh`, `code/sync_repo.py`, `code/compare_results.py`: comments, release list, tolerated path fields.

### 5. Checks before the run (a failure stops the run and is reported)

(a) Pooled LASIESTA ground-truth hit rate ≥ 0.9 under the new order, and clearly above the ±1-frame offsets.

(b) Events per dataset compared with topic 17 (BMC 261, CDnet 2,516, LASIESTA 393; total 3,170). Any difference is explained row by row against the topic 17 file; it is not forced to match.

(c) CDnet and BMC rows 100 % identical to the v1 corpus.

(d) TRAIN/TEST video lists identical to v1.

### 6. Reporting

- Both versions are reported. The v1 outputs are frozen in `results/_v1_corpus3713/` with a SHA-256 manifest.
- Every prediction is scored PASS/FAIL against its v1 criterion on the corrected data. A verdict that changes is reported as it is, and neither the prediction nor a theorem is edited to match (PREREG §4).
- A floor or sandwich violation on the corrected corpus is reported, and the theorem is not edited here.
- E1–E3 stay exploratory.

### 7. What the analyst had seen (disclosure)

The v2 scoring is **not** a blind test.

- The analyst has seen all v1 outputs on TEST, including the 16/18 score (CP-B1) and E1–E3.
- Before writing this amendment the analyst saw duration-law summaries of the corrected corpus computed from the topic 17 file: E[D] 39.9, P(D = 1) 0.414, P(D < 8) 77.3 %, ε\*(1/8) 0.577 (all videos).
- No policy, replay, floor check, sizing or bootstrap result on the corrected corpus had been seen.
- The predictions were written from a TRAIN exploration that carried the ordering error, so v2 tests them against data they were not formed on.

### 8. Note on the earlier corpus count

An earlier paper from the same pipeline reports a corpus of 3,713 events on the previous frame index. This topic uses the time-ordered corpus of 3,170 events.
