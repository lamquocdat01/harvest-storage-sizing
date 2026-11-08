"""Exact miss (Lemma 1) of the realised slot schedule of a fluid run (Amendment A2, prereg/AMENDMENT_LOG.md).

A fluid run gives, per sub-step j of n slots, an on-fraction f_j (the node is on during the first f_j n slots)
and a rate a_j in [0, 1]. Its realised slot schedule is the phase-continuous interleaving (Bresenham) of the
cumulative fluid activation count
    A(t) = P_j + a_j * min(u, f_j n),   t = j n + u,   P_j = sum_{i<j} a_i f_i n,
with a FIXED phase phi (A2: phi = 0.5): the k-th activation (k = 1, 2, ...) happens at the real time tau_k where
A(tau_k) = k - phi, i.e. in slot sigma_k = ceil(tau_k) - 1. This is the schedule that `metrics.replay_miss`
replays (there the phase is random): an event [s, s + d) is caught iff some tau_k lies in (s, s + d], i.e. iff
some sigma_k lies in {s, ..., s + d - 1}. The rate cap a_j <= 1 gives at most one activation per slot.

On the cyclic horizon of T = J n slots, Lemma 1 gives
    miss = 1 - (1/T) sum_i G(g_i),   G(g) = sum_{k<g} P(D > k) = E[min(g, D)]  (= E[D] for g >= D_max),
over the cyclic gaps g_i of the activation slots (wrap gap sigma_1 + T - sigma_N).

Fast path, O(J): inside a sub-step the crossing times form an arithmetic progression with step 1/a_j, so
consecutive activation slots differ by floor(1/a_j) or floor(1/a_j) + 1 (ceil(y + c) - ceil(y) is one of these
two values). The m_j - 1 gaps inside sub-step j are therefore fixed by their sum sigma_last - sigma_first and
their count: n_hi = sum - (m_j - 1) g with g = floor(sum / (m_j - 1)). Only the first and the last activation of
each sub-step are computed; gaps between sub-steps and the wrap gap are computed directly.
`activation_slots` + `exact_miss_from_slots` is the direct O(#activations) reference used by the tests.
"""
from __future__ import annotations

import numpy as np

from .events import DurationLaw

PHASE = 0.5        # A2: fixed phase
N_SUB = 600        # slots per 1-min sub-step at 10 fps


def _prep(on_frac, rate, n):
    f = np.asarray(on_frac, float)
    a = np.asarray(rate, float)
    if f.shape != a.shape:
        raise ValueError("on_frac and rate must have the same length")
    if np.any(a < -1e-12) or np.any(a > 1 + 1e-12):
        raise ValueError("rate cap violated: rates must lie in [0, 1]")
    a = np.clip(a, 0.0, 1.0)
    f = np.clip(f, 0.0, 1.0)
    per = a * f * n                                     # fluid activations per sub-step
    P = np.r_[0.0, np.cumsum(per)]
    return f, a, P


def _first_last(f, a, P, n, phase):
    """Per active sub-step: index j, count m_j, first and last activation slot."""
    klo = np.floor(P[:-1] + phase) + 1.0                # first k with k - phase > P_j
    khi = np.floor(P[1:] + phase)                       # last k with k - phase <= P_{j+1}
    m = (khi - klo + 1.0).astype(np.int64)
    act = (m > 0) & (a > 0)
    j = np.flatnonzero(act)
    if j.size == 0:
        return j, m[j], np.zeros(0, np.int64), np.zeros(0, np.int64)
    aj = a[j]
    base = j * float(n)
    tau_first = base + (klo[j] - phase - P[j]) / aj
    tau_last = base + (khi[j] - phase - P[j]) / aj
    s_first = (np.ceil(tau_first) - 1.0).astype(np.int64)
    s_last = (np.ceil(tau_last) - 1.0).astype(np.int64)
    return j, m[j], s_first, s_last


def exact_miss(on_frac, rate, law: DurationLaw, n=N_SUB, phase=PHASE, return_detail=False):
    """Exact miss (Lemma 1) of the realised schedule; O(J) in the number of sub-steps."""
    f, a, P = _prep(on_frac, rate, n)
    J = f.size
    T = J * int(n)
    j, m, s_first, s_last = _first_last(f, a, P, n, phase)
    N = int(m.sum())
    if N == 0:
        out = 1.0
        return (out, {"n_act": 0, "T": T, "gap_sum": 0}) if return_detail else out
    # inside sub-steps
    inner_cnt = m - 1
    span = s_last - s_first
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.where(inner_cnt > 0, span // np.maximum(inner_cnt, 1), 0)
    n_hi = np.where(inner_cnt > 0, span - inner_cnt * g, 0)
    n_lo = inner_cnt - n_hi
    if np.any(n_hi < 0) or np.any(n_lo < 0):
        raise AssertionError("inner gaps are not in {g, g+1}: numerical issue in the crossing times")
    tot = float((n_lo * law.phi(g)).sum() + (n_hi * law.phi(g + 1)).sum())
    # between active sub-steps, and the wrap gap
    between = s_first[1:] - s_last[:-1]
    wrap = s_first[0] + T - s_last[-1]
    gaps_b = np.r_[between, wrap]
    if np.any(gaps_b < 1):
        raise AssertionError("two activations in one slot: rate cap or numerical issue")
    tot += float(law.phi(gaps_b).sum())
    gap_sum = int(span.sum() + gaps_b.sum())
    if gap_sum != T:
        raise AssertionError(f"gaps sum to {gap_sum}, not T = {T}")
    miss = 1.0 - tot / T
    if return_detail:
        return miss, {"n_act": N, "T": T, "gap_sum": gap_sum, "a_real": N / T}
    return miss


def activation_slots(on_frac, rate, n=N_SUB, phase=PHASE):
    """Direct reference: every activation slot sigma_k = ceil(tau_k) - 1 (O(#activations) memory)."""
    f, a, P = _prep(on_frac, rate, n)
    j, m, s_first, _ = _first_last(f, a, P, n, phase)
    if j.size == 0:
        return np.zeros(0, np.int64)
    klo = np.floor(P[j] + phase) + 1.0
    rep_j = np.repeat(j, m)
    k = np.repeat(klo, m) + (np.arange(m.sum()) - np.repeat(np.cumsum(m) - m, m))
    tau = rep_j * float(n) + (k - phase - P[rep_j]) / a[rep_j]
    return (np.ceil(tau) - 1.0).astype(np.int64)


def exact_miss_from_slots(slots, T, law: DurationLaw):
    """Lemma 1 on an explicit set of activation slots of a cyclic horizon of T slots."""
    s = np.unique(np.asarray(slots, np.int64))
    if s.size == 0:
        return 1.0
    gaps = np.r_[np.diff(s), s[0] + T - s[-1]]
    return 1.0 - float(law.phi(gaps).sum()) / T


def brute_force_miss(x, law: DurationLaw):
    """Definition 3 directly: x in {0,1}^T, onsets uniform on Z_T, D ~ law, cyclic. O(T * D_max)."""
    x = np.asarray(x, bool)
    T = x.size
    xx = np.r_[x, x]
    miss = 0.0
    for d in np.flatnonzero(law.pmf):
        dd = int(min(d, T))
        win = np.convolve(xx.astype(int), np.ones(dd, int), "full")[dd - 1: dd - 1 + T]   # window [s, s+dd)
        miss += law.pmf[d] * np.mean(win == 0)
    return float(miss)


def slot_schedule_by_crossing(on_frac, rate, n=N_SUB, phase=PHASE):
    """Independent construction for the brute-force test: x_t = 1 iff floor(A(t+1) + phase) > floor(A(t) + phase),
    with A evaluated at integer slot boundaries from its piecewise-linear definition."""
    f, a, P = _prep(on_frac, rate, n)
    J = f.size
    t = np.arange(J * int(n) + 1)
    j = np.minimum(t // int(n), J - 1)
    u = t - j * int(n)
    A = P[j] + a[j] * np.minimum(u, f[j] * n)
    A[-1] = P[-1]
    return np.floor(A[1:] + phase) > np.floor(A[:-1] + phase)
