"""P06 — a graph whose edges are coupling certificates, searched not asserted.

R12 replaced a blanket cross-domain refusal with a *certificate*: a
licence to model one directed transfer between two physical domains,
carrying nine declarations and, crucially, a falsifying measurement that
has not been performed. Every R12 certificate is therefore
``AWAITING_FALSIFICATION`` and its claim class is ``ENGINEERING_CANDIDATE``,
never a bench result.

This module is the machinery for *searching* over such certificates
without ever letting the search invent an equivalence.

**The graph.** :class:`CouplingGraph` is a directed graph whose **edges
are certificates**. There is no edge between two domains unless a
*complete* certificate licenses that directed pair; an uncertified pair
is simply not an edge, so :meth:`CouplingGraph.path` can only ever route
through declarations someone actually made. A missing edge yields
``None``, not a guess.

**Hypotheses, not couplings.** :func:`search_candidate_bridges`
enumerates the domain pairs that *could* bridge a source to a target --
the direct pair and every one-intermediate pair. It returns each as a
:class:`CandidateBridge` with ``status == "REQUIRES_CERTIFICATE"``. A
candidate is a thing to go and certify, never an established coupling.

**Composition is not free.** A chain of ``N`` certificates, each an
``ENGINEERING_CANDIDATE`` awaiting its own falsification, composes to an
end-to-end path that is at best ``ENGINEERING_CANDIDATE`` and whose
confidence is the **weakest link**. :func:`path_claim_class` returns
``ENGINEERING_CANDIDATE`` and never a measurement class, however strong
the individual links claim to be. A composite A->C has its own overlap,
detuning, phase matching and energy budget, so the certificates do **not**
automatically compose: :func:`refuse_automatic_composition` refuses that
move, consistent with :func:`r12.bridge.refuse_chained_transfer`, and
:func:`refuse_path_as_measured` refuses treating a routed path as a
measurement.

Nothing here is measured. No coupling is asserted to exist; the graph
only records which licences to model have been written down.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from r12.bridge import (
    REQUIRED_DECLARATIONS,
    BridgeError,
    CertificateStatus,
    CouplingCertificate,
    Domain,
    refuse_chained_transfer,
)

# --- verdict and claim vocabulary ----------------------------------------

#: The standing verdict for this module.
VERDICT = "COUPLING_GRAPH_SEARCH_CERTIFICATE_GATED"

#: The claim class of a certificate awaiting its falsifying measurement,
#: and of any path composed from such certificates.
ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"

#: Sentinels for a broken chain: a link that is incomplete, or a term with
#: no input at all. Verbatim from the R13 claim ladder.
UNSUPPORTED = "UNSUPPORTED"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

#: The measurement classes. A composed path never reaches these; the
#: names are held so the refusal can be stated in the ladder's own terms.
MEASUREMENT_CLASSES: frozenset[str] = frozenset(
    {"BENCH_MEASUREMENT", "INDEPENDENTLY_REPLICATED"})

#: The status every enumerated candidate carries: it must be certified
#: before it is anything more than a pair of domain names.
REQUIRES_CERTIFICATE = "REQUIRES_CERTIFICATE"

#: The status a multi-hop path carries: it is a routed chain, not a
#: licensed transfer, until its own end-to-end certificate exists.
REQUIRES_END_TO_END_CERTIFICATE = "REQUIRES_END_TO_END_CERTIFICATE"


class BridgeGraphError(RuntimeError):
    """Raised when a graph or path claim exceeds what the certificates license.

    Covers the structural guards (an incomplete certificate offered as an
    edge, a same-domain path, an empty path), and the two composition
    refusals (:func:`refuse_automatic_composition`,
    :func:`refuse_path_as_measured`).
    """


# --- (1) candidate bridges: hypotheses that require a certificate ----------

@dataclass(frozen=True)
class CandidateBridge:
    """One hypothesised bridge from a source domain to a target domain.

    It is a *pair to certify*, not a coupling: ``hops`` records the domain
    sequence the hypothesis would route through, and ``status`` is fixed
    at ``REQUIRES_CERTIFICATE``. Building one asserts nothing about the
    physics; it only names a transfer that a certificate could license.
    """

    source: Domain
    target: Domain
    hops: tuple[Domain, ...]
    status: str = REQUIRES_CERTIFICATE

    def __post_init__(self) -> None:
        if self.source is self.target:
            raise BridgeGraphError(
                "a candidate bridge connects two DIFFERENT domains")
        if len(self.hops) < 2:
            raise BridgeGraphError(
                "a candidate bridge needs at least a source and a target")
        if self.hops[0] is not self.source or self.hops[-1] is not self.target:
            raise BridgeGraphError(
                "the hop sequence must start at the source and end at the "
                "target")
        if self.status != REQUIRES_CERTIFICATE:
            raise BridgeGraphError(
                "a candidate bridge is a hypothesis; its status is "
                "REQUIRES_CERTIFICATE and it is never an established "
                "coupling")

    @property
    def n_intermediate(self) -> int:
        return max(0, len(self.hops) - 2)

    def as_dict(self) -> dict:
        return {
            "source": self.source.value,
            "target": self.target.value,
            "hops": [d.value for d in self.hops],
            "n_intermediate": self.n_intermediate,
            "status": self.status,
            "note": ("a hypothesis: this pairing MAY be certifiable, but a "
                     "certificate declaring the operator, overlap, "
                     "detuning, phase matching, energy path and a "
                     "falsifying measurement must be written before it is "
                     "anything more than two domain names"),
        }


def search_candidate_bridges(
        source: Domain, target: Domain,
        domains: "tuple[Domain, ...] | None" = None) -> tuple[CandidateBridge, ...]:
    """Enumerate the pairings that *could* bridge ``source`` to ``target``.

    Returns the direct hypothesis and every one-intermediate hypothesis
    over ``domains`` (default: all of :class:`r12.bridge.Domain`). Each is
    a :class:`CandidateBridge` with ``status == "REQUIRES_CERTIFICATE"``.
    The function proposes where a certificate might be written; it never
    reports a coupling as established, and it consults no registry to
    decide what to enumerate.
    """
    if source is target:
        raise BridgeGraphError(
            "a search enumerates bridges between two DIFFERENT domains")
    pool = tuple(Domain) if domains is None else tuple(domains)
    if source not in pool or target not in pool:
        raise BridgeGraphError("source and target must be in the domain pool")
    out: list[CandidateBridge] = [
        CandidateBridge(source, target, (source, target))]
    for mid in pool:
        if mid is source or mid is target:
            continue
        out.append(CandidateBridge(source, target, (source, mid, target)))
    return tuple(out)


# --- (2) the claim class of a composed path -------------------------------

def path_claim_class(certs: "tuple[CouplingCertificate, ...]"
                     "| list[CouplingCertificate]") -> str:
    """The claim class of a chain of certificates: the weakest link, capped.

    A path is only as strong as its weakest certificate, and a *composed*
    path is weaker still than any single licensed edge, because the
    composition has an overlap, detuning, phase matching and energy budget
    of its own that no member certificate declared. So the result is
    ``ENGINEERING_CANDIDATE`` for any chain of complete certificates --
    and **never** a measurement class, however strong a link claims to be.
    A broken link (an incomplete or input-less certificate) dominates and
    is reported as such rather than hidden inside a rosy composite.
    """
    chain = tuple(certs)
    if not chain:
        raise BridgeGraphError("an empty path has no claim class")
    classes = [c.claim_class for c in chain]
    for broken in (BLOCKED_MISSING_INPUT, UNSUPPORTED):
        if broken in classes:
            return broken
    # Every intact link is at best ENGINEERING_CANDIDATE for the *chain*:
    # a member that is itself a bench result does not make the composite
    # one, because the composite transfer was never measured.
    result = ENGINEERING_CANDIDATE
    assert result not in MEASUREMENT_CLASSES
    return result


# --- (3) a routed path ----------------------------------------------------

@dataclass(frozen=True)
class Path:
    """A chain of certificated edges connecting two domains.

    ``certificates`` is the ordered list of edges; ``domains`` is the
    sequence of domains it visits. A path of more than one edge is a
    *composite* and carries ``REQUIRES_END_TO_END_CERTIFICATE``: the
    individual edges are licensed, the end-to-end transfer is not.
    """

    certificates: tuple[CouplingCertificate, ...]

    def __post_init__(self) -> None:
        if not self.certificates:
            raise BridgeGraphError("a path has at least one edge")
        for a, b in zip(self.certificates, self.certificates[1:]):
            if a.target is not b.source:
                raise BridgeGraphError(
                    "path edges must join head to tail: "
                    f"{a.target.value!r} != {b.source.value!r}")

    @property
    def domains(self) -> tuple[Domain, ...]:
        return ((self.certificates[0].source,)
                + tuple(c.target for c in self.certificates))

    @property
    def source(self) -> Domain:
        return self.certificates[0].source

    @property
    def target(self) -> Domain:
        return self.certificates[-1].target

    @property
    def n_edges(self) -> int:
        return len(self.certificates)

    @property
    def is_composite(self) -> bool:
        return self.n_edges > 1

    @property
    def needs_end_to_end_certificate(self) -> bool:
        """A multi-edge path needs its own certificate; a single edge is one."""
        return self.is_composite

    @property
    def claim_class(self) -> str:
        return path_claim_class(self.certificates)

    @property
    def status(self) -> str:
        return (REQUIRES_END_TO_END_CERTIFICATE if self.is_composite
                else self.certificates[0].status.value)

    def as_dict(self) -> dict:
        return {
            "domains": [d.value for d in self.domains],
            "certificate_ids": [c.certificate_id for c in self.certificates],
            "n_edges": self.n_edges,
            "is_composite": self.is_composite,
            "needs_end_to_end_certificate": self.needs_end_to_end_certificate,
            "claim_class": self.claim_class,
            "status": self.status,
            "measured_here": "nothing",
            "note": ("each edge is a licensed model of one transfer, "
                     "awaiting its own falsifying measurement; a multi-edge "
                     "path is a routed chain, not a licensed A..C transfer, "
                     "until its own end-to-end certificate is written"),
        }


# --- (4) the graph --------------------------------------------------------

@dataclass
class CouplingGraph:
    """A directed graph whose edges are coupling certificates.

    An edge exists from ``source`` to ``target`` only when a **complete**
    certificate licenses that directed pair. :meth:`path` routes over
    those edges alone, so a route can never pass through a pairing nobody
    certified.
    """

    _edges: dict[tuple[Domain, Domain], CouplingCertificate] = field(
        default_factory=dict)

    # -- construction ----------------------------------------------------
    def add_edge(self, certificate: CouplingCertificate) -> str:
        """Add a certificate as a directed edge. Incomplete is not an edge.

        A certificate missing any of the nine declarations is not a weak
        edge, it is not an edge: it is refused rather than added, so the
        graph contains only pairings that were fully declared. Returns the
        certificate digest.
        """
        if not isinstance(certificate, CouplingCertificate):
            raise BridgeGraphError("an edge is a CouplingCertificate")
        missing = certificate.missing_declarations()
        if missing:
            raise BridgeGraphError(
                f"refused: certificate {certificate.certificate_id!r} is "
                f"missing {list(missing)} and cannot be an edge. An "
                f"uncertified pairing is not an edge, and an incomplete "
                f"certificate is not a certificate.")
        self._edges[(certificate.source, certificate.target)] = certificate
        return certificate.digest

    def has_edge(self, source: Domain, target: Domain) -> bool:
        return (source, target) in self._edges

    def edge(self, source: Domain,
             target: Domain) -> "CouplingCertificate | None":
        return self._edges.get((source, target))

    def neighbours(self, source: Domain
                   ) -> tuple[tuple[Domain, CouplingCertificate], ...]:
        """The (target, certificate) pairs reachable from ``source`` in one hop."""
        return tuple((t, cert) for (s, t), cert in self._edges.items()
                     if s is source)

    @property
    def n_edges(self) -> int:
        return len(self._edges)

    @property
    def domains(self) -> tuple[Domain, ...]:
        seen: list[Domain] = []
        for s, t in self._edges:
            for d in (s, t):
                if d not in seen:
                    seen.append(d)
        return tuple(seen)

    # -- routing ---------------------------------------------------------
    def path(self, source: Domain, target: Domain) -> "Path | None":
        """A chain of certificated edges from ``source`` to ``target``, or None.

        Breadth-first over the certificate edges, so the route returned is
        one with the fewest edges. There is no route unless every step is
        a complete certificate; a missing edge anywhere on the way yields
        ``None``. A returned :class:`Path` flags whether it still needs an
        end-to-end certificate.
        """
        if source is target:
            raise BridgeGraphError(
                "source and target are the same domain; a same-domain "
                "transfer needs no bridge and no certificate")
        prev: dict[Domain, "tuple[Domain, CouplingCertificate] | None"] = {
            source: None}
        queue: deque[Domain] = deque([source])
        while queue:
            current = queue.popleft()
            if current is target:
                break
            for nxt, cert in self.neighbours(current):
                if nxt not in prev:
                    prev[nxt] = (current, cert)
                    queue.append(nxt)
        if target not in prev:
            return None
        chain: list[CouplingCertificate] = []
        node = target
        while prev[node] is not None:
            back, cert = prev[node]        # type: ignore[misc]
            chain.append(cert)
            node = back
        chain.reverse()
        return Path(tuple(chain))

    def reachable(self, source: Domain, target: Domain) -> bool:
        return self.path(source, target) is not None


# --- (5) the refusals -----------------------------------------------------

def refuse_path_as_measured(path: "Path | None" = None,
                            claim: str = "the path is a measurement") -> None:
    """Refuse a routed path being read as a measurement. Always raises.

    A path is a chain of licences to model. Every edge is an
    ``ENGINEERING_CANDIDATE`` whose falsifying measurement has not been
    performed, so their composition is not a bench result and cannot
    become one by being routed. Promoting a path to a measurement is the
    simulation-to-measurement move under another name.
    """
    where = ""
    if isinstance(path, Path):
        where = (f" The path {[d.value for d in path.domains]} composes "
                 f"{path.n_edges} certificate(s), each AWAITING_"
                 f"FALSIFICATION.")
    raise BridgeGraphError(
        f"refused: {claim!r}. A path over coupling certificates is a chain "
        f"of licences to MODEL cross-domain transfers, not a record of "
        f"measuring them.{where} Each edge is an {ENGINEERING_CANDIDATE} "
        f"whose falsifying measurement has not been performed, none exists "
        f"in this environment, and a composed path is at best "
        f"{ENGINEERING_CANDIDATE} and NEVER a measurement class. {VERDICT}")


def refuse_automatic_composition(*_certs: CouplingCertificate,
                                 claim: str = "A->B and B->C give A->C") -> None:
    """Refuse the idea that licensed edges compose into a licensed path.

    Always raises, and is consistent with
    :func:`r12.bridge.refuse_chained_transfer`: a licensed A->B and a
    licensed B->C do not license A->C. The composite has its own overlap,
    detuning, phase matching and energy budget, and needs its own
    certificate and its own falsifying measurement. The graph may *route*
    a chain, but routing is not composing.
    """
    try:
        refuse_chained_transfer(*_certs)
    except BridgeError as exc:
        raise BridgeGraphError(
            f"refused: {claim!r}. {exc} A routed path exhibits that a chain "
            f"of edges exists; it does not license the end-to-end transfer, "
            f"which is a new certificate with its own falsifying "
            f"measurement. {VERDICT}") from exc
    # refuse_chained_transfer always raises; reaching here is a contract
    # breach and must not be read as a licensed composition.
    raise BridgeGraphError(
        f"refused: {claim!r}. Certificates do not automatically compose. "
        f"{VERDICT}")


# --- (6) the report -------------------------------------------------------

def bridgegraph_report() -> dict:
    """The standing statement of what this module is and is not."""
    return {
        "what_this_is": (
            "a directed graph whose edges are R12 coupling certificates, "
            "with a certificate-gated path search: an edge exists only "
            "where a complete certificate licenses a directed domain pair, "
            "a path is a chain of such edges, and a candidate bridge is a "
            "hypothesis that still requires a certificate"),
        "rule": [
            "an uncertified pairing is not an edge",
            "an incomplete certificate is not an edge",
            "a candidate bridge is REQUIRES_CERTIFICATE, never a coupling",
            "a composed path is ENGINEERING_CANDIDATE at best, weakest "
            "link, and never a measurement class",
            "certificates do not automatically compose; a composite needs "
            "its own certificate and its own falsifying measurement",
        ],
        "required_declarations": list(REQUIRED_DECLARATIONS),
        "candidate_status": REQUIRES_CERTIFICATE,
        "composite_status": REQUIRES_END_TO_END_CERTIFICATE,
        "awaiting_falsification": CertificateStatus.AWAITING_FALSIFICATION.value,
        "measurement_classes": sorted(MEASUREMENT_CLASSES),
        "refusals": [
            "refuse_path_as_measured",
            "refuse_automatic_composition",
        ],
        "consistent_with": "r12.bridge.refuse_chained_transfer",
        "claim_class": ENGINEERING_CANDIDATE,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any cross-domain coupling exists. An edge in "
            "this graph is a licence to model one transfer, written down "
            "and awaiting a falsifying measurement that has not been "
            "performed; a path is a chain of such licences and is an "
            "ENGINEERING_CANDIDATE at best, never a bench result. It does "
            "not say a candidate bridge is real: enumerating a pairing "
            "proposes where a certificate could be written, not that the "
            "coupling has been demonstrated. It does not say certificates "
            "compose: a routed A..C chain still needs its own end-to-end "
            "certificate. No apparatus was operated and nothing was "
            "measured."),
    }
