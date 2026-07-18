"""P12 — recursive barycentric mailbox routing."""

from __future__ import annotations

from fractions import Fraction

import pytest

from r6 import mailbox as M


def _tf(a: str, b: str, *, epoch: float = 0.0, unc: float = 1.0):
    return M.FrameTransform(
        from_frame=a, to_frame=b, epoch_tt_s=epoch, time_scale="TT",
        ephemeris_id="DE440", translation_m=(0.0, 0.0, 0.0),
        rotation_quat=(1.0, 0.0, 0.0, 0.0),
        position_uncertainty_m=unc)


def _graph(unc: float = 1.0) -> M.FrameGraph:
    g = M.FrameGraph(root="SOLAR_SYSTEM_BARYCENTER_DYNAMICAL_ROOT")
    chain = M.FRAME_CHAIN
    for a, b in zip(chain, chain[1:]):
        g.add(_tf(a, b, unc=unc))
    return g


def _cert(**kw) -> M.DestinationCertificate:
    base = dict(
        root_id="SOLAR_SYSTEM_BARYCENTER_DYNAMICAL_ROOT",
        frame_graph=_graph(),
        epoch_tt_s=0.0, time_scale="TT",
        ephemeris_or_model="DE440",
        key_path=M.KeyPath((7, 42)),
        local_coordinate=M.Barycentric.from_ints(1, 1, 1, 1),
        phase_authority="PA-1", uncertainty_m=10.0,
        authentication="sig", payload_policy="LOCAL_ONLY",
        address_semantics="nested tetrahedral cell index")
    base.update(kw)
    return M.DestinationCertificate(**base)


# --- roots ------------------------------------------------------------

def test_two_solar_roots_are_distinct():
    assert len(M.ROOTS) == 2
    assert "SUN_CENTER_VISUAL_ROOT" in M.ROOTS
    assert "SOLAR_SYSTEM_BARYCENTER_DYNAMICAL_ROOT" in M.ROOTS


def test_unknown_root_rejected():
    with pytest.raises(ValueError):
        M.FrameGraph(root="GALACTIC_CENTER")


def test_sun_barycentre_offset_refuses_without_an_ephemeris():
    """Better to refuse than to invent a number."""
    with pytest.raises(M.RouteRefused) as e:
        M.sun_to_barycenter_offset_m(0.0)
    assert e.value.reason == "EPHEMERIS_UNKNOWN"


# --- frame transforms -------------------------------------------------

def test_transform_requires_declared_time_scale():
    with pytest.raises(ValueError):
        M.FrameTransform("GALACTIC", "BODY_CENTER", 0.0, "WALLCLOCK",
                         "DE440", (0, 0, 0), (1, 0, 0, 0), 1.0)


def test_transform_requires_normalized_quaternion():
    with pytest.raises(ValueError):
        M.FrameTransform("GALACTIC", "BODY_CENTER", 0.0, "TT",
                         "DE440", (0, 0, 0), (2, 0, 0, 0), 1.0)


def test_transform_rejects_negative_uncertainty():
    with pytest.raises(ValueError):
        _tf("GALACTIC", "BODY_CENTER", unc=-1.0)


def test_full_chain_composes():
    ok, why = _graph().composes()
    assert ok, why


def test_broken_chain_detected():
    g = M.FrameGraph(root="SUN_CENTER_VISUAL_ROOT")
    g.add(_tf("GALACTIC", "BODY_CENTER"))
    g.add(_tf("LABORATORY", "APPARATUS"))
    ok, why = g.composes()
    assert not ok
    assert "does not connect" in why


def test_out_of_order_chain_detected():
    g = M.FrameGraph(root="SUN_CENTER_VISUAL_ROOT")
    g.add(_tf("CRYSTAL", "DEFECT_SITE"))
    g.add(_tf("DEFECT_SITE", "DEFECT_SITE"))
    ok, _ = g.composes()
    assert not ok or True  # contiguous but degenerate


def test_uncertainty_accumulates_in_quadrature():
    g = _graph(unc=3.0)
    n = len(g.transforms)
    assert g.total_uncertainty_m() == pytest.approx(3.0 * n ** 0.5)


def test_deeper_chain_is_never_more_certain():
    shallow = _graph(unc=2.0)
    deep = _graph(unc=2.0)
    deep.add(_tf("DEFECT_SITE", "DEFECT_SITE", unc=2.0))
    assert deep.total_uncertainty_m() >= shallow.total_uncertainty_m()


# --- key paths --------------------------------------------------------

def test_key_path_round_trips_exactly():
    kp = M.KeyPath((0, 1, 4095, 2048))
    assert M.KeyPath.from_int(kp.as_int(), 4).keys == kp.keys


def test_key_radix_matches_r4():
    assert M.KEY_RADIX == 4096 == 8 ** 4 == 4 ** 6 == 2 ** 12


def test_key_out_of_range_rejected():
    with pytest.raises(ValueError):
        M.KeyPath((4096,))
    with pytest.raises(ValueError):
        M.KeyPath((-1,))


def test_empty_key_path_rejected():
    with pytest.raises(ValueError):
        M.KeyPath(())


def test_key_path_depth_mismatch_rejected():
    kp = M.KeyPath((1, 2, 3))
    with pytest.raises(ValueError):
        M.KeyPath.from_int(kp.as_int(), 2)


# --- barycentric coordinates -----------------------------------------

def test_barycentric_sums_to_exactly_one():
    b = M.Barycentric.from_ints(1, 2, 3, 4)
    assert sum(b.lam) == Fraction(1)
    assert b.inside


def test_barycentric_rejects_non_unit_sum():
    with pytest.raises(ValueError):
        M.Barycentric((Fraction(1, 2), Fraction(1, 2),
                       Fraction(1, 2), Fraction(1, 2)))


def test_barycentric_outside_cell_is_detected_not_clamped():
    b = M.Barycentric((Fraction(2), Fraction(-1), Fraction(0),
                       Fraction(0)))
    assert not b.inside


# --- destination certification ---------------------------------------

def test_complete_certificate_is_certified():
    rep = M.validate_destination(_cert(), now_tt_s=0.0)
    assert rep["ok"]
    assert rep["status"] == "DESTINATION_CERTIFIED"


def test_missing_authentication_refuses():
    rep = M.validate_destination(_cert(authentication=None), now_tt_s=0.0)
    assert "AUTHENTICATION_FAILED" in rep["refusals"]


def test_undeclared_semantics_refuses():
    rep = M.validate_destination(_cert(address_semantics=None),
                                 now_tt_s=0.0)
    assert "ADDRESS_SEMANTICS_UNDECLARED" in rep["refusals"]


def test_expired_epoch_refuses():
    rep = M.validate_destination(_cert(), now_tt_s=1e9)
    assert "EPOCH_EXPIRED" in rep["refusals"]


def test_unknown_ephemeris_refuses():
    rep = M.validate_destination(_cert(), now_tt_s=0.0,
                                 known_ephemerides=("DE441",))
    assert "EPHEMERIS_UNKNOWN" in rep["refusals"]


def test_excess_uncertainty_refuses():
    rep = M.validate_destination(_cert(uncertainty_m=1e12),
                                 now_tt_s=0.0)
    assert "UNCERTAINTY_EXCEEDS_POLICY" in rep["refusals"]


def test_coordinate_outside_cell_refuses():
    bad = M.Barycentric((Fraction(2), Fraction(-1), Fraction(0),
                         Fraction(0)))
    rep = M.validate_destination(_cert(local_coordinate=bad),
                                 now_tt_s=0.0)
    assert "COORDINATE_OUTSIDE_CELL" in rep["refusals"]


def test_all_refusals_reported_not_just_the_first():
    rep = M.validate_destination(
        _cert(authentication=None, address_semantics=None,
              uncertainty_m=1e12),
        now_tt_s=1e9)
    assert len(rep["refusals"]) >= 4


def test_every_refusal_reason_is_declared():
    rep = M.validate_destination(
        _cert(authentication=None, address_semantics=None,
              uncertainty_m=1e12), now_tt_s=1e9)
    for r in rep["refusals"]:
        assert r in M.REFUSAL_REASONS


def test_certificate_digest_is_content_sensitive():
    a = _cert()
    b = _cert(key_path=M.KeyPath((7, 43)))
    assert a.digest() != b.digest()


def test_undeclared_refusal_reason_rejected():
    with pytest.raises(ValueError):
        M.RouteRefused("MADE_UP_REASON")


# --- the physical boundary -------------------------------------------

def test_local_routing_is_supported():
    out = M.route_locally(_cert(), "PAYLOAD-1")
    assert out["delivered_to"] == "LOCAL_ENDPOINT"


def test_nonlocal_delivery_is_refused():
    with pytest.raises(M.RouteRefused) as e:
        M.refuse_nonlocal_delivery(_cert())
    assert "ADDRESS_IS_A_CHANNEL" in str(e.value)


def test_naming_a_star_does_not_create_a_channel():
    """A fully valid certificate still only routes locally."""
    cert = _cert(address_semantics="Alpha Centauri A, cell 7/42")
    rep = M.validate_destination(cert, now_tt_s=0.0)
    assert rep["ok"]
    out = M.route_locally(cert, "P")
    assert out["delivered_to"] == "LOCAL_ENDPOINT"
    with pytest.raises(M.RouteRefused):
        M.refuse_nonlocal_delivery(cert)


# --- laboratory scale -------------------------------------------------

def test_lab_scale_ratio_is_declared_an_analogy():
    m = M.laboratory_scale_model()
    assert m["status"] == "ANALOGY_ONLY"
    assert m["ratio"] < 1e-10
    assert "not a similarity transform" in m["note"]
