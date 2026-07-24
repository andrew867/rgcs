"""R13 apparatus — the P20/P21 bench as a preregistered design, not built.

The bill of materials is non-empty, every line is DESIGN_ONLY, and its
total is the sum of the line estimates. The excitation and readout chains
reference only registered components and connect (each stage's output port
feeds the next stage's input port). A component with a BUILT or MEASURED
status is refused at construction. check_safety returns a pass/fail
without ever marking anything validated, and the two design refusals both
raise. The report carries the verdict and the disclaimers.
"""

from __future__ import annotations

import pytest

from r13 import apparatus as AP


# --- (1) the bill of materials -------------------------------------------

def test_bom_is_non_empty_all_design_only_and_total_is_the_sum():
    bom = AP.bill_of_materials()
    assert bom["n_items"] >= 7
    assert bom["items"], "the bill of materials must be non-empty"
    assert all(item["status"] == "DESIGN_ONLY" for item in bom["items"])
    assert bom["all_design_only"] is True
    expected = sum(c.est_cost_usd for c in AP.DESIGN.values())
    assert bom["total_est_cost_usd"] == pytest.approx(expected)
    # and the total is genuinely the sum of the reported line items
    line_sum = sum(item["est_cost_usd"] for item in bom["items"])
    assert bom["total_est_cost_usd"] == pytest.approx(line_sum)


def test_registry_holds_the_expected_apparatus_and_generic_vendors():
    names = set(AP.DESIGN)
    for required in ("drive_coils_helmholtz", "piezo_transducer",
                     "mechanical_fixture", "signal_generator",
                     "lock_in_receiver", "low_noise_preamp",
                     "temperature_control"):
        assert required in names
    # every component carries the engineering-candidate claim class and a
    # generic vendor category, never a real part number
    for c in AP.DESIGN.values():
        assert c.claim_class == "ENGINEERING_CANDIDATE"
        assert c.status == "DESIGN_ONLY"
        assert c.spec


# --- (2) the chains -------------------------------------------------------

def test_excitation_chain_references_registered_components_and_connects():
    chain = AP.excitation_chain()
    assert len(chain) >= 2
    for c in chain:
        assert c.name in AP.DESIGN
    for upstream, downstream in zip(chain, chain[1:]):
        assert upstream.output_port is not None
        assert upstream.output_port == downstream.input_port
    assert AP.chain_is_connected(AP.EXCITATION_CHAIN) is True


def test_readout_chain_references_registered_components_and_connects():
    chain = AP.readout_chain()
    assert len(chain) >= 2
    for c in chain:
        assert c.name in AP.DESIGN
    for upstream, downstream in zip(chain, chain[1:]):
        assert upstream.output_port is not None
        assert upstream.output_port == downstream.input_port
    assert AP.chain_is_connected(AP.READOUT_CHAIN) is True


def test_a_broken_or_unregistered_chain_is_not_connected():
    # an unregistered component
    assert AP.chain_is_connected(("signal_generator", "not_a_part")) is False
    # a disconnected pair: the receiver's output does not feed the coils
    assert AP.chain_is_connected(
        ("lock_in_receiver", "drive_coils_helmholtz")) is False


# --- (3) construction refuses a built or measured component --------------

def test_a_component_cannot_be_constructed_as_built():
    with pytest.raises(AP.ApparatusError):
        AP.Component(name="x", function="f", spec={"a": 1},
                     vendor_class="generic", est_cost_usd=1.0,
                     status="BUILT")


def test_a_component_cannot_be_constructed_as_measured():
    with pytest.raises(AP.ApparatusError):
        AP.Component(name="x", function="f", spec={"a": 1},
                     vendor_class="generic", est_cost_usd=1.0,
                     status="MEASURED")


def test_a_component_needs_a_function_and_a_spec():
    with pytest.raises(AP.ApparatusError):
        AP.Component(name="x", function="   ", spec={"a": 1},
                     vendor_class="generic", est_cost_usd=1.0)
    with pytest.raises(AP.ApparatusError):
        AP.Component(name="x", function="f", spec={},
                     vendor_class="generic", est_cost_usd=1.0)


def test_a_valid_design_component_constructs():
    c = AP.Component(name="x", function="f", spec={"rating": 1.0},
                     vendor_class="generic category", est_cost_usd=10.0)
    assert c.status == "DESIGN_ONLY"
    assert c.claim_class == "ENGINEERING_CANDIDATE"


# --- (4) the safety envelope ---------------------------------------------

def test_check_safety_passes_a_setting_inside_the_envelope():
    result = AP.check_safety({"drive_voltage_vpp": 5.0,
                              "drive_current_a": 1.0,
                              "magnetic_field_mt": 2.0,
                              "temperature_c": 25.0})
    assert result["pass"] is True
    assert result["within_envelope"] is True


def test_check_safety_fails_a_setting_outside_the_envelope():
    result = AP.check_safety({"drive_current_a": 999.0})
    assert result["pass"] is False
    assert result["checks"]["drive_current_a"]["pass"] is False


def test_check_safety_never_marks_anything_validated():
    """A pass is a bound check, never a validation or a clearance."""
    for settings in ({"drive_voltage_vpp": 1.0}, {"drive_current_a": 1.0}):
        result = AP.check_safety(settings)
        assert result["validated"] is False
        assert result["is_clearance_to_energise"] is False
        assert result["physical_validation"] == \
            "PHYSICAL_VALIDATION_NOT_CLAIMED"


def test_check_safety_refuses_an_unrecognised_setting():
    with pytest.raises(AP.ApparatusError):
        AP.check_safety({"unknown_knob": 1.0})


# --- (5) the design refusals ---------------------------------------------

def test_refuse_design_as_built_always_raises():
    with pytest.raises(AP.ApparatusError) as exc:
        AP.refuse_design_as_built()
    assert "DESIGN" in str(exc.value)


def test_refuse_design_as_measurement_always_raises():
    with pytest.raises(AP.ApparatusError) as exc:
        AP.refuse_design_as_measurement()
    assert "BLOCKED_MISSING_INPUT" in str(exc.value)


# --- (6) the report -------------------------------------------------------

def test_report_carries_the_verdict_and_the_disclaimers():
    report = AP.apparatus_report()
    assert report["verdict"] == "APPARATUS_DESIGN_PREREGISTERED_NOT_BUILT"
    assert AP.VERDICT == "APPARATUS_DESIGN_PREREGISTERED_NOT_BUILT"
    assert report["measured_here"] == "nothing"
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert report["claim_class"] == "ENGINEERING_CANDIDATE"
    assert report["claim_class"] in AP.CLAIM_CLASSES
    assert report["all_design_only"] is True
    assert report["chains_connected"] is True
    assert report["what_this_does_not_say"]


def test_module_imports_under_its_package_name():
    from r13 import apparatus
    assert apparatus.VERDICT == AP.VERDICT
