"""R12 red team — the decoder discipline and the cross-domain rule.

Each attack must fail with a typed reason, executed against the real API.
"""

from __future__ import annotations

import pytest

from r11 import sources
from r12 import (bodylock, bridge, epochcand, homelab, icosapacket,
                 igrf14root, reciprocal, shells8)


# 1 — read the icosahedral grammar as a geographic decoder
def test_attack_grammar_as_geographic_decoder():
    with pytest.raises(icosapacket.IcosaPacketError):
        icosapacket.refuse_geographic_decode()


# 2 — read the shared 13-bit prefix as shared content
def test_attack_shared_prefix_as_content():
    with pytest.raises(icosapacket.IcosaPacketError):
        icosapacket.refuse_prefix_as_content()


# 3 — privilege one packet layout without preregistering it
def test_attack_single_layout_without_prereg():
    with pytest.raises(icosapacket.IcosaPacketError):
        icosapacket.refuse_single_layout()


# 4 — parse decimal digits 8/9 as octal
def test_attack_decimal_digits_as_octal():
    with pytest.raises(icosapacket.IcosaPacketError):
        icosapacket.refuse_decimal_digits_as_octal("165879123")   # has 8,9


# 5 — force a hemisphere inversion (north/south double-inversion)
def test_attack_forced_hemisphere_inversion():
    ops = (bodylock.SouthOperation.MIRROR_IMPROPER,
           bodylock.SouthOperation.LATITUDE_SIGN_FLIP)
    with pytest.raises(bodylock.BodyLockError):
        bodylock.refuse_forced_inversion(ops)


def test_attack_frame_without_declared_handedness():
    with pytest.raises(bodylock.BodyLockError):
        bodylock.refuse_undeclared_handedness(None)


# 6 — turn a 3-bit shell index into a radius with nothing declared
def test_attack_radius_from_bare_index():
    with pytest.raises(shells8.Shells8Error):
        shells8.refuse_radius_from_index(3)   # index alone, no basis/origin/law


def test_attack_eight_shells_as_atomic_structure():
    with pytest.raises(shells8.Shells8Error):
        shells8.refuse_atomic_shell_physics()


# 7 — an IGRF root with no epoch, and identifying a root at all
def test_attack_magnetic_root_without_epoch():
    with pytest.raises(igrf14root.Igrf14Error):
        igrf14root.refuse_root_without_epoch()


def test_attack_identify_a_magnetic_root():
    with pytest.raises(igrf14root.Igrf14Error):
        igrf14root.refuse_root_identification()


# 8 — claim a unique creation epoch / misuse the clocks
def test_attack_unique_epoch():
    with pytest.raises(epochcand.EpochCandError):
        epochcand.refuse_unique_epoch()


def test_attack_cs133_as_a_dating_clock():
    with pytest.raises(epochcand.EpochCandError):
        epochcand.refuse_cs133_as_dating_clock()


# 9 — treat reciprocal / Q-space as a place, or claim a measured pattern
def test_attack_reciprocal_space_as_a_place():
    with pytest.raises(reciprocal.ReciprocalError):
        reciprocal.refuse_reciprocal_as_physical_space()


def test_attack_qspace_as_geographic():
    with pytest.raises(reciprocal.ReciprocalError):
        reciprocal.refuse_qspace_as_geographic()


def test_attack_measured_diffraction_pattern():
    with pytest.raises(reciprocal.ReciprocalError):
        reciprocal.refuse_measured_pattern_claim()


# 10 — call anisotropy in an anisotropic crystal an anomaly
def test_attack_anisotropy_as_anomaly():
    with pytest.raises(homelab.HomeLabError):
        homelab.refuse_anisotropy_as_anomaly()


def test_attack_bench_result_without_running_it():
    with pytest.raises(homelab.HomeLabError):
        homelab.refuse_bench_claim()


# 11 — the cross-domain rule: uncertified transfer, and certificate abuse
def test_attack_uncertified_cross_domain_transfer():
    with pytest.raises(bridge.BridgeError):
        bridge.refuse_uncertified_transfer(bridge.Domain.MAGNETIC,
                                           bridge.Domain.OPTICAL_CAVITY)


def test_attack_certificate_treated_as_evidence():
    # a complete but unmeasured certificate is only a candidate
    c = bridge.CouplingCertificate(
        "x", bridge.Domain.MACROSCOPIC_ELASTIC, bridge.Domain.ELECTRICAL_BVD,
        ("strain", "P"), ("1", "C/m^2"), "d_ij", 0.5, 0.0, 1.0,
        "quasi-static", True, "in", "out", "10%", "centrosym control",
        "charge vs strain")
    with pytest.raises(bridge.BridgeError):
        bridge.refuse_certificate_as_evidence(c)


def test_attack_certificates_compose():
    with pytest.raises(bridge.BridgeError):
        bridge.refuse_chained_transfer()


# 12 — leak private provenance (incl. this pack's private dir)
def test_attack_private_provenance_leak():
    with pytest.raises(sources.SourceError):
        sources.refuse_private_delta_read("private_do_not_commit/x.md")
    with pytest.raises(sources.SourceError):
        sources.refuse_new_identity_exposure("a new name")


# --- cross-cutting -----------------------------------------------------

def test_nothing_in_r12_claims_a_measurement():
    import importlib
    import r12
    for m in r12.__all__:
        mod = importlib.import_module(f"r12.{m}")
        rep = getattr(mod, f"{m}_report")()
        assert rep["measured_here"] == "nothing", m
        assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED", m


def test_the_new_cross_domain_rule_is_stated():
    r = bridge.bridge_report()
    assert "NO_AUTOMATIC_EQUIVALENCE" in r["rule"]
    assert "TRANSFER_ALLOWED_WITH_EXPLICIT_COUPLING_CERTIFICATE" in r["rule"]
