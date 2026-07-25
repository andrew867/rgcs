"""P04 — the R15 crystal and specimen registry.

Focused, negative and determinism tests. Registered is not measured; a
nominal value cannot masquerade as measured; unknown stays unknown; damage
creates a new state; synthetic specimens are visibly synthetic; the content
hash detects tamper; a missing dimension refuses promotion; and the whole
registry claims nothing measured.
"""

from __future__ import annotations

import pytest

from r13.crystalframe import QUARTZ_A_ANGSTROM, QUARTZ_C_ANGSTROM
from r15 import claims
from r15.claims import ClaimClass
from r15 import specimens as S


# --- Quantity: unknown / nominal / measured -----------------------------

def test_unknown_remains_unknown():
    u = S.Quantity.unknown("g")
    assert u.value is None
    assert not u.known
    assert not u.measured
    # an unknown quantity may not smuggle in a value
    with pytest.raises(S.SpecimenError):
        S.Quantity(value=1.0, unit="g", field_class=S.FieldClass.UNKNOWN)


def test_nominal_cannot_masquerade_as_measured():
    nominal = S.Quantity(4.0e-2, "g", S.FieldClass.NOMINAL)
    with pytest.raises(claims.ClaimError):
        S.require_measured(nominal, "mass")
    measured = S.Quantity(4.0e-2, "g", S.FieldClass.MEASURED, uncertainty=1e-4)
    assert S.require_measured(measured, "mass") is measured


def test_only_measured_carries_uncertainty():
    with pytest.raises(S.SpecimenError):
        S.Quantity(4.0e-2, "g", S.FieldClass.NOMINAL, uncertainty=1e-4)


def test_finite_value_required_for_known_class():
    with pytest.raises(S.SpecimenError):
        S.Quantity(value=None, unit="g", field_class=S.FieldClass.NOMINAL)


# --- registration vs measurement ----------------------------------------

def test_registered_is_not_measured():
    reg = S.SpecimenRegistry()
    rec = reg.register(S.make_quartz_blank())
    assert rec.state is S.SpecimenState.REGISTERED
    assert not rec.has_physical_artifact
    assert S.specimen_claim_class(rec) is ClaimClass.SOURCE_CLAIM
    assert S.specimen_claim_class(rec) not in claims.MEASUREMENT_CLASSES


def test_refuse_specimen_as_measured_always_raises():
    reg = S.SpecimenRegistry()
    rec = reg.register(S.make_quartz_blank())
    with pytest.raises(claims.ClaimError):
        S.refuse_specimen_as_measured(rec)


def test_promotion_without_artifacts_is_refused():
    reg = S.SpecimenRegistry()
    reg.register(S.make_quartz_blank(seed="q1"))
    sid = reg.ids()[0]
    with pytest.raises(claims.ClaimError):
        reg.promote_to_measured(sid, artifacts=(),
                                mode=S.AcquisitionMode.SYNTHETIC)


def test_real_acquisition_is_blocked():
    reg = S.SpecimenRegistry()
    rec = reg.register(S.make_quartz_blank(seed="q2"))
    with pytest.raises(S.SpecimenError):
        reg.promote_to_measured(rec.specimen_id, artifacts=("raw.bin",),
                                mode=S.AcquisitionMode.REAL)


def test_missing_dimension_refuses_promotion():
    reg = S.SpecimenRegistry()
    bare = S.SpecimenRecord(
        specimen_id=S.derive_specimen_id("bare"),
        material=S.Material.METAL_DISK,
        mass=S.Quantity(1.0, "g", S.FieldClass.NOMINAL),
        geometry=S.Geometry(shape="disk", dimensions=()),
        orientation=S.Orientation.amorphous(scheme="metal"),
        provenance=S.Provenance(supplier="X"))
    reg.register(bare)
    with pytest.raises(S.SpecimenError):
        reg.promote_to_measured(bare.specimen_id, artifacts=("raw.bin",),
                                mode=S.AcquisitionMode.SYNTHETIC)


def test_synthetic_promotion_stays_non_physical():
    reg = S.SpecimenRegistry()
    rec = reg.register(S.make_quartz_blank(seed="q3"))
    measured = reg.promote_to_measured(
        rec.specimen_id, artifacts=("synthetic_scan.npz",),
        mode=S.AcquisitionMode.SYNTHETIC)
    assert measured.state is S.SpecimenState.MEASURED
    assert measured.is_synthetic
    assert S.specimen_claim_class(measured) is ClaimClass.SYNTHETIC_FIXTURE
    assert S.specimen_claim_class(measured) not in claims.MEASUREMENT_CLASSES


# --- synthetic specimens are visibly synthetic --------------------------

def test_synthetic_specimen_is_visibly_synthetic():
    synth = S.make_synthetic_specimen()
    assert synth.is_synthetic
    assert S.specimen_claim_class(synth) is ClaimClass.SYNTHETIC_FIXTURE
    rec = synth.to_record()
    assert rec["synthetic"] is True
    assert rec["claim_class"] == "SYNTHETIC_FIXTURE"


def test_real_material_specimen_is_not_flagged_synthetic():
    quartz = S.make_quartz_blank()
    assert not quartz.is_synthetic
    assert quartz.to_record()["synthetic"] is False


# --- lifecycle: damage / quarantine / retire ----------------------------

def test_damage_creates_a_new_state_and_revision():
    reg = S.SpecimenRegistry()
    rec = reg.register(S.make_quartz_blank(seed="q4"))
    assert rec.revision == 0 and rec.state is S.SpecimenState.REGISTERED
    damaged = reg.mark_damaged(
        rec.specimen_id, S.Defect(kind="chip", severity="minor"))
    assert damaged.state is S.SpecimenState.DAMAGED
    assert damaged.revision == 1
    assert len(damaged.defects) == 1
    # identity is preserved across the revision
    assert damaged.specimen_id == rec.specimen_id
    assert len(reg.history(rec.specimen_id)) == 2


def test_quarantine_and_retire_and_terminal():
    reg = S.SpecimenRegistry()
    rec = reg.register(S.make_quartz_blank(seed="q5"))
    reg.quarantine(rec.specimen_id)
    assert reg.current(rec.specimen_id).state is S.SpecimenState.QUARANTINED
    retired = reg.retire(rec.specimen_id)
    assert retired.state is S.SpecimenState.RETIRED
    # a retired specimen is terminal
    with pytest.raises(S.SpecimenError):
        reg.quarantine(rec.specimen_id)


def test_revision_history_preserves_prior_records():
    reg = S.SpecimenRegistry()
    rec = reg.register(S.make_quartz_blank(seed="q6"))
    reg.mark_damaged(rec.specimen_id, S.Defect(kind="scratch"))
    hist = reg.history(rec.specimen_id)
    assert [h.revision for h in hist] == [0, 1]
    assert hist[0].state is S.SpecimenState.REGISTERED
    assert hist[1].state is S.SpecimenState.DAMAGED


def test_duplicate_registration_refused():
    reg = S.SpecimenRegistry()
    rec = S.make_quartz_blank(seed="dup")
    reg.register(rec)
    with pytest.raises(S.SpecimenError):
        reg.register(S.make_quartz_blank(specimen_id=rec.specimen_id))


# --- content hash and tamper --------------------------------------------

def test_content_hash_is_deterministic():
    a = S.make_quartz_blank(seed="hash-me")
    b = S.make_quartz_blank(seed="hash-me")
    assert a.content_hash() == b.content_hash()
    assert S.verify_record(a.to_record())


def test_hash_tamper_is_detected():
    rec = S.make_quartz_blank(seed="tamper").to_record()
    assert S.verify_record(rec)
    rec["mass"]["value"] = 999.0            # tamper with a field
    assert not S.verify_record(rec)


def test_hash_changes_when_any_field_changes():
    a = S.make_quartz_blank(seed="A")
    reg = S.SpecimenRegistry()
    reg.register(a)
    damaged = reg.mark_damaged(a.specimen_id, S.Defect(kind="chip"))
    assert damaged.content_hash() != a.content_hash()


def test_missing_hash_fails_verification():
    rec = S.make_quartz_blank(seed="nohash").to_record(include_hash=False)
    assert "content_hash" not in rec
    assert not S.verify_record(rec)


# --- crystallographic frame reuse ---------------------------------------

def test_quartz_orientation_reuses_lattice_frame():
    o = S.Orientation.quartz(cut="c-plane", plane_hkl=(0, 0, 1))
    assert o.lattice_a == QUARTZ_A_ANGSTROM
    assert o.lattice_c == QUARTZ_C_ANGSTROM
    assert "P3_121" in o.space_groups
    frame = o.frame()
    # the frame is the r13 alpha-quartz lattice frame
    assert frame.a == QUARTZ_A_ANGSTROM
    # a cut plane has a finite reciprocal-space normal (geometry, not
    # a measurement)
    normal = o.plane_normal()
    assert normal.shape == (3,)
    assert float((normal * normal).sum()) > 0.0


def test_zero_plane_is_refused():
    with pytest.raises(S.SpecimenError):
        S.Orientation.quartz(plane_hkl=(0, 0, 0))


def test_amorphous_orientation_has_no_lattice_frame():
    o = S.Orientation.amorphous(scheme="glass")
    with pytest.raises(S.SpecimenError):
        o.frame()


# --- inferred density ---------------------------------------------------

def test_density_is_inferred_not_measured():
    q = S.make_quartz_blank()
    assert q.density.field_class is S.FieldClass.INFERRED
    assert q.density.value is not None
    # a measured density would have to come from an instrument, not here
    with pytest.raises(claims.ClaimError):
        S.require_measured(q.density, "density")


def test_density_unknown_when_inputs_unknown():
    geom = S.Geometry(shape="disk", dimensions=(
        ("diameter", S.Quantity.unknown("cm")),
        ("thickness", S.Quantity(3.0e-2, "cm", S.FieldClass.NOMINAL)),
    ))
    d = S.infer_density(S.Quantity(4.0e-2, "g", S.FieldClass.NOMINAL), geom)
    assert not d.known


# --- schema conformance --------------------------------------------------

def test_record_conforms_to_specimen_schema():
    import json
    import pathlib
    import jsonschema

    root = pathlib.Path(__file__).resolve().parents[2]
    schema = json.loads(
        (root / "r15" / "schemas" / "specimen_record.schema.json").read_text())
    for maker in (S.make_quartz_blank, S.make_glass_control,
                  S.make_synthetic_specimen):
        jsonschema.validate(maker().to_record(), schema)


# --- report claims nothing measured -------------------------------------

def test_report_claims_nothing_measured():
    r = S.specimens_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == S.DEFAULT_VERDICT
    assert r["example_quartz_claim_class"] == "SOURCE_CLAIM"
    assert r["example_synthetic_claim_class"] == "SYNTHETIC_FIXTURE"


def test_report_is_deterministic():
    assert S.specimens_report() == S.specimens_report()


def test_specimen_id_is_deterministic_and_immutable():
    assert S.derive_specimen_id("x") == S.derive_specimen_id("x")
    assert S.derive_specimen_id("x") != S.derive_specimen_id("y")
    with pytest.raises(S.SpecimenError):
        S.derive_specimen_id("")
