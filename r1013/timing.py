"""R10.13 Phase 25 — dynamic-boundary timing compiler (exact integers).

Regenerates the 4096 Hz / 552 ms family from equations with
fractions.Fraction — nothing is hard-coded as a float. RESEARCH ONLY:
this is arithmetic about a source-described timing scheme; it makes no
physical claim and outputs no detection of anything.
"""

from __future__ import annotations

from fractions import Fraction

CARRIER_HZ = 4096
NOMINAL_MACROCYCLE_S = Fraction(552, 1000)


def timing_relationship() -> dict:
    """The exact closure arithmetic, derived not asserted."""
    cycles = CARRIER_HZ * NOMINAL_MACROCYCLE_S          # f_c * T0
    assert cycles == Fraction(2260992, 1000) == 2260 + Fraction(124, 125)
    next_int = int(cycles) + 1                           # 2261
    t_closed = Fraction(next_int, CARRIER_HZ)            # s
    delta = t_closed - NOMINAL_MACROCYCLE_S
    # Delta t = 1/512000 s = 1.953125 us; states = T_carrier / delta
    carrier_period = Fraction(1, CARRIER_HZ)
    n_states = carrier_period / delta
    assert n_states == 125
    phase_step_deg = Fraction(360, int(n_states))
    return {
        "carrier_hz": CARRIER_HZ,
        "nominal_macrocycle_ms": float(NOMINAL_MACROCYCLE_S * 1000),
        "carrier_cycles_nominal": {"integer": int(cycles),
                                   "fraction": [cycles.numerator,
                                                cycles.denominator],
                                   "exact": "2260 + 124/125"},
        "closure_cycles": next_int,
        "closed_macrocycle_ms": float(t_closed * 1000),
        "closed_macrocycle_exact_ms": [t_closed.numerator * 1000,
                                       t_closed.denominator],
        "trim_us": float(delta * 1_000_000),
        "trim_exact_s": [delta.numerator, delta.denominator],
        "phase_states": int(n_states),
        "phase_step_deg": float(phase_step_deg),
        "evidence_class": "SOURCE_PROVENANCE_ONLY",
        "note": "exact arithmetic on a source-described timing scheme; "
                "no physical claim",
    }


def timing_table() -> list[dict]:
    """Deterministic q = 0..124 table: trim and phase per state."""
    rel = timing_relationship()
    dn, dd = rel["trim_exact_s"]
    delta = Fraction(dn, dd)
    step = Fraction(360, rel["phase_states"])
    return [{"q": q,
             "delta_t_us": float(q * delta * 1_000_000),
             "delta_t_exact_s": [(q * delta).numerator,
                                 (q * delta).denominator],
             "phase_deg": float(q * step)}
            for q in range(rel["phase_states"])]
