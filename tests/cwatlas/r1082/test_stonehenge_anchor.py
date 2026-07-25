"""P17 — Stonehenge training-anchor authority.

Import/validation, tokenisation, non-zero uncertainty, ledger binding,
determinism, privacy, and the never-measured negatives.
"""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import privacy
from cwatlas import provenance_ledger as pl
from cwatlas.r1082 import claims
from cwatlas.r1082 import stonehenge_anchor as A


def test_build_anchor_tokenization_and_fields():
    anchor = A.build_anchor()
    assert anchor.fixture_id == "STONEHENGE_PRIVATE_001"
    assert anchor.tokens == (1, 65, 87, 65, 23)          # 01|65|87|65|23
    assert anchor.evidence_class == "OPERATOR_SELECTION"
    assert anchor.source_status == "SOURCE"
    assert anchor.use == "training_anchor"


def test_public_coordinate_is_synthetic_with_nonzero_uncertainty():
    anchor = A.build_anchor()
    assert abs(anchor.public_lat_deg - 51.1789) < 1e-6
    assert abs(anchor.public_lon_deg - (-1.8262)) < 1e-6
    # Uncertainty never collapsed to a point.
    assert anchor.uncertainty_region.area_m2 > 0.0
    assert anchor.public_projection()["uncertainty"]["collapsed_to_point"] is False


def test_anchor_unit_vector_is_unit():
    v = A.build_anchor().anchor_unit_vector()
    assert v.shape == (3,)
    assert abs(np.linalg.norm(v) - 1.0) < 1e-12


def test_import_binds_to_hash_chained_ledger():
    imp = A.import_anchor(epoch=2020.0)
    assert imp.anchor_record.fixture_id == "STONEHENGE_PRIVATE_001"
    assert imp.anchor_record.use is not None
    # The ledger event binds the sanitised route string on a verifiable chain.
    assert imp.ledger_head != pl.GENESIS_HASH
    # Rebuild an equivalent ledger and confirm the chain verifies.
    led = pl.Ledger()
    imp2 = A.import_anchor(epoch=2020.0, ledger=led)
    assert led.verify_chain() is True
    assert imp2.ledger_head == led.head()


def test_determinism_of_hash_and_projection():
    a1 = A.build_anchor()
    a2 = A.build_anchor()
    assert a1.anchor_hash() == a2.anchor_hash()
    assert a1.public_projection() == a2.public_projection()


# -- negatives --------------------------------------------------------------

def test_negative_anchor_is_never_measured():
    anchor = A.build_anchor()
    with pytest.raises(claims.R1082ClaimError):
        anchor.refuse_as_measured()
    with pytest.raises(claims.R1082ClaimError):
        anchor.promote_to(claims.EvidenceClass.MEASURED)
    with pytest.raises(claims.R1082ClaimError):
        anchor.promote_to(claims.EvidenceClass.REPLICATED)


class _ZeroAreaRegion:
    """A stand-in region presenting area_m2 == 0 for the negative test."""

    def __init__(self, base):
        self.kind = base.kind
        self.area_m2 = 0.0
        self.radius_m = 0.0


def test_negative_zero_uncertainty_refused():
    good = A.build_anchor()
    # A zero-area (point) region asserts invented precision and is refused.
    with pytest.raises(A.StonehengeAnchorError):
        A.StonehengeAnchor(
            fixture_id=A.STONEHENGE_FIXTURE_ID,
            tokens=A.EXPECTED_TOKENS,
            route_raw=good.route_raw,
            route_hash=good.route_hash,
            public_lat_deg=A.STONEHENGE_PUBLIC_LAT_DEG,
            public_lon_deg=A.STONEHENGE_PUBLIC_LON_DEG,
            uncertainty_region=_ZeroAreaRegion(good.uncertainty_region),
        )


def test_negative_wrong_tokens_refused():
    good = A.build_anchor()
    with pytest.raises(A.StonehengeAnchorError):
        A.StonehengeAnchor(
            fixture_id=A.STONEHENGE_FIXTURE_ID,
            tokens=(9, 9, 9, 9, 9),
            route_raw=good.route_raw,
            route_hash=good.route_hash,
            public_lat_deg=A.STONEHENGE_PUBLIC_LAT_DEG,
            public_lon_deg=A.STONEHENGE_PUBLIC_LON_DEG,
            uncertainty_region=good.uncertainty_region,
        )


# -- privacy ----------------------------------------------------------------

def test_privacy_projection_carries_no_narrative_or_private_tokens():
    anchor = A.build_anchor()
    proj = anchor.public_projection()
    # Opaque id only; no private label / narrative fields.
    for k in proj:
        assert k not in privacy.PRIVATE_FIELDS
    assert "narrative" not in proj and "label" not in proj
    # Nothing in the projection trips the private-token scanner.
    import json
    assert privacy.scan_for_private(json.dumps(proj)) == []


def test_report_seals_claims():
    r = A.stonehenge_anchor_report()
    assert r["phase_id"] == "P17"
    assert r["tranche"] == "T05"
    assert r["evidence_class"] == "OPERATOR_SELECTION"
    assert r["source_status"] == "SOURCE"
    assert r["never_measured"] is True
    assert r["scored_as_holdout"] is False
    assert r["uncertainty_collapsed_to_point"] is False
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
