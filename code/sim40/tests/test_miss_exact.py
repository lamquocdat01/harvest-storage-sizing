"""Tests of the exact miss of the realised slot schedule (Amendment A2).

t1  constant rate a with aT integer: exact miss = eps*(a) within 1e-12 (Theorem 1(v)).
t2  5 random fluid schedules (with outages): exact miss agrees with metrics.replay_miss within 3 SE,
    at the phase that replay_miss draws.
t3  brute force over onsets and durations (Definition 3) on small T, from an independently built slot
    schedule: equal to 1e-12; the O(J) path equals the direct O(#activations) reference.
Run: python -m pytest code/sim40/tests/test_miss_exact.py -q
"""
from __future__ import annotations

import numpy as np
import pytest

from sim40 import metrics as M
from sim40 import miss_exact as X
from sim40.events import DurationLaw, corpus_law


@pytest.fixture(scope="module")
def law():
    return corpus_law()


@pytest.mark.parametrize("K", [2, 3, 7, 8, 13, 64])
def test_t1_constant_rate_attains_floor(law, K):
    n, J = 600, 96                      # T = 57,600 slots; if aT is not an integer, use J = 10 K instead
    a = 1.0 / K
    T = n * J
    if abs(a * T - round(a * T)) > 1e-9:
        J = K * 10
        T = n * J
    m = X.exact_miss(np.ones(J), np.full(J, a), law, n=n)
    assert abs(m - float(law.eps_star(a)[0])) <= 1e-12


def test_t1_interleaved_noninteger_period(law):
    n, J = 600, 100
    T = n * J
    for nact in (7_919, 12_345, 21_000):     # aT integer, 1/a not integer
        a = nact / T
        m = X.exact_miss(np.ones(J), np.full(J, a), law, n=n)
        assert abs(m - float(law.eps_star(a)[0])) <= 1e-12


def _random_schedule(rng, J):
    """Piecewise rates with day/night structure and a few partial outages."""
    a = np.clip(rng.gamma(2.0, 0.06, J) * (rng.random(J) < 0.85), 0, 1)
    f = np.ones(J)
    out = rng.random(J) < 0.03
    f[out] = rng.random(out.sum())
    f[rng.random(J) < 0.02] = 0.0
    return f, a


def test_t2_matches_replay(law):
    durations = np.repeat(np.arange(law.pmf.size), np.round(law.pmf * 3170).astype(int))
    rng = np.random.default_rng(42)
    n, J, n_ev = 600, 2000, 200_000
    for i in range(5):
        f, a = _random_schedule(rng, J)
        seed = 1000 + i
        r2 = np.random.default_rng(seed)          # replicate the draws of replay_miss to read its phase
        d = durations[r2.integers(0, len(durations), n_ev)]
        r2.integers(0, J * n, d.size)
        phase = r2.random()
        rep, ne = M.replay_miss(f, a, durations, n_ev, np.random.default_rng(seed), n_sub=n)
        ex = X.exact_miss(f, a, law, n=n, phase=phase)
        se = np.sqrt(max(rep * (1 - rep), 1e-12) / ne)
        assert abs(ex - rep) <= 3 * se, (i, ex, rep, se)


def test_t3_brute_force_small_T():
    rng = np.random.default_rng(7)
    law = DurationLaw(np.array([1, 1, 1, 2, 3, 3, 5, 8, 13, 21]))
    for trial in range(40):
        n, J = int(rng.integers(3, 12)), int(rng.integers(2, 9))
        a = np.clip(rng.random(J) * (rng.random(J) < 0.8), 0, 1)
        f = np.where(rng.random(J) < 0.2, rng.random(J), 1.0)
        phase = float(rng.random())
        x = X.slot_schedule_by_crossing(f, a, n=n, phase=phase)
        bf = X.brute_force_miss(x, law)
        ex = X.exact_miss(f, a, law, n=n, phase=phase)
        ref = X.exact_miss_from_slots(np.flatnonzero(x), n * J, law)
        assert abs(ex - bf) <= 1e-12, (trial, ex, bf)
        assert abs(ref - bf) <= 1e-12


def test_t3_fast_equals_direct_reference(law):
    rng = np.random.default_rng(11)
    n, J = 600, 3000
    for _ in range(5):
        f, a = _random_schedule(rng, J)
        slots = X.activation_slots(f, a, n=n)
        assert np.all(np.diff(slots) >= 1)
        assert abs(X.exact_miss(f, a, law, n=n) - X.exact_miss_from_slots(slots, n * J, law)) <= 1e-12


def test_rate_cap_enforced(law):
    with pytest.raises(ValueError):
        X.exact_miss(np.ones(3), np.array([0.2, 1.5, 0.1]), law)
