"""R10.30 — the 13 MHz operating-frequency law, and the Apollo lane.

THE CANDIDATE LAW

    F_op = (F_carrier - F_LO) / 4096
    F_carrier = 94 GHz, F_LO = 40 GHz
    F_op = 54 GHz / 4096 = 13.18359375 MHz   EXACTLY

That is exact dyadic arithmetic: 4096 = 2**12, and 54e9/2**12 lands on
13183593.75 Hz with no rounding. The source's "13.1835 MHz" sits
93.75 Hz below it, which is consistent with a truncated transcription of
the exact value rather than a different number.

WHY THIS IS INTERESTING BUT NOT YET EVIDENCE
--------------------------------------------
The law has THREE free inputs (F_carrier, F_LO, divisor) fitted to ONE
output. Any target frequency can be hit by choosing F_LO, so "it comes
out exact" is not by itself surprising -- what is checkable is whether
the chosen constants are independently attested. 94 GHz is claimed from
the metasurface literature (unverified here); 40 GHz is NOT attested
anywhere in the source notes and is currently a free parameter.

So the finding is recorded as: EXACT ARITHMETIC, ONE FITTED CONSTANT.
Direct power-of-two division of 94 GHz is tested and is WORSE -- it
misses 13 MHz entirely - which is a real (if small) discriminator in
the law's favour.

4096 RECURS ELSEWHERE, AND THAT IS NOT AN ARGUMENT
   2**36 = 4096**3          the 36-bit word width
   4096 Hz                  the Scale A crystal fundamental (R10.15A)
   4096 = 2**12             12 octal digits
These are all powers of two in a system built from powers of two.
Recorded, explicitly NOT treated as corroboration.

APOLLO LANE: registered, not asserted. The pack's instruction is to stop
forcing Apollo into a 13 MHz comms story and instead register the
lunar-ranging reference. No external fact is asserted from memory here.
"""

from __future__ import annotations

DIVISOR = 4096                      # 2**12
F_CARRIER_HZ = 94e9
F_LO_HZ = 40e9
SOURCE_CLAIM_HZ = 13.1835e6


def f_op(carrier_hz: float = F_CARRIER_HZ, lo_hz: float = F_LO_HZ,
         divisor: int = DIVISOR) -> float:
    return (carrier_hz - lo_hz) / divisor


def law_tests() -> list:
    rows = []
    exact = f_op()
    rows.append({
        "test": "HETERODYNE_THEN_DIVIDE",
        "formula": "(94 GHz - 40 GHz) / 4096",
        "result_hz": exact,
        "result_mhz": exact / 1e6,
        "delta_from_source_claim_hz": exact - SOURCE_CLAIM_HZ,
        "is_exact_dyadic": (54e9 / 2 ** 12) == exact,
        "free_constants_fitted": 1,
        "verdict": "EXACT_ARITHMETIC_ONE_FITTED_CONSTANT_F_LO"})
    rows.append({
        "test": "SOURCE_CLAIM_TIMES_DIVISOR",
        "formula": "13.1835 MHz * 4096",
        "result_hz": SOURCE_CLAIM_HZ * DIVISOR,
        "result_mhz": SOURCE_CLAIM_HZ * DIVISOR / 1e6,
        "delta_from_source_claim_hz": "",
        "is_exact_dyadic": False,
        "free_constants_fitted": 0,
        "verdict": "53.999616_GHz_NEAR_54_GHz_WITHIN_384_kHz"})
    for d in (2048, 4096, 8192, 16384):
        v = F_CARRIER_HZ / d
        rows.append({
            "test": f"DIRECT_DIVIDE_94GHZ_BY_{d}",
            "formula": f"94 GHz / {d}",
            "result_hz": v, "result_mhz": v / 1e6,
            "delta_from_source_claim_hz": v - SOURCE_CLAIM_HZ,
            "is_exact_dyadic": False,
            "free_constants_fitted": 0,
            "verdict": ("REJECTED_WORSE_THAN_HETERODYNE_LAW"
                        if abs(v - SOURCE_CLAIM_HZ)
                        > abs(exact - SOURCE_CLAIM_HZ) else "COMPARABLE")})
    return rows


def power_of_two_recurrences() -> list:
    return [
        {"quantity": "36-bit word width", "relation": "2**36 == 4096**3",
         "holds": 2 ** 36 == 4096 ** 3, "is_corroboration": False},
        {"quantity": "12 octal digits", "relation": "4096 == 2**12",
         "holds": 4096 == 2 ** 12, "is_corroboration": False},
        {"quantity": "Scale A crystal fundamental",
         "relation": "4096 Hz (R10.15A mechanical lane)",
         "holds": True, "is_corroboration": False},
        {"quantity": "note", "relation":
            "all are powers of two in a system built from powers of two; "
            "co-occurrence is expected and is NOT evidence",
         "holds": True, "is_corroboration": False},
    ]


#: Apollo / lunar-ranging lane. REGISTERED, not asserted.
APOLLO_LANE = [
    {"item": "Apollo 11 landing, July 1969", "role": "date reference",
     "state": "REQUIRES_PRIMARY_SOURCE_NOT_VERIFIED_IN_THIS_RUN",
     "codec_relevance": "NONE_ESTABLISHED"},
    {"item": "EASEP / lunar laser retroreflector",
     "role": "Earth-Moon range/phase/time reference",
     "state": "REQUIRES_PRIMARY_SOURCE_NOT_VERIFIED_IN_THIS_RUN",
     "codec_relevance": "CANDIDATE_FIXED_LUNAR_COORDINATE_ONLY"},
    {"item": "fixed lunar coordinate", "role": "possible body-profile anchor",
     "state": "UNRESOLVED_NO_COORDINATE_SOURCED",
     "codec_relevance": "would pair with the frozen lunar holdout 167854923; "
                        "NOT used, NOT promoted"},
    {"item": "Apollo forced into a 13 MHz comms story",
     "role": "REJECTED FRAMING", "state": "DROPPED_PER_R10_30",
     "codec_relevance": "NONE"},
]

#: July 1969 patent window. Search slot, deliberately empty.
PATENT_WINDOW = {
    "window": "July 1969",
    "classes": ["resonator", "piezoelectric", "high-frequency device"],
    "results": [],
    "state": "SEARCH_NOT_EXECUTED_WEB_RESEARCH_NOT_AUTHORIZED",
    "required_source": "primary patent office records with number and "
                       "filing/grant date",
    "disqualifying": "secondary indexes, undated citations",
}


def report() -> dict:
    return {
        "schema": "rgcs.r1030.frequency-law.v1",
        "law": {"formula": "F_op = (F_carrier - F_LO) / 4096",
                "F_carrier_hz": F_CARRIER_HZ, "F_LO_hz": F_LO_HZ,
                "divisor": DIVISOR, "F_op_hz": f_op(),
                "F_op_mhz": f_op() / 1e6,
                "exact": True, "free_constants_fitted": 1,
                "fitted_constant": "F_LO = 40 GHz is not attested in the "
                                   "source notes and is a free parameter"},
        "tests": law_tests(),
        "power_of_two_recurrences": power_of_two_recurrences(),
        "apollo_lane": APOLLO_LANE,
        "patent_window": PATENT_WINDOW,
        "mechanism_proposed": False,
        "physical_validation_claimed": False,
        "external_facts_asserted": 0,
        "verdict": "R10_30_FREQUENCY_LAW_EXACT_ARITHMETIC_ONE_FITTED_CONSTANT",
    }
