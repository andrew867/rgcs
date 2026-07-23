"""A13 — the R11 red team.

Sixteen named attacks, each of which would manufacture a result. Every
one must fail with a TYPED reason, not merely return something odd. A
refusal that is only a docstring is not a refusal, so each attack is
executed here against the real module API.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from r11 import (atomicarch, carrier, dynboundary, earthface, isotope,
                 numcorpus, phasealpha, planetroot, shelladdr, sources)

ROOT = Path(__file__).resolve().parents[2]


# 1 — rotate the root after seeing targets
def test_attack_01_rotate_frozen_solid_after_seeing_targets():
    with pytest.raises(earthface.EarthFaceError):
        earthface.refuse_rotate_after_load("target data already loaded")


# 2 — choose a magnetic scalar target-by-target
def test_attack_02_choose_magnetic_scalar_per_target():
    with pytest.raises(earthface.EarthFaceError):
        earthface.refuse_single_zero_direction()      # nothing fixed
    with pytest.raises(planetroot.PlanetRootError):
        planetroot.refuse_target_dependent_selection(
            reason="scalar picked after seeing the target")


# 3 — reverse the gradient sign target-by-target
def test_attack_03_flip_gradient_sign_per_target():
    import numpy as np
    direction = np.array([0.3, 0.4, 0.86])
    direction = direction / np.linalg.norm(direction)
    face = sorted(earthface.ray_face_intersection(direction))[0]
    frame = earthface.local_face_frame(direction, face)
    aliases = earthface.gradient_zero_alias_set(direction, frame)
    assert len(aliases) > 1, "both signs must survive as aliases"
    with pytest.raises(earthface.EarthFaceError):
        earthface.refuse_single_zero_direction(
            scalar=earthface.MagneticScalar.TOTAL_INTENSITY)  # sign unfixed


# 4 — treat decimal digits as octal
def test_attack_04_decimal_digits_read_as_octal():
    with pytest.raises(shelladdr.ShellAddrError):
        shelladdr.refuse_decimal_digits_as_octal("344478312553")  # has 8s


# 5 — truncate payload bits and call it faithful
def test_attack_05_lossy_envelope_presented_as_lossless():
    with pytest.raises(shelladdr.ShellAddrError):
        shelladdr.refuse_lossy_as_lossless()


# 6 — reorder the shell observations
def test_attack_06_reorder_shell_observations():
    with pytest.raises(shelladdr.ShellAddrError):
        shelladdr.refuse_reordering(proposed_order=(1238, 3478, 1903))


# 7 — invent timestamps, then speed / orbit / ETA
def test_attack_07_invent_kinematics_without_timestamps():
    for fn in (shelladdr.refuse_speed, shelladdr.refuse_orbit,
               shelladdr.refuse_eta):
        with pytest.raises(shelladdr.ShellAddrError):
            fn()


# 8 — pick the isotope ratio orientation that yields a nicer year
def test_attack_08_orientation_chosen_from_desired_year():
    with pytest.raises(isotope.IsotopeError):
        isotope.refuse_orientation_chosen_from_desired_year(
            192, 55, desired_year=1957)


# 9 — select the crystal mode after seeing 9192
def test_attack_09_carrier_selected_after_seeing_target():
    with pytest.raises(carrier.CarrierError):
        carrier.refuse_carrier_selected_after_target()


# 10 — add an arbitrary correction to force closure
def test_attack_10_arbitrary_correction_to_force_closure():
    """13772.28*2/3 misses 9192 by 10.48 Hz; adding 63/6 closes it to
    9192.02. That is a post-hoc correction and must be labelled."""
    audit = carrier.audit_high_priority_candidate()
    assert audit["target_fitted"] is True, audit
    with pytest.raises(carrier.CarrierError):
        carrier.refuse_carrier_selected_after_target(
            expression_text="13772.28 * 2/3 + 63/6")


# 11 — equate degrees, hertz, microtesla or miles by number alone
def test_attack_11_equate_incompatible_units_by_number():
    deg = phasealpha.Quantity(180.0, phasealpha.Unit.DEGREES)
    hz = phasealpha.Quantity(180.0, phasealpha.Unit.CYCLES_PER_SECOND)
    with pytest.raises(phasealpha.PhaseAlphaError):
        phasealpha.refuse_unit_confusion(deg, hz)
    # same unit kind is fine — the guard is not a blanket refusal
    assert phasealpha.refuse_unit_confusion(
        deg, phasealpha.Quantity(90.0, phasealpha.Unit.DEGREES))


# 12 — treat nuclear spin 7/2 as the phase fraction 7/2
def test_attack_12_spin_seven_halves_is_not_a_phase():
    with pytest.raises(phasealpha.PhaseAlphaError):
        phasealpha.refuse_spin_phase_conflation(
            Fraction(7, 2), context="Cs-133 nuclear spin")
    with pytest.raises(isotope.IsotopeError):
        isotope.refuse_isotope_conflation(isotope.CS133, isotope.CS137)


# 13 — call destructive interference a broken photon
def test_attack_13_interference_called_a_broken_photon():
    with pytest.raises(dynboundary.DynBoundaryError):
        dynboundary.refuse_interference_as_broken_photon()
    with pytest.raises(dynboundary.DynBoundaryError):
        dynboundary.refuse_fractional_photon()
    with pytest.raises(dynboundary.DynBoundaryError):
        dynboundary.refuse_new_particle_claim()


# 14 — call the instantaneous divergence free infinite energy
def test_attack_14_divergence_called_free_energy():
    with pytest.raises(dynboundary.DynBoundaryError):
        dynboundary.refuse_infinite_free_energy()
    with pytest.raises(dynboundary.DynBoundaryError):
        dynboundary.refuse_energy_from_nothing()
    # and the model itself refuses tau = 0 rather than returning a number
    with pytest.raises(dynboundary.DynBoundaryError):
        dynboundary.expected_photon_number(0.0)


# 15 — use an Earth dynamo root on a body without one
@pytest.mark.parametrize("body_id", ["MARS", "MOON", "VENUS"])
def test_attack_15_earth_root_on_non_dynamo_body(body_id):
    body = planetroot.BODIES[body_id]
    with pytest.raises(planetroot.PlanetRootError):
        planetroot.refuse_earth_method_on_non_dynamo_body(
            body, planetroot.RootMethod.RADIAL_FIELD_EXTREMUM)


def test_attack_15b_gas_giant_has_no_surface():
    with pytest.raises(planetroot.PlanetRootError):
        planetroot.refuse_surface_assumption_for_gas_giant(
            planetroot.BODIES["JUPITER"])


# 16 — leak private provenance into the public tree / history
def test_attack_16_private_delta_read_during_public_generation():
    with pytest.raises(sources.SourceError):
        sources.refuse_private_delta_read(
            "internal-docs/plans-v5/pack/02_PRIVATE_OPERATOR_DELTA.md")
    with pytest.raises(sources.SourceError):
        sources.refuse_new_identity_exposure("a new name")


def test_attack_16b_public_tree_scan_is_clean_with_declared_residual():
    # the deeper scan lives in test_r11_sources; keep this one shallow
    rep = sources.privacy_scan(ROOT, max_commits=3)
    assert rep["committed_clean"], rep
    assert rep["history_serious"] == []
    assert rep["declared_residual"]["status"] == "DECLARED_RESIDUAL_EXPOSURE"


# --- cross-cutting: the standing refusals ------------------------------

def test_no_decoded_location_verdict_anywhere():
    from r11 import identifiability
    with pytest.raises(identifiability.IdentifiabilityError):
        identifiability.refuse_decoded_location_verdict()


def test_retired_sequences_cannot_return():
    with pytest.raises(numcorpus.CorpusError):
        numcorpus.refuse_retired_sequence("0000000000")


def test_storage_bulb_is_not_an_oscillator():
    with pytest.raises(atomicarch.AtomicArchError):
        atomicarch.refuse_bulb_as_oscillator()
    with pytest.raises(atomicarch.AtomicArchError):
        atomicarch.refuse_coils_as_state_selector()


def test_nothing_in_r11_claims_a_measurement():
    for mod, fn in ((sources, "sources_report"),
                    (planetroot, "planetroot_report"),
                    (earthface, "earthface_report"),
                    (shelladdr, "shelladdr_report"),
                    (phasealpha, "phasealpha_report"),
                    (carrier, "carrier_report"),
                    (isotope, "isotope_report"),
                    (dynboundary, "dynboundary_report"),
                    (atomicarch, "atomicarch_report"),
                    (numcorpus, "numcorpus_report")):
        rep = getattr(mod, fn)()
        assert rep["measured_here"] == "nothing", fn
        assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED", fn
