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

## A4 (09-11-2026): post-hoc report-energy sensitivity and counting on 17 cells

*Written and hashed before any A4 code exists and before any A4 number is computed. Tag: `prereg-40-a4`. Sections A1, A2 and A3 above are unchanged. Decision source: CP3b items 1, 2, 4, 5 and 11, after the round-2 review `P3S/R2_REVIEW_40_v2.md` (F1, M1, M3, M4, M10).*

### 1. Status: post hoc, descriptive

A4 is a sensitivity analysis added after every v2 TEST, A2 and A3 result was seen. It has no pass criterion. It changes no prediction, threshold, grid, seed, verdict or earlier number, and no A4 quantity may be used to re-score anything. Table III keeps its registered counting.

### 2. Report energy in r

r := (E_det + E_rep) / e_idle, where E_det is the detector energy of one activation slot and E_rep is the energy of sending one report. Worst case: **one report on every activation**. The schedule therefore stays event-independent, and the storage need is an upper bound for any rule that reports less often. Every theorem is unchanged, because r is only a parameter.

The registered value r_reg = 14.3 (reference node, e_idle = 0.248 mJ, so E_det = r_reg × e_idle = 3.546 mJ) is the baseline. The measured loop of its source (capture, demosaic, inference, post-processing, `P0/ENERGY_MODEL_40.md`) has no transmission stage, so r_reg absorbs **0 mJ** of report energy per activation. Reported in addition: the report energy per activation that the registered panel margin at m = 0.25 and at m = 1 could pay without changing the panel, from the energy balance at a = 1/8.

r_radio = r_reg + E_rep / e_idle. E_rep comes from reference [2] (Van Leemput et al., IEEE IoT-J 2023, doi 10.1109/JIOT.2023.3263543, read from the Ghent University repository copy, submitted version, `lit/sources/radio/`). One uplink report with an 8-byte application payload (the fixed payload of the LoRaWAN measurement that [2] builds on), one hop, no retransmission:

- **LoRaWAN Class A**, Eq. (9)–(11) and Table VI (SODAQ ExpLoRer, 2.7 V, 14 dBm, sleep between tasks so no start-up energy): E_rep = 166 mJ + 134 mW × T_TX, with T_TX from Eq. (9)–(10) at SF7, 125 kHz, coding rate 4/5, 8 preamble symbols, explicit header, no low-data-rate optimisation, PL = 8.
- **BLE Mesh low-power node**, Eq. (15)–(16) and Table VII (nRF52840, 1.8 V, 4 dBm, three advertising channels): E_rep = 6.2 µJ + 16.4 mW × 3 T_TX, with T_TX = 8 (PL + 18) / R and R = 1 Mbit/s, PL = 8. The periodic poll task of Eq. (17) is not per activation and is left out.
- **6TiSCH leaf node**, Eq. (22) and Table VIII (OpenMote, CC2538 at 2.4 GHz, 3.3 V): E_rep = 336.5 µJ + 0.174 µJ × S_TX with S_TX = 38 + 8 = 46 bytes.

Energies are taken at the voltages of [2]; no regulator loss is added. Recorded for each radio: E_rep, r_radio, and whether the radio task fits the activation period of 0.8 s at K = 8. The task lengths of [2] are 2.2 s + T_TX for LoRaWAN Class A (Eq. 13), 24.3 ms + 3 T_TX for BLE (Eq. 20) and one 15-ms slot for 6TiSCH. A radio whose task does not fit is reported as an **energy-only sensitivity, not a schedulable configuration**, in the main text.

### 3. Cells and products

Primary cells: **17 site–season cells** = HCMC 4 (Himawari-9), Madrid 4 and Uppsala 4 with the **MSG** product, indoor 5. MSG is primary because it has the finer native step (15 min against 30 min for SARAH-3) and is the first listed product of the registered site table. The second product is a sensitivity: the 8 SARAH-3 cells are run identically and reported separately.

Counts of adverse outcomes use **either product**: a site–season cell counts if either of its products shows the outcome, so that choosing a primary product cannot remove an adverse cell. The medians use the primary product, with the value on the other product in brackets where the text gives a Madrid or Uppsala median.

### 4. Quantities

Reference node l = 0.036, K = 8, a = 1/8, slot 0.1 s, full-trace series (`split = all`, as Table IV). For each cell, each r in {r_reg, r_BLE, r_6TiSCH, r_LoRaWAN} and m = 0.25 (primary) and m = 1.0 (secondary):

- the panel is rescaled at each r by the registered definition `traces.scale_panel` (mean harvest = (1 + m)(1 + l + (r − 1)/8));
- **C\*** = `energy.C_periodic` on the full series, which equals C_per at ε = ε\*(1/8); at r_reg it must reproduce `results/F5_sizing_all.json` (relative difference ≤ 10⁻⁹) or the run stops;
- **C_LB^lo, C_LB^hi** and **C_TS^exact** at ε = ε\*(1/8) + 10⁻⁹ with the law of `split = all` and the A2 functions (`P3R/run_a2_sizing.py`: `lb_bounds`, `ts_exact_hi`, relative tolerance 0.01);
- C\*(r_radio)/C\*(r_reg), in J and in e_idle;
- the implied panel: P_mean = (1 + m)(1 + l + (r − 1)/8) e_idle / 0.1 s and W_p = P_mean × 1000 / mean(GHI), for outdoor cells. This assumes a horizontal panel with constant conversion efficiency, so module efficiency cancels; no temperature, MPPT or regulator loss is included.

Output `results/a4_radio.json`, including `a_eps`, the trace length in days and the mean GHI.

### 5. Counting on 17 cells (read-only; no simulation)

From existing result files, written to `results/a4_count17.json`:

- (a) Holm's correction (`bootstrap.holm`, α = 0.05) on the p-values of `results/boot_test.json` restricted to the 17 primary cells: 17 × 2 sign tests plus the taut-string test of the primary cells among the six bootstrap cells.
- (b) Harvest-following ranges (`dmiss`, `dC_rel`) over the 17 cells.
- (c) Sizing-rule ratio medians per site from `results/summary_test.json` `main.baselines`, for the primary cells and for the second product, computed like the registered group medians.
- (d) A3 recounted: worst-spell ratio over the 17 cells; k = C_TEST/C_TRAIN over the 17 cells (median) and the adverse counts by the either-product rule of §3: number of site–season cells with k > 2 and with k infinite; per-cell ranges of A3 §4 for the primary cells.
- (e) One source for Tables IV and S14–S18: C\* of Table IV stays `results/F5_sizing_all.json`. A3 removed a final partial day, so its base value can differ for the indoor traces; the difference is recorded per cell.

### 6. Consequence for the earlier article (read-only)

For reference [14] (Deep3): the quantities of [14] whose definition coincides with this project's (E[D], median, CV, maximum and ε\*(a) = E[(1 − aD)^+] at the activations printed in [14], and the miss of a Bernoulli schedule E[(1 − a)^D]) are computed with the `events` module on both the earlier corpus (3,713 events, `results/_v1_corpus3713/event_corpus_40.csv`) and the corrected corpus (3,170). The earlier-corpus column must reproduce the values printed in [14] to the printed precision; a mismatch is reported as a definition mismatch and that row becomes "not recomputed". Quantities that need the per-frame gate scores or the timeline replay of [14] are marked "not recomputed". Output `P3T/DEEP3_IMPACT_40.md`.

### 7. What will be run

`code/sim40/a4_sensitivity.py` (parts `radio`, `count17`, `deep3`), one process, inside 08:00–23:00, with at least 7 GB of free RAM at the start of each step; m = 1.0 only if the window allows. Existing result files are not overwritten; `grid_ckpt_v2` is not written. Code added: that module, its tests on synthetic data, `code/a4b_fetch_hcmc.py`; no existing module of `code/sim40/` changes. `code/paper/build_tgcn.py` may change, since it only typesets.

### 8. Reporting

All A4 numbers are labelled post hoc and descriptive in the sizing section and in Threats to Validity. A value that is unfavourable, including a radio whose task does not fit the activation period, is reported as computed.

### 9. What the analyst had seen (disclosure)

Every v2 TEST, A2 and A3 number, including the per-cell k values, among them that the only infinite k of A3 is a SARAH-3 cell (which is why §3 uses the either-product rule for adverse counts). Before writing this amendment the analyst worked out E_rep from [2] by hand: about 171 mJ (LoRaWAN), 0.016 mJ (BLE), 0.34 mJ (6TiSCH), hence r of about 703, 14.4 and 15.7, and saw that the LoRaWAN task is longer than the activation period. The analyst read the headline statistics of [14]. No C\*, bound or schedule at any r_radio had been computed, and no value of §5 or §6 had been computed except those already printed in the manuscript and in A1 §7.

## A4b (09-11-2026): post-hoc inter-annual sensitivity, one site

*Written and hashed with A4, before any data of this section was downloaded. Tag: `prereg-40-a4`. Decision source: CP3b item 6, review item M5.*

### 1. Status

Post hoc, descriptive; no pass criterion; changes no verdict and no earlier number.

### 2. Data

Ho Chi Minh City, the same request as the 2025 file (`code/p0_fetch_irradiance.py`): latitude 10.80, longitude 106.70, Open-Meteo satellite archive, `models=jma_jaxa_himawari`, `hourly=shortwave_radiation`, `temporal_resolution=native`, quarterly requests, for the calendar years 2020–2024. No e-mail or key in any parameter. Files `HCMC_jma_jaxa_himawari_<year>.csv` in `$THS_DATASETS/OpenMeteo_HCMC_2020_2024/` with `DATA_SOURCES.md` (URLs, SHA-256, licence CC BY 4.0). Free space on drive D is checked and logged first. A year or season the archive does not serve at that step is reported as missing and is not filled from another product. The satellite changed from Himawari-8 to Himawari-9 during this period; this is noted in the reporting.

### 3. Quantities

The 2025 pipeline: gaps interpolated up to one hour, zero-order hold to 1-min sub-steps, a season = the months of that calendar year in the climatological order (DJF = December, January, February of the same year, as for 2025), cyclic. Panel scaled for each year–season by the registered definition at m = 0.25 and m = 1. Reference node r_reg. C\* per year × 4 seasons (J), and the same for 2025 from the 2025 file (must equal `results/F5_sizing_all.json`, relative difference ≤ 10⁻⁹, or the run stops). Per season: minimum, maximum and max/min over the years; over seasons: the largest max/min. Because the panel is rescaled every year, this measures the variability of the worst spell at a matched mean harvest, not the shortfall of a fixed panel in a dark year; the reporting says so. Output `results/a4b_interannual.json`.

### 4. What will be run

`code/a4b_fetch_hcmc.py`, then part `a4b` of `code/sim40/a4_sensitivity.py`, under the guards of A4 §7, before part `radio`.

### 5. What the analyst had seen

No irradiance of 2020–2024 and no inter-annual statistic.

*SHA-256 of the A4 + A4b text above, as appended (from the blank line before "## A4 (09-11-2026)" through the line before this note, with its final newline): `d7d1b7da2ac53b7cd2e59f1b36319efd08a4a8958bdf064a647d70b573681a1f`. The hash of the whole file is in `AMENDMENT_LOG.sha256`.*

## A5 (09-11-2026): post-hoc fixed-panel sensitivity of the report energy

*Written and hashed before any A5 code exists and before any A5 number is computed. Tag: `prereg-40-a5`. Sections A1–A4b above are unchanged. Decision source: CP3c item 3, after the round-3 review `P3T/R2_REVIEW_40_v3.md` (§2, N9).*

### 1. Status: post hoc, descriptive

A5 is a sensitivity analysis added after every earlier result was seen. It has no pass criterion. It changes no prediction, threshold, grid, seed, verdict or earlier number, and no A5 quantity may be used to re-score anything. Table III is unchanged.

### 2. Definition

The panel stays at the size registered for r_reg = 14.3 at m = 0.25 (`traces.scale_panel(g, 14.3, 0.036, 0.25)` on the full-trace cell, as Table IV), and is not rescaled. The node then pays the A4 report energy: r_BLE and r_6TiSCH of `results/a4_radio.json` (one report on every activation). LoRaWAN is not run: at a = 1/8 its demand exceeds the registered panel's mean income, by A4 §2 (margin 1.34 mJ per activation against 171 mJ).

Reference node l = 0.036, K = 8, a = 1/8, slot 0.1 s, `split = all`. Cells: the 17 primary site–season cells of A4 §3, with the 8 SARAH-3 cells run identically and reported separately. For each cell and each radio:

- **C\*_fixed** = `energy.C_periodic(h, 600, r_radio, 0.036, 1/8)`, the capacity at ε = ε\*(1/8), infinite if the cycle has a net deficit. At r_reg the same code path must reproduce `results/F5_sizing_all.json` (relative difference ≤ 10⁻⁹) or the run stops.
- **C_LB^lo, C_LB^hi** and **C_TS^exact** at ε = ε\*(1/8) + 10⁻⁹ with the A2 functions, as in A4 §4.
- The ratio C\*_fixed / C\*_reg, and the ratio C\*_fixed / C\*_rescaled (A4 value at the same radio).
- The energy balance: mean income minus demand per slot, and whether the cell has lost it.

Reported per radio over the 17 cells, and separately over the 8 sensitivity cells: minimum, median and maximum ratio; the cells that lost energy balance, printed by name; the number of cases with C_LB^lo > C_TS^exact. Output `results/a5_fixed_panel.json`.

### 3. Reporting

All A5 numbers are labelled post hoc and descriptive. An unfavourable result, including a cell that loses energy balance, is printed as computed.

## A5b (09-11-2026): reproduction of the gate results of the earlier article on the corrected corpus

*Written and hashed with A5, before this rerun. Tag: `prereg-40-a5`. Decision source: CP3c item 1. This is a reproduction of reference [14] (doi 10.1109/JIOT.2026.3740931), not a new experiment of this project, and it changes nothing in this project's results.*

### 1. What is reproduced

The corpus-dependent gate results of [14]: the gain–cost decomposition at the deployed gate (Sec. VI, Thm. 9); the operating family against the frontier (Sec. VII-D, Fig. 2 and Table S5 inputs, per-dataset peaks); ablation and baselines at equal energy (Sec. VII-E, Table S5); event density and the alignment–density law (Sec. VII-F, Fig. 3, Fig. S8); the certification table and the leak-then-fix witness (Sec. VII, Table S2, Fig. S6). Also the other corpus-dependent statistics that the same batch produces (Sec. V, Tables S1, S3, S4). **The hardware energy measurements of [14] (Jetson Orin Nano on INA3221, ESP32-S3 on INA219) do not depend on the corpus and are not rerun.**

### 2. Code and inputs

The Deep3 code as copied by the audit of topic 17 on 27-09-2026 (`17_Sim2Real_Certification/legacy/audit_B0_deep3_pa/deep3/`, runs `run_old` = 3,713 events and `run_corr` = 3,170 events, protocol and seeds of the article: run_all 42, A1 7, A5/A6 20260916, B1 3, B2 21). Folder 17, the Deep3 folders and repository, and #05 are **read only**. The two runs are copied to `$THS_DATASETS/_derived/40/deep3_rerun/`; in the copy the absolute paths are rewritten to the copy and nothing else changes, and the rewrite is logged. `cfs/` and `scripts/` are checked file by file against the published Deep3 repository.

The inputs are the processed files of those runs. In `run_corr` the LASIESTA rows come from the gate re-run of 27-09-2026 on time-ordered detections; CDnet 2014 and BMC rows are the published ones. The gate pass on LASIESTA is not re-executed here: the audit validated it by reproducing all 936 published LASIESTA event outcomes in text order.

### 3. What will be compared

The batch `run_batch.sh` of the audit (run_all phases 1–2, sim_phase, analyze_mdep, analyze_relcorr, analyze_detector, sweep_tau, analyze_alignment, analyze_activation, check_thm4_and_integrity, b1_ablation_sota, b2_dilution), for both runs, one process at a time. Every numeric value in the output JSON files is compared with the audit's outputs (absolute tolerance 10⁻⁹). If they agree, the 67 rows of `17_Sim2Real_Certification/results/b0_deep3_impact.json` are adopted; a value that differs is printed and the rerun value is used. Rows the audit marks as not reproducible on 3,713 events stay marked. Printed values are checked against the FINAL manuscript and supplement PDFs of [14] in this machine. A step that cannot run is reported as "not reproducible from available code" with the reason. Output `results/a5b_deep3_gate.json`, `P3U/DEEP3_IMPACT_40_v2.md`.

### 4. What will be run

`code/sim40/a5_sensitivity.py`, `P3U/setup_deep3_rerun.py`, `P3U/run_a5_chain.py` (one process; each step starts inside 08:00–23:00 with at least 7 GB free), `P3U/a5b_compare.py`. Existing result files are not overwritten; `grid_ckpt_v2` is not written. No existing module of `code/sim40/` changes.

### 5. What the analyst had seen (disclosure)

For A5: every earlier number of this project, the panel margin of A4 and the round-3 review's expectation that C\* rises by a cell-dependent factor. No C\* at a fixed panel with a radio had been computed. For A5b: the full table of the 27-09-2026 audit (`17_Sim2Real_Certification/notes/_b0_deep3_section.md`), including its corrected gate values and its list of conclusions that change. The rerun therefore reproduces known numbers and is not blind.

*SHA-256 of the A5 + A5b text above, as appended (from the blank line before "## A5 (09-11-2026)" through the line before this note, with its final newline): `5d48dfbd74f19a1fd7f91ed583ac8d7d955c559d2de9bea23b28e4c00a115307`. The hash of the whole file is in `AMENDMENT_LOG.sha256`.*
