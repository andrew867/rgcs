"""A07 — corpus frequency decoder.

Applies the frozen simplicity metric (A06) to independent frequency
corpora and reports, with correction for the number of tests run,
whether the predeclared coordinate system describes any of them more
simply than range-matched chance.

The bundled corpora are deliberately unflattering:

- ``JUST_INTONATION``: small-integer interval ratios (3/2, 4/3, 5/4…)
  against a rational base. **Positive control** — these are rationally
  simple by definition, so the metric must detect them or it is broken.
- ``EQUAL_TEMPERAMENT``: semitones at 440·2^(n/12). **Irrational by
  construction**, so a rational-ratio metric should NOT find them
  simple. This is the control that stops the metric from merely
  detecting "is a tidy frequency table". (An earlier draft mislabelled
  this a positive control; it is not, and the correction stands.)
- ``ISM_BANDS``: allocated radio bands. Intended as a negative control
  and it is **not** one: 13.56 / 27.12 / 40.68 MHz are harmonically
  related round numbers chosen by regulators, so they score strongly
  simple. That is a true detection of *human convention*, not nature.
- ``QUARTZ_CLOCK``: 32.768 kHz family. Binary by manufacture, so
  simplicity reflects industry convention.
- ``CSPC_CANDIDATES``: the programme's own register, constructed from
  powers of two and eight relative to 2.45 GHz and 4096 — circular by
  construction, and flagged as such.

**Standing interpretation of the panel (NUMERICAL_SIMULATION).** Every
corpus that survives correction is either constructed from the
reference it is scored against, or is a table of human-chosen round
numbers. The metric measures number-choosing convention. No result
here is evidence that any physical system prefers any frequency, and
the programme's own candidate set is simple for the least interesting
possible reason: it was built that way.

A corpus scoring 'simple' against a reference it was BUILT from is
circular by construction. ``circularity_warning`` marks exactly that.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .nulls import (corpus_score, family_report, metric_fingerprint,
                    permutation_test, simplicity)
from .units import exact

#: Just-intonation intervals on a 240 Hz base: small integer ratios.
#: POSITIVE CONTROL — the metric must find these simple.
JUST_RATIOS = ((1, 1), (16, 15), (9, 8), (6, 5), (5, 4), (4, 3),
               (45, 32), (3, 2), (8, 5), (5, 3), (16, 9), (15, 8),
               (2, 1))
JUST_INTONATION = tuple(Fraction(240 * p, q) for p, q in JUST_RATIOS)

#: Equal-tempered semitones from A440. IRRATIONAL by construction
#: (440*2^(n/12)); a rational-ratio metric should NOT rank these
#: simple. Rounded to a fixed grid for exact representation.
EQUAL_TEMPERAMENT = tuple(
    Fraction(round(440 * (2 ** (n / 12)) * 10 ** 6), 10 ** 6)
    for n in range(-12, 13))

#: Allocated ISM centre frequencies, Hz (negative control).
ISM_BANDS = (Fraction(6780000), Fraction(13560000), Fraction(27120000),
             Fraction(40680000), Fraction(433920000),
             Fraction(915000000), Fraction(2450000000),
             Fraction(5800000000), Fraction(24125000000))

#: Common quartz tuning-fork / clock crystals, Hz.
QUARTZ_CLOCK = (Fraction(32768), Fraction(65536), Fraction(76800),
                Fraction(1843200), Fraction(3579545),
                Fraction(4194304), Fraction(8388608),
                Fraction(11059200), Fraction(16777216))


def cspc_candidates() -> tuple:
    """The programme's own registered candidates, in Hz."""
    from .exact import registry
    out = []
    for cid, c in registry().items():
        if c.unit == "Hz":
            out.append(c.exact_hz)
    return tuple(sorted(out))


CORPORA = {
    "JUST_INTONATION": JUST_INTONATION,
    "EQUAL_TEMPERAMENT": EQUAL_TEMPERAMENT,
    "ISM_BANDS": ISM_BANDS,
    "QUARTZ_CLOCK": QUARTZ_CLOCK,
}


@dataclass(frozen=True)
class CorpusResult:
    corpus: str
    reference: str
    n: int
    result: object                  # NullResult
    circularity_warning: str | None

    def to_dict(self) -> dict:
        d = {"corpus": self.corpus, "reference": self.reference,
             "n": self.n}
        d.update(self.result.to_dict())
        d["circularity_warning"] = self.circularity_warning
        return d


#: References a corpus is considered CONSTRUCTED from — scoring simple
#: against these is circular, not discovery.
CONSTRUCTED_FROM = {
    "JUST_INTONATION": {"240"},
    "EQUAL_TEMPERAMENT": {"440"},
    "QUARTZ_CLOCK": {"32768", "2"},
    "CSPC_CANDIDATES": {"2450000000", "4096", "8", "2"},
}


def analyse(corpus_name: str, frequencies, reference_hz,
            reference_name: str, n_null: int = 400,
            seed: int = 20260718) -> CorpusResult:
    res = permutation_test(frequencies, reference_hz, n_null, seed)
    warn = None
    built = CONSTRUCTED_FROM.get(corpus_name, set())
    if str(exact(reference_hz)) in built:
        warn = (f"CIRCULAR: {corpus_name} is constructed from "
                f"{reference_name}; a low score here reflects how the "
                f"corpus was built, not a discovery about nature.")
    return CorpusResult(corpus_name, reference_name,
                        len(tuple(frequencies)), res, warn)


def run_panel(n_null: int = 400, seed: int = 20260718) -> dict:
    """Run every corpus against every declared reference, then correct
    for the size of the family.

    This is the preregistered analysis: references and corpora are
    fixed in code before execution, and the correction accounts for
    every test in the panel.
    """
    from .coordinates import REFERENCES
    corpora = dict(CORPORA)
    corpora["CSPC_CANDIDATES"] = cspc_candidates()

    results, pvals = [], {}
    for cname, freqs in corpora.items():
        for rname, rhz in REFERENCES.items():
            if rhz <= 0:
                continue
            r = analyse(cname, freqs, rhz, rname, n_null, seed)
            results.append(r)
            pvals[f"{cname}@{rname}"] = r.result.p_value
    fam = family_report(pvals)
    return {
        "metric_fingerprint": metric_fingerprint(),
        "n_tests": len(pvals),
        "results": [r.to_dict() for r in results],
        "family": fam,
        "evidence_class": "NUMERICAL_SIMULATION",
        "claim_boundary":
            "Simplicity under a frozen arithmetic metric. Nothing here "
            "is evidence that any specimen responds to any frequency. "
            "Corpora marked CIRCULAR were built from the reference "
            "they score well against.",
    }
