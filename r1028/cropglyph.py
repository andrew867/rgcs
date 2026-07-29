"""R10.41 — crop-glyph rings as codec candidates, and the timing test.

SCOPE, fixed before analysis: symbolic/geometric reading and source
provenance ONLY. No claim of authorship, origin, or physical validation.

THE TIMING TEST IS THE REAL ONE
-------------------------------
The source condition is: *if the circle was made BEFORE the number was
given, the circle is the location.* That is a falsifiable ordering
claim, and it is the only test here that does not depend on choosing a
counting convention.

On repository evidence the condition HOLDS:

    Bishopstone A/B  2026-07-03   |
    Avebury          2026-07-14   |  all precede
    Fox Hill         2026-07-21   |
    orange vectors first in repo  2026-07-25/26

So the formations predate the numbers by 4–22 days.

TWO CAVEATS THAT DECIDE HOW MUCH THIS IS WORTH
----------------------------------------------
1. The repo date is an UPPER BOUND on receipt. It records when a vector
   was committed, not when the operator received it. If the orange
   vectors were received before 2026-07-03, the ordering fails. Only the
   operator can close this, and it is the single highest-value fact in
   the whole lane.

2. The formations predate the numbers, but the DECODE RULE does not.
   "3 clusters x 3 levels -> tail 27" was chosen after 165892763 was
   known. So the ordering is satisfied for the glyph's EXISTENCE and not
   for the reading. A glyph that predates a number proves nothing if the
   rule mapping glyph to number is fitted afterwards.

WHAT WOULD SETTLE IT, and it is cheap
-------------------------------------
Pre-register the counting rule NOW, before the next formation appears.
Then a formation arrives, the rule is applied blind, a number falls out,
and only then is it checked against source. That is a real experiment
and the operator is already positioned to run it.

WHY THE RATIO EVIDENCE CARRIES LITTLE WEIGHT
--------------------------------------------
Simple ratios p/q (p,q <= 9) with +-5% windows already cover 86% of the
range 1-4, and 100% at +-8%. At the stated pixel precision a near-match
to something simple is expected, not notable.
"""

from __future__ import annotations

from fractions import Fraction

#: The orange same-cell key. Supplied by the CORPUS, not by any glyph.
ORANGE_CELL = {"R4": 2, "S8": 120, "P12": 3402}
ORANGE_BASE = 165892736                    # this cell with tail6 = 0

#: Formation dates, and the date the orange vectors first appear in the
#: repository. The latter is an UPPER BOUND on receipt.
FORMATION_DATES = {
    "BISHOPSTONE_20260703_A": "2026-07-03",
    "BISHOPSTONE_20260703_B": "2026-07-03",
    "AVEBURY_20260714_A": "2026-07-14",
    "FOXHILL_20260721_A": "2026-07-21",
}
ORANGE_FIRST_IN_REPO = "2026-07-25"

CLASSES = ("MEASUREMENT_CONFIRMED", "BEST_SYMBOLIC_CANDIDATE",
           "WEAK_COUNT_CANDIDATE", "UNDERDETERMINED",
           "REFUTED_BY_GEOMETRY")


def vector_for_tail(tail6: int) -> int:
    if not 0 <= tail6 < 64:
        raise ValueError("tail6 must be 0..63")
    return ORANGE_BASE + tail6


def tail_from_counts(o3: int, m3: int) -> int:
    return (o3 & 7) * 8 + (m3 & 7)


def timing_test() -> dict:
    """Does each formation predate the number, per repo evidence?"""
    rows = []
    for gid, date in sorted(FORMATION_DATES.items()):
        rows.append({
            "glyph": gid, "formation_date": date,
            "vector_first_in_repo": ORANGE_FIRST_IN_REPO,
            "formation_precedes_number": date < ORANGE_FIRST_IN_REPO,
            "days_before": (int(ORANGE_FIRST_IN_REPO[8:10])
                            - int(date[8:10])
                            + 30 * (int(ORANGE_FIRST_IN_REPO[5:7])
                                    - int(date[5:7]))),
        })
    return {
        "rows": rows,
        "all_formations_precede": all(r["formation_precedes_number"]
                                      for r in rows),
        "repo_date_is_upper_bound_on_receipt": True,
        "blocking_question": "when were the orange vectors ACTUALLY "
                             "received from source? The repo says "
                             f"{ORANGE_FIRST_IN_REPO}, but that is a "
                             "commit date. If receipt was before "
                             "2026-07-03 the ordering fails.",
        "decode_rule_was_chosen_after": True,
        "caveat": "the ordering holds for the glyph's EXISTENCE, not for "
                  "the reading; the counting rule was fitted afterwards",
        "status": "ORDERING_HOLDS_ON_REPO_EVIDENCE_RECEIPT_DATE_UNCONFIRMED",
    }


def alternative_readings(max_count: int = 3) -> list:
    """Every defensible (o3, m3) count and the vector it lands on."""
    return [{"o3": a, "m3": b, "tail6": tail_from_counts(a, b),
             "vector": vector_for_tail(tail_from_counts(a, b))}
            for a in range(max_count + 1) for b in range(max_count + 1)]


def simple_ratio_coverage(tol: float, lo: float = 1.0, hi: float = 4.0,
                          maxpq: int = 9) -> float:
    vals = sorted({float(Fraction(p, q)) for p in range(1, maxpq + 1)
                   for q in range(1, maxpq + 1) if lo <= p / q <= hi})
    merged = []
    for a, b in sorted((v * (1 - tol), v * (1 + tol)) for v in vals):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return sum(min(b, hi) - max(a, lo) for a, b in merged
               if b > lo and a < hi) / (hi - lo)


def ratio_claim(name: str, measured: float, tol: float = 0.05) -> dict:
    vals = {Fraction(p, q) for p in range(1, 10) for q in range(1, 10)
            if 1.0 <= p / q <= 4.0}
    best = min(vals, key=lambda f: abs(float(f) - measured))
    return {"claim": name, "measured_ratio": measured,
            "nearest_simple": str(best), "nearest_value": float(best),
            "percent_off": 100 * abs(float(best) - measured) / measured,
            "null_coverage_at_tol": simple_ratio_coverage(tol),
            "informative": False,
            "why": "simple-ratio windows cover most of the range at this "
                   "tolerance, so a near-match is expected"}


def information_budget() -> dict:
    return {
        "cell_key_bits_from_corpus": 24,
        "tail_bits_claimed_from_glyph": 6,
        "p_hit_prechosen_tail": 1 / 64,
        "reading_was_prechosen": False,
        "conflicting_readings": [
            {"reading": "3 clusters x 3 levels", "tail6": 27,
             "vector": 165892763, "attributed_to": "Avebury"},
            {"reading": "2 rings x 3 clusters", "tail6": 19,
             "vector": 165892755, "attributed_to": "Fox Hill"},
        ],
        "conclusion": "the same nested-ring picture supports both "
                      "readings, so the glyph does not select between "
                      "them; only a pre-registered rule can",
    }


def prereg_protocol() -> dict:
    """The experiment to run on the NEXT formation."""
    return {
        "fix_before_next_formation": [
            "counting rule: what exactly is o3, what exactly is m3",
            "which cluster is read first (leftmost? largest? most nested?)",
            "whether concentric rings or filled discs are counted",
            "what counts as a distinct 'level'",
            "the tolerance for any ratio claim",
        ],
        "then": "apply the rule BLIND to the new formation, emit the "
                "vector, timestamp it, and only afterwards compare with "
                "source",
        "success_criterion": "the predicted tail6 matches, at p = 1/64 "
                             "per formation; two independent formations "
                             "give 1/4096",
        "stronger_still": "a glyph that supplies CELL-KEY bits (R4/S8/"
                          "P12) rather than only a tail. That is 24 bits "
                          "and cannot be reached by choosing a counting "
                          "convention.",
    }


def glyph_registry() -> list:
    return [
        {"id": "BISHOPSTONE_20260703_A", "role": "SHELL_OR_RADIAL_STACK",
         "claimed_tail6": 5, "claimed_vector": vector_for_tail(5),
         "classification": "WEAK_COUNT_CANDIDATE",
         "reason": "five radial levels is one of several defensible "
                   "counts; the 2:1 relation sits inside the ratio null"},
        {"id": "BISHOPSTONE_20260703_B", "role": "LOGO_OR_LOCK_KEY_BRIDGE",
         "claimed_tail6": None, "claimed_vector": None,
         "classification": "UNDERDETERMINED",
         "reason": "no standalone vector proposed; source ontology only"},
        {"id": "AVEBURY_20260714_A", "role": "THREE_CLUSTER_NESTED_RINGS",
         "claimed_tail6": 27, "claimed_vector": vector_for_tail(27),
         "classification": "UNDERDETERMINED",
         "reason": "recovers a vector already held; 24 of the 30 bits "
                   "came from the corpus and the tail reading is not "
                   "forced -- [2,3] is equally defensible and yields the "
                   "Fox Hill vector instead"},
        {"id": "FOXHILL_20260721_A", "role": "DOT_SPLIT_2_3",
         "claimed_tail6": 19, "claimed_vector": vector_for_tail(19),
         "classification": "WEAK_COUNT_CANDIDATE",
         "reason": "an explicit 2|3 dot split is a firmer count than a "
                   "nested-ring tally, but was still read after the fact"},
    ]


def tail_state_table() -> list:
    rows = []
    for t, src in ((5, "BISHOPSTONE_A weak"), (7, "orange low"),
                   (19, "FOXHILL primary"),
                   (27, "orange centre / AVEBURY"), (47, "orange high")):
        rows.append({"tail6": t, "vector": vector_for_tail(t), "source": src,
                     "sundial_rel_deg": (t - 27) * 0.25,
                     "epoch_o3": (t >> 3) & 7, "check_m3": t & 7,
                     "epoch_hours_o3_only": ((t >> 3) & 7) * 3.0})
    return rows


def report() -> dict:
    return {
        "schema": "rgcs.r1041.cropglyph.v1",
        "scope": "SYMBOLIC_AND_PROVENANCE_ONLY",
        "timing_test": timing_test(),
        "ratio_claims": [
            ratio_claim("BishopstoneA_152_over_76", 2.000),
            ratio_claim("BishopstoneB_86_over_44", 1.955),
            ratio_claim("Avebury_L_over_M", 2.032),
            ratio_claim("Avebury_M_over_R", 1.537),
            ratio_claim("Avebury_L_over_R", 3.122)],
        "ratio_null_at_5pct": simple_ratio_coverage(0.05),
        "ratio_null_at_8pct": simple_ratio_coverage(0.08),
        "information_budget": information_budget(),
        "prereg_protocol": prereg_protocol(),
        "registry": glyph_registry(),
        "tail_state_table": tail_state_table(),
        "measurements_independently_verified": False,
        "measurement_note": "pixel values are taken AS STATED; the "
                            "source images were not re-measured here, so "
                            "every ratio conclusion is conditional",
        "authorship_claimed": False,
        "origin_claimed": False,
        "physical_validation_claimed": False,
        "verdict": "R10_41_CROP_GLYPH_RING_VECTOR_INTEGRATION_COMPLETE",
        "headline": "the TIMING condition holds on repo evidence -- all "
                    "four formations predate the vectors by 4-22 days -- "
                    "but the decode rule was fitted afterwards, so the "
                    "glyph decodes stay UNDERDETERMINED. Pre-registering "
                    "the counting rule before the next formation turns "
                    "this into a real experiment.",
    }


# --- R10.41B: claim downgrade + pre-registered grammar test -----------

#: Ari's downgrade, adopted. A glyph supplies AT MOST a 6-bit tail.
CLAIM_LEVELS = ("DISCOVERY", "RECOVERY", "VALIDATION")
GLYPH_CLAIM_LEVEL = "DISCOVERY"

#: Stated features per glyph. These are RECONSTRUCTED from the reported
#: descriptions, not measured from the images, so the grammar test below
#: is conditional on them and re-runs if corrected counts arrive.
GLYPH_FEATURES = {
    "BISHOPSTONE_A": {"groups": 1, "levels_total": 5,
                      "levels_first_group": 5, "filled": 1, "rings": 4,
                      "dots": 0, "claimed_tail": 5},
    "AVEBURY": {"groups": 3, "levels_total": 9, "levels_first_group": 3,
                "filled": 3, "rings": 6, "dots": 0, "claimed_tail": 27},
    "FOXHILL": {"groups": 4, "levels_total": 8, "levels_first_group": 2,
                "filled": 4, "rings": 4, "dots": 5, "claimed_tail": 19},
}

GRAMMARS = {
    "G1_groups_x_levelsFirstGroup":
        lambda f: (f["groups"], f["levels_first_group"]),
    "G2_zero_x_levelsTotal": lambda f: (0, f["levels_total"]),
    "G3_groups_x_levelsTotal": lambda f: (f["groups"], f["levels_total"]),
    "G4_filled_x_rings": lambda f: (f["filled"], f["rings"]),
    "G5_levelsFirst_x_groups":
        lambda f: (f["levels_first_group"], f["groups"]),
    "G6_dots_split": lambda f: (f["dots"] // 2, f["dots"] - f["dots"] // 2),
    "G7_groupsMinus1_x_levelsFirst":
        lambda f: (f["groups"] - 1, f["levels_first_group"]),
}


def bits_supplied(glyph: str) -> dict:
    """How much of a 30-bit vector does the glyph actually provide?"""
    return {"glyph": glyph, "supplied_bits_max": 6,
            "inherited_bits": 24, "total_bits": 30,
            "fraction_supplied": 6 / 30,
            "claim_level": GLYPH_CLAIM_LEVEL,
            "status": "TAIL_STATE_CANDIDATE",
            "note": "a 30-bit vector may NOT be called recovered when "
                    "the glyph constrains at most 6 of its bits"}


def grammar_test() -> dict:
    """Does ONE grammar reproduce every claimed tail? Ari's stop test."""
    rows, consistent = [], []
    for name, fn in GRAMMARS.items():
        hits, detail = 0, {}
        for g, f in GLYPH_FEATURES.items():
            a, b = fn(f)
            valid = 0 <= a < 8 and 0 <= b < 8
            val = (a & 7) * 8 + (b & 7)
            hit = valid and val == f["claimed_tail"]
            hits += hit
            detail[g] = {"o3": a, "m3": b, "tail6": val,
                         "valid": valid, "hit": hit}
        row = {"grammar": name, "hits": hits,
               "glyphs": len(GLYPH_FEATURES),
               "reads_all": hits == len(GLYPH_FEATURES), "detail": detail}
        rows.append(row)
        if row["reads_all"]:
            consistent.append(name)
    return {
        "rows": rows,
        "grammars_tested": len(GRAMMARS),
        "consistent_grammars": consistent,
        "any_single_grammar_reads_all": bool(consistent),
        "features_were_measured": False,
        "conditional_on": "reconstructed feature counts; re-runs if "
                          "corrected counts are supplied",
        "verdict": ("R10_41B_TAIL_STATE_CANDIDATES_SURVIVE" if consistent
                    else "R10_41B_GLYPH_GRAMMAR_UNDERDETERMINED"),
        "conclusion": ("one grammar reads every glyph" if consistent else
                       "each claimed reading needs its OWN rule -- "
                       "Bishopstone A ignores groups, Avebury multiplies "
                       "groups by levels, Fox Hill ignores geometry and "
                       "counts dots. Switching grammar per image to hit "
                       "known numbers is the operator's own stop "
                       "condition."),
    }


def downgrade_registry() -> list:
    """R10.41B corrected statuses."""
    return [
        {"glyph": "FOXHILL_20260721_A", "reading": "visible split 2|3",
         "E3": [2, 3], "tail6": 19, "vector_after_packing": 165892755,
         "old_status": "CROP_GLYPH_VECTOR_DECODE",
         "new_status": "TAIL_STATE_CANDIDATE", "supplied_bits": 6},
        {"glyph": "AVEBURY_20260714_A",
         "reading": "3 clusters x 3 levels", "E3": [3, 3], "tail6": 27,
         "vector_after_packing": 165892763,
         "old_status": "AVEBURY_VECTOR_165892763_DECODED",
         "new_status": "TAIL_STATE_CANDIDATE", "supplied_bits": 6},
        {"glyph": "BISHOPSTONE_20260703_A", "reading": "5 total levels",
         "E3": [0, 5], "tail6": 5, "vector_after_packing": 165892741,
         "old_status": "WEAK_VECTOR_CANDIDATE",
         "new_status": "WEAK_TAIL_STATE_CANDIDATE", "supplied_bits": 6},
        {"glyph": "BISHOPSTONE_20260703_B", "reading": "logo/lock/bridge",
         "E3": None, "tail6": None, "vector_after_packing": None,
         "old_status": "LOGO_GLYPH",
         "new_status": "GLYPH_ONTOLOGY_ONLY", "supplied_bits": 0},
    ]


# --- R10.41C: temporal-precedence location holdout --------------------

EVIDENCE_CLASSES = (
    "GLYPH_TAIL_CANDIDATE",              # A: glyph gives tail bits only
    "TEMPORAL_PRECEDENCE_LOCATION_HOLDOUT",   # B: the strong case
    "POSTHOC_CROP_SEARCH",               # C: selection penalty required
)

#: The three conditions Ari specifies for class B.
CLASS_B_CONDITIONS = (
    "formation_predates_vector",
    "location_known_before_decode",
    "codec_frozen_before_comparison",
)

FORMATION_RECORDS = [
    {"id": "BISHOPSTONE_20260703_A", "date": "2026-07-03",
     "place": "Bishopstone, Oxfordshire, England",
     "latlon_status": "ARCHIVE_PAGE_NOT_FETCHED_NO_COORDS_HERE"},
    {"id": "BISHOPSTONE_20260703_B", "date": "2026-07-03",
     "place": "Bishopstone, Oxfordshire, England",
     "latlon_status": "ARCHIVE_PAGE_NOT_FETCHED_NO_COORDS_HERE"},
    {"id": "AVEBURY_20260714_A", "date": "2026-07-14",
     "place": "Avebury Stone Circle, Wiltshire, England",
     "latlon_status": "ARCHIVE_PAGE_NOT_FETCHED_NO_COORDS_HERE"},
    {"id": "FOXHILL_20260721_A", "date": "2026-07-21",
     "place": "Fox Hill, Wiltshire, England",
     "latlon_status": "ARCHIVE_PAGE_NOT_FETCHED_NO_COORDS_HERE"},
]


def codec_freeze_status() -> dict:
    """Was the grammar frozen BEFORE these comparisons? It was not.

    The variable-length codec (R4|S8|P12|tail, widths 27/30/33/36) was
    corrected during THIS session, after the vectors were already held.
    So condition 3 of class B fails on honest bookkeeping, regardless of
    how the ordering comes out.
    """
    return {
        "codec_version_at_comparison": "R10.38 variable-length",
        "codec_changed_during_analysis": True,
        "changed_what": "root width 5->4 bits; fixed 36-bit -> variable "
                        "27/30/33/36",
        "frozen_before_comparison": False,
        "consequence": "condition 'codec_frozen_before_comparison' FAILS, "
                       "so no formation can be class B yet even though "
                       "the ordering holds",
        "how_to_fix": "freeze the codec now, hash it, and apply it "
                      "unchanged to the NEXT formation/vector pair",
    }


def location_test_blocker() -> dict:
    """Can we score a residual distance at all? No."""
    return {
        "requires": "decoded coordinate from R4/S8/P12",
        "projector_status": "UNRECOVERED (R10.25 exact failure; 99,072 "
                            "candidates, 0 evidential survivors)",
        "can_emit_coordinate": False,
        "can_score_residual": False,
        "consequence": "the location holdout CANNOT be run, not because "
                       "of the crop data but because the decoder cannot "
                       "turn a cell key into a coordinate",
    }


def geographic_null() -> dict:
    """How surprising is 'formation in Britain, cell is the British cell'?"""
    return {
        "observation": "all four formations are in Wiltshire/Oxfordshire "
                       "and the orange cell (S8=120) is the same surface "
                       "band as Stonehenge",
        "why_weak": "the overwhelming majority of catalogued crop "
                    "formations occur in a small area of southern "
                    "England, so 'the formation is British' is close to "
                    "the base rate of the catalogue itself",
        "information_content_bits": "<= 1",
        "verdict": "CONSISTENT_BUT_NEAR_FREE",
    }


def temporal_ledger() -> list:
    freeze = codec_freeze_status()
    rows = []
    for f in FORMATION_RECORDS:
        predates = f["date"] < ORANGE_FIRST_IN_REPO
        loc_known = True          # public archive, dated before decode
        conds = {
            "formation_predates_vector": predates,
            "location_known_before_decode": loc_known,
            "codec_frozen_before_comparison": freeze[
                "frozen_before_comparison"],
        }
        cls = ("TEMPORAL_PRECEDENCE_LOCATION_HOLDOUT" if all(conds.values())
               else "GLYPH_TAIL_CANDIDATE")
        rows.append({
            "formation": f["id"], "formation_date": f["date"],
            "formation_location": f["place"],
            "latlon_source_status": f["latlon_status"],
            "vector_received_time": ORANGE_FIRST_IN_REPO + " (REPO COMMIT, "
                                    "upper bound on receipt)",
            "did_formation_predate_vector": predates,
            "was_location_known_before_decode": loc_known,
            "codec_frozen_before_comparison":
                freeze["frozen_before_comparison"],
            "conditions_met": sum(conds.values()),
            "conditions_required": len(conds),
            "evidence_class": cls,
            "blocking_condition": ("codec_frozen_before_comparison"
                                   if not freeze["frozen_before_comparison"]
                                   else ""),
        })
    return rows


def temporal_report() -> dict:
    led = temporal_ledger()
    return {
        "schema": "rgcs.r1041c.temporal-precedence.v1",
        "ledger": led,
        "codec_freeze": codec_freeze_status(),
        "location_blocker": location_test_blocker(),
        "geographic_null": geographic_null(),
        "all_predate": all(r["did_formation_predate_vector"] for r in led),
        "any_class_b": any(r["evidence_class"]
                           == "TEMPORAL_PRECEDENCE_LOCATION_HOLDOUT"
                           for r in led),
        "verdict": "R10_41C_FORMATION_PREDATES_VECTOR_BUT_"
                   "CODEC_LOCATION_UNRESOLVED",
        "headline": "the ORDERING condition holds for all four "
                    "formations, but class B needs three conditions and "
                    "two of them fail: the codec was changed during this "
                    "analysis, and the projector cannot emit a "
                    "coordinate to score a residual against.",
        "what_makes_the_next_one_count": [
            "freeze and hash the codec NOW, before the next formation",
            "log the number, its exact receipt time and wording BEFORE "
            "decoding",
            "fix the candidate formation list and the distance threshold "
            "in advance",
            "then decode once, and score the residual",
        ],
    }


# --- R10.41E: multi-field hypothesis, and how to keep it falsifiable --

SUBSYSTEM_ROLES = ("R4_ROOT_HEADER", "S8_SURFACE_ZONE", "P12_LOCAL_CELL",
                   "SHELL_RADIAL_STACK", "TAIL_STATE_CHECK",
                   "ROUTE_OPERATOR_BRIDGE", "APERTURE_PHASE_GATE")

#: H_MULTI is MORE flexible than H_BAD: with 7 roles and 4 glyphs an
#: assignment always exists. So each role must carry a PREDICTION that
#: the glyph can fail. These are those predictions.
ROLE_PREDICTIONS = {
    "SHELL_RADIAL_STACK":
        "successive radii ratios should reproduce the constants the "
        "source names (phi, sqrt2) rather than arbitrary simple ratios",
    "TAIL_STATE_CHECK":
        "every visible count must fit a 3-bit field, i.e. lie in 0..7",
    "P12_LOCAL_CELL":
        "P12 is FOUR 3-bit octal steps, so a path diagram should show "
        "four levels",
    "ROUTE_OPERATOR_BRIDGE":
        "a bridge glyph should show exactly two terminals joined by one "
        "connector, with no free-standing third terminal",
}


def multi_field_assessment() -> list:
    """Each glyph against its proposed role's own prediction."""
    return [
        {"glyph": "BISHOPSTONE_20260703_A",
         "role": "SHELL_RADIAL_STACK",
         "prediction": ROLE_PREDICTIONS["SHELL_RADIAL_STACK"],
         "observed": "44/27=1.630 (phi, 0.7% off); 62/44=1.409 "
                     "(sqrt2, 0.4% off); 152/76=2.000",
         "prediction_met": True,
         "null": "phi or sqrt2 within 2% covers 4% of the range; "
                 "P(>=2 of 4 ratios hit) = 0.0094 ~ 1 in 106",
         "why_this_null_is_fair": "phi and sqrt2 are named in the "
                                  "source check formula sqrt(2)/phi "
                                  "BEFORE measurement, so they are "
                                  "pre-specified targets, unlike "
                                  "'nearest of 22 simple ratios'",
         "class": "BEST_SUBSYSTEM_CANDIDATE"},
        {"glyph": "FOXHILL_20260721_A", "role": "TAIL_STATE_CHECK",
         "prediction": ROLE_PREDICTIONS["TAIL_STATE_CHECK"],
         "observed": "dot split 2|3, both within 0..7",
         "prediction_met": True,
         "null": "any small count satisfies 0..7; weak",
         "class": "CONSISTENT_BUT_WEAK"},
        {"glyph": "AVEBURY_20260714_A", "role": "P12_LOCAL_CELL",
         "prediction": ROLE_PREDICTIONS["P12_LOCAL_CELL"],
         "observed": "3 clusters, not 4 path levels",
         "prediction_met": False,
         "null": "n/a - the prediction simply fails",
         "class": "ROLE_PREDICTION_NOT_MET"},
        {"glyph": "BISHOPSTONE_20260703_B",
         "role": "ROUTE_OPERATOR_BRIDGE",
         "prediction": ROLE_PREDICTIONS["ROUTE_OPERATOR_BRIDGE"],
         "observed": "two terminals joined by one bar",
         "prediction_met": True,
         "null": "the glyph is visually a dumbbell; the prediction is "
                 "nearly restating the observation",
         "class": "CONSISTENT_BUT_NEARLY_TAUTOLOGICAL"},
    ]


def multi_field_report() -> dict:
    rows = multi_field_assessment()
    met = [r for r in rows if r["prediction_met"]]
    return {
        "schema": "rgcs.r1041e.multifield.v1",
        "hypothesis_refuted": "H_BAD: one universal grammar reads every "
                              "glyph as a tail6 value",
        "hypothesis_open": "H_MULTI: different glyphs diagram different "
                           "codec subsystems",
        "assessment": rows,
        "predictions_met": len(met), "predictions_total": len(rows),
        "flexibility_warning": "with 7 roles and 4 glyphs an assignment "
                               "ALWAYS exists, so H_MULTI is only "
                               "meaningful where a role makes a "
                               "prediction the glyph could fail",
        "falsifiability_demonstrated": any(not r["prediction_met"]
                                           for r in rows),
        "strongest": "BISHOPSTONE_A as shell/radial stack - phi then "
                     "sqrt2 in successive ratios, the two constants the "
                     "source names, at ~1 in 106",
        "weakest": "AVEBURY as P12 local cell - fails its own prediction "
                   "(3 clusters vs 4 octal path steps)",
        "verdict": "R10_41E_UNIVERSAL_TAIL_GRAMMAR_REFUTED_"
                   "MULTI_FIELD_GLYPH_CODEC_HYPOTHESIS_OPEN",
    }
