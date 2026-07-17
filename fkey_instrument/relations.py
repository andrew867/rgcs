"""Exact frequency relation engine (Agent A04) and the frequency-key
registry (from the pack's seed data).

All values are `fractions.Fraction`; parsing accepts int, str decimal,
or Fraction. Equality is exact; there is no float tolerance anywhere
in this module. Each relation carries exactly one primary mechanism
class, a mechanism order, and an explanatory note — because the class,
not the arithmetic, controls both language and scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from . import MECHANISM_CLASSES


class RelationError(ValueError):
    pass


def hz(value) -> Fraction:
    """Exact parse: int | Fraction | decimal string. Floats are
    REFUSED — a binary float is already an approximation and would
    poison exact comparison."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        raise RelationError(
            f"float {value!r} refused: pass a decimal string for "
            "exactness (A04)")
    if isinstance(value, str):
        return Fraction(value.strip())
    raise RelationError(f"cannot parse {value!r} as exact hertz")


# --- frequency keys (seed corpus from the pack) -------------------------------

SEED_KEYS = {
    "FKEY-8HZ": ("8", "REGISTERED_CANDIDATE", ("base", "modulation")),
    "FKEY-20_48HZ": ("20.48", "REGISTERED_CANDIDATE",
                     ("modulation", "binary-family")),
    "FKEY-40_96HZ": ("40.96", "REGISTERED_CANDIDATE",
                     ("modulation", "binary-family")),
    "FKEY-587HZ": ("587", "SOURCE_CLAIM", ("sound-key",)),
    "FKEY-644HZ": ("644", "SOURCE_CLAIM", ("sound-key",)),
    "FKEY-787HZ": ("787", "SOURCE_CLAIM", ("body-mapped",)),
    "FKEY-880HZ": ("880", "SOURCE_CLAIM", ("body-mapped",)),
    "FKEY-1496HZ": ("1496", "SOURCE_CLAIM", ("sound-key",)),
    "FKEY-4096HZ": ("4096", "REGISTERED_CANDIDATE",
                    ("crystal-tuner", "clock")),
    "FKEY-20480HZ": ("20480", "REGISTERED_TARGET",
                     ("target", "octave-family")),
    "FKEY-32768HZ": ("32768", "REGISTERED_CANDIDATE",
                     ("crystal-clock",)),
    "FKEY-40960HZ": ("40960", "REGISTERED_TARGET",
                     ("target", "octave-family")),
}


def key_registry() -> dict:
    return {kid: {"id": kid, "hz": hz(v), "status": st,
                  "tags": list(tags),
                  "provenance": "pack seed data "
                                "(frequency_keys_seed.json)"}
            for kid, (v, st, tags) in SEED_KEYS.items()}


# --- relations -----------------------------------------------------------------

# Practical-order thresholds (declared, not tuned): a harmonic above
# PRACTICAL_HARMONIC_MAX is exact arithmetic but has no practical
# spectral amplitude from any realistic waveform.
PRACTICAL_HARMONIC_MAX = 15
PRACTICAL_INTERMOD_MAX = 5


@dataclass(frozen=True)
class Relation:
    inputs: tuple                      # ((coeff, Fraction hz), ...)
    operation: str                     # "scale" | "sum"
    output_hz: Fraction
    target_hz: Fraction
    primary_class: str
    order: int
    note: str
    secondary_tags: tuple = field(default=())

    @property
    def abs_error_hz(self) -> Fraction:
        return abs(self.output_hz - self.target_hz)

    @property
    def rel_error(self) -> Fraction:
        return self.abs_error_hz / self.target_hz

    @property
    def exact(self) -> bool:
        return self.output_hz == self.target_hz


def classify_scale(f_in: Fraction, n, target: Fraction) -> Relation:
    """f_out = n * f_in. Classification per the taxonomy:

    - integer n within practical order, and the drive waveform can
      contain the nth harmonic -> HARMONIC;
    - integer n beyond practical order -> the arithmetic is exact but
      no realizable waveform delivers usable power there: it can only
      matter as timing/phase relationship -> PHASE_CLOSURE_ONLY;
    - non-integer rational n -> PHASE_CLOSURE_ONLY (commensurate
      periods, no harmonic line)."""
    n = Fraction(n) if not isinstance(n, Fraction) else n
    out = f_in * n
    if n.denominator == 1 and 1 <= n <= PRACTICAL_HARMONIC_MAX:
        cls, note = "HARMONIC", (
            f"order-{n} harmonic: a nonsinusoidal drive at "
            f"{f_in} Hz can physically contain this line (an ideal "
            "sine cannot; a 50% square carries odd harmonics at 1/k "
            "amplitude)")
        order = int(n)
    elif n.denominator == 1:
        cls = "PHASE_CLOSURE_ONLY"
        order = int(n)
        note = (f"exact x{n} but order {n} far exceeds any practical "
                f"harmonic content (> {PRACTICAL_HARMONIC_MAX}); the "
                "relation is a timing/phase-closure statement, not a "
                "spectral generation mechanism")
    else:
        cls = "PHASE_CLOSURE_ONLY"
        order = max(n.numerator, n.denominator)
        note = (f"rational ratio {n}: commensurate periods (phase "
                "closure) without a harmonic line")
    return Relation(((n, f_in),), "scale", out, target, cls, order,
                    note)


def classify_sum(terms, target: Fraction) -> Relation:
    """sum(c_i * f_i). A weighted sum of distinct tones is NOT an
    emitted frequency in a linear system: it becomes a spectral line
    only through nonlinear mixing of total order sum(|c_i|). Within
    practical intermod order it is INTERMODULATION (requires a
    declared nonlinearity); beyond it, ARITHMETIC_COINCIDENCE."""
    terms = tuple((Fraction(c), hz(f) if not isinstance(f, Fraction)
                   else f) for c, f in terms)
    out = sum((c * f for c, f in terms), Fraction(0))
    total_order = sum(abs(int(c)) for c, _ in terms)
    if len(terms) == 1:
        return classify_scale(terms[0][1], terms[0][0], target)
    if total_order <= PRACTICAL_INTERMOD_MAX:
        cls = "INTERMODULATION"
        note = (f"order-{total_order} intermodulation product: exists "
                "ONLY if a nonlinearity of at least that order is "
                "physically present and modeled (A06/A08 gate)")
    else:
        cls = "ARITHMETIC_COINCIDENCE"
        note = (f"arithmetic identity of mixing order {total_order}: "
                "no realistic nonlinearity produces a usable "
                "component at this order; the sum is bookkeeping, "
                "not an emitted frequency")
    return Relation(terms, "sum", out, target, cls, total_order, note)


def classify_subharmonic_clock(f_target: Fraction, n: int) -> Relation:
    """f_clock = f_target / n: driving with a clock whose nth harmonic
    lands on the target. The mechanism is the drive waveform's
    harmonic content, so practical-order limits apply to n."""
    if n < 1:
        raise RelationError("n >= 1")
    f_clock = f_target / n
    cls = "SUBHARMONIC_CLOCK" if n <= PRACTICAL_HARMONIC_MAX else \
        "PHASE_CLOSURE_ONLY"
    note = (f"clock at target/{n} = {f_clock} Hz reaches the target "
            f"through its {n}th harmonic"
            if cls == "SUBHARMONIC_CLOCK" else
            f"target/{n} is a timing subdivision only at this order")
    return Relation(((Fraction(1), f_clock),), "scale", f_clock * n,
                    f_target, cls, n, note)


def am_sidebands(carrier: Fraction, envelope: Fraction) -> dict:
    """AM at envelope fm on carrier fc puts sidebands at fc +/- fm
    (first order). Exact."""
    return {"carrier_hz": carrier, "envelope_hz": envelope,
            "lower_hz": carrier - envelope,
            "upper_hz": carrier + envelope,
            "primary_class": "AMPLITUDE_MODULATION_SIDEBAND",
            "note": "first-order AM sidebands; higher-order terms "
                    "require modulation depth accounting (A06)"}


# --- the frozen seed corpus (orchestrator: required cases) ---------------------

def seed_relations() -> list:
    t20480 = hz("20480")
    t20280 = hz("20280")
    rel = [
        classify_scale(hz("4096"), 5, t20480),
        classify_scale(hz("8"), 2560, t20480),
        classify_scale(hz("20.48"), 1000, t20480),
        classify_scale(hz("40.96"), 500, t20480),
        classify_sum([(1, "1496"), (32, "587")], t20280),
        classify_sum([(3, "644"), (4, "787"), (9, "880"),
                      (5, "1496")], t20480),
        classify_scale(hz("8"), 2535, t20280),
    ]
    return rel


def seed_explanation() -> dict:
    """The explanation the orchestrator requires, produced from the
    classifications rather than hand-written around them."""
    rels = seed_relations()
    return {
        "4096*5": {
            "class": rels[0].primary_class,
            "why": "order 5 is a LOW-ORDER PRACTICAL harmonic: a "
                   "square/pulse drive at 4096 Hz physically carries "
                   "a fifth-harmonic line at 1/5 Fourier amplitude",
        },
        "8*2560 | 20.48*1000 | 40.96*500": {
            "classes": [r.primary_class for r in rels[1:4]],
            "why": "exact arithmetic but orders 2560/1000/500 are "
                   "far beyond any waveform's usable harmonic "
                   "content; these are phase/timing closures, not "
                   "generation mechanisms",
        },
        "mixed sums": {
            "classes": [rels[4].primary_class, rels[5].primary_class],
            "why": "weighted sums of distinct tones are NOT "
                   "automatically emitted frequencies: in a linear "
                   "system nothing appears at the sum; only a "
                   "physical nonlinearity of the stated mixing order "
                   "(33 and 21 here — unrealistically high) could "
                   "produce a line there",
        },
    }


def rank(relations: list) -> list:
    """Mechanism-first ranking (A10 gate): class priority, then
    order, then exactness. Arithmetic closeness alone never ranks."""
    class_rank = {"MEASURED_RESONANCE_MATCH": 0, "HARMONIC": 1,
                  "SUBHARMONIC_CLOCK": 1,
                  "AMPLITUDE_MODULATION_SIDEBAND": 2,
                  "FREQUENCY_MODULATION_SIDEBAND": 2,
                  "INTERMODULATION": 3, "PHASE_CLOSURE_ONLY": 4,
                  "ARITHMETIC_COINCIDENCE": 5, "UNKNOWN": 6}
    return sorted(relations,
                  key=lambda r: (class_rank[r.primary_class],
                                 r.order, r.abs_error_hz))


def dedup(relations: list) -> list:
    """Two relations with identical inputs/coefficients/output are
    one relation."""
    seen, out = set(), []
    for r in relations:
        k = (r.inputs, r.operation, r.output_hz, r.target_hz)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def enumerate_harmonics(keys: dict, target: Fraction,
                        max_order: int = 40) -> list:
    """Exact census: which registered keys reach the target by
    integer scaling within max_order."""
    out = []
    for k in keys.values():
        f = k["hz"]
        if f <= 0 or f > target:
            continue
        n = target / f
        if n.denominator == 1 and n <= max_order:
            out.append(classify_scale(f, int(n), target))
        elif n.denominator == 1:
            out.append(classify_scale(f, int(n), target))
    return rank(dedup(out))


def validate_class(cls: str) -> str:
    if cls not in MECHANISM_CLASSES:
        raise RelationError(f"unknown mechanism class {cls}")
    return cls
