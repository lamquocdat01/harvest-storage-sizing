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

## A2 (07-11-2026): sandwich brackets and exact miss of the taut-string schedule

*Written and hashed before any A2 code exists and before any A2 number is computed. Tag: `prereg-40-a2`. Sections A1.1–A1.8 above are unchanged. Decision source: CP_S3B item 4 (proposal = default, 07-11-2026), after the independent proof check `P0R/PROOF_CHECK_40.md` (S3b).*

### 1. Reason (post hoc, disclosed)

The proof check (S3b, items §1.11, §1.15, §5.4) found two reporting choices that do not match Theorem 3 (THEORY v2.1; Theorem 2b in v2.0):

- C_LB is reported as the **upper** end of a bisection with 1 % relative tolerance, so it can exceed the true C_LB by up to 1 %;
- C_TS is the upper end of a bisection whose test uses the **block surrogate** miss Σ_j (n/T) Ψ(a_j) with n = 600 slots per block, while D_max = 6,300 slots, so the surrogate is not the miss of any slot schedule.

On v2 TEST 396 of 1,550 finite cells have C_LB/C_TS > 1 (max 1.0093), which the theorem forbids. This amendment is a change made **after** the v2 TEST results were seen. It does not replace the registered scoring.

### 2. Definitions

For each eps-sizing cell (site, season, r, ℓ̃, m) and target ε of the v2 `frontier` stage (TEST: 300 combinations × ε ∈ {0.45, 0.5, 0.55, 0.6, 0.66, 0.75}; cells with a_ε > a_bal stay infinite):

- **C_LB_lo, C_LB_hi:** the lower and upper ends of the same bisection as v2 (`energy.C_for_amax`, test A(C) ≥ a_ε, relative tolerance 0.01). C_LB_lo has A(C_LB_lo) < a_ε, so C_LB ≥ C_LB_lo. C_LB_hi equals the v2 value.
- **C_TS_sur_hi:** the v2 value (surrogate test).
- **Realised schedule:** from the per-sub-step (on_frac_j, rate_j) of a run, the slot schedule with phase-continuous interleaving (Bresenham): the k-th activation is in the slot where the cumulative fluid activation count A(t) crosses k − φ, with fixed phase **φ = 0.5**, n_sub = 600 slots per sub-step, activations only in the on part of a sub-step, and the rate cap a_j ≤ 1 (at most one activation per slot).
- **Exact miss:** Lemma 1 on the cyclic gaps of the realised schedule, miss = 1 − (1/T) Σ_i G(g_i) with G(g) = Σ_{k<g} P(D > k), clamped at D_max.
- **Feasible C:** the realised taut-string schedule at C (`policies.taut`, unchanged) has **exact miss ≤ ε and no outage** (fluid on-fraction 1 in every sub-step, tolerance 10⁻⁹).
- **C_TS_exact_hi:** the upper end of a bisection with relative tolerance 0.01 whose upper end is always a C verified feasible. Start: C_TS_sur_hi if it is feasible; otherwise multiply by 1.25 until feasible, up to the v2 search cap (50 × C\* of periodic K = 8); if none is feasible, ∞. Lower end: C_LB_lo (no policy in the class is feasible below C_LB). No monotonicity of the exact miss in C is assumed: the result is a verified feasible point, which is all Theorem 3(b) needs.

Recorded per (cell, ε): C_LB_lo, C_LB_hi; C_TS_sur_hi with miss_exact and outage there; C_TS_exact_hi with outage there (must be 0); abs_exact_minus_sur = |miss_exact − miss_surrogate| at C_TS_exact_hi; C_per (v2).

### 3. Pass rule of the amendment

**PASS iff 0 cells have C_LB_lo > C_TS_exact_hi**, and the code tests pass: (t1) constant rate a with aT ∈ ℕ gives exact miss = ε\*(a) within 10⁻¹²; (t2) 5 random schedules agree with `metrics.replay_miss` within 3 standard errors; (t3) brute force over onsets and durations on small T agrees exactly. A cell with C_LB_lo > C_TS_exact_hi is reported verbatim as a code error or a gap in the theorem, and the A2 stage stops; nothing is edited to make it pass.

### 4. Scoring

- H4a–H4d keep their registered definitions and their registered verdicts (computed from C_LB_hi and C_TS_sur_hi). Those verdicts are what the paper reports as the pre-registered outcome.
- An **A2 column** is printed next to them: H4a–H4c recomputed with C_TS_exact_hi in place of C_TS and C_LB_lo in place of C_LB, same thresholds; H4d recomputed on the same 6 bootstrap cells, the same 7-day block resamples (the seed-42 generator of `bootstrap.run_boot` replayed in its original order) and B_ts = 100, with the exact feasibility test. Because the H4d target equals the floor ε\*(1/8) exactly, where the exact miss of any non-periodic schedule sits on a knife edge, the A2 version of H4d uses ε\*(1/8) + 10⁻⁴; the share of resamples that is also feasible at ε\*(1/8) + 10⁻⁹ is reported.
- A verdict that differs between the registered and the A2 column is printed with both values, in the main text if it concerns a headline number.
- Tolerance 1 % as before. Seed 42. No other prediction, threshold or grid is changed.

### 5. What will be run

`P3R/run_a2_sizing.py --split test` (checkpoints in `$THS_DATASETS/_derived/40/a2_ckpt/`, one file per combination, resumable; never writes into `grid_ckpt_v2`; reads the v2 frontier checkpoints read-only), then its bootstrap part for H4d. Output `results/a2_sizing_test.json`; v2 files are not overwritten. TRAIN (`--split train`) only after the TRAIN rerun of A1 is complete. Code added: `code/sim40/miss_exact.py`, `code/sim40/tests/test_miss_exact.py`, `P3R/run_a2_sizing.py`; no existing module is changed.

### 6. What the analyst had seen (disclosure)

The proof check (`P0R/PROOF_CHECK_40.md`); the v2 cell with C_LB/C_TS = 1.0093 and the count of cells above 1; every v2 TEST number (`results/`, `P2R/DIFF_v1_v2_40.md`), including H4a–H4d v2 and the E1 median outage difference per_abarK − Kansal of −0.055. No exact-miss value of any schedule on the traces had been computed.

## A3 (08-11-2026): post-hoc sizing sensitivities requested by review

*Written and hashed before any A3 code exists and before any A3 number is computed. Tag: `prereg-40-a3`. Sections A1 and A2 above are unchanged. Decision source: CP0R2 item 4 and the S6 review (`P3R/R2_REVIEW_40.md`, items M6, M7, M8).*

### 1. Status: post hoc, descriptive

A3 adds three descriptive quantities after every v2 TEST result was seen. It has no pass criterion. It changes no prediction, threshold, grid, seed, verdict or earlier number. H1–H7, E1–E3 and the A2 column keep the verdicts already reported. No A3 quantity may be used to re-score anything.

### 2. Common definitions

- Reference node: r = 14.3, leakage l = 0.036, K = 8, activation rate a = 1/8 (the node of Table IV, `code/sim40/sizing.py`).
- Cells: the 25 cells of `traces.cells()` (5 outdoor site–product series × 4 seasons, plus 5 indoor setups).
- C\* is `energy.C_periodic(h, 600, r, l, a)` on the 1-min sub-step series.
- Days are 1440 sub-steps from the start of the cell series; a final partial day is dropped, as in `run_grid.baselines`.
- Medians and percentiles over cells count each of the 25 cells once. p90 is the smallest cell value with at least 90 % of the cells at or below it. An infinite value counts as larger than every finite value.

### 3. (a) Worst-spell sensitivity (review item M6)

Split `all` (the full-year cells of Table IV), m = 0.25 and m = 1.0, panel scaled once on the whole cell by `traces.scale_panel`.

For window length L days, the net income of day d is the sum over its sub-steps of (h − e), with e = 1 + l + a(r − 1). The worst window is the run of L consecutive days, on the cyclic day index, with the smallest total net income (first such run on ties). It is deleted, the remaining days are concatenated in order, and C\* is recomputed on the shorter cycle with the panel scale unchanged.

- Primary: L = 7 days, the block length of the registered block bootstrap.
- Secondary: L = 1 and L = 3 days.
- Reported per cell: C\*, C\* without the worst window, and their ratio. Over cells: median, minimum and maximum of the ratio per site group.

### 4. (b) Per-cell ranges of the sizing rules (review item M7)

Read-only, from `results/summary_test.json`, field `main.baselines` (1,600 combinations, split test). No simulation.

For each ratio C\*/C_avgday, C\*/C_buchli_daily, C\*/C_kansal_mean and C\*/C_3day, and each cell: the median, minimum and maximum over the 64 (r, l, m) combinations with a finite value. Then per site group (HCMC 4 cells, Madrid 8, Uppsala 8, indoor 5): the minimum and maximum of the per-cell medians.

### 5. (c) Train-to-test margin factor (review item M8)

The panel is scaled on the TRAIN months only (`traces.scale_panel` applied to the TRAIN series), and the same scale is applied to the TEST months, because a designer has no TEST data. C_TRAIN = C\* on the scaled TRAIN series and C_TEST = C\* on the scaled TEST series of the same cell. The margin factor is

k = C_TEST / C_TRAIN.

- If C_TRAIN is infinite the cell is excluded and counted. If C_TEST is infinite (the TRAIN panel cannot sustain a = 1/8 on the TEST months at any capacity), k is infinite and the cell is kept and counted.
- Primary: the reference node at m = 0.25, over the 25 cells: median, p90 and maximum of k, the share with k > 1, and the number with k infinite.
- Secondary: the same at m = 1.0; and over the full grid of `R_LEVELS` × `L_LEVELS` × `M_LEVELS`, with each cell counted through its median over the grid so that the effective sample stays 25.
- Deterministic; no seed is used.

### 6. What will be run

`code/sim40/a3_sensitivity.py`, after the TRAIN rerun of A1 and A2-TRAIN have finished, inside the 08:00–23:00 window with at least 7 GB of free RAM, as one process. Output: `results/a3_worst_spell.json`, `results/a3_per_cell_ranges.json`, `results/a3_margin_k.json`. Existing result files are not overwritten and `grid_ckpt_v2` is not written. Code added: that module only; no existing module changes.

### 7. Reporting

The paper labels all A3 numbers as post hoc and descriptive, in the sizing section and in Threats to Validity. A value that is unfavourable to the paper's sizing rule is reported as computed.

### 8. What the analyst had seen (disclosure)

Every v2 TEST number and every A2 TEST number, including Table IV, the block-bootstrap sensitivity (Tables S9–S10), the group-level medians of the sizing rules, and E3 (a constant rate sized on TRAIN had outages in about half of the TEST cases). None of the three A3 quantities had been computed: no C\* with a window removed, no per-cell summary of the rule ratios and no C_TEST/C_TRAIN.
