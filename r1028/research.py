"""R10.28 Agent 06 / R10.29 — the external research lane.

PACK INSTRUCTION, HONOURED LITERALLY: "Do not fill facts from memory.
Require web/primary-source verification later." Web research is not
authorized in this run, so this module emits QUESTIONS and REQUIRED
SOURCE QUALITY. It contains no asserted external facts.

Every claim carried over from the R10.29 deltas is stored with its
verification state, and the states that matter are the negative ones:
an unverified claim is recorded as unverified rather than quietly
promoted.

The music/date/patent cues are kept in a SEPARATE lane from codec maths
on purpose. A song release date is not evidence about a bit field, and
letting the two share a table is how coincidence becomes "structure".
"""

from __future__ import annotations

UNVERIFIED = "REQUIRES_PRIMARY_SOURCE_NOT_VERIFIED_IN_THIS_RUN"

#: Claims carried in from the R10.29 research deltas. `state` records
#: what the pack itself asserted about verification -- NOT what this
#: run confirmed. This run confirmed nothing externally.
RESEARCH_CLAIMS = [
    {"id": "RC01", "lane": "music_cue",
     "claim": "Blue Rodeo / 'Rose-Coloured Glasses' associated with "
              "March 26 1987 metadata",
     "state": UNVERIFIED, "codec_relevance": "NONE_ESTABLISHED"},
    {"id": "RC02", "lane": "music_cue",
     "claim": "The Tragically Hip / 'Grace, Too' associated with "
              "September 24 1994 metadata",
     "state": UNVERIFIED, "codec_relevance": "NONE_ESTABLISHED"},
    {"id": "RC03", "lane": "date_cue",
     "claim": "Apollo 7 flew October 11 1968, not 1969",
     "state": "PACK_ASSERTS_CORRECTION_" + UNVERIFIED,
     "codec_relevance": "NONE_ESTABLISHED",
     "note": "the pack flags this as a correction to an earlier note; "
             "this run does not independently verify it"},
    {"id": "RC04", "lane": "rf",
     "claim": "13.56 MHz NFC/ISM band is a real allocated lane",
     "state": "PACK_ASSERTS_REAL_" + UNVERIFIED,
     "codec_relevance": "CANDIDATE_CARRIER_ONLY"},
    {"id": "RC05", "lane": "rf",
     "claim": "13.1835 MHz Apollo link frequency",
     "state": "PACK_ASSERTS_NOT_VERIFIED",
     "codec_relevance": "NONE_ESTABLISHED"},
    {"id": "RC06", "lane": "metasurface",
     "claim": "94 GHz programmable space-time metasurface work exists",
     "state": "PACK_ASSERTS_REAL_" + UNVERIFIED,
     "codec_relevance": "NONE_ESTABLISHED"},
    {"id": "RC07", "lane": "metasurface",
     "claim": "a 94 GHz -> 13 MHz downshift law",
     "state": "UNRESOLVED_NO_MECHANISM",
     "codec_relevance": "NONE_ESTABLISHED"},
    {"id": "RC08", "lane": "avian",
     "claim": "avian EEG / navigation research lane exists",
     "state": "PACK_ASSERTS_REAL_" + UNVERIFIED,
     "codec_relevance": "NONE_ESTABLISHED"},
    {"id": "RC09", "lane": "avian",
     "claim": "a distance-to-frequency conversion law",
     "state": "UNRESOLVED_NO_LAW",
     "codec_relevance": "NONE_ESTABLISHED"},
]

RESEARCH_QUESTIONS = [
    {"id": "Q01", "lane": "avian",
     "question": "What are measured avian EEG frequency bands during "
                 "sustained flight, in Hz, with species and method?",
     "required_source": "peer-reviewed electrophysiology with stated "
                        "electrode placement and sampling rate",
     "disqualifying": "secondary summaries, popular science, any source "
                      "without a stated measurement method"},
    {"id": "Q02", "lane": "avian",
     "question": "Is there ANY published distance-to-frequency mapping "
                 "in avian navigation, or is the mapping an artifact of "
                 "the source note?",
     "required_source": "primary literature; a null answer is an "
                        "acceptable and useful result",
     "disqualifying": "analogy from another organism"},
    {"id": "Q03", "lane": "epoch",
     "question": "What exact epoch and tick does the source's 'epoch "
                 "refinement' field reference, and what is its 1-second "
                 "scale relation?",
     "required_source": "the source notes themselves, quoted exactly",
     "disqualifying": "inference from field width alone"},
    {"id": "Q04", "lane": "rf",
     "question": "Is 13.1835 MHz attested in any primary Apollo comms "
                 "document?",
     "required_source": "NASA primary technical documentation",
     "disqualifying": "forum posts, aggregated frequency lists"},
    {"id": "Q05", "lane": "metasurface",
     "question": "In published 94 GHz space-time metasurface work, what "
                 "is the actual modulation frequency, and is any MHz-scale "
                 "control signal involved?",
     "required_source": "peer-reviewed paper with stated modulation rate",
     "disqualifying": "press release"},
]

#: Formula slots, deliberately EMPTY. Naming a slot is not filling it.
FORMULA_SLOTS = [
    {"slot": "EPOCH_TO_FREQUENCY", "form": "UNDEFINED",
     "status": "EMPTY_AWAITING_SOURCE"},
    {"slot": "DISTANCE_TO_FREQUENCY", "form": "UNDEFINED",
     "status": "EMPTY_AWAITING_SOURCE"},
    {"slot": "VECTOR_EPOCH_TO_1_SECOND_SCALE", "form": "UNDEFINED",
     "status": "EMPTY_AWAITING_SOURCE"},
]


def report() -> dict:
    return {
        "schema": "rgcs.r1028.research-lane.v1",
        "claims": RESEARCH_CLAIMS,
        "questions": RESEARCH_QUESTIONS,
        "formula_slots": FORMULA_SLOTS,
        "external_facts_asserted_by_this_run": 0,
        "web_research_performed": False,
        "web_research_authorized": False,
        "music_cues_separated_from_codec_maths": True,
        "verdict": "R10_28_RESEARCH_LANE_PREPARED_NOT_EXECUTED",
        "boundary": "no external fact is asserted from memory; every "
                    "claim carries its verification state and the "
                    "unverified ones stay unverified",
    }
