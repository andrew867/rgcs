"""P06 — blinded matched natural-vs-synthetic quartz: matching, blinding,
preregistration, null, power, multiplicity, and the ordinary firewall."""

from __future__ import annotations

import numpy as np
import pytest

from r10 import natsynth as N


def _specimen(sid, cls, *, mass=10.0):
    return N.Specimen(
        specimen_id=sid,
        true_class=cls,
        geometry="cylinder_10x2mm",
        handedness="R",
        mass_g=mass,
        c_axis="Z_parallel",
        fixture="fixture_A",
    )


def _matched_kwargs():
    return dict(
        geometry="cylinder_10x2mm",
        handedness="R",
        mass_g=10.0,
        c_axis="Z_parallel",
        fixture="fixture_A",
        excitation="swept_sine",
        endpoints=("acoustic_Q", "dielectric_loss"),
        preregistration=("acoustic_Q", "dielectric_loss", "absorption"),
    )


def _design():
    naturals = (_specimen("N1", N.SpecimenClass.NATURAL),
                _specimen("N2", N.SpecimenClass.NATURAL))
    synthetics = (_specimen("S1", N.SpecimenClass.SYNTHETIC),
                  _specimen("S2", N.SpecimenClass.FUSED_SILICA))
    dummies = (_specimen("D1", N.SpecimenClass.DUMMY),)
    return N.matched_protocol(naturals, synthetics, dummies,
                              **_matched_kwargs())


# --- matching -----------------------------------------------------------

def test_matched_protocol_matches_required_variables_and_has_dummies():
    design = _design()
    assert N.matches_required_variables(design)
    assert len(design.dummies) >= 1
    for v in N.REQUIRED_MATCHING_VARIABLES:
        assert v in design.matching_variables


def test_unmatched_mass_is_refused():
    naturals = (_specimen("N1", N.SpecimenClass.NATURAL, mass=10.0),)
    synthetics = (_specimen("S1", N.SpecimenClass.SYNTHETIC, mass=12.0),)
    dummies = (_specimen("D1", N.SpecimenClass.DUMMY),)
    with pytest.raises(N.NatSynthError):
        N.matched_protocol(naturals, synthetics, dummies, **_matched_kwargs())


def test_missing_dummies_is_refused():
    naturals = (_specimen("N1", N.SpecimenClass.NATURAL),)
    synthetics = (_specimen("S1", N.SpecimenClass.SYNTHETIC),)
    with pytest.raises(N.NatSynthError):
        N.matched_protocol(naturals, synthetics, (), **_matched_kwargs())


# --- blinding round-trip ------------------------------------------------

def test_blind_and_reveal_round_trip_hides_identity():
    design = _design()
    specimens = design.all_specimens()
    labels = N.blind_labels(specimens, seed=1)
    # every specimen got an opaque code, and codes do not leak the class
    assert len(labels.codes) == len(specimens)
    for code in labels.codes.values():
        assert code.startswith("code_")
        assert "NATURAL" not in code and "SYNTHETIC" not in code
    revealed = N.reveal(labels, labels.key)
    # each code maps back to exactly one true class
    for sid, code in labels.codes.items():
        sp = next(s for s in specimens if s.specimen_id == sid)
        assert revealed[code] == sp.true_class


def test_reveal_rejects_a_foreign_key():
    design = _design()
    labels = N.blind_labels(design.all_specimens(), seed=2)
    with pytest.raises(N.NatSynthError):
        N.reveal(labels, {"not_a_code": N.SpecimenClass.NATURAL})


# --- preregistration ----------------------------------------------------

def test_refuse_unpreregistered_endpoint_raises():
    with pytest.raises(N.NatSynthError):
        N.refuse_unpreregistered_endpoint(
            "surprise_resonance", ("acoustic_Q", "dielectric_loss"))


def test_preregistered_endpoint_is_allowed():
    # does not raise
    N.refuse_unpreregistered_endpoint(
        "acoustic_Q", ("acoustic_Q", "dielectric_loss"))


def test_protocol_refuses_endpoint_not_preregistered():
    kwargs = _matched_kwargs()
    kwargs["endpoints"] = ("acoustic_Q", "unplanned_endpoint")
    naturals = (_specimen("N1", N.SpecimenClass.NATURAL),)
    synthetics = (_specimen("S1", N.SpecimenClass.SYNTHETIC),)
    dummies = (_specimen("D1", N.SpecimenClass.DUMMY),)
    with pytest.raises(N.NatSynthError):
        N.matched_protocol(naturals, synthetics, dummies, **kwargs)


# --- null and power -----------------------------------------------------

def test_null_no_difference_gives_p_not_small():
    """Control: with no group difference the p-value is not small."""
    rng = np.random.default_rng(3)
    n = 12
    measurements = rng.normal(0.0, 1.0, size=2 * n)  # identical groups
    labels = np.array(["NATURAL"] * n + ["NOT"] * n, dtype=object)
    res = N.label_shuffle_null(measurements, labels, trials=1000, seed=4)
    assert res["p_value"] > 0.2
    assert res["verdict"] == "NO_GROUP_DIFFERENCE"


def test_power_planted_effect_is_recovered():
    """Power: a real natural-group effect is detected with a small p."""
    pw = N.planted_group_effect_power(n_per_group=12, effect=3.0, trials=1000)
    assert pw["has_power"]
    assert pw["p_value"] < 0.05


def test_group_difference_needs_both_labels():
    with pytest.raises(N.NatSynthError):
        N.group_difference([1.0, 2.0], ["NATURAL", "NATURAL"])


# --- multiplicity -------------------------------------------------------

def test_multiplicity_correction_shrinks_significance():
    p = 0.03
    one = N.multiplicity_correct([p])
    many = N.multiplicity_correct([p, p, p, p, p])
    # a raw-significant p survives alone but not under many endpoints
    assert one["n_significant_corrected"] == 1
    assert many["n_significant_corrected"] == 0
    assert many["corrected"][0] > one["corrected"][0]


def test_multiplicity_rejects_empty():
    with pytest.raises(N.NatSynthError):
        N.multiplicity_correct([])


# --- the ordinary-explanation firewall ---------------------------------

def test_refuse_exotic_explanation_raises():
    with pytest.raises(N.NatSynthError):
        N.refuse_exotic_explanation(2.5)


# --- report -------------------------------------------------------------

def test_report_is_software_only_and_measures_nothing():
    r = N.natsynth_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "MATCHED_PROTOCOL_SOFTWARE_ONLY"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["real_data"]["status"] == "BLOCKED_NO_SPECIMENS"
    assert "not_faked" in r["real_data"]
    assert "what_this_does_not_say" in r
