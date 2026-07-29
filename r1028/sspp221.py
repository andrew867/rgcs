"""R10.28 Agent 05 — the 2,2,2,1 stepping law on a 35-position ring.

THE ARITHMETIC THAT MAKES THIS LAW EXACT:

    2 + 2 + 2 + 1 = 7        one cycle advances 7 positions
    35 / 7 = 5               exactly 5 cycles close the ring
    beam step 1/7            matches the cycle sum
    2*pi / 7                 the implied phase increment

So the source's "2,2,2,1 stepping", "35 positions" and "step 1/7" are
one statement, not three: the cycle advances 1/5 of the ring per cycle
and 1/7 of a cycle per unit step, and it closes with no remainder. That
is a real consistency check and it passes exactly.

The ring closes after 20 steps having visited 20 of the 35 positions.
The 15 unvisited positions are a DERIVED consequence of the law, and
they are NOT the same thing as the source's "33 active / 2 blank". That
discrepancy is reported, not smoothed over.

NO PHYSICAL VALIDATION. This module emits geometry and drive tables for
a bench that does not exist. No force, thrust or momentum claim is made
anywhere; any such claim requires a closed-surface momentum balance
(see ``rgcs_surface_wave.momentum``).
"""

from __future__ import annotations

import math

RING_POSITIONS = 35
STEP_CYCLE = (2, 2, 2, 1)
CYCLE_SUM = sum(STEP_CYCLE)            # 7
SOURCE_ACTIVE = 33
SOURCE_BLANK = 2


def ring_arithmetic() -> dict:
    return {
        "ring_positions": RING_POSITIONS,
        "step_cycle": list(STEP_CYCLE),
        "cycle_sum": CYCLE_SUM,
        "cycles_to_close_ring": RING_POSITIONS / CYCLE_SUM,
        "ring_closes_exactly": RING_POSITIONS % CYCLE_SUM == 0,
        "beam_step_fraction": f"1/{CYCLE_SUM}",
        "phase_increment_rad": 2 * math.pi / CYCLE_SUM,
        "phase_increment_deg": 360.0 / CYCLE_SUM,
        "position_increment_rad": 2 * math.pi / RING_POSITIONS,
        "note": "2+2+2+1 = 7 and 35/7 = 5, so the stepping law closes "
                "the 35-position ring in exactly 5 cycles with no "
                "remainder; the source's '1/7 beam step' is the same 7",
    }


def stepping_sequence(start: int = 0) -> list:
    """Walk the ring under the 2,2,2,1 cycle until it closes."""
    seq, pos, i = [start], start, 0
    while True:
        pos = (pos + STEP_CYCLE[i % len(STEP_CYCLE)]) % RING_POSITIONS
        i += 1
        if pos == start:
            break
        seq.append(pos)
        if i > 4 * RING_POSITIONS:                # pragma: no cover
            break
    return seq


def modulation_table(start: int = 0) -> list:
    """Per-position drive table for the 35-element ring."""
    visited = stepping_sequence(start)
    order = {p: k for k, p in enumerate(visited)}
    rows = []
    for p in range(RING_POSITIONS):
        active = p in order
        k = order.get(p)
        rows.append({
            "position_index": p,
            "mechanical_angle_deg": round(360.0 * p / RING_POSITIONS, 4),
            "in_stepping_orbit": active,
            "step_order": "" if k is None else k,
            "drive_phase_rad": ("" if k is None
                                else round((2 * math.pi / CYCLE_SUM) * k
                                           % (2 * math.pi), 6)),
            "drive_phase_deg": ("" if k is None
                                else round((360.0 / CYCLE_SUM) * k % 360.0,
                                           4)),
            "state": "ACTIVE" if active else "NOT_VISITED_BY_STEPPING_LAW",
        })
    return rows


def variants() -> list:
    """Bench control variants required by the pack."""
    base = len(stepping_sequence(0))
    return [
        {"variant": "V1_221_STEPPING", "description":
            "2,2,2,1 forward stepping from position 0",
         "active_positions": base, "is_control": False},
        {"variant": "V2_35_OF_35_ALL_ACTIVE", "description":
            "all positions driven; symmetric control",
         "active_positions": 35, "is_control": True},
        {"variant": "V3_33_ACTIVE_2_BLANK", "description":
            "source-stated active/blank split; blank placement is a "
            "free parameter and must be swept",
         "active_positions": SOURCE_ACTIVE, "is_control": False},
        {"variant": "V4_REVERSED_STEPPING", "description":
            "1,2,2,2 reversed cycle; parity control",
         "active_positions": base, "is_control": True},
        {"variant": "V5_REVERSED_DRIVE_DIRECTION", "description":
            "same geometry, travelling wave reversed; sign-flip control",
         "active_positions": base, "is_control": True},
        {"variant": "V6_RANDOM_BLANKS", "description":
            "randomised blank placement, same blank count; null control",
         "active_positions": SOURCE_ACTIVE, "is_control": True},
    ]


def resonator_matrix() -> list:
    """Comparison slots. Every performance cell is UNMEASURED."""
    rows = []
    for name, note in (
            ("I_SHAPED", "source baseline"),
            ("PLATE", "source claims may outperform I-shaped"),
            ("CIRCULAR_PATCH", "looped SSPP line radiator")):
        rows.append({
            "resonator": name, "source_note": note,
            "simulated": False, "measured": False,
            "q_factor": "UNMEASURED", "bandwidth": "UNMEASURED",
            "coupling": "UNMEASURED",
            "status": "DESIGN_SLOT_ONLY_NO_SOLVER_RUN"})
    return rows


def downshift_ratio_tests() -> list:
    """94 GHz -> 13 MHz family. Arithmetic only, no mechanism claimed."""
    rows = []
    f_hi = 94e9
    for label, f_lo in (("13_MHz_ISM_NFC", 13.56e6),
                        ("13p1835_MHz_CLAIMED", 13.1835e6),
                        ("13_MHz_ROUND", 13.0e6)):
        ratio = f_hi / f_lo
        rows.append({
            "high_hz": f_hi, "low_label": label, "low_hz": f_lo,
            "ratio": round(ratio, 6),
            "nearest_power_of_2": round(math.log2(ratio), 6),
            "is_integer_ratio": abs(ratio - round(ratio)) < 1e-9,
            "nearest_integer": round(ratio),
            "integer_error": round(abs(ratio - round(ratio)), 6),
            "mechanism": "NONE_PROPOSED",
            "status": "ARITHMETIC_ONLY_NO_DOWNCONVERSION_MECHANISM_CLAIMED"})
    return rows


def report() -> dict:
    ring = ring_arithmetic()
    seq = stepping_sequence()
    return {
        "schema": "rgcs.r1028.sspp-221.v1",
        "ring": ring,
        "stepping_sequence": seq,
        "positions_visited": len(seq),
        "positions_not_visited": RING_POSITIONS - len(seq),
        "source_active_blank": [SOURCE_ACTIVE, SOURCE_BLANK],
        "discrepancy": (
            f"the stepping law visits {len(seq)} of {RING_POSITIONS} "
            f"positions, while the source states {SOURCE_ACTIVE} active / "
            f"{SOURCE_BLANK} blank. These are NOT the same partition and "
            f"the source notes do not say how they reconcile. Reported as "
            f"an open discrepancy; neither is adjusted to fit the other."),
        "verdict": "R10_28_SSPP_OAM_221_STEP_DESIGN_READY",
        "physical_validation_claimed": False,
    }
