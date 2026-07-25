"""P30 — Atlas UI view-model tests.

The view-model is deterministic, serializable, carries the two-layer-root globe
overlay layers and the agreement surface, states its assumptions before
execution with no hidden defaults, and never renders a candidate as measured or
a validated source origin.
"""

from __future__ import annotations

import json

import pytest

from cwatlas.r1082 import root_certificate
from cwatlas.r1082 import ui_state as U


@pytest.fixture(autouse=True)
def _clear_cache():
    root_certificate.cache_clear()
    yield


def _seals_ok(model):
    blob = json.dumps(model, default=float)
    assert '"MEASURED"' not in blob
    assert "SOURCE_ORIGIN_VALIDATED" not in blob
    assert model["measured_here"] == "nothing"
    assert model["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert model["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"


def test_view_model_serializable_and_deterministic():
    a = U.build_view_model(2020.0, 3)
    b = U.build_view_model(2020.0, 3)
    assert U.is_serializable(a) is True
    assert a == b
    _seals_ok(a)


def test_map_to_vector_mode_when_no_vector():
    m = U.build_view_model(2020.0, 3)
    assert m["mode"] == "MAP_TO_VECTOR"
    assert m["candidate_panel"]["present"] is False


def test_vector_to_map_mode_with_vector():
    m = U.build_view_model(2020.0, 3, source_vector="165876523",
                           profile_kind="single")
    assert m["mode"] == "VECTOR_TO_MAP"
    panel = m["candidate_panel"]
    assert panel["present"] is True
    assert panel["result_type"] == "CANDIDATE_CALIBRATED_POINT"
    assert panel["rendered_as_measured"] is False
    assert len(panel["pins"]) >= 1
    _seals_ok(m)


def test_overlay_has_two_layer_root_layers():
    m = U.build_view_model(2020.0, 3)
    kinds = [l["kind"] for l in m["overlay"]["layers"]]
    assert kinds == ["FIXED_ROOT_MARKER", "DYNAMIC_SAA_PHASE_ZERO",
                     "ORIENTATION_FRAME", "SHELL_SURFACE", "CANDIDATE_OUTPUTS"]


def test_agreement_surface_present_and_not_collapsed():
    m = U.build_view_model(2020.0, 3)
    surf = m["agreement_surface"]
    assert surf["member_count"] > 0
    assert surf["cluster_count"] >= 1
    assert surf["collapsed_to_point"] is False
    assert "per_component_variance" in surf


def test_alias_set_surfaced_for_all_families():
    m = U.build_view_model(2020.0, 3, source_vector="165876523",
                           profile_kind="all")
    panel = m["candidate_panel"]
    assert panel["result_type"] in {"CANDIDATE_ALIAS_SET",
                                    "CANDIDATE_CALIBRATED_POINT"}
    if panel["result_type"] == "CANDIDATE_ALIAS_SET":
        assert panel["is_alias_set"] is True


def test_controls_have_no_hidden_defaults():
    m = U.build_view_model(2020.0, 3)
    assert set(m["controls"]) >= {"shell", "epoch", "profile", "packet_depth",
                                  "mode"}
    assumptions = m["assumptions"]
    assert assumptions["shell_supplies_radius"] is True
    assert assumptions["altitude_missing"] is False
    assert assumptions["locked_decisions_reopened"] is False
    assert len(assumptions["frozen_parameters"]) == 7


def test_invalid_vector_records_decode_error():
    m = U.build_view_model(2020.0, 3, source_vector="not-valid",
                           profile_kind="single")
    assert m["decode_error"] is not None
    assert "INVALID_SOURCE_VECTOR" in m["decode_error"]
    _seals_ok(m)


def test_bad_shell_refused():
    with pytest.raises(ValueError):
        U.build_view_model(2020.0, 99)


def test_out_of_validity_overlay_refusal():
    m = U.build_view_model(3000.0, 3)
    assert m["overlay"]["in_validity"] is False


def test_export_one_click():
    m = U.build_view_model(2020.0, 3)
    assert m["export"]["one_click"] is True
    assert set(m["export"]["formats"]) == {"JSON", "GeoJSON", "KML"}


def test_report_seals_claims():
    r = U.ui_state_report()
    assert r["phase_id"] == "P30"
    assert r["tranche"] == "T08"
    assert r["hidden_defaults"] is False
    assert r["assumptions_shown_before_execution"] is True
    assert r["alias_set_and_agreement_surface_shown"] is True
    assert r["uncertainty_collapsed_to_point"] is False
    assert r["measured_here"] == "nothing"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
