"""R10.8.5A locks — the corrected forward/inverse projection.

The frozen packet parser is untouched; hierarchical indices are never
coordinates; the Stonehenge word is a hard TRAINING equality under the
declared training alignment; the orange-slice active solve uses shells
7,7,7 with the raw 7,3,7 retained in provenance; there is no per-vector
offset and no post-reveal retuning; the reverse encoder reproduces the
original packet and states its aliasing explicitly."""

import inspect

import pytest

from r12 import icosapacket as pk

from cwatlas.claims import ClaimError
from cwatlas.r1085a import final_projection as fp
from cwatlas.r1085a import magnetic_shell as ms
from cwatlas.r1085a import orange_slice as osl
from cwatlas.r1085a import shell_profile as sp
from cwatlas.r1085a.land_zero import land_zero

EPOCH = 2025.0


@pytest.fixture(scope="module")
def trained():
    frame, receipt = fp.training_alignment(EPOCH)
    return frame, receipt


# --- packet authority untouched ----------------------------------------

def test_frozen_parser_reused_verbatim():
    rec = pk.decode_record(fp.TRAINING_WORD)
    assert rec["bits"] == "001001111000110001001100101011"
    assert rec["octal"] == "1170611453"
    assert rec["face"] == 4 and rec["shell"] == 3
    assert tuple(rec["path_levels"]) == (3, 3, 0, 1, 2, 0, 2, 1, 2, 1, 1)
    a = fp.parse_address(fp.TRAINING_WORD)
    assert (a.octree_x, a.octree_y, a.octree_z) == (83, 80, 461)


# --- hierarchical indices are never coordinates ------------------------

def test_indices_never_accepted_as_coordinates():
    a = fp.parse_address(fp.TRAINING_WORD)
    for method in (a.as_latitude, a.as_longitude,
                   a.as_cartesian_km, a.as_altitude):
        with pytest.raises(ClaimError, match="not"):
            method()
    with pytest.raises(ClaimError, match="addresses"):
        fp.refuse_indices_as_coordinates("kilometres")


# --- ground/time frame is mandatory ------------------------------------

def test_frame_requires_epoch_and_ground_reference():
    from cwatlas.r1085a import ground_time_frame as gtf
    with pytest.raises(ClaimError, match="epoch"):
        gtf.refuse_frame_without_epoch()
    with pytest.raises(ClaimError, match="ground reference"):
        gtf.refuse_frame_without_ground_reference()
    with pytest.raises(ClaimError, match="ground_reference_id"):
        gtf.GroundTimeFrame(
            epoch_year=EPOCH, ground_reference_id="",
            alignment_mode="SEALED_R1082",
            rotation=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            rotational_phase_deg=0.0, south_up=True)


# --- the hard training equality ----------------------------------------

def test_stonehenge_training_equality_under_trained_frame(trained):
    """Under the training-equality alignment the decoded terminal cell
    CONTAINS Stonehenge, and the forward projection lands within the
    level-11 cell quantization (~3.4 km edge). This is CALIBRATION —
    the word trained the frame — never validation."""
    frame, receipt = trained
    addr = fp.parse_address(fp.TRAINING_WORD)
    assert fp.cell_contains(frame, addr,
                            fp.TRAINING_LAT_DEG, fp.TRAINING_LON_DEG)
    r = fp.forward(fp.TRAINING_WORD, frame,
                   sp.profile("ATMOSPHERIC_LADDER_V1"), land_zero(),
                   ms.member("GRAVITY_ONLY"), field_line_step_m=5000.0)
    d = fp.surface_distance_km(r.latitude_deg, r.longitude_deg,
                               fp.TRAINING_LAT_DEG, fp.TRAINING_LON_DEG)
    assert d < 3.5, "training equality must hold within cell quantization"
    assert r.radial_mode == "OUTER_IN_GRAVITY_FIELD_LINE"
    # the roll DOF is declared undetermined, not silently chosen
    assert "ROLL_ABOUT_TRAINING_ANCHOR_AXIS" in frame.undetermined_dof
    assert receipt["chosen_context"] in receipt["context_angles_deg"]


def test_sealed_frame_still_misses_and_is_not_retuned():
    """The sealed R10.8.2 contexts are reused exactly as frozen: under
    them the training cell does NOT contain Stonehenge (the R10.8.5
    finding stands); the trained frame is a separate declared object,
    not an in-place edit of the freeze."""
    addr = fp.parse_address(fp.TRAINING_WORD)
    for ctx in fp.sealed_contexts():
        frame = fp.sealed_frame(ctx, EPOCH)
        assert not fp.cell_contains(frame, addr,
                                    fp.TRAINING_LAT_DEG,
                                    fp.TRAINING_LON_DEG)


def test_no_post_reveal_retuning(trained):
    """The training alignment is a deterministic function of the sealed
    freeze and the training equality alone: re-solving reproduces it
    bit-for-bit, and its API exposes no tuning parameter."""
    frame, receipt = trained
    frame2, receipt2 = fp.training_alignment(EPOCH)
    assert frame.rotation == frame2.rotation
    assert receipt == receipt2
    assert set(inspect.signature(fp.training_alignment).parameters) == \
        {"epoch_year"}


# --- no per-vector offsets ---------------------------------------------

def test_forward_has_no_per_vector_offset(trained):
    """One frame, one profile, one land reference, one magnetic member —
    identical declared context for every word; the signature carries no
    offset parameter of any kind."""
    frame, _ = trained
    params = set(inspect.signature(fp.forward).parameters)
    assert params == {"word", "frame", "profile", "land_ref", "magnetic",
                      "zeta_convention", "field_line_step_m"}
    prof, lref = sp.profile("UNIFORM_100KM_V1"), land_zero()
    mag = ms.member("GRAVITY_ONLY")
    r1 = fp.forward(fp.TRAINING_WORD, frame, prof, lref, mag,
                    field_line_step_m=5000.0)
    r2 = fp.forward(int(osl.ORANGE_SLICE_VECTORS[0]), frame, prof, lref,
                    mag, field_line_step_m=5000.0)
    assert (r1.frame_mode, r1.profile_id, r1.land_reference_id,
            r1.magnetic_member_id) == \
           (r2.frame_mode, r2.profile_id, r2.land_reference_id,
            r2.magnetic_member_id)


# --- orange slice: active 7,7,7, raw 7,3,7 in provenance ---------------

def test_orange_triplet_active_solve_uses_777():
    rows = osl.rows()
    assert [r.active_shell for r in rows] == [7, 7, 7]
    assert [r.raw_shell for r in rows] == [7, 3, 7]     # provenance, verbatim
    mid = rows[1]
    assert mid.corrected and mid.vector == "165892763"
    assert mid.correction_claim == \
        "OPERATOR_CORRECTION_TRANSCRIPTION_OR_PACKET_ERROR"
    p = osl.provenance()
    assert p["raw_shells"] == [7, 3, 7]
    assert p["active_shells"] == [7, 7, 7]


def test_corrected_forward_only_accepts_registered_corrections(trained):
    frame, _ = trained
    prof, lref = sp.profile("UNIFORM_100KM_V1"), land_zero()
    mag = ms.member("GRAVITY_ONLY")
    r = fp.forward_with_operator_correction(
        165892763, 7, frame, prof, lref, mag, field_line_step_m=5000.0)
    assert r.shell_id == 7
    with pytest.raises(ClaimError, match="per-vector offsets"):
        fp.forward_with_operator_correction(
            165892763, 5, frame, prof, lref, mag)
    with pytest.raises(ClaimError, match="per-vector offsets"):
        fp.forward_with_operator_correction(
            fp.TRAINING_WORD, 7, frame, prof, lref, mag)


def test_physical_737_pattern_refused():
    with pytest.raises(ClaimError, match="transcription or packet error"):
        osl.refuse_physical_737_pattern()


# --- reverse encoding --------------------------------------------------

def test_reverse_encode_reproduces_packet_and_reports_aliasing(trained):
    frame, _ = trained
    prof = sp.profile("ATMOSPHERIC_LADDER_V1")
    r = fp.forward(fp.TRAINING_WORD, frame, prof, land_zero(),
                   ms.member("GRAVITY_ONLY"), field_line_step_m=5000.0)
    inv = fp.inverse(fp.TRAINING_LAT_DEG, fp.TRAINING_LON_DEG,
                     r.height_above_land_zero_km, frame, prof)
    assert inv.word == fp.TRAINING_WORD
    assert inv.octal == "1170611453"
    assert "aliasing" in inv.aliasing_note


def test_inverse_refuses_unencodable_shell_8(trained):
    frame, _ = trained
    prof = sp.profile("UNIFORM_100KM_V1")   # shell 8 spans 500..600 km
    with pytest.raises(ClaimError, match="never auto-applied"):
        fp.inverse(fp.TRAINING_LAT_DEG, fp.TRAINING_LON_DEG, 550.0,
                   frame, prof)


# --- claims discipline -------------------------------------------------

def test_source_origin_not_validated():
    from cwatlas import r1085a
    assert r1085a.SOURCE_ORIGIN_VALIDATED == "no"
    assert "YELLOW" in r1085a.VERDICTS[1]
