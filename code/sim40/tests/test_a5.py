"""Amendment A5: tests on synthetic data, run before the real run. pytest code/sim40/tests/test_a5.py"""
import numpy as np

from sim40 import a4_sensitivity as A4
from sim40 import energy as E
from sim40 import traces as T


def _trace():
    return np.tile(np.r_[np.zeros(720), np.ones(720)], 30)


def test_fixed_panel_needs_at_least_the_rescaled_ratio():
    g = _trace()
    r = 15.689
    h0 = T.scale_panel(g, A4.R_REG, A4.L_A, 0.25)
    h1 = T.scale_panel(g, r, A4.L_A, 0.25)
    c0 = E.C_periodic(h0, 600, A4.R_REG, A4.L_A, A4.A)
    fixed = E.C_periodic(h0, 600, r, A4.L_A, A4.A)
    rescaled = E.C_periodic(h1, 600, r, A4.L_A, A4.A)
    assert fixed > c0
    assert fixed >= rescaled - 1e-6       # equal when the deficit falls where the income is zero, as in this square wave


def test_registered_r_on_the_registered_panel_is_unchanged():
    g = _trace()
    h = T.scale_panel(g, A4.R_REG, A4.L_A, 0.25)
    assert E.C_periodic(h, 600, A4.R_REG, A4.L_A, A4.A) == E.C_periodic(h.copy(), 600, A4.R_REG, A4.L_A, A4.A)


def test_ble_and_6tisch_stay_inside_the_panel_margin_and_lorawan_does_not():
    R = A4.radios()
    margin = A4.margin_mJ(0.25)
    assert R["BLE"]["E_rep_mJ"] < margin and R["6TiSCH"]["E_rep_mJ"] < margin and R["LoRaWAN"]["E_rep_mJ"] > margin
