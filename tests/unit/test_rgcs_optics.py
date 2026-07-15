"""Unit tests for the Agent 06 crystal optical application
(rgcs_core.optics): quartz constants, ray/path model, photoelastic and
acousto-optic estimates.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from rgcs_core.optics import (QUARTZ_N_E, QUARTZ_N_O, QUARTZ_PHOTOELASTIC,
                              acousto_optic_m2, optical_path_length_mm,
                              optical_phase_rad, photoelastic_index_shift,
                              quartz_acousto_optic_m2, quartz_birefringence,
                              quartz_indices, ray_to_target,
                              snell_refraction)


def test_quartz_indices_positive_uniaxial():
    idx = quartz_indices()
    assert idx["n_o"] == QUARTZ_N_O and idx["n_e"] == QUARTZ_N_E
    # positive uniaxial: n_e > n_o, delta_n ~ +0.0091
    assert quartz_birefringence() == pytest.approx(0.0091, abs=1e-4)


def test_snell():
    # normal incidence passes straight through
    assert snell_refraction(0.0, 1.0, QUARTZ_N_O) == pytest.approx(0.0)
    # bends toward the normal entering the denser medium
    assert snell_refraction(30.0, 1.0, QUARTZ_N_O) < 30.0
    # explicit value check
    expect = math.degrees(math.asin(math.sin(math.radians(30.0)) / QUARTZ_N_O))
    assert snell_refraction(30.0, 1.0, QUARTZ_N_O) == pytest.approx(expect)
    # TIR only possible high -> low index
    with pytest.raises(ValueError):
        snell_refraction(80.0, QUARTZ_N_O, 1.0)


def test_opl_and_phase():
    opl = optical_path_length_mm(100.0, QUARTZ_N_O)
    assert opl == pytest.approx(154.43)
    # phase = 2*pi*OPL/lambda; one wavelength of OPL = 2*pi
    lam_nm = 632.8
    phi = optical_phase_rad(lam_nm * 1e-6, lam_nm)   # OPL of one lambda in mm
    assert phi == pytest.approx(2 * math.pi)


def test_ray_to_target_addresses_node():
    # entry on a facet to the measured node: geometry answers 'can an
    # optical path address a measured mode-overlap region' affirmatively
    r = ray_to_target(np.array([12.0, 0.0, 40.0]),
                      np.array([0.0, 0.0, 71.5]))
    expect_len = float(np.linalg.norm([12.0, 0.0, -31.5]))
    assert r["geometric_length_mm"] == pytest.approx(expect_len)
    assert r["optical_path_length_mm"] == pytest.approx(
        expect_len * QUARTZ_N_O)
    assert r["transit_time_s"] == pytest.approx(
        r["optical_path_length_mm"] * 1e-3 / 299_792_458.0)
    assert np.linalg.norm(r["direction"]) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        ray_to_target(np.zeros(3), np.zeros(3))


def test_photoelastic_shift_magnitude():
    # quartz p11 with a typical acoustic strain 1e-7: delta_n ~ -3e-8
    dn = photoelastic_index_shift(QUARTZ_N_O, QUARTZ_PHOTOELASTIC["p11"],
                                  1e-7)
    assert dn == pytest.approx(-0.5 * QUARTZ_N_O ** 3 * 0.16 * 1e-7)
    assert -5e-8 < dn < -1e-8


def test_quartz_m2_order_of_magnitude():
    # quartz is a POOR acousto-optic material; M2 must be small,
    # order 1e-15 s^3/kg (dedicated AO materials are 100-1000x higher)
    m2 = quartz_acousto_optic_m2()
    assert 1e-16 < m2 < 1e-14
    # generic formula sanity: fused-silica-like inputs give ~1.5e-15
    fs = acousto_optic_m2(1.46, 0.27, 2200.0, 5960.0)
    assert fs == pytest.approx(1.51e-15, rel=0.05)


def test_v2_classification_attached():
    # every public rgcs_core.optics function must carry the v2 provenance
    # decorator (test_experiments_provenance scans all rgcs_core functions)
    for fn in (quartz_indices, quartz_birefringence, snell_refraction,
               optical_path_length_mm, optical_phase_rad, ray_to_target,
               photoelastic_index_shift, acousto_optic_m2,
               quartz_acousto_optic_m2):
        assert hasattr(fn, "classification")
        assert fn.classification.label in ("Established", "Derived")
