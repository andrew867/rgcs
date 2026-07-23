"""A11 — the R11.1 red team.

Sixteen mandated attacks. Each must fail with a TYPED reason, executed
against the real module API — a refusal that lives only in a docstring is
not a refusal.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from r11 import (anglerecon, carrier, detectors, dynboundary, energyledger,
                 modemix, n7geom, picorrection, rotfield, rotor, sources)


# 1 — confuse III-V atomic-lattice mixing with alpha-quartz macroscopic
def test_attack_01_cross_domain_transfer_atomic_to_macroscopic():
    with pytest.raises(modemix.ModeMixError):
        modemix.refuse_cross_domain_transfer(
            modemix.Domain.ATOMIC_LATTICE_PHONON,
            modemix.Domain.MACROSCOPIC_QUARTZ_ELASTIC)


@pytest.mark.parametrize("a", list(modemix.Domain))
@pytest.mark.parametrize("b", list(modemix.Domain))
def test_attack_01b_every_cross_pair_is_refused(a, b):
    if a is b:
        modemix.refuse_cross_domain_transfer(a, b)     # same->same is fine
    else:
        with pytest.raises(modemix.ModeMixError):
            modemix.refuse_cross_domain_transfer(a, b)


# 2 — treat modal truncation as physically cutting a phonon
def test_attack_02_modal_truncation_is_not_a_physical_cut():
    with pytest.raises(modemix.ModeMixError):
        modemix.refuse_modal_truncation_as_physical_cut()


# 3 — compare microseconds directly with hertz
def test_attack_03_microseconds_versus_hertz():
    t = n7geom.Quantity(Fraction(1, 1000), n7geom.Unit.SECOND)
    f = n7geom.Quantity(Fraction(4096), n7geom.Unit.HERTZ)
    with pytest.raises(n7geom.N7GeomError):
        n7geom.refuse_unit_comparison(t, f)


# 4 — compare degrees directly with a field unit
def test_attack_04_degrees_versus_length_or_field():
    a = n7geom.Quantity(Fraction(360, 7), n7geom.Unit.DEGREE)
    L = n7geom.Quantity(Fraction(110), n7geom.Unit.MILLIMETRE)
    with pytest.raises(n7geom.N7GeomError):
        n7geom.refuse_unit_comparison(a, L)


# 5 — use radians where degrees were specified
def test_attack_05_radians_where_degrees_were_specified():
    with pytest.raises(picorrection.PiCorrectionError):
        picorrection.refuse_unit_confusion()


# 6 — add new pi denominators after seeing residuals
def test_attack_06_new_pi_denominator_after_scoring():
    with pytest.raises(picorrection.PiCorrectionError):
        picorrection.refuse_new_denominator(201)
    with pytest.raises(picorrection.PiCorrectionError):
        picorrection.refuse_new_denominator(103)


def test_attack_06b_the_frozen_family_is_actually_frozen():
    assert 200 in picorrection.FROZEN_DENOMINATORS
    assert 201 not in picorrection.FROZEN_DENOMINATORS


# 7 — adjust velocity, length, angle and support at once to force a target
def test_attack_07_scalar_model_forced_to_a_target():
    with pytest.raises(n7geom.N7GeomError):
        n7geom.refuse_scalar_model_as_specimen_prediction()


# 8 — hide mode energy in a discarded basis
def test_attack_08_hidden_basis_energy():
    # modal fractions that do not sum to 1: energy has been dropped on
    # the floor by discarding part of the post-switch basis
    with pytest.raises(energyledger.EnergyLedgerError):
        energyledger.refuse_hidden_basis_energy((0.4, 0.3))
    # a complete basis is accepted, so the guard is not a blanket refusal
    energyledger.refuse_hidden_basis_energy((0.4, 0.35, 0.25))


# 9 — call transferred energy loss
def test_attack_09_transferred_energy_called_loss():
    with pytest.raises(energyledger.EnergyLedgerError):
        energyledger.refuse_transferred_energy_as_loss()


# 10 — ignore switching work
def test_attack_10_switching_work_ignored():
    with pytest.raises(energyledger.EnergyLedgerError):
        energyledger.refuse_ignored_switching_work()


# 11 — use a CCD as a remote phonon detector
def test_attack_11_ccd_as_remote_phonon_detector():
    with pytest.raises(detectors.DetectorError):
        detectors.refuse_ccd_phonon_claim()
    assert detectors.can_detect(detectors.DetectorKind.CCD,
                                detectors.Observable.PHONON) is False


# 12 — infer a photon-number state from a classical transient
def test_attack_12_photon_number_from_a_classical_transient():
    with pytest.raises(dynboundary.DynBoundaryError):
        dynboundary.refuse_new_particle_claim()
    with pytest.raises(energyledger.EnergyLedgerError):
        energyledger.refuse_unknown_channel_claim()


# 13 — omit rotor containment
def test_attack_13_rotor_without_containment():
    with pytest.raises(rotor.SafetyViolation):
        rotor.refuse_spin_authorization()


# 14 — claim 0.03 Hz convergence as bench accuracy
def test_attack_14_003_hz_convergence_called_bench_accuracy():
    a = carrier.audit_high_priority_candidate()
    # the 0.03 Hz figure is registered as arithmetic about rounding only
    assert "rounding" in a["near_mode_note"]
    assert a["target_fitted"] is True
    with pytest.raises(rotfield.RotFieldError):
        rotfield.refuse_bench_claim()


# 15 — claim a historical derivation from a numerical reconstruction
def test_attack_15_historical_authorship_from_arithmetic():
    with pytest.raises(anglerecon.AngleReconError):
        anglerecon.refuse_authorship_claim()
    assert anglerecon.historical_evidence_status() == "BLOCKED_MISSING_DATA"


# 16 — leak private provenance
def test_attack_16_private_provenance_leak():
    with pytest.raises(sources.SourceError):
        sources.refuse_private_delta_read(
            "private_do_not_commit/whatever.md")
    with pytest.raises(sources.SourceError):
        sources.refuse_new_identity_exposure("a new name")


# --- cross-cutting standing refusals -----------------------------------

def test_the_n7_identity_is_never_evidence():
    with pytest.raises(n7geom.N7GeomError):
        n7geom.refuse_identity_as_evidence()


def test_shared_matrix_math_is_not_a_shared_mechanism():
    with pytest.raises(modemix.ModeMixError):
        modemix.refuse_shared_math_as_shared_mechanism()


def test_the_rotating_field_experiment_needs_all_controls():
    with pytest.raises(rotfield.RotFieldError):
        rotfield.refuse_result_without_controls(())


def test_nothing_in_r11_1_claims_a_measurement():
    for mod, fn in ((n7geom, "n7geom_report"),
                    (picorrection, "picorrection_report"),
                    (anglerecon, "anglerecon_report"),
                    (modemix, "modemix_report"),
                    (rotfield, "rotfield_report"),
                    (energyledger, "energyledger_report")):
        rep = getattr(mod, fn)()
        assert rep["measured_here"] == "nothing", fn
        assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED", fn
