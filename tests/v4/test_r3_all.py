"""v4.7.x R3: root space, phase lens, tetrahedral addressing,
spin/torsion, optical spin, HAL memory, nested atlas — plus the
adversarial campaign.

The load-bearing tests are the root-space corrections: zero wrapped
residual is never a root, gauge orbits need declared representative
rules, the certificate's best status is a BOUNDED relational lock,
and the two absolute readings are UNSUPPORTED as standing statuses.
"""
from __future__ import annotations

import math
import random

import numpy as np
import pytest


# --- doctrine ------------------------------------------------------------

def test_root_classes_statuses_and_collapses_present():
    import r3
    assert len(r3.ROOT_CLASSES) == 6
    assert "ABSOLUTE_VACUUM_ROOT_UNSUPPORTED" in r3.ROOT_STATUSES
    assert "NONLOCAL_REFERENCE_FRAME_UNSUPPORTED" in r3.ROOT_STATUSES
    assert len(r3.FORBIDDEN_COLLAPSES) == 6
    with pytest.raises(r3.ClaimBoundaryError):
        r3.refuse_collapse("PHASE_ZERO_IS_ABSOLUTE_PHASE")


# --- addressing (P02/P03) ------------------------------------------------

def test_hierarchy_is_exact_powers_of_eight():
    from r3.address import level_count
    assert [level_count(d) for d in range(5)] == [1, 8, 64, 512, 4096]


def test_codec_roundtrip_over_all_depth3_addresses():
    from r3.address import decode, encode
    for k in range(512):
        assert encode(decode(k, 3)) == k


def test_parent_reduces_to_hierarchy_root_which_is_not_vacuum():
    import r3
    from r3.address import hierarchy_root_is_not_vacuum, parent
    assert parent(4095, 4, 4) == 0
    with pytest.raises(r3.ClaimBoundaryError):
        hierarchy_root_is_not_vacuum()


def test_k_value_requires_declared_semantic():
    import r3
    from r3.address import split_k
    assert split_k(4095, "ORIGIN_DESTINATION")["destination"] == 63
    with pytest.raises(r3.ClaimBoundaryError):
        split_k(4095, "WHATEVER")


def test_barycentric_rejects_outside_points():
    import r3
    from r3.address import barycentric_locate
    ok = barycentric_locate((0.25, 0.25, 0.25, 0.25))
    assert ok["inside"] and not ok["on_face"]
    with pytest.raises(r3.ClaimBoundaryError):
        barycentric_locate((0.5, 0.6, -0.1, 0.0))


def test_destination_certificate_refuses_bookkeeping_addresses():
    import r3
    from r3.address import DestinationCertificate
    with pytest.raises(r3.ClaimBoundaryError):
        DestinationCertificate(100, "REGION_SUBREGION", "", "", "", "",
                               1.0, "")
    ok = DestinationCertificate(
        100, "REGION_SUBREGION", "EARTH_FIXED_ITRF",
        "2026-07-18T00:00:00Z", "WGS84+EGM2008", "DE440",
        3.0, "survey 2026-07")
    assert ok.position_uncertainty_m == 3.0


def test_route_and_transitions_are_labelled_bookkeeping():
    from r3.address import route, transition_4096
    r = route(5, 60)
    assert "not transport" in r["claim"]
    t = transition_4096(0, 4095)
    assert t["to_digits"] == [7, 7, 7, 7]
    assert "synthetic state space" in t["claim"]


# --- phase lens (P01) ----------------------------------------------------

def test_lens_inversion_recovers_wellposed_case():
    from r3.lens import invert, make_lens
    L = make_lens(6, 10)
    x = np.linspace(0, 1, 6)
    est = invert(L, L @ x, lam=1e-8)["estimate"]
    assert np.linalg.norm(est - x) < 1e-4


def test_unregularized_inversion_is_refused():
    import r3
    from r3.lens import invert, make_lens
    L = make_lens(4, 6)
    with pytest.raises(r3.ClaimBoundaryError):
        invert(L, np.zeros(6), lam=0.0)


def test_underobserved_lens_is_reported_not_hidden():
    from r3.lens import make_lens, observability
    L = make_lens(10, 4)          # 4 observations, 10 modes
    rep = observability(L)
    assert rep["fully_observable"] is False
    assert rep["null_space_dim"] == 6


def test_adjoint_passes_dot_product_test():
    from r3.lens import adjoint_test, make_lens
    assert adjoint_test(make_lens(7, 9))["passes"]


def test_directionality_is_anisotropy_not_exotic_physics():
    from r3.lens import directionality, make_lens
    d = directionality(make_lens(6, 6))
    assert d["transpose_asymmetry"] > 0
    assert "NOT evidence" in d["meaning"]


# --- spin/torsion + metric boundary (P04/P05) ----------------------------

def test_spin_categories_never_merge():
    import r3
    from r3.spin_torsion import SpinQuantity
    a = SpinQuantity("CLASSICAL_ANGULAR_MOMENTUM", 1.0, "J*s")
    b = SpinQuantity("INTRINSIC_SPIN_DENSITY", 1.0, "J*s/m^3")
    with pytest.raises(r3.ClaimBoundaryError):
        a + b
    assert (a + a).value == 2.0


def test_einstein_cartan_torsion_is_unmeasurably_small():
    from r3.spin_torsion import einstein_cartan_torsion
    t = einstein_cartan_torsion(1e10)     # generous spin density
    # ~6e-25 1/m for a fully polarized solid: some 24 orders
    # below anything measurable, which is the point
    assert t["torsion_scale_1_per_m"] < 1e-20
    assert t["verdict"] == "UNMEASURABLE_AT_LABORATORY_SCALE"


def test_laboratory_spin_firewall_refuses_the_three_slides():
    from r3.spin_torsion import laboratory_spin_firewall
    for claim in ("rotating_mass_produces_torsion_field",
                  "toroidal_coil_is_spacetime_torsion",
                  "twisted_crystal_is_einstein_cartan_source"):
        assert laboratory_spin_firewall(claim)["status"] == "REFUSED"


def test_inverse_einstein_prices_the_wish_honestly():
    from r3.spin_torsion import metric_actuation_verdict
    v = metric_actuation_verdict(1e-9, 1.0)
    assert v["required_mass_kg"] > 1e17
    assert v["verdict"] == "REFUSED_BY_ARITHMETIC"
    assert v["audit"]["achievable"] is False


def test_inverse_einstein_rejects_strong_field_targets():
    import r3
    from r3.spin_torsion import inverse_einstein
    with pytest.raises(r3.ClaimBoundaryError):
        inverse_einstein(1.5, 1.0)


# --- optical spin (P09) --------------------------------------------------

def test_sam_and_oam_do_not_merge_into_one_scalar():
    import r3
    from r3.optical_spin import OpticalSpinState
    from r3.spin_torsion import SpinQuantity
    s = OpticalSpinState(
        "V1", SpinQuantity("EM_SPIN_ANGULAR_MOMENTUM", 1.0, "hbar"),
        SpinQuantity("EM_ORBITAL_ANGULAR_MOMENTUM", 2.0, "hbar"),
        "circular", 532.0)
    with pytest.raises(r3.ClaimBoundaryError):
        _ = s.total


def test_voxel_dose_enforces_the_programme_ceiling():
    from r3.optical_spin import voxel_dose
    hot = voxel_dose(1.0, 10.0, 1.0)      # 1 W into 10 um
    assert hot["verdict"] == "REFUSED_DOSE"
    cool = voxel_dose(1e-6, 100.0, 1.0)
    assert cool["verdict"] == "PLAN_OK"


def test_quartz_spin_transfer_stays_hypothesis():
    from r3.optical_spin import sam_oam_transfer_audit
    rep = sam_oam_transfer_audit("sam_to_lattice_spin_texture")
    assert rep["status"] == "OPERATIONAL_HYPOTHESIS"


def test_relaxation_refuses_infinite_memory_and_t2_violation():
    import r3
    from r3.optical_spin import relaxation_ledger
    ok = relaxation_ledger(1.0, 0.5, 2.0)
    assert 0 < ok["coherence_remaining"] < 1
    with pytest.raises(r3.ClaimBoundaryError):
        relaxation_ledger(1.0, 3.0, 1.0)      # T2 > 2*T1


# --- HAL memory (P10) ----------------------------------------------------

def test_hal_records_are_synthetic_only():
    import r3
    from r3.hal_memory import MemoryRecord
    with pytest.raises(r3.ClaimBoundaryError):
        MemoryRecord(10, 2, "PERSONAL", 0.0)
    ok = MemoryRecord(10, 2, "SYNTHETIC", 0.0)
    assert ok.payload_class == "SYNTHETIC"


def test_hal_partition_and_activation():
    from r3.hal_memory import MemoryRecord, activation, partition
    recs = [MemoryRecord(k, 2, "SYNTHETIC", 0.0) for k in range(64)]
    p = partition(recs, 1)
    assert p["n_groups"] == 8
    a = activation(recs[0], 3600.0, 0.5)
    assert 0 < a["activation"] < 0.5
    assert "SYNTHETIC" in a["claim"]


def test_hal_consent_audit_proves_the_invariant():
    from r3.hal_memory import MemoryRecord, consent_audit
    recs = [MemoryRecord(k, 2, "SYNTHETIC", 0.0) for k in range(8)]
    rep = consent_audit(recs)
    assert rep["all_synthetic"] and "consent" in rep["policy"]


# --- atlas (P11) ----------------------------------------------------------

def _random_landmarks(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        z = rng.uniform(-1, 1)
        th = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(1 - z * z)
        out.append((r * math.cos(th), r * math.sin(th), z))
    return out


def test_random_landmarks_do_not_beat_random_rotations():
    from r3.atlas import null_rotation_campaign
    rep = null_rotation_campaign(_random_landmarks(24, 5), 51.843,
                                 n_null=100)
    assert rep["beats_random_at_0_05"] is False
    assert rep["grid_status"] == "REPRESENTATION_ARTIFACT"


def test_planted_landmarks_are_detected():
    """Positive control: landmarks ON the vertices of the claimed grid
    must beat random rotations, or the campaign is blind."""
    from r3.atlas import null_rotation_campaign, tetra_vertices_on_sphere
    lms = tetra_vertices_on_sphere(33.0) * 3
    # tight tolerance: the tetrahedron's 180-degree z-symmetry makes a
    # loose tolerance let random rotations tie the planted one
    rep = null_rotation_campaign(list(lms), 33.0, n_null=200,
                                 tolerance_deg=1.0)
    assert rep["observed_hit_rate"] == 1.0
    assert rep["beats_random_at_0_05"] is True


def test_portal_claims_have_no_physical_rung():
    from r3.atlas import PORTAL_CLAIM_ONTOLOGY
    assert "UNSUPPORTED" in PORTAL_CLAIM_ONTOLOGY["PORTAL"]


def test_nested_address_requires_ordered_frame_chain():
    import r3
    from r3.address import DestinationCertificate
    from r3.atlas import NestedAddress
    cert = DestinationCertificate(
        7, "REGION_SUBREGION", "EARTH_FIXED_ITRF",
        "2026-07-18T00:00:00Z", "WGS84", "DE440", 5.0, "cal")
    ok = NestedAddress(cert, ("EARTH_FIXED_ITRF",
                              "SOLAR_SYSTEM_BARYCENTRIC"))
    assert ok.frame_chain[0] == "EARTH_FIXED_ITRF"
    with pytest.raises(r3.ClaimBoundaryError):
        NestedAddress(cert, ("GALACTIC", "EARTH_FIXED_ITRF"))


# --- root space (P13) — the R3 centre --------------------------------------

def test_zero_wrapped_residual_is_never_a_root():
    from r3.root_space import zero_residual_aliases
    z = zero_residual_aliases(4096.0, 1.0)
    assert z["zero_residual_candidates"] == 4097
    assert z["status"] == "ROOT_ALIAS_UNRESOLVED"
    assert "never a root" in z["statement"]


def test_dual_lattice_thins_the_root_alias_set():
    from r3.root_space import dual_lattice_root_search
    d = dual_lattice_root_search(4096.0, 4375.0, 0.001)
    assert d["resolved_within_window"] is True


def _authority():
    from pmwr.phase_authority import PhaseAuthority
    return PhaseAuthority("A", 4096.0, "2026-07-18T00:00:00Z", "UTC")


def _root(cycles=(3,)):
    from r3.root_space import RootState
    return RootState(
        "PHYSICAL_REFERENCE_NETWORK_ROOT", "REGION_SUBREGION",
        "RELATIONAL-NET-1", (0.0, 0.0, 0.0, 0.0),
        "2026-07-18T00:00:00Z", ("W1", "W2", "W3", "W4"),
        _authority(), "cal-2026-07", "min-norm representative",
        cycles)


def test_root_state_requires_all_declared_components():
    import r3
    from r3.root_space import RootState
    with pytest.raises(r3.ClaimBoundaryError):
        RootState("PHYSICAL_REFERENCE_NETWORK_ROOT", "", "F",
                  (0, 0, 0, 0), "e", ("W1",) * 4, _authority(),
                  "c", "g", None)
    with pytest.raises(r3.ClaimBoundaryError):
        RootState("PHYSICAL_REFERENCE_NETWORK_ROOT", "S", "F",
                  (0, 0, 0, 0), "e", ("W1", "W2"), _authority(),
                  "c", "g", None)      # < 4 worldlines


def test_gauge_orbit_needs_a_declared_representative_rule():
    import r3
    from r3.root_space import gauge_orbit_audit
    with pytest.raises(r3.GaugeError):
        gauge_orbit_audit(["global phase", "relabeling"], None)
    rep = gauge_orbit_audit(["global phase"], "min-norm")
    assert "CONVENTION" in rep["collapse_refused"]


def test_emission_localization_recovers_position_relationally():
    from r3.root_space import emission_localize
    emitters = [(0, 0, 0), (1000, 0, 0), (0, 1000, 0), (0, 0, 1000)]
    target = (100.0, 200.0, 300.0)
    ranges = [math.dist(target, e) for e in emitters]
    rep = emission_localize(emitters, ranges)
    assert rep["solved"]
    assert max(abs(a - b) for a, b in
               zip(rep["position_m"], target)) < 1e-3
    assert "RELATIONAL" in rep["frame"]


def test_three_emitters_are_partial_not_solved():
    from r3.root_space import emission_localize
    rep = emission_localize([(0, 0, 0), (1, 0, 0), (0, 1, 0)],
                            [1.0, 1.0, 1.0])
    assert rep["solved"] is False
    assert rep["status"] == "ROOT_PARTIALLY_IDENTIFIED"


def test_root_lock_certificate_best_case_is_bounded():
    from r3.root_space import root_lock_certificate
    cert = root_lock_certificate(
        _root(), [4096.0, 4133.0, 4211.0], [1e-4], 0.001,
        aliases_in_domain=1, independent_channels_agree=True,
        holdout_passed=True)
    assert cert["status"] == "ROOT_LOCK_BOUNDED"
    assert cert["absolute_vacuum_root"] == \
        "ABSOLUTE_VACUUM_ROOT_UNSUPPORTED"
    assert cert["nonlocal_frame"] == \
        "NONLOCAL_REFERENCE_FRAME_UNSUPPORTED"
    assert "BOUNDED RELATIONAL" in cert["claim_boundary"]


def test_root_lock_fails_honestly_for_each_criterion():
    from r3.root_space import root_lock_certificate
    unresolved = root_lock_certificate(
        _root(cycles=None), [4096.0, 4133.0], [1e-4], 0.001,
        1, True, True)
    assert unresolved["status"] == "ROOT_ALIAS_UNRESOLVED"
    nonunique = root_lock_certificate(
        _root(), [4096.0, 4133.0], [1e-4], 0.001, 5, True, True)
    assert nonunique["status"] == "ROOT_NON_UNIQUE"
    rejected = root_lock_certificate(
        _root(), [4096.0, 4133.0], [1e-4], 0.001, 1, False, True)
    assert rejected["status"] == "ROOT_LOCK_REJECTED"


# --- adversarial ----------------------------------------------------------

def test_attack_first_zero_of_residual_cannot_be_sold_as_root():
    """The R3 correction as an attack: pick the first zero, call it
    the root — the audit's own status blocks it."""
    from r3.root_space import zero_residual_aliases
    z = zero_residual_aliases(20480.0, 0.1)
    assert z["status"] == "ROOT_ALIAS_UNRESOLVED"
    assert z["zero_residual_candidates"] > 2000


def test_attack_no_detected_phryll_in_r3_either():
    import pathlib

    import r3
    pkg = pathlib.Path(r3.__file__).parent
    for p in pkg.glob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert "DETECTED_PHRYLL" not in text
        assert "PHRYLL_DETECTED" not in text


def test_attack_absolute_root_language_absent_from_certificates():
    from r3.root_space import root_lock_certificate
    cert = root_lock_certificate(
        _root(), [4096.0, 4133.0, 4211.0], [1e-4], 0.001, 1, True,
        True)
    # the standing UNSUPPORTED statuses are present...
    assert cert["absolute_vacuum_root"].endswith("UNSUPPORTED")
    assert cert["nonlocal_frame"].endswith("UNSUPPORTED")
    # ...and any mention of the absolute readings in prose is a
    # refusal ("no vacuum origin"), never an assertion
    text = str(cert).lower()
    for phrase in ("vacuum origin", "preferred frame"):
        idx = text.find(phrase)
        while idx != -1:
            assert text[max(0, idx - 3):idx].startswith("no "),                 f"{phrase!r} appears outside refusal context"
            idx = text.find(phrase, idx + 1)
