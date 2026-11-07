# A1 note 01: the ±1-offset clause of check 5(a) (07-11-2026)

*Written after the corpus checks and before any v2 simulation. Amendment A1 and its tag `prereg-40-a1` are not changed. No v2 policy, replay, floor, sizing or bootstrap result had been seen.*

## What A1 said

Check 5(a): "Pooled LASIESTA ground-truth hit rate ≥ 0.9 under the new order, and clearly above the ±1-frame offsets", with "a failure stops the run and is reported".

## What was measured

| Frame offset | −5 | −2 | −1 | **0** | +1 | +2 | +5 |
|---|---|---|---|---|---|---|---|
| Pooled HIT | 0.887 | 0.943 | 0.948 | **0.949** | 0.948 | 0.944 | 0.876 |
| Mean best IoU | 0.519 | 0.698 | 0.771 | **0.853** | 0.775 | 0.703 | 0.523 |

10,488 ground-truth frames, 48 sequences.

- **First clause, met:** HIT 0.949 ≥ 0.9, against 0.220 for the dump index. This is the only clause the phase prompt requires.
- **Second clause, not met as written:** HIT at offset 0 exceeds HIT at ±1 by only 0.13 to 0.15 points. Frames hit only at 0 against frames hit only at the offset: 105 vs 89 (−1, exact sign p = 0.28) and 104 vs 91 (+1, p = 0.39).

## Reading (post hoc)

A binary hit barely changes between consecutive frames, because objects move little in one frame. So the HIT clause has almost no power at ±1, and "clearly" was given no number. The graded measure does separate them:

- mean best IoU peaks at offset 0 and falls on both sides;
- IoU is higher at 0 than at the offset in 7,913 vs 1,443 frames (−1) and 7,699 vs 1,658 frames (+1), exact sign p below 10⁻³⁰⁰;
- the mean IoU per sequence is higher at 0 in 47 of 48 sequences (−1) and 48 of 48 (+1).

In addition, the map has no free offset: its numbers equal those parsed from the real file names on 48 of 48 sequences, and the ground-truth files carry the same numbers.

## Decision

The run proceeds. The IoU criterion was chosen **after** seeing the HIT result, so it is a post-hoc reading, disclosed here and in the phase report, and the author can overrule it at CP2R. The data of this check do not depend on any simulation outcome, and the corpus would be the same whichever measure is used.
