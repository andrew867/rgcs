"""P15 — a memory handshake over the fading crystal, software only.

Every test is written to be *capable of failing*: for each claim there is
an input that would flip the assertion. The load-bearing ones are the
firewall tests -- that a destructive read without a refresh loses the
data, that a faded frame is unreadable, and that ordered readout is the
only thing separating the store from ordinary relaxation.
"""

from __future__ import annotations

import pytest

from r10 import crystalmem as cm
from r10 import memhandshake as M


# --- module discipline -------------------------------------------------

def test_module_imports_and_reuses_crystalmem():
    assert M.READ_THRESHOLD == cm.READ_THRESHOLD
    assert M.DEFAULT_A0 == cm.DEFAULT_A0


def test_nothing_is_measured_and_validation_is_disclaimed():
    r = M.memhandshake_report()
    assert r["measured_here"] == "nothing"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == "MEMORY_HANDSHAKE_SOFTWARE_ONLY"


# --- 1. addressed frames and checksums --------------------------------

def test_make_frame_computes_a_matching_checksum():
    f = M.make_frame(3, [1, 0, 1, 1])
    assert M.verify_checksum(f)
    assert f.address == 3
    assert f.payload == (1, 0, 1, 1)


def test_checksum_is_position_weighted_and_catches_reorder():
    """Reordering the payload changes the checksum, so a shuffled payload
    fails verification. A plain popcount would miss this."""
    a = M.frame_checksum([1, 1, 0, 0])
    b = M.frame_checksum([0, 0, 1, 1])
    assert a != b


def test_a_frame_with_a_wrong_checksum_is_refused():
    with pytest.raises(ValueError):
        M.MemoryFrame(0, (1, 0, 1), 0.0, checksum=999)


def test_a_non_bit_payload_is_refused():
    with pytest.raises(ValueError):
        M.make_frame(0, [1, 2, 0])


# --- 2. write then ordered_read returns frames in write order ---------

def _store():
    s = M.new_store([0, 1, 2, 3])
    s = M.write(s, M.make_frame(2, [1, 0, 1]))
    s = M.write(s, M.make_frame(0, [1, 1, 0]))
    s = M.write(s, M.make_frame(3, [0, 1, 1]))
    return s


def test_ordered_read_returns_frames_in_write_order():
    """Falsifiable: if ordered_read followed address order instead of
    write order, the sequence 2,0,3 would come back as 0,2,3 and fail."""
    s = _store()
    readout = M.ordered_read(s)
    assert tuple(f.address for f in readout) == (2, 0, 3)
    assert M.verify_write_order(readout, s.write_order)


def test_a_shuffled_readout_fails_the_order_check():
    """The falsifiable core of the ordered-readout claim: reverse the
    readout and the order check must reject it."""
    s = _store()
    readout = M.ordered_read(s)
    shuffled = tuple(reversed(readout))
    assert not M.verify_write_order(shuffled, s.write_order)
    assert M.ordered_readout_demonstrates_memory(readout, s.write_order)
    assert not M.ordered_readout_demonstrates_memory(shuffled, s.write_order)


def test_a_misaddressed_frame_is_refused():
    s = M.new_store([0, 1])
    with pytest.raises(M.MemHandshakeError):
        M.write(s, M.make_frame(7, [1, 0]))


# --- 3. destructive read, re-read refusal, and refresh ----------------

def _written_cell(address=1, payload=(1, 0, 1)):
    s = M.new_store([address])
    s = M.write(s, M.make_frame(address, payload))
    return s.cells[address]


def test_destructive_read_returns_the_frame_and_consumes_the_cell():
    cell = _written_cell()
    frame, consumed = M.destructive_read(cell)
    assert frame is not None and frame.payload == (1, 0, 1)
    assert consumed.consumed is True
    assert consumed.bit.amplitude == 0.0


def test_reread_without_refresh_raises():
    """A consumed cell cannot be read again until refreshed. If the read
    were non-destructive this would not raise."""
    cell = _written_cell()
    _, consumed = M.destructive_read(cell)
    with pytest.raises(M.MemHandshakeError):
        M.refuse_reread_without_refresh(consumed)
    with pytest.raises(M.MemHandshakeError):
        M.destructive_read(consumed)


def test_refresh_then_read_works():
    """A refresh restores the cell so the next read succeeds. Falsifiable:
    if refresh did not clear the consumed flag / restore amplitude, the
    read would raise or return nothing."""
    cell = _written_cell()
    _, consumed = M.destructive_read(cell)
    restored = M.refresh(consumed)
    assert restored.consumed is False
    frame, _ = M.destructive_read(restored)
    assert frame is not None and frame.payload == (1, 0, 1)


def test_refreshing_an_empty_cell_is_refused():
    empty = M.MemoryCell(5)
    with pytest.raises(M.MemHandshakeError):
        M.refresh(empty)


# --- 4. retention: a faded frame is unreadable ------------------------

def test_a_frame_within_the_retention_window_is_readable():
    f = M.make_frame(0, [1, 0])
    tau = 1.0
    inside = cm.retention_window(tau) * 0.5
    assert M.is_readable(f, inside, tau)


def test_a_frame_past_the_retention_window_is_not_readable():
    """Reuses crystalmem's decay: past t_max the envelope is below
    threshold. If retention did not fade this could never flip."""
    f = M.make_frame(0, [1, 0])
    tau = 1.0
    outside = cm.retention_window(tau) * 1.01
    assert not M.is_readable(f, outside, tau)


def test_an_aged_out_cell_reads_back_nothing():
    """Age a written cell past its window and the destructive read
    recovers no frame, even though the cell was written."""
    cell = _written_cell()
    aged = M.age_cell(cell, tau=1.0, dt=cm.retention_window(1.0) * 1.01)
    frame, consumed = M.destructive_read(aged)
    assert frame is None
    assert consumed.consumed is True


# --- 5. the firewall: no memory from a decay curve alone --------------

def test_memory_claim_is_refused_without_ordered_readout():
    with pytest.raises(M.MemHandshakeError) as e:
        M.refuse_memory_claim_without_ordered_readout()
    msg = str(e.value)
    assert "ordinary material relaxation" in msg
    assert "ordered delayed readout" in msg
    assert "point-for-point identical" in msg
    assert "nothing here is measured" in msg


def test_report_disclaims_and_names_the_firewall():
    r = M.memhandshake_report()
    assert "ordered delayed readout" in r["the_firewall"]
    assert "Nothing has been measured" in r["what_this_does_not_say"]
    assert "crystalmem" in r["reuses"]
