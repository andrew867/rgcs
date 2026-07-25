"""P02 -- the locked-decision ADR and configuration authority."""

from __future__ import annotations

import dataclasses
import json

import pytest

from cwatlas.r1082 import claims
from cwatlas.r1082 import config_authority as CA


def test_fifteen_locked_decisions_encoded():
    assert len(CA.LOCKED_DECISIONS) == 15
    # Every decision is an operator-selected input, not a measured fact.
    assert all(d.evidence_class == claims.EvidenceClass.OPERATOR_SELECTION.value
               for d in CA.LOCKED_DECISIONS)
    numbers = [d.number for d in CA.LOCKED_DECISIONS]
    assert numbers == list(range(1, 16))


def test_load_validates_public_fixture():
    auth = CA.ConfigurationAuthority.load()
    assert auth.profile_id == "EARTH_ROOT_D_V1"
    # A representative sample of the locked selections.
    assert auth.decision("origin").value == "EARTH_CENTER_OF_MASS"
    assert auth.decision("root_feature").value == "ICOSAHEDRAL_FACE_CENTER"
    assert auth.decision("route_core").value == "FIVE_TOKEN_BASE_100"
    assert auth.decision("local_coordinate").value == "BARYCENTRIC"


def test_freeze_hash_is_deterministic():
    a = CA.ConfigurationAuthority.load().freeze_hash()
    b = CA.ConfigurationAuthority.load().freeze_hash()
    assert a == b
    assert len(a) == 64  # SHA-256 hex


def test_locked_decision_mutation_is_refused():
    auth = CA.ConfigurationAuthority.load()
    # A locked decision may not be changed after the freeze.
    with pytest.raises(claims.R1082ClaimError):
        auth.refuse_change("root_feature")
    with pytest.raises(claims.R1082ClaimError):
        auth.refuse_change("route_core")


def test_authority_object_is_immutable():
    auth = CA.ConfigurationAuthority.load()
    with pytest.raises(dataclasses.FrozenInstanceError):
        auth.profile_id = "EARTH_ROOT_E_V1"


def test_unknown_decision_key_raises():
    auth = CA.ConfigurationAuthority.load()
    with pytest.raises(CA.ConfigAuthorityError):
        auth.decision("handedness_flip")
    with pytest.raises(CA.ConfigAuthorityError):
        auth.refuse_change("handedness_flip")


def test_fixture_drift_from_adr_is_rejected(tmp_path):
    # A tampered fixture that silently rotates the root feature is rejected.
    drifted = json.loads(CA.FIXTURE_PATH.read_text(encoding="utf-8"))
    drifted["root_feature"] = "ICOSAHEDRAL_VERTEX"
    p = tmp_path / "drifted.json"
    p.write_text(json.dumps(drifted), encoding="utf-8")
    with pytest.raises(CA.ConfigAuthorityError):
        CA.ConfigurationAuthority.load(p)


def test_report_seals_origin_and_effects():
    r = CA.config_authority_report()
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["measured_here"] == "nothing"
    assert r["locked_decision_count"] == 15
    assert r["fixture_validated"] is True
