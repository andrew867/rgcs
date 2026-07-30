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


# --- R10.39B: the sundial refines the EPOCH, not the position ---------

SECONDS_PER_DAY = 86400
OCTAL = 8


def epoch_refinement(value: int) -> dict:
    """Nested sundial epoch refinement.

    OPERATOR INSIGHT (R10.39B): the sundial calculation refines the
    EPOCH, not the location. This is what the source's own field names
    say -- "o3: epoch refinement / o3: epoch refinement / o3: epoch
    frequency" -- and it explains why a 15 deg/hour rule appears at all:
    a sundial IS a time-to-angle conversion.

    Each o3 field is one octal digit refining the level above by 1/8:

        1 field   8 states    45 deg      3 h
        2 fields  64          5.625 deg   22.5 min
        3 fields  512         0.703 deg   168.75 s

    which is exactly "epoch refinement, epoch refinement, epoch
    frequency" as successive refinement.

    THIS CORRECTS R10.39A. There I converted the FULL 6-bit tail, which
    mixes the o3 epoch field with the m3 check digit. That produced the
    tidy -5/0/+5 spacing for orange -- but the check digit has no
    business inside an angle. Using the epoch field alone gives
    0 h / 9 h / 15 h, which is NOT evenly spaced. The even spacing was
    an artifact of including the check bits.
    """
    d = decode(value)
    o = d["E3"][:-1]                    # drop the mandatory check digit
    deg = sum(g * 360.0 / OCTAL ** (i + 1) for i, g in enumerate(o))
    sec = sum(g * SECONDS_PER_DAY / OCTAL ** (i + 1) for i, g in enumerate(o))
    return {
        "value": value, "o3_fields": o, "levels": len(o),
        "epoch_angle_deg": deg,
        "epoch_seconds": sec, "epoch_hours": sec / 3600.0,
        "resolution_deg": 360.0 / OCTAL ** len(o) if o else None,
        "resolution_seconds": (SECONDS_PER_DAY / OCTAL ** len(o)
                               if o else None),
        "check_digit_excluded": True,
    }


def levels_for_one_second() -> dict:
    """How many o3 levels reach the source's '1 second' time scale."""
    rows = []
    for k in range(1, 8):
        rows.append({"levels": k, "states": OCTAL ** k,
                     "deg": 360.0 / OCTAL ** k,
                     "seconds": SECONDS_PER_DAY / OCTAL ** k})
    reach = next(r["levels"] for r in rows if r["seconds"] <= 1.0)
    return {"rows": rows, "levels_to_reach_1_second": reach,
            "note": "the 12-bit tail carries only 3 epoch levels "
                    "(168.75 s); reaching 1 s needs 6 levels, so a "
                    "single word cannot express a 1-second epoch"}


def epoch_is_not_longitude(pairs) -> dict:
    """Discriminating test: if o3 were a SPATIAL angle, two points at
    nearly the same longitude would need nearly the same o3."""
    rows = []
    for name, value, lon in pairs:
        e = epoch_refinement(value)
        rows.append({"name": name, "lon": lon,
                     "o3_first": e["o3_fields"][0] if e["o3_fields"] else None,
                     "epoch_hours": e["epoch_hours"]})
    verdict = None
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if a["lon"] is None or b["lon"] is None:
                continue
            dlon = abs(a["lon"] - b["lon"])
            do3 = abs(a["o3_first"] - b["o3_first"])
            if dlon < 2.0 and do3 >= 2:
                verdict = {
                    "pair": [a["name"], b["name"]],
                    "delta_longitude_deg": round(dlon, 4),
                    "delta_o3_units": do3,
                    "delta_o3_deg": do3 * 45.0,
                    "spatial_reading": "CONTRADICTED",
                    "epoch_reading": "CONSISTENT",
                }
    return {"rows": rows, "discriminating_pair": verdict,
            "conclusion": ("o3 cannot be a spatial longitude: two points "
                           "under 2 deg apart carry o3 values many "
                           "sectors apart. Under an epoch reading this "
                           "is expected, since nearby places need not "
                           "share an epoch."
                           if verdict else "no discriminating pair")}
