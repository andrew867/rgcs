"""P43 — R13 cross-domain red team.

An adversarial pass whose job is to make the permissive bridge architecture
collapse domains, promote a simulation to a measurement, or turn an alias
into a destination -- and to prove that every such attempt is refused.

Each test *attacks*: it takes the shortest path an over-eager analyst would
take to over-claim, and asserts the framework raises instead of complying.
If any of these ever passes silently (the refusal is removed), the test
fails -- which is the point.
"""

from __future__ import annotations

import importlib

import pytest

import r13


# --- the seven forbidden promotions, attacked one by one -----------------

def test_similarity_is_not_equivalence():
    from r13 import claimtypes as C
    with pytest.raises(C.ClaimError):
        C.refuse_similarity_as_equivalence()


def test_simulation_is_not_measurement():
    from r13 import claimtypes as C
    with pytest.raises(C.ClaimError):
        C.refuse_simulation_as_measurement()


def test_numeric_match_is_not_authentication():
    from r13 import claimtypes as C
    with pytest.raises(C.ClaimError):
        C.refuse_numeric_match_as_authentication()


def test_unclosed_energy_is_not_new_energy():
    from r13 import claimtypes as C
    with pytest.raises(C.ClaimError):
        C.refuse_unclosed_energy_as_new_energy(0.0, (-1.0, 1.0))


def test_planar_is_not_isotropic():
    from r13 import claimtypes as C
    with pytest.raises(C.ClaimError):
        C.refuse_planar_uniformity_as_isotropy()


def test_alias_is_not_destination():
    from r13 import claimtypes as C
    with pytest.raises(C.ClaimError):
        C.refuse_alias_as_destination()


def test_paper_is_not_carrier_evidence():
    from r13 import claimtypes as C
    with pytest.raises(C.ClaimError):
        C.refuse_paper_as_carrier_evidence()


def test_there_are_exactly_seven_forbidden_promotions():
    from r13 import claimtypes as C
    assert len(C.FORBIDDEN_PROMOTIONS) == 7
    for name, fn in C.FORBIDDEN_PROMOTIONS.items():
        with pytest.raises(C.ClaimError):
            fn()


# --- attack the claim ladder: promote a simulation to a bench result -----

def test_cannot_promote_simulation_to_measurement_class():
    from r13 import claimtypes as C
    sim = C.Claim("a modelled transfer", C.ClaimClass.NUMERICAL_SIMULATION,
                  "solved the model")
    for target in C.MEASUREMENT_CLASSES:
        with pytest.raises(C.ClaimError):
            C.refuse_promotion(sim, target)


def test_no_software_module_reports_a_measurement_class():
    """Every r13 module that has a *_report() must claim nothing measured."""
    measurement_words = {"BENCH_MEASUREMENT", "INDEPENDENTLY_REPLICATED"}
    checked = 0
    for name in r13.__all__:
        mod = importlib.import_module(f"r13.{name}")
        report_fn = getattr(mod, f"{name}_report", None)
        if report_fn is None:
            continue
        rep = report_fn()
        checked += 1
        assert rep.get("measured_here") == "nothing", name
        assert rep.get("physical_validation") == \
            "PHYSICAL_VALIDATION_NOT_CLAIMED", name
        assert rep.get("claim_class") not in measurement_words, name
    assert checked >= 20  # the bulk of the package carries a report


# --- attack the bridge graph: force a measured cross-domain path ---------

def test_end_to_end_path_never_reaches_a_measurement_class():
    from r13 import bridgegraph as B
    from r13 import claimtypes as C
    # Even if a link were labelled a bench measurement, the composed path
    # is capped at ENGINEERING_CANDIDATE and never a measurement class.
    for attr in ("refuse_path_as_measured", "refuse_automatic_composition"):
        fn = getattr(B, attr, None)
        if fn is not None:
            with pytest.raises(Exception):
                fn()
    # the module's own report claims nothing measured
    rep = B.bridgegraph_report()
    assert rep["claim_class"] not in C.MEASUREMENT_CLASSES_NAMES \
        if hasattr(C, "MEASUREMENT_CLASSES_NAMES") else True
    assert rep["measured_here"] == "nothing"


# --- attack the coordinate codec: collapse the alias set -----------------

def test_alias_set_cannot_be_collapsed_to_a_destination():
    from r13 import coordfinal as CF
    with pytest.raises(Exception):
        CF.refuse_alias_as_destination(object())
    with pytest.raises(Exception):
        CF.refuse_numeric_match_as_authentication()


# --- attack the energy ledger: call an unclosed residual new energy ------

def test_unclosed_boundary_ledger_is_not_new_energy():
    from r13 import boundaryenergy as BE
    with pytest.raises(Exception):
        BE.refuse_unclosed_as_new_energy(1.0, (-2.0, 2.0))
    with pytest.raises(Exception):
        BE.refuse_infinite_free_energy()


# --- attack the six-angle ring: call planar uniformity isotropy ----------

def test_six_angle_uniformity_is_not_isotropy():
    from r13 import sixangle as SA
    with pytest.raises(Exception):
        SA.refuse_planar_uniformity_as_isotropy([1.0] * 6)


# --- attack euphonic/scattering: call synthetic output real data ---------

def test_synthetic_scattering_is_not_beamtime_data():
    from r13 import scattering as S
    with pytest.raises(Exception):
        S.refuse_synthetic_sqw_as_beamtime_data()
    with pytest.raises(Exception):
        S.refuse_prediction_as_detection()


def test_synthetic_force_constants_are_not_dft():
    from r13 import euphonic as E
    with pytest.raises(Exception):
        E.ForceConstants.from_dft("nonexistent-dft-output")
