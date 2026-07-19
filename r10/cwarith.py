"""P08/P09 — exact CW arithmetic, and the null that decides what it means.

The source material offers a set of five integers and two relations:

    1516 = 1496 + 20
    2160 = 1516 + 644 = 1496 + 20 + 644

Both are **exactly true**. This module verifies them in integer
arithmetic, and then asks the only question that matters: *is being
true surprising?*

The answer depends entirely on the null, and the two plausible nulls
disagree by five orders of magnitude:

**Naive null** -- five integers drawn uniformly from 1..2200. Three
additive relations occur in about 1 in 100,000 draws. p = 1e-5. On
this basis the relations look like a striking discovery.

**Selection-process null** -- sets assembled as the partial-sum
closure of three generators, ``{a, b, c, a+b, a+b+c}``. Three
relations occur in **every single such set**. p = 1.0000.

And the observed set is exactly that:

    sorted(observed)                     == [20, 644, 1496, 1516, 2160]
    sorted({a, b, c, a+b, a+b+c}) for
        a=1496, b=20, c=644              == [20, 644, 1496, 1516, 2160]

They are identical. So the relations are not a property discovered
*in* the set; they are the construction *of* the set restated. A
partial-sum closure contains its partial sums the way a list of even
numbers contains no odd ones.

There is a further overcount. The three relations are not three
independent facts: given ``1516 = 1496 + 20`` and ``2160 = 1516 +
644``, the third follows by substitution. **Two independent facts,
presented as three.**

None of this says the numbers are meaningless or that the source is
mistaken. It says this particular arithmetic carries no evidential
weight about origin, because any three numbers whatsoever, closed
under partial sums, produce it. The correct verdict is
``EXPLAINED_BY_CONSTRUCTION``.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass

#: The five values, as supplied. Public anonymised fixture; attributed
#: only to the omega region, and no step below depends on provenance.
CW_INTEGER_SET = (1516, 1496, 20, 644, 2160)

#: The relations offered in the source material, as (addends, total).
OFFERED_RELATIONS = (
    ((1496, 20), 1516),
    ((1516, 644), 2160),
    ((1496, 20, 644), 2160),
)

#: The alternate branch: substituting 21 for 20 gives 2161, not 2160.
ALTERNATE_BRANCH = {"substitute": 21, "for": 20, "yields": 2161,
                    "target": 2160}

NULL_TRIALS = 200_000
NULL_SEED = 20260719

#: Provenance status a relation may carry. Only PRE_REGISTERED
#: relations may contribute to a verdict.
RELATION_STATUS = (
    "PRE_REGISTERED",
    "POST_HOC",
    "GENERATED_BY_GRAMMAR",
    "IMPLIED_BY_OTHERS",
)


class SemanticDecodeRefused(RuntimeError):
    """Raised when arithmetic is offered as semantic decoding."""


# --- exact verification -------------------------------------------------

def verify(addends, total) -> bool:
    """Exact integer check. No tolerance, no floats."""
    return sum(addends) == total


def verify_all() -> dict:
    return {f"{' + '.join(map(str, a))} = {t}": verify(a, t)
            for a, t in OFFERED_RELATIONS}


def alternate_branch() -> dict:
    """The 21-Hz branch, which does NOT reach the target."""
    b = ALTERNATE_BRANCH
    got = 1496 + b["substitute"] + 644
    return {
        "substitution": f"{b['for']} -> {b['substitute']}",
        "yields": got,
        "target": b["target"],
        "reaches_target": got == b["target"],
        "off_by": got - b["target"],
        "note": (
            "the alternate branch misses by exactly 1, which is what a "
            "one-unit change to an addend must do. It is arithmetic "
            "bookkeeping, not a second independent confirmation."),
    }


# --- independence -------------------------------------------------------

def independent_relation_count() -> dict:
    """How many of the offered relations are independent facts?

    Two. The third is the first substituted into the second.
    """
    return {
        "offered": len(OFFERED_RELATIONS),
        "independent": 2,
        "implied": [
            {"relation": "1496 + 20 + 644 = 2160",
             "status": "IMPLIED_BY_OTHERS",
             "derivation": ("substitute 1516 = 1496 + 20 into "
                            "2160 = 1516 + 644")},
        ],
        "note": (
            "presenting three relations where two are independent "
            "inflates the apparent weight of the evidence by half"),
    }


# --- relation counting and the two nulls -------------------------------

def count_relations(values) -> int:
    """Distinct additive relations among the values (2- and 3-term)."""
    seen = set()
    vals = list(values)
    for r in (2, 3):
        for sub in itertools.combinations(vals, r):
            for tgt in vals:
                if tgt in sub:
                    continue
                if sum(sub) == tgt:
                    seen.add((tuple(sorted(sub)), tgt))
    return len(seen)


def naive_null(trials: int = NULL_TRIALS, seed: int = NULL_SEED) -> dict:
    """Five integers drawn uniformly over the observed magnitude range.

    This is the null that makes the relations look remarkable, and it
    is the wrong one -- it models a process nobody claims occurred.
    """
    rng = random.Random(seed)
    hi = max(CW_INTEGER_SET)
    obs = count_relations(CW_INTEGER_SET)
    at_least = sum(
        1 for _ in range(trials)
        if count_relations([rng.randint(1, hi) for _ in range(5)]) >= obs)
    return {
        "null": "NAIVE_UNIFORM",
        "observed_relations": obs,
        "p_value": (at_least + 1) / (trials + 1),
        "models": "five unrelated integers of similar magnitude",
        "why_wrong": (
            "nobody proposes the values were drawn independently at "
            "random. A null must model the process actually in "
            "question, not a strawman that no one asserts."),
    }


def is_partial_sum_closure(values) -> dict:
    """Is this set exactly {a, b, c, a+b, a+b+c} for some a, b, c?"""
    vals = sorted(values)
    for a, b, c in itertools.permutations(vals, 3):
        if sorted([a, b, c, a + b, a + b + c]) == vals:
            return {"is_closure": True, "generators": (a, b, c)}
    return {"is_closure": False, "generators": None}


def selection_process_null(trials: int = 20_000,
                           seed: int = NULL_SEED + 1) -> dict:
    """Sets assembled the way this one demonstrably was.

    Every such set contains the relations, so observing them carries
    no information about anything.
    """
    rng = random.Random(seed)
    obs = count_relations(CW_INTEGER_SET)
    at_least = 0
    for _ in range(trials):
        a, b, c = (rng.randint(1, 1500) for _ in range(3))
        if count_relations([a, b, c, a + b, a + b + c]) >= obs:
            at_least += 1
    return {
        "null": "SELECTION_PROCESS",
        "observed_relations": obs,
        "p_value": at_least / trials,
        "models": "the partial-sum closure of three generators",
        "why_right": (
            "the observed set IS such a closure, exactly, so this is "
            "the process that produced it"),
    }


def null_hierarchy() -> dict:
    """Both nulls side by side. The gap is the whole lesson."""
    closure = is_partial_sum_closure(CW_INTEGER_SET)
    naive = naive_null()
    selection = selection_process_null()
    return {
        "closure_check": closure,
        "naive_null": naive,
        "selection_process_null": selection,
        "p_value_ratio": selection["p_value"] / naive["p_value"],
        "verdict": ("EXPLAINED_BY_CONSTRUCTION" if closure["is_closure"]
                    else "NOT_EXPLAINED_BY_CONSTRUCTION"),
        "lesson": (
            "the same true arithmetic scores p = 1e-5 against a null "
            "nobody proposes and p = 1.0 against the null that "
            "describes how the set was actually built. Choosing the "
            "null is choosing the answer, which is why it has to be "
            "chosen for reasons that are stated and defensible."),
        "what_this_does_not_say": (
            "It does not say the numbers are meaningless, arbitrary, "
            "or that the source is mistaken. The relations are exactly "
            "true and remain so. It says they carry no evidential "
            "weight about origin, because ANY three integers closed "
            "under partial sums exhibit them. If the generators "
            "themselves have meaning, that meaning has to be "
            "established some other way -- this arithmetic cannot do "
            "it."),
    }


# --- description length -------------------------------------------------

@dataclass(frozen=True)
class MDLScore:
    """Minimum-description-length: does the relation compress the set?"""

    raw_bits: float
    model_bits: float

    @property
    def saved_bits(self) -> float:
        return self.raw_bits - self.model_bits

    @property
    def compresses(self) -> bool:
        return self.saved_bits > 0


def mdl_score(values=CW_INTEGER_SET) -> MDLScore:
    """Bits to write the set literally, versus via its generators.

    A relation that genuinely captures structure should shorten the
    description. Here it does -- which confirms the set is redundant,
    i.e. that two of the five values are derivable. That is the same
    finding as the closure check, arrived at by counting bits, and it
    is evidence about REDUNDANCY, not about origin.
    """
    raw = sum(max(1, v.bit_length()) for v in values)
    closure = is_partial_sum_closure(values)
    if not closure["is_closure"]:
        return MDLScore(raw_bits=float(raw), model_bits=float(raw))
    gens = closure["generators"]
    # three generators, plus a constant-size recipe for the closure
    model = sum(max(1, g.bit_length()) for g in gens) + 8
    return MDLScore(raw_bits=float(raw), model_bits=float(model))


# --- refusals -----------------------------------------------------------

def refuse_semantic_decoding() -> None:
    """Arithmetic identity is not meaning."""
    raise SemanticDecodeRefused(
        "these relations are exactly true and semantically empty. The "
        "five values are the partial-sum closure of three generators, "
        "so the relations restate the construction rather than "
        "revealing content. No semantic decoding is claimed, and none "
        "follows from arithmetic identity.")


def refuse_source_authentication() -> None:
    """Correct arithmetic authenticates nothing about origin."""
    raise SemanticDecodeRefused(
        "correct arithmetic does not authenticate a source. Any three "
        "integers closed under partial sums produce exactly these "
        "relations, so they cannot distinguish one origin from "
        "another -- terrestrial, constructed, coincidental or "
        "otherwise. Origin claims require evidence this arithmetic "
        "does not contain.")
