"""P13 — HAL frame memory.

The two properties the phase turns on, tested as properties rather
than as single cases: a retrieval without a complete epoched frame
chain is refused, and uncertainty along a chain only ever grows. The
second is checked over randomly ordered chains as well as fixed ones,
because "grows monotonically" is easy to satisfy for one hand-picked
example and is meant to hold for every chain.
"""

from __future__ import annotations

import itertools
import math

import pytest

from r8 import framemem


EPOCH = "2026-07-19T00:00:00Z"
EPHEM = "JPL-DE440"


def tf(a, b, sigma, *, epoch=EPOCH, ephemeris=EPHEM):
    return framemem.FrameTransform(a, b, sigma, epoch=epoch,
                                   ephemeris=ephemeris)


@pytest.fixture
def chain():
    return (tf("LAB", "BODY_FIXED", 0.1),
            tf("BODY_FIXED", "BODY_CENTERED", 2.0),
            tf("BODY_CENTERED", "BARYCENTRIC", 50.0))


@pytest.fixture
def record():
    return framemem.FrameRecord(
        payload={"engram": "alpha"}, recorded_frame="LAB",
        recorded_epoch="2019-03-04T12:00:00Z", root_frame="LAB",
        intrinsic_uncertainty_m=0.01)


# --- the record --------------------------------------------------------

def test_record_carries_frame_epoch_and_root(record):
    rec = record.as_record()
    assert rec["recorded_frame"] == "LAB"
    assert rec["recorded_epoch"] == "2019-03-04T12:00:00Z"
    assert rec["root_frame"] == "LAB"


def test_record_without_an_epoch_cannot_be_constructed():
    with pytest.raises(ValueError):
        framemem.FrameRecord(payload=1, recorded_frame="LAB",
                             recorded_epoch="", root_frame="LAB")


def test_record_without_a_frame_or_root_cannot_be_constructed():
    with pytest.raises(ValueError):
        framemem.FrameRecord(payload=1, recorded_frame="",
                             recorded_epoch=EPOCH, root_frame="LAB")
    with pytest.raises(ValueError):
        framemem.FrameRecord(payload=1, recorded_frame="LAB",
                             recorded_epoch=EPOCH, root_frame="")


def test_only_synthetic_payloads_are_admitted():
    with pytest.raises(framemem.FrameRefused):
        framemem.FrameRecord(payload=1, recorded_frame="LAB",
                             recorded_epoch=EPOCH, root_frame="LAB",
                             payload_class="PERSONAL")


def test_negative_uncertainty_is_rejected():
    with pytest.raises(ValueError):
        framemem.FrameRecord(payload=1, recorded_frame="LAB",
                             recorded_epoch=EPOCH, root_frame="LAB",
                             intrinsic_uncertainty_m=-1.0)


def test_provenance_completeness_is_computed(record):
    assert record.provenance_complete()      # empty chain is complete
    incomplete = framemem.FrameRecord(
        payload=1, recorded_frame="LAB", recorded_epoch=EPOCH,
        root_frame="BARYCENTRIC",
        provenance=(framemem.FrameTransform("LAB", "BARYCENTRIC", 1.0),))
    assert not incomplete.provenance_complete()


# --- transforms --------------------------------------------------------

def test_a_transform_needs_both_an_epoch_and_an_ephemeris():
    assert tf("A", "B", 1.0).complete
    assert not framemem.FrameTransform("A", "B", 1.0,
                                       epoch=EPOCH).complete
    assert not framemem.FrameTransform("A", "B", 1.0,
                                       ephemeris=EPHEM).complete
    assert not framemem.FrameTransform("A", "B", 1.0).complete


def test_missing_names_what_is_missing():
    t = framemem.FrameTransform("A", "B", 1.0, epoch=EPOCH)
    assert t.missing() == ("ephemeris",)
    assert framemem.FrameTransform("A", "B", 1.0).missing() == \
        ("epoch", "ephemeris")


def test_incomplete_transforms_can_be_inspected_not_used():
    """Constructible on purpose: an invisible gap cannot be reported."""
    t = framemem.FrameTransform("A", "B", 1.0)
    rec = t.as_record()
    assert rec["complete"] is False
    assert rec["missing"] == ["epoch", "ephemeris"]


def test_identity_and_nameless_transforms_are_rejected():
    with pytest.raises(ValueError):
        tf("A", "A", 1.0)
    with pytest.raises(ValueError):
        tf("", "B", 1.0)
    with pytest.raises(ValueError):
        tf("A", "B", -1.0)


# --- uncertainty growth ------------------------------------------------

def test_growth_is_quadrature(chain):
    g = framemem.uncertainty_growth(chain)
    expected = math.sqrt(sum(t.uncertainty_m ** 2 for t in chain))
    assert g["total_uncertainty_m"] == pytest.approx(expected)


def test_growth_is_monotonically_nondecreasing(chain):
    g = framemem.uncertainty_growth(chain, initial_m=0.01)
    cum = g["cumulative_m"]
    assert all(a <= b for a, b in zip(cum, cum[1:]))
    assert g["monotone_nondecreasing"]


def test_growth_is_strictly_increasing_when_every_step_costs(chain):
    cum = framemem.uncertainty_growth(chain, initial_m=0.01)[
        "cumulative_m"]
    assert all(a < b for a, b in zip(cum, cum[1:]))


@pytest.mark.parametrize("order", list(itertools.permutations(range(3))))
def test_growth_is_monotone_for_every_chain_ordering(chain, order):
    """Order changes the path; it never changes the direction."""
    permuted = tuple(chain[i] for i in order)
    g = framemem.uncertainty_growth(permuted, initial_m=0.5)
    cum = g["cumulative_m"]
    assert all(a <= b for a, b in zip(cum, cum[1:]))


def test_total_is_order_independent(chain):
    totals = {
        framemem.uncertainty_growth(
            tuple(chain[i] for i in order))["total_uncertainty_m"]
        for order in itertools.permutations(range(3))}
    assert len(totals) == 1


def test_longer_chains_are_never_more_certain(chain):
    """Adding a transform cannot help, whatever it is."""
    for k in range(len(chain)):
        short = framemem.uncertainty_growth(chain[:k])
        long_ = framemem.uncertainty_growth(chain[:k + 1])
        assert (long_["total_uncertainty_m"]
                >= short["total_uncertainty_m"])


def test_an_empty_chain_costs_nothing():
    g = framemem.uncertainty_growth((), initial_m=0.4)
    assert g["total_uncertainty_m"] == pytest.approx(0.4)
    assert g["steps"] == []


def test_growth_rejects_negative_initial():
    with pytest.raises(ValueError):
        framemem.uncertainty_growth((), initial_m=-1.0)


def test_dominant_transform_is_the_largest_term(chain):
    d = framemem.dominant_transform(chain)
    assert d["uncertainty_m"] == max(t.uncertainty_m for t in chain)
    assert d["to_frame"] == "BARYCENTRIC"
    assert d["variance_share"] > 0.99


def test_dominant_transform_refuses_an_empty_chain():
    with pytest.raises(framemem.FrameRefused):
        framemem.dominant_transform(())


# --- retrieval ---------------------------------------------------------

def test_retrieval_returns_the_payload_unchanged(record, chain):
    out = framemem.retrieve_in_frame(record, "BARYCENTRIC", chain)
    assert out["payload"] == {"engram": "alpha"}
    assert out["target_frame"] == "BARYCENTRIC"


def test_retrieval_reports_the_accumulated_uncertainty(record, chain):
    out = framemem.retrieve_in_frame(record, "BARYCENTRIC", chain)
    expected = math.sqrt(
        record.intrinsic_uncertainty_m ** 2
        + sum(t.uncertainty_m ** 2 for t in chain))
    assert out["accumulated_uncertainty_m"] == pytest.approx(expected)
    assert out["degraded"]
    assert out["uncertainty_added_m"] > 0


def test_distant_retrieval_is_less_certain_than_in_place(record, chain):
    here = framemem.retrieve_in_frame(record, "LAB")
    there = framemem.retrieve_in_frame(record, "BARYCENTRIC", chain)
    assert here["accumulated_uncertainty_m"] == \
        record.intrinsic_uncertainty_m
    assert not here["degraded"]
    assert (there["accumulated_uncertainty_m"]
            > here["accumulated_uncertainty_m"])


def test_certainty_falls_monotonically_with_frame_distance(record,
                                                           chain):
    frames = ["BODY_FIXED", "BODY_CENTERED", "BARYCENTRIC"]
    sigmas = [
        framemem.retrieve_in_frame(record, f, chain[:i + 1])[
            "accumulated_uncertainty_m"]
        for i, f in enumerate(frames)]
    assert all(a < b for a, b in zip(sigmas, sigmas[1:]))


def test_retrieval_records_which_epochs_and_ephemerides_were_used(
        record, chain):
    out = framemem.retrieve_in_frame(record, "BARYCENTRIC", chain)
    assert out["epochs_used"] == [EPOCH] * 3
    assert out["ephemerides_used"] == [EPHEM] * 3
    assert "reproduce or dispute" in out["epoch_note"]


def test_retrieval_refuses_a_transform_missing_an_epoch(record):
    broken = (framemem.FrameTransform("LAB", "BARYCENTRIC", 1.0,
                                      ephemeris=EPHEM),)
    with pytest.raises(framemem.FrameRefused) as exc:
        framemem.retrieve_in_frame(record, "BARYCENTRIC", broken)
    assert "missing epoch" in str(exc.value)


def test_retrieval_refuses_a_transform_missing_an_ephemeris(record):
    broken = (framemem.FrameTransform("LAB", "BARYCENTRIC", 1.0,
                                      epoch=EPOCH),)
    with pytest.raises(framemem.FrameRefused) as exc:
        framemem.retrieve_in_frame(record, "BARYCENTRIC", broken)
    assert "missing ephemeris" in str(exc.value)


def test_one_bad_link_poisons_an_otherwise_complete_chain(record):
    mixed = (tf("LAB", "BODY_FIXED", 0.1),
             framemem.FrameTransform("BODY_FIXED", "BARYCENTRIC", 5.0,
                                     epoch=EPOCH))
    with pytest.raises(framemem.FrameRefused):
        framemem.retrieve_in_frame(record, "BARYCENTRIC", mixed)


def test_retrieval_refuses_a_broken_chain(record):
    disjoint = (tf("LAB", "BODY_FIXED", 0.1),
                tf("BODY_CENTERED", "BARYCENTRIC", 5.0))
    with pytest.raises(framemem.FrameRefused) as exc:
        framemem.retrieve_in_frame(record, "BARYCENTRIC", disjoint)
    assert "broken" in str(exc.value)


def test_retrieval_refuses_a_chain_ending_in_the_wrong_frame(record,
                                                             chain):
    with pytest.raises(framemem.FrameRefused) as exc:
        framemem.retrieve_in_frame(record, "GALACTIC", chain)
    assert "ends in" in str(exc.value)


def test_retrieval_refuses_a_frame_change_with_no_chain(record):
    with pytest.raises(framemem.FrameRefused) as exc:
        framemem.retrieve_in_frame(record, "BARYCENTRIC")
    assert "not a relabelling" in str(exc.value)


def test_retrieval_refuses_an_unnamed_target(record):
    with pytest.raises(framemem.FrameRefused):
        framemem.retrieve_in_frame(record, "")


def test_in_place_retrieval_rejects_a_pointless_chain(record, chain):
    with pytest.raises(framemem.FrameRefused):
        framemem.retrieve_in_frame(record, "LAB", chain[:1])


def test_retrieval_refuses_a_record_with_incomplete_provenance():
    orphan = framemem.FrameRecord(
        payload=1, recorded_frame="LAB", recorded_epoch=EPOCH,
        root_frame="BARYCENTRIC",
        provenance=(framemem.FrameTransform("LAB", "BARYCENTRIC", 1.0),))
    with pytest.raises(framemem.FrameRefused) as exc:
        framemem.retrieve_in_frame(orphan, "BODY_FIXED",
                                   (tf("LAB", "BODY_FIXED", 0.1),))
    assert "provenance" in str(exc.value)


def test_retrieval_type_checks_its_record(chain):
    with pytest.raises(TypeError):
        framemem.retrieve_in_frame({"payload": 1}, "BARYCENTRIC", chain)


# --- round trip --------------------------------------------------------

def test_a_round_trip_returns_the_value_and_not_the_precision(record,
                                                              chain):
    back = (tf("BARYCENTRIC", "BODY_CENTERED", 50.0),
            tf("BODY_CENTERED", "BODY_FIXED", 2.0),
            tf("BODY_FIXED", "LAB", 0.1))
    rt = framemem.round_trip_cost(record, "BARYCENTRIC", chain, back)
    assert rt["payload_unchanged"]
    assert not rt["precision_restored"]
    assert rt["permanent_loss_m"] > 0
    assert (rt["after_round_trip_uncertainty_m"]
            > rt["at_target_uncertainty_m"])


# --- refusal -----------------------------------------------------------

def test_frameless_retrieval_always_raises():
    with pytest.raises(framemem.FrameRefused):
        framemem.refuse_frameless_retrieval()


def test_frameless_refusal_raises_even_with_a_record(record):
    with pytest.raises(framemem.FrameRefused):
        framemem.refuse_frameless_retrieval(record, "BARYCENTRIC")


def test_frameless_refusal_says_it_is_undefined_not_lossy():
    with pytest.raises(framemem.FrameRefused) as exc:
        framemem.refuse_frameless_retrieval()
    msg = str(exc.value)
    assert "undefined one" in msg
    assert "not a lossy operation" in msg


# --- evidence discipline -----------------------------------------------

def _every_record(record, chain):
    yield record.as_record()
    yield chain[0].as_record()
    yield framemem.uncertainty_growth(chain)
    yield framemem.dominant_transform(chain)
    yield framemem.retrieve_in_frame(record, "BARYCENTRIC", chain)
    yield framemem.programme_summary()


def test_every_returned_record_carries_an_evidence_class(record, chain):
    for rec in _every_record(record, chain):
        assert rec["evidence_class"] in ("SYNTHETIC_MODEL",
                                         "DERIVED_ARITHMETIC")


def test_every_returned_record_states_no_measurement_was_taken(record,
                                                               chain):
    for rec in _every_record(record, chain):
        assert rec["no_measurement_statement"] == framemem.NO_MEASUREMENT
        assert "No measurement has been taken" in \
            rec["no_measurement_statement"]


def test_programme_summary_reports_untested_status():
    s = framemem.programme_summary()
    assert s["status"] == "MODEL_SPECIFIED_PHYSICALLY_UNTESTED"
    assert "not a brain interface" in s["statement"]
    assert any("monotonically non-decreasing" in inv
               for inv in s["invariants"])
