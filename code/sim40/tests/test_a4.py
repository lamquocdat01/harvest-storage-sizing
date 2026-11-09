"""Amendment A4: tests on synthetic data, run before the real run. pytest code/sim40/tests/test_a4.py"""
import math

import numpy as np

from sim40 import a4_sensitivity as A4
from sim40 import energy as E
from sim40 import traces as T


def test_radio_values_match_the_formulas_of_ref2():
    r = A4.radios()
    t, s = A4.t_lora(8)
    assert s == 35.25                                     # 8 + 4.25 + 8 + ceil(80/28) * 5
    assert abs(t - 35.25 * 128 / 125e3) < 1e-12
    assert abs(r["LoRaWAN"]["E_rep_mJ"] - (166 + 134 * t)) < 1e-9
    assert abs(r["BLE"]["E_rep_mJ"] - (6.2 + 16.4e3 * 3 * 208e-6) / 1e3) < 1e-12
    assert abs(r["6TiSCH"]["E_rep_mJ"] - 344.504e-3) < 1e-9


def test_r_adds_report_energy_in_units_of_idle():
    r = A4.radios()
    for x in r.values():
        assert abs((x["r"] - A4.R_REG) * A4.EIDLE_J * 1e3 - x["E_rep_mJ"]) < 1e-9


def test_lorawan_task_does_not_fit_the_activation_period_and_the_others_do():
    r = A4.radios()
    assert not r["LoRaWAN"]["fits_activation_period"]
    assert r["BLE"]["fits_activation_period"] and r["6TiSCH"]["fits_activation_period"]


def test_panel_margin_is_the_energy_balance_at_a_eighth():
    for m in (0.25, 1.0):
        e = A4.margin_mJ(m) / (A4.EIDLE_J * 1e3)              # extra r the panel pays
        h = (1 + m) * (1 + A4.L_A + (A4.R_REG - 1) / 8)
        assert abs(1 + A4.L_A + (A4.R_REG + e - 1) / 8 - h) < 1e-12


def test_storage_need_grows_with_r_at_rescaled_panel():
    g = np.tile(np.r_[np.zeros(720), np.ones(720)], 30)
    c = [E.C_periodic(T.scale_panel(g, r, A4.L_A, 0.25), 600, r, A4.L_A, A4.A) for r in (14.3, 15.7, 703.2)]
    assert c[0] < c[1] < c[2] and all(math.isfinite(x) for x in c)


def test_primary_set_has_17_site_season_cells():
    n = sum(1 for s, _ in T.cells() if A4.is_primary(s))
    assert n == 17 and all(A4.is_primary(s) for s in A4.SECOND)
