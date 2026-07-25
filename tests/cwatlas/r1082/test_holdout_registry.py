"""P25 — holdout vector registry and body-scope firewall.

Train/holdout disjointness, the foreign-body firewall, sealed anchors barred
from holdouts, opaque-id-only records, deterministic sealing, and the
candidate-not-measured refusal.
"""

from __future__ import annotations

import pytest

from cwatlas.r1082 import claims, holdout_registry as H
from cwatlas.r1082.holdout_registry import BodyScope, Partition


def test_body_scope_firewall_classifies_foreign_bodies():
    assert H.classify_body("EARTH") is BodyScope.IN_SCOPE
    assert H.classify_body("terra") is BodyScope.IN_SCOPE
    assert H.classify_body("MARS") is BodyScope.FOREIGN_OUT_OF_SCOPE
    assert H.classify_body("PROXIMA_CENTAURI_B") is BodyScope.FOREIGN_OUT_OF_SCOPE


def test_foreign_body_routed_out_of_scope_not_force_decoded():
    reg = H.HoldoutRegistry()
    # Shares the 01|65 prefix with Stonehenge but declared MARS.
    rec = reg.register("V_FOREIGN", (1, 65, 87, 65, 23),
                       partition=Partition.HOLDOUT, body="MARS")
    # Firewall overrides the requested partition: it is FOREIGN, not a holdout.
    assert rec.partition is Partition.FOREIGN
    assert rec.in_scope is False
    assert "V_FOREIGN" not in reg.holdout_ids
    assert "V_FOREIGN" in reg.foreign_ids


def test_in_scope_vector_cannot_be_filed_foreign():
    reg = H.HoldoutRegistry()
    with pytest.raises(H.HoldoutRegistryError):
        reg.register("V1", (1, 2, 3, 4, 5), partition=Partition.FOREIGN,
                     body="EARTH")


def test_train_holdout_disjointness_enforced():
    reg = H.HoldoutRegistry()
    reg.register("V1", (1, 2, 3, 4, 5), partition=Partition.TRAIN)
    with pytest.raises(H.HoldoutRegistryError):
        reg.register("V1", (1, 2, 3, 4, 5), partition=Partition.HOLDOUT)
    reg.assert_disjoint()
    assert "V1" in reg.train_ids
    assert "V1" not in reg.holdout_ids


def test_duplicate_registration_refused():
    reg = H.HoldoutRegistry()
    reg.register("V1", (1, 2, 3, 4, 5), partition=Partition.HOLDOUT)
    with pytest.raises(H.HoldoutRegistryError):
        reg.register("V1", (1, 2, 3, 4, 5), partition=Partition.HOLDOUT)


def test_sealed_fit_anchor_never_registered_as_holdout():
    reg = H.HoldoutRegistry()
    for anchor_id in H.FIT_USED_ANCHOR_IDS:
        with pytest.raises(H.HoldoutRegistryError):
            reg.register(anchor_id, (1, 2, 3, 4, 5), partition=Partition.HOLDOUT)


def test_records_are_opaque_id_only_no_raw_or_narrative():
    reg = H.build_default_registry()
    for rec in reg.vectors:
        proj = rec.public_projection()
        assert set(proj) == {
            "opaque_id", "tokens", "route_hash", "body", "body_scope",
            "partition", "in_scope", "claim_class"}
        assert "raw" not in proj
        assert "narrative" not in proj
        assert proj["route_hash"].startswith("sha256:")


def test_seal_is_deterministic():
    a = H.build_default_registry().seal()
    b = H.build_default_registry().seal()
    assert a.holdout_digest == b.holdout_digest
    assert a.holdout_count == b.holdout_count == 2


def test_no_holdout_added_after_seal():
    reg = H.build_default_registry()
    reg.seal()
    with pytest.raises(H.HoldoutRegistryError):
        reg.register("HOLDOUT_LATE", (3, 3, 3, 3, 3), partition=Partition.HOLDOUT)
    # A non-holdout (dev) may still be added — only the holdout set is sealed.
    reg.register("DEV_LATE", (4, 4, 4, 4, 4), partition=Partition.DEV)


def test_invalid_route_refused():
    reg = H.HoldoutRegistry()
    with pytest.raises(H.HoldoutRegistryError):
        reg.register("V1", (1, 2, 3), partition=Partition.TRAIN)
    with pytest.raises(H.HoldoutRegistryError):
        reg.register("V2", (1, 2, 3, 4, 100), partition=Partition.TRAIN)


def test_candidate_not_measured_raises():
    reg = H.HoldoutRegistry()
    rec = reg.register("V1", (1, 2, 3, 4, 5), partition=Partition.HOLDOUT)
    with pytest.raises(claims.R1082ClaimError):
        rec.assert_not_measured()


def test_default_registry_partition_counts():
    reg = H.build_default_registry()
    assert len(reg.train_ids) == 2
    assert len(reg.dev_ids) == 1
    assert len(reg.holdout_ids) == 2
    assert len(reg.foreign_ids) == 2
    reg.assert_disjoint()


def test_report_governance_fields():
    r = H.holdout_registry_report()
    assert r["phase_id"] == "P25"
    assert r["tranche"] == "T07"
    assert r["train_holdout_disjoint"] is True
    assert r["foreign_bodies_force_decoded"] is False
    assert r["holdouts_used_in_fit"] is False
    assert r["opaque_ids_only"] is True
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["verdict"]
