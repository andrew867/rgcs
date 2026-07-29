"""R10.39A -- tail as intra-cell sundial phase, and the sqrt(2)/phi state table.

OPERATOR CORRECTION ACCEPTED. My earlier "the tail is not spatial" was
too broad. The correct statement is narrower:

    the tail does not change the CELL KEY (R4/S8/P12),
    but it may encode intra-cell phase that converts to a sublocation.

Those are different claims and only the first is established.

SUNDIAL CONVERSION
    15 deg / hour = 0.25 deg / minute = 1 deg / 4 minutes

Orange tail6 values 7, 27, 47 step by +20, which under 0.25 deg/unit is
exactly +5 deg, giving -5 / 0 / +5 about the centre. That is coherent.

ONE THING THE OPERATOR SHOULD KNOW, stated plainly rather than used to
dismiss the idea: the +20 step is ARITHMETICALLY FORCED. The three
decimal vectors differ by exactly 20, tail6 = value mod 64, and 20 < 64
with no wrap -- so the tail MUST step by 20 whatever it means. The open
and genuinely interesting question is whether the source CHOSE decimals
20 apart so that the tail would land on 5 deg steps. That is a question
about intent, and it can only be settled by a same-cell group whose
members are 20 apart AND have independently known positions.
"""

from __future__ import annotations

import math

from r1028.varcodec36 import decode

SQRT2_OVER_PHI = math.sqrt(2) / ((1 + math.sqrt(5)) / 2)
DEG_PER_HOUR, DEG_PER_MINUTE, MINUTES_PER_DEG = 15.0, 0.25, 4.0


def tail_value(value: int) -> tuple:
    d = decode(value)
    return d, value & ((1 << d["tail_bits"]) - 1)


def sundial_conversions(value: int, centre: int | None = None) -> dict:
    d, t = tail_value(value)
    w = d["tail_bits"]
    out = {
        "value": value, "tail_bits": w, "tail_dec": t,
        "deg_minute_rule_t_x_0p25": t * DEG_PER_MINUTE,
        "deg_hour_rule_t_x_15": t * DEG_PER_HOUR,
        "deg_full_turn_t_over_2pow_w": 360.0 * t / (2 ** w),
        "deg_15_x_t_over_2pow_w": DEG_PER_HOUR * t / (2 ** w),
    }
    if centre is not None:
        out["deg_relative_0p25"] = (t - centre) * DEG_PER_MINUTE
        out["deg_relative_15_over_4"] = DEG_PER_HOUR * (t - centre) / 4.0
        out["minutes_relative"] = t - centre
    return out


def phi_state_tests(value: int, sizes=(8, 16, 32, 64, 120, 360)) -> list:
    """sqrt(2)/phi state-table conversions. Reports, never selects."""
    _, t = tail_value(value)
    x = t * SQRT2_OVER_PHI
    frac = math.modf(x)[0]
    rows = []
    for N in sizes:
        rows.append({
            "value": value, "tail_dec": t, "N": N,
            "state_raw": x, "state_frac": frac,
            "floor_N_frac": int(N * frac),
            "round_N_frac": round(N * frac) % N,
            "floor_mod_N": int(x % N),
            "round_mod_N": round(x % N) % N,
        })
    return rows


def check_digit_search(values) -> dict:
    """Does ANY sqrt(2)/phi quantization reproduce the m3 check digit?"""
    D = [(v, *tail_value(v)) for v in values]
    tests = []
    for N in (8, 16, 32, 64, 120, 360):
        tests += [
            (f"floor({N}*frac(t*c))%8",
             lambda t, N=N: int(N * math.modf(t * SQRT2_OVER_PHI)[0]) % 8),
            (f"round({N}*frac(t*c))%8",
             lambda t, N=N: round(N * math.modf(t * SQRT2_OVER_PHI)[0]) % 8),
            (f"floor((t*c)%{N})%8",
             lambda t, N=N: int((t * SQRT2_OVER_PHI) % N) % 8),
            (f"round((t*c)%{N})%8",
             lambda t, N=N: round((t * SQRT2_OVER_PHI) % N) % 8),
        ]
    tests += [("floor(t*c)%8", lambda t: int(t * SQRT2_OVER_PHI) % 8),
              ("round(t*c)%8", lambda t: round(t * SQRT2_OVER_PHI) % 8)]
    surv = [nm for nm, fn in tests
            if all(fn(t) == d["check_digit_m3"] for _, d, t in D)]
    n, p = len(tests), (1 / 8) ** len(D)
    return {
        "rules_tested": n, "examples": len(D), "survivors": surv,
        "survivor_count": len(surv), "expected_false": n * p,
        "had_power": n * p < 0.05,
        "verdict": ("PHI_STATE_RULE_FOUND" if len(surv) == 1 and n * p < 0.05
                    else "ALL_PHI_CHECK_RULES_REFUTED" if not surv
                    else "AMBIGUOUS"),
        "scope_note": "this refutes 'sqrt(2)/phi predicts the m3 CHECK "
                      "DIGIT'. It does NOT refute 'sqrt(2)/phi yields a "
                      "state-table index' -- that needs a known table "
                      "size N and a known expected state per vector, "
                      "neither of which exists yet.",
    }


def orange_intracell(centre_tail: int = 27) -> dict:
    """The same-cell group, under the sundial reading."""
    vals = [165892743, 165892763, 165892783]
    rows = [sundial_conversions(v, centre=centre_tail) for v in vals]
    rel = [r["deg_relative_0p25"] for r in rows]
    steps = [round(rel[i + 1] - rel[i], 9) for i in range(len(rel) - 1)]
    return {
        "cell_key": "(R4=2, S8=120, P12=3402)",
        "rows": rows,
        "relative_deg": rel,
        "steps_deg": steps,
        "evenly_spaced": len(set(steps)) == 1,
        "step_deg": steps[0] if steps else None,
        "monotone": rel == sorted(rel),
        "tail_step_is_arithmetically_forced": True,
        "forced_because": "the three decimals differ by exactly 20 and "
                          "tail6 = value mod 64 with no wrap, so the +20 "
                          "tail step follows from the decimals alone",
        "testable_only_by": "a same-cell group with independently known "
                            "positions; no such group exists yet",
        "status": "SELF_CONSISTENT_UNFALSIFIED_UNTESTED",
    }
