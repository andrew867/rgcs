"""P13 - open protocol, conformance suite and standardization governance.

R6 publishes an experimental protocol. It does not publish a standard,
and it is not able to, because the difference between the two is not a
difference of quality (core/15):

    Authority follows adoption, interoperability, and governance.
    It is not asserted by authorship.

One implementation exists. One author wrote it. No independent body
governs it. No third party has implemented it, reviewed it, or adopted
it. Those are facts about the world, not about the code, and no amount
of further work *inside this repository* can change any of them. That is
why :func:`current_maturity` cannot exceed ``DRAFT_PROTOCOL`` here, why
:func:`advance` gates every rung on a named party who is not the author,
and why :func:`governance_status` reads like a list of things that are
absent. It is a list of things that are absent.

What the repository can honestly supply is the machinery a second
implementor would need: a versioned schema, a documented change process,
a deprecation policy, and :data:`TEST_VECTORS` - deterministic
input/output pairs for the R6 record types, with expected values written
as literals so that a regression in the underlying functions fails the
suite instead of quietly redefining what conformance means.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from . import (FORBIDDEN_COLLAPSES, PROGRAMME_ID, PROTOCOL_MATURITY,
               SCHEMA_VERSION)
from . import mailbox as _mailbox
from . import witness as _witness

#: The single author of this implementation. Every independence check
#: below is a comparison against this identity.
AUTHOR_ID = "RGCS_R6_AUTHOR"

#: The highest rung this repository could reach even with every
#: in-repository box ticked. Rungs above it require parties that do not
#: exist, so they are unreachable by construction rather than by
#: modesty.
MAX_SUPPORTABLE_MATURITY = "DRAFT_PROTOCOL"


class ProtocolRefused(RuntimeError):
    """Raised when protocol authority is claimed rather than earned."""


# --------------------------------------------------------------------
# Version
# --------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolVersion:
    """A protocol version and where it sits on the maturity ladder."""

    major: int
    minor: int
    patch: int
    maturity: str
    schema_version: str = SCHEMA_VERSION
    programme_id: str = PROGRAMME_ID

    def __post_init__(self) -> None:
        if self.maturity not in PROTOCOL_MATURITY:
            raise ValueError(
                f"maturity {self.maturity!r} is not on the ladder "
                f"{PROTOCOL_MATURITY}")
        for name in ("major", "minor", "patch"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")

    @property
    def rung(self) -> int:
        return PROTOCOL_MATURITY.index(self.maturity)

    def __str__(self) -> str:
        return (f"{self.programme_id} v{self.major}.{self.minor}."
                f"{self.patch} [{self.maturity}]")

    @classmethod
    def for_this_repository(cls) -> "ProtocolVersion":
        return cls(major=0, minor=1, patch=0, maturity=current_maturity())

    def as_record(self) -> dict:
        d = asdict(self)
        d["rung"] = self.rung
        d["display"] = str(self)
        return d


# --------------------------------------------------------------------
# The maturity ladder and its gates
# --------------------------------------------------------------------

def _present(key: str, description: str):
    """Requirement satisfied by a truthy in-repository artefact."""
    def check(ev: dict) -> tuple[bool, str]:
        if ev.get(key):
            return True, f"{key}: present"
        return False, f"{key} absent - {description}"
    check.__name__ = f"present_{key}"
    return check


def _independent_party(key: str, description: str):
    """Requirement satisfied only by a named party who is not the author.

    This is the load-bearing check. A requirement that the author can
    satisfy alone is not a requirement; it is a restatement of the
    author's intention.
    """
    def check(ev: dict) -> tuple[bool, str]:
        who = ev.get(key)
        if not who or not isinstance(who, str) or not who.strip():
            return False, f"{key} absent - {description}"
        aliases = {AUTHOR_ID.strip().lower()}
        aliases |= {str(a).strip().lower()
                    for a in ev.get("author_aliases") or ()}
        aliases.add(str(ev.get("author") or AUTHOR_ID).strip().lower())
        if who.strip().lower() in aliases:
            return False, (
                f"{key} names the author ({who!r}); authorship cannot "
                f"satisfy an independence requirement "
                f"(FORBIDDEN_COLLAPSES: PUBLICATION_IS_STANDARDIZATION)")
        return True, f"{key}: {who}"
    check.__name__ = f"independent_{key}"
    return check


def _interop_agreement(ev: dict) -> tuple[bool, str]:
    """Cross-implementation agreement on the test vectors."""
    rep = ev.get("cross_implementation_conformance")
    if not isinstance(rep, dict):
        return False, (
            "cross_implementation_conformance absent - interoperability "
            "means two independent implementations producing identical "
            "outputs for every vector in TEST_VECTORS, not one "
            "implementation agreeing with itself")
    impls = rep.get("implementations") or ()
    if len(set(impls)) < 2:
        return False, (
            f"cross_implementation_conformance names "
            f"{len(set(impls))} implementation(s); at least two "
            f"independent ones are required")
    agreed = rep.get("vectors_agreed")
    total = rep.get("vectors_total")
    if agreed is None or total is None:
        return False, (
            "cross_implementation_conformance does not report "
            "vectors_agreed / vectors_total")
    if total < len(TEST_VECTORS):
        return False, (
            f"only {total} vectors compared; the suite has "
            f"{len(TEST_VECTORS)}")
    if agreed != total:
        return False, (
            f"{total - agreed} of {total} vectors disagree across "
            f"implementations")
    return True, f"{agreed}/{total} vectors agree across {len(set(impls))}"


def _independent_adopters(minimum: int):
    def check(ev: dict) -> tuple[bool, str]:
        adopters = ev.get("independent_adopters") or ()
        aliases = {AUTHOR_ID.strip().lower()}
        aliases.add(str(ev.get("author") or AUTHOR_ID).strip().lower())
        real = [a for a in adopters
                if str(a).strip().lower() not in aliases]
        if len(real) < minimum:
            return False, (
                f"{len(real)} independent adopter(s); {minimum} "
                f"required. Self-adoption is not adoption")
        return True, f"{len(real)} independent adopters"
    check.__name__ = f"adopters_{minimum}"
    return check


#: Requirements to *enter* each rung. EXPERIMENTAL_SCHEMA is the floor
#: and has no entry requirement: it is what you have when you have
#: written something down.
MATURITY_REQUIREMENTS: dict[str, tuple[Callable[[dict],
                                                tuple[bool, str]], ...]] = {
    "DRAFT_PROTOCOL": (
        _present("public_specification",
                 "the specification must be published where a second "
                 "implementor can read it without asking the author"),
        _present("versioned_change_process",
                 "a documented, versioned change process is required; "
                 "see change_process()"),
        _present("issue_and_correction_log",
                 "an open log of issues and corrections is required"),
        _present("test_vectors", "deterministic test vectors"),
        _present("conformance_suite", "a runnable conformance suite"),
        _present("deprecation_policy",
                 "a stated deprecation policy; see deprecation_policy()"),
    ),
    "REFERENCE_IMPLEMENTATION": (
        _present("reference_implementation_public",
                 "the reference implementation source must be public"),
        _present("conformance_suite_passes",
                 "the reference implementation must pass its own suite"),
    ),
    "SECOND_INDEPENDENT_IMPLEMENTATION": (
        _independent_party(
            "second_implementor",
            "a second implementation written by someone who is not the "
            "author, from the specification rather than from this "
            "source"),
        _present("second_implementation_passes_conformance",
                 "the second implementation must pass the suite"),
    ),
    "INTEROPERABILITY_DEMONSTRATED": (
        _interop_agreement,
    ),
    "SECURITY_REVIEWED": (
        _independent_party(
            "security_review_by",
            "a security and privacy review by a party who is not the "
            "author"),
        _present("security_review_findings_published",
                 "the findings, including unresolved ones, must be "
                 "published"),
    ),
    "OPEN_GOVERNANCE": (
        _independent_party(
            "governance_body",
            "a named governance body that is not the author and can "
            "make decisions the author disagrees with"),
        _present("no_single_vendor_lock",
                 "no single-vendor lock (core/15)"),
        _present("patent_and_licensing_review",
                 "a completed patent and licensing review (core/15)"),
    ),
    "CANDIDATE_STANDARD": (
        _independent_adopters(1),
    ),
    "ADOPTED_STANDARD": (
        _independent_adopters(3),
        _present("recognized_standards_body_publication",
                 "publication by a recognized standards body"),
    ),
}

#: Rungs whose requirements CANDIDATE_STANDARD re-checks. "All of the
#: above" is implemented as actually re-running all of the above,
#: because a ladder you can skip rungs on is a list.
_CUMULATIVE_FOR = ("DRAFT_PROTOCOL", "REFERENCE_IMPLEMENTATION",
                   "SECOND_INDEPENDENT_IMPLEMENTATION",
                   "INTEROPERABILITY_DEMONSTRATED", "SECURITY_REVIEWED",
                   "OPEN_GOVERNANCE")


def refuse_authority_by_authorship(*args: Any, **kwargs: Any):
    """Always refuses. Writing a protocol does not make it a standard.

    Called whenever evidence tries to advance maturity on the strength
    of who wrote the document, published it, or declared it normative.
    """
    raise ProtocolRefused(
        "protocol authority may not be claimed by authorship: "
        + FORBIDDEN_COLLAPSES["PUBLICATION_IS_STANDARDIZATION"]
        + ". Advancement requires a second independent implementation, "
          "demonstrated interoperability, independent security review, "
          "a governance body that is not the author, and adoption. "
          "None of these can be produced from inside this repository.")


#: Evidence keys that assert authority rather than demonstrate it.
_AUTHORSHIP_ASSERTIONS = (
    "author_declares_standard",
    "authority_by_authorship",
    "declared_normative_by_author",
    "published_therefore_standard",
    "self_certified",
)


def advance(current: str, evidence: dict) -> dict:
    """Attempt to advance one rung, and report exactly what is missing.

    Returns a report; it raises only when the evidence tries to advance
    by authorship, which is not a missing requirement but a category
    error and so gets a refusal rather than a "false".
    """
    if current not in PROTOCOL_MATURITY:
        raise ValueError(
            f"{current!r} is not on the ladder {PROTOCOL_MATURITY}")
    if not isinstance(evidence, dict):
        raise TypeError("evidence must be a mapping")

    asserted = [k for k in _AUTHORSHIP_ASSERTIONS if evidence.get(k)]
    if asserted:
        refuse_authority_by_authorship(current, asserted)

    idx = PROTOCOL_MATURITY.index(current)
    if idx == len(PROTOCOL_MATURITY) - 1:
        return {
            "from": current, "to": current, "advanced": False,
            "missing": [], "satisfied": [],
            "reason": "already at the top of the ladder",
        }

    target = PROTOCOL_MATURITY[idx + 1]
    checks = list(MATURITY_REQUIREMENTS.get(target, ()))
    if target == "CANDIDATE_STANDARD":
        for rung in _CUMULATIVE_FOR:
            checks = list(MATURITY_REQUIREMENTS[rung]) + checks

    missing: list[str] = []
    satisfied: list[str] = []
    for check in checks:
        ok, why = check(evidence)
        (satisfied if ok else missing).append(why)

    advanced = not missing
    return {
        "from": current,
        "to": target if advanced else current,
        "target": target,
        "advanced": advanced,
        "missing": missing,
        "satisfied": satisfied,
        "reason": (
            f"advanced to {target}" if advanced
            else f"{len(missing)} requirement(s) unmet for {target}"),
    }


def repository_evidence() -> dict:
    """The truthful evidence this repository can supply. Nothing more.

    Read it as an inventory of what is and is not here. The false
    entries are not aspirational placeholders; they are the state of
    the world on the date of writing.
    """
    return {
        "author": AUTHOR_ID,
        # In-repository artefacts that do exist.
        "versioned_change_process": True,
        "issue_and_correction_log": True,
        "test_vectors": True,
        "conformance_suite": True,
        "deprecation_policy": True,
        "reference_implementation_public": False,
        "conformance_suite_passes": True,
        # Everything requiring another party.
        "public_specification": False,
        "second_implementor": None,
        "second_implementation_passes_conformance": False,
        "cross_implementation_conformance": None,
        "security_review_by": None,
        "security_review_findings_published": False,
        "governance_body": None,
        "no_single_vendor_lock": False,
        "patent_and_licensing_review": False,
        "independent_adopters": (),
        "recognized_standards_body_publication": False,
    }


def current_maturity() -> str:
    """The rung this repository actually occupies.

    Derived by climbing from the floor with :func:`repository_evidence`
    and stopping where the evidence stops, then clamped at
    :data:`MAX_SUPPORTABLE_MATURITY`. It is not a constant, so that it
    cannot drift away from the gates that are supposed to justify it.
    """
    ev = repository_evidence()
    level = PROTOCOL_MATURITY[0]
    while True:
        rep = advance(level, ev)
        if not rep["advanced"]:
            break
        level = rep["to"]
    ceiling = PROTOCOL_MATURITY.index(MAX_SUPPORTABLE_MATURITY)
    if PROTOCOL_MATURITY.index(level) > ceiling:
        return MAX_SUPPORTABLE_MATURITY
    return level


# --------------------------------------------------------------------
# Conformance vectors
# --------------------------------------------------------------------

@dataclass(frozen=True)
class TestVector:
    """One deterministic (input, expected_output) conformance pair.

    ``expected`` is a literal. It was produced by running ``probe``
    against this implementation once, and then written down. That is the
    whole point of a conformance vector: if the underlying function
    changes behaviour, the literal no longer matches and the suite
    fails, rather than the "expected" value silently changing with it.
    """

    vector_id: str
    target: str
    description: str
    inputs: dict
    expected: Any
    probe: Callable[[Any], Any] = field(repr=False, compare=False)
    #: Absolute tolerance for float comparisons; ``None`` means exact.
    tolerance: float | None = None

    def evaluate(self, implementation: Any) -> Any:
        return self.probe(implementation)


def _cv_exact_core(impl: Any):
    w = impl.witness
    return w.ExactCore(
        address="R6/CV/0001",
        source_hash="0" * 64,
        permissions=("read",),
        chain_of_custody=("origin",),
        calibration_ids=("CAL-0",),
        transformation_receipts=())


def _cv_payload(impl: Any):
    return impl.witness.ProbabilisticPayload(
        payload_id="R6-CV-PAYLOAD",
        p0=[0.70, 0.20, 0.10],
        prior=[1.0, 1.0, 1.0],
        t0=0.0, tau=100.0, beta=1.0)


def _probe_chain_hash(impl: Any) -> str:
    rec = impl.witness.WitnessRecord(
        record_id="R6-CV-RECORD",
        exact=_cv_exact_core(impl),
        payload=_cv_payload(impl),
        witness=None,
        event_counter=1,
        prev_chain_hash=None)
    return rec.chain_hash()


def _probe_key_path(impl: Any) -> list:
    kp = impl.mailbox.KeyPath((1, 2, 4095))
    packed = kp.as_int()
    restored = impl.mailbox.KeyPath.from_int(packed, 3)
    return [packed, list(restored.keys)]


def _probe_barycentric(impl: Any) -> list[str]:
    b = impl.mailbox.Barycentric.from_ints(1, 2, 3, 4)
    return [str(x) for x in b.lam]


def _probe_decayed_posterior(impl: Any) -> list[float]:
    return list(_cv_payload(impl).state(50.0))


def _probe_informative_bits(impl: Any) -> float:
    return _cv_payload(impl).informative_bits(50.0)


TEST_VECTORS: tuple[TestVector, ...] = (
    TestVector(
        vector_id="R6-TV-001",
        target="witness.WitnessRecord.chain_hash",
        description=(
            "SHA-256 chain link over the exact core, payload id, "
            "counter and previous hash, for the first record in a "
            "chain. Fixes both the hash construction and the exact-core "
            "digest it contains."),
        inputs={
            "record_id": "R6-CV-RECORD",
            "address": "R6/CV/0001",
            "source_hash": "0" * 64,
            "permissions": ["read"],
            "chain_of_custody": ["origin"],
            "calibration_ids": ["CAL-0"],
            "payload_id": "R6-CV-PAYLOAD",
            "witness": None,
            "event_counter": 1,
            "prev_chain_hash": None,
        },
        expected=(
            "499b4250694fe50b9a1a6478c20836ea"
            "5896c2754dd6463e83cb72513eb229a0"),
        probe=_probe_chain_hash,
    ),
    TestVector(
        vector_id="R6-TV-002",
        target="mailbox.KeyPath.as_int / from_int",
        description=(
            "A three-level key path packed at twelve bits per level and "
            "unpacked again. Fixes the radix, the bit order and the "
            "round trip."),
        inputs={"keys": [1, 2, 4095], "depth": 3},
        expected=[16789503, [1, 2, 4095]],
        probe=_probe_key_path,
    ),
    TestVector(
        vector_id="R6-TV-003",
        target="mailbox.Barycentric.from_ints",
        description=(
            "Barycentric weights from integer ratios, as exact "
            "fractions. Fixes that the weights are rational and sum to "
            "exactly one rather than to 0.9999999999999999."),
        inputs={"weights": [1, 2, 3, 4]},
        expected=["1/10", "1/5", "3/10", "2/5"],
        probe=_probe_barycentric,
    ),
    TestVector(
        vector_id="R6-TV-004",
        target="witness.ProbabilisticPayload.state",
        description=(
            "Stretched-exponential payload posterior at t = 50 s with "
            "tau = 100 s, beta = 1, relaxing toward a uniform prior. "
            "Fixes the decay law, the normalization of p0 and the "
            "mixing with the prior."),
        inputs={
            "payload_id": "R6-CV-PAYLOAD",
            "p0": [0.70, 0.20, 0.10],
            "prior": [1.0, 1.0, 1.0],
            "t0": 0.0, "tau": 100.0, "beta": 1.0, "t": 50.0,
        },
        expected=[0.555727908561, 0.252462578705, 0.191809512734],
        probe=_probe_decayed_posterior,
        tolerance=1e-12,
    ),
    TestVector(
        vector_id="R6-TV-005",
        target="witness.ProbabilisticPayload.informative_bits",
        description=(
            "Bits the same payload still holds relative to its own "
            "prior at t = 50 s. Fixes the KL convention, in bits, and "
            "in the direction D(p || prior)."),
        inputs={"payload_id": "R6-CV-PAYLOAD", "t": 50.0},
        expected=0.155661733177,
        probe=_probe_informative_bits,
        tolerance=1e-12,
    ),
)


@dataclass(frozen=True)
class _ReferenceImplementation:
    """The bundle of modules a conformance run is executed against."""

    name: str
    witness: Any
    mailbox: Any


def default_implementation() -> _ReferenceImplementation:
    """This repository's implementation, as a conformance target."""
    return _ReferenceImplementation(
        name=f"{PROGRAMME_ID}-reference",
        witness=_witness, mailbox=_mailbox)


def _matches(actual: Any, expected: Any, tolerance: float | None) -> bool:
    if tolerance is None:
        return actual == expected
    if isinstance(expected, (int, float)) and \
            isinstance(actual, (int, float)):
        return abs(float(actual) - float(expected)) <= tolerance
    if isinstance(expected, (list, tuple)) and \
            isinstance(actual, (list, tuple)):
        if len(actual) != len(expected):
            return False
        return all(_matches(a, e, tolerance)
                   for a, e in zip(actual, expected))
    return actual == expected


def run_conformance(implementation: Any = None) -> dict:
    """Run every vector against ``implementation``.

    A vector that raises is a failure, not an error to propagate: an
    implementation that crashes on a vector has failed that vector, and
    the report should say so alongside the ones that merely disagreed.
    """
    impl = implementation if implementation is not None \
        else default_implementation()

    results = []
    for v in TEST_VECTORS:
        try:
            actual = v.evaluate(impl)
            ok = _matches(actual, v.expected, v.tolerance)
            detail = "" if ok else "output does not match the vector"
        except Exception as exc:                      # noqa: BLE001
            actual, ok = None, False
            detail = f"{type(exc).__name__}: {exc}"
        results.append({
            "vector_id": v.vector_id,
            "target": v.target,
            "passed": ok,
            "expected": v.expected,
            "actual": actual,
            "detail": detail,
        })

    passed = sum(1 for r in results if r["passed"])
    return {
        "implementation": getattr(impl, "name", repr(impl)),
        "schema_version": SCHEMA_VERSION,
        "maturity": current_maturity(),
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "ok": passed == len(results),
        "results": results,
        "note": (
            "passing the suite demonstrates conformance to this "
            "implementation's behaviour. It is not interoperability: "
            "interoperability requires two implementations that did not "
            "share an author"),
    }


# --------------------------------------------------------------------
# Governance - the honest inventory
# --------------------------------------------------------------------

def governance_status() -> dict:
    """What governance exists for this protocol. Mostly: none.

    Every field is true of this repository as written. If a reader
    finds a field flattering, it is a bug.
    """
    return {
        "programme_id": PROGRAMME_ID,
        "schema_version": SCHEMA_VERSION,
        "maturity": current_maturity(),
        "maturity_ceiling_for_this_repository": MAX_SUPPORTABLE_MATURITY,

        "implementations": 1,
        "independent_implementations": 0,
        "single_implementation": True,
        "authors": 1,
        "single_author": True,
        "author": AUTHOR_ID,

        "public_specification": False,
        "versioned_change_process": True,
        "issue_and_correction_log": True,
        "test_vectors": len(TEST_VECTORS),
        "conformance_suite": True,

        "independent_governance_body": None,
        "has_independent_governance_body": False,
        "governance_process": "NONE",
        "single_vendor_lock": True,
        "single_vendor_lock_note": (
            "one author, one repository, one implementation: the "
            "protocol is entirely controlled by its author"),

        "adopters": 0,
        "independent_adopters": 0,
        "adoption": "NONE",

        "security_review": "NOT_PERFORMED",
        "privacy_review": "NOT_PERFORMED",
        "patent_review": "NOT_PERFORMED",
        "licensing_review": "NOT_PERFORMED",

        "interoperability_demonstrated": False,
        "cross_implementation_test_vectors_compared": 0,

        "deprecation_policy": "DOCUMENTED",
        "source_community_attribution": "RECORDED_IN_CLAIMS_REGISTRY",

        "summary": (
            "an experimental schema with a conformance suite, written "
            "and implemented by one person, governed by nobody, "
            "implemented independently by nobody, reviewed by nobody "
            "and adopted by nobody. It is publishable as a draft and is "
            "not a standard"),
        "authority_note": FORBIDDEN_COLLAPSES[
            "PUBLICATION_IS_STANDARDIZATION"],
    }


def deprecation_policy() -> str:
    """How a protocol element stops being supported."""
    return (
        "DEPRECATION POLICY\n"
        "\n"
        "1. Nothing is removed without first being deprecated. A "
        "deprecated element continues to work, unchanged, for at least "
        "one full minor version.\n"
        "2. A deprecation is announced in the change log with: the "
        "element, the version that deprecates it, the earliest version "
        "that may remove it, the reason, and the replacement. A "
        "deprecation without a stated replacement or a stated reason is "
        "not accepted.\n"
        "3. Removal requires a major version increment. Wire formats, "
        "hash constructions and test vectors are covered by this rule: "
        "any change that would alter an existing TEST_VECTORS expected "
        "value is a breaking change by definition.\n"
        "4. Test vectors are never edited to match new behaviour. A "
        "changed behaviour gets a new vector at a new version; the old "
        "vector is retired with the version that deprecated it, and the "
        "retirement is recorded.\n"
        "5. Corrections of factually wrong content are exempt from the "
        "notice period, are applied immediately, and are recorded in "
        "the correction log with what was wrong and what it is now.\n"
        "6. Safety and refusal behaviour is never deprecated toward a "
        "weaker position. A refusal may be removed only by evidence "
        "that makes it unnecessary, never by a version bump.\n"
    )


def change_process() -> str:
    """How a change to the protocol is proposed, reviewed and landed."""
    return (
        "CHANGE PROCESS\n"
        "\n"
        "1. PROPOSE. A change is filed in the open issue log with: the "
        "problem, the proposed change, the affected record types, the "
        "compatibility impact, and the test vectors it would add or "
        "break.\n"
        "2. CLASSIFY. Editorial (no behaviour change), additive "
        "(minor version), or breaking (major version). A change that "
        "alters any expected value in TEST_VECTORS is breaking, "
        "regardless of how small it looks.\n"
        "3. REVIEW. Open comment period before the change lands. While "
        "there is one author, review is a public record of the "
        "reasoning rather than an independent check, and this document "
        "says so rather than implying otherwise.\n"
        "4. TEST VECTORS FIRST. An additive or breaking change lands "
        "with its vectors in the same change, computed from the new "
        "implementation and written as literals.\n"
        "5. VERSION AND LOG. The schema version is incremented per the "
        "classification and the change log records what changed, why, "
        "and what a second implementor must do about it.\n"
        "6. GOVERNANCE ESCALATION. If and when an independent "
        "governance body exists, steps 3 and 5 pass to it, and the "
        "author's ability to land a change unilaterally ends. Until "
        "then this process documents a single-maintainer project "
        "honestly; it does not simulate a committee.\n"
    )


def protocol_report() -> dict:
    """Everything this module knows, in one record."""
    return {
        "version": ProtocolVersion.for_this_repository().as_record(),
        "maturity": current_maturity(),
        "ladder": list(PROTOCOL_MATURITY),
        "next_rung_report": advance(current_maturity(),
                                    repository_evidence()),
        "governance": governance_status(),
        "conformance": run_conformance(),
        "deprecation_policy": deprecation_policy(),
        "change_process": change_process(),
    }
