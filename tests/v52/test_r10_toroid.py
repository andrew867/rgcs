"""P04-P07 — torus geometry, CW toroidal address, channels, signs.

The load-bearing tests are the causality firewall (no channel beats
light) and the torsion firewall (toroidal EM is not spacetime torsion).
"""

from __future__ import annotations

import math

import pytest

from r10 import toroid as T


# --- P04: ordinary geometry --------------------------------------------

def test_ring_torus_area_and_volume():
    t = T.Torus(3, 1)
    assert t.is_ring_torus
    assert t.surface_area == pytest.approx(4 * math.pi ** 2 * 3 * 1)
    assert t.volume == pytest.approx(2 * math.pi ** 2 * 3 * 1)


def test_a_point_lies_on_the_surface():
    t = T.Torus(3, 1)
    x, y, z = t.point(0.7, 1.3)
    # distance from the tube-centre circle equals r
    rho = math.hypot(x, y)
    assert math.hypot(rho - 3, z) == pytest.approx(1.0)


def test_degenerate_radii_refused():
    with pytest.raises(ValueError):
        T.Torus(0, 1)
    with pytest.raises(ValueError):
        T.Torus(3, 0)


def test_the_zero_point_is_the_origin_and_a_hole():
    assert T.Torus(3, 1).central_zero_point() == (0.0, 0.0, 0.0)


# --- P05: the toroidal address -----------------------------------------

def test_address_requires_frame_and_epoch():
    with pytest.raises(ValueError):
        T.ToroidalAddress("dom", 4, 4, 1, 1, "", "e", "shell", 1.0)
    with pytest.raises(ValueError):
        T.ToroidalAddress("dom", 4, 4, 1, 1, "f", "", "shell", 1.0)


def test_address_indices_are_range_checked():
    with pytest.raises(ValueError):
        T.ToroidalAddress("d", 3, 3, 8, 0, "f", "e", "s", 1.0)


def test_address_angles_are_cell_centres():
    a = T.ToroidalAddress("d", 2, 2, 0, 0, "f", "e", "s", 1.0)
    th, ph = a.angles()
    assert th == pytest.approx(2 * math.pi * 0.5 / 4)
    assert ph == pytest.approx(2 * math.pi * 0.5 / 4)


def test_parent_prepend_nests_the_domain():
    a = T.ToroidalAddress("earth", 4, 4, 1, 1, "f", "e", "s", 1.0)
    b = a.with_parent("solar_system")
    assert b.parent_domain == "solar_system/earth"
    assert b.total_bits == a.total_bits


# --- P06: the causality firewall ---------------------------------------

def test_light_delay_is_distance_over_c():
    assert T.light_delay_seconds(T.C_M_PER_S) == pytest.approx(1.0)
    assert T.light_delay_seconds(1.496e11) == pytest.approx(499.0, abs=1)


def test_a_sub_light_latency_claim_is_impossible():
    au = 1.496e11
    r = T.assess_channel("CONVENTIONAL_DELAYED", au, 0.0)
    assert r["beats_light_speed"]
    assert r["verdict"] == "PHYSICALLY_IMPOSSIBLE"


def test_an_honest_latency_is_within_the_light_cone():
    au = 1.496e11
    r = T.assess_channel("CONVENTIONAL_DELAYED", au, 600.0)
    assert not r["beats_light_speed"]
    assert r["verdict"] == "WITHIN_LIGHT_CONE"


def test_nonlocal_transfer_is_unsupported():
    assert T.CHANNEL_MODELS["NONLOCAL_TRANSFER"]["status"] == "UNSUPPORTED"
    supported = T.toroid_report()["only_supported_channels"]
    assert "NONLOCAL_TRANSFER" not in supported
    assert set(supported) == {"CONVENTIONAL_DELAYED", "SHARED_STATE"}


def test_shared_state_carries_no_information_faster_than_light():
    """It is a real model, but not an FTL one."""
    assert not T.CHANNEL_MODELS["SHARED_STATE"]["faster_than_light"]


def test_instantaneous_broadcast_is_refused():
    with pytest.raises(T.CausalityViolation) as e:
        T.refuse_instantaneous_channel(1.496e11)
    msg = str(e.value)
    assert "no mechanism" in msg
    assert "UNSUPPORTED" in msg


# --- P07: sign conventions ---------------------------------------------

def test_every_sign_convention_is_plus_or_minus_one():
    for name, (sign, meaning) in T.SIGN_CONVENTIONS.items():
        assert sign in (-1, 1), name
        assert meaning


def test_reversal_flips_the_sign_and_keeps_the_meaning():
    for name in T.SIGN_CONVENTIONS:
        orig_sign, orig_meaning = T.SIGN_CONVENTIONS[name]
        rev_sign, rev_meaning = T.reverse_sign(name)
        assert rev_sign == -orig_sign
        assert rev_meaning == orig_meaning


def test_the_five_conventions_are_all_present():
    assert set(T.SIGN_CONVENTIONS) == {
        "EARTH_ROTATION", "EQUATORIAL_CIRCULATION", "COIL_ROTATION",
        "CRYSTAL_AXIAL", "HANDEDNESS"}


# --- firewalls and claim discipline ------------------------------------

def test_toroidal_em_is_not_spacetime_torsion():
    with pytest.raises(T.TorsionConflation) as e:
        T.refuse_torsion_conflation()
    msg = str(e.value)
    assert "ordinary magnetic field" in msg
    assert "not a modification of spacetime" in msg


def test_report_disclaims_the_cosmology():
    r = T.toroid_report()
    n = r["what_this_does_not_say"]
    assert "does not say the universe is a torus" in n
    assert "cosmology is not entailed" in n
    assert r["measured_here"] == "nothing"


def test_report_lists_the_firewalls():
    r = T.toroid_report()
    assert any("not spacetime torsion" in f for f in r["firewalls"])
    assert any("light-delay floor" in f for f in r["firewalls"])
    assert any("hole, not a source of energy" in f for f in r["firewalls"])
