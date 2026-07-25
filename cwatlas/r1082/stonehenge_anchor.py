"""P17 — Stonehenge training-anchor authority (the second sealed anchor).

The operator reported a single user-supplied training correspondence: the
source route ``165876523`` (tokenised ``01|65|87|65|23``) is said to name
Stonehenge (Locked Decision 11). This module imports and validates that
correspondence as the **second calibration anchor**, under the same privacy
firewall as the source registry (:mod:`cwatlas.r1082.source_import`):

* the reported vector is referenced **only by an opaque fixture id**
  (:data:`STONEHENGE_FIXTURE_ID`, ``STONEHENGE_PRIVATE_001``) — never the raw
  private narrative;
* Stonehenge's **public** coordinate (~51.1789 N, 1.8262 W) is used as a
  *synthetic public anchor value* carrying a **non-zero** positional
  uncertainty. It is a well-known public place, not private data;
* the anchor's evidence class is ``OPERATOR_SELECTION`` (an operator-selected
  input) sourced from a ``SOURCE`` claim (user-reported). It is **never**
  ``MEASURED``: promoting it to a measured fact is refused through
  :func:`cwatlas.r1082.claims.refuse_candidate_as_measured`.

The anchor is bound to the hash-chained provenance ledger
(:mod:`cwatlas.provenance_ledger`): importing it appends an immutable event
binding the sanitised route string, so the training correspondence is
tamper-evident. A training anchor is **never scored as a holdout prediction**
(Acceptance gates).

    SOURCE_ORIGIN_NOT_VALIDATED
    PHYSICAL_VALIDATION_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from cwatlas import geodesy, uncertainty
from cwatlas import provenance_ledger as pl
from cwatlas.r1082 import claims, route_core
from cwatlas.r1082 import source_import

#: The opaque public id for the Stonehenge training anchor (shared with the
#: source registry). Public artifacts reference the anchor by this id only.
STONEHENGE_FIXTURE_ID = source_import.STONEHENGE_FIXTURE_ID

#: The sanitised, public route-shape of the reported source vector ``165876523``
#: (tokenised ``01|65|87|65|23``). This is the same public route shape already
#: planted in :data:`cwatlas.r1082.spatialization.PLANTED_ROUTES`.
SANITIZED_ROUTE_DIGITS = "165876523"
EXPECTED_TOKENS: Tuple[int, ...] = (1, 65, 87, 65, 23)
EXPECTED_WIRE = "01|65|87|65|23"

#: Stonehenge's *public* coordinate, used as a SYNTHETIC public anchor value.
#: A famous public place, not private data. Degrees, WGS84.
STONEHENGE_PUBLIC_LAT_DEG = 51.1789
STONEHENGE_PUBLIC_LON_DEG = -1.8262

#: Declared positional uncertainty of the synthetic public anchor (metres,
#: 1-sigma). NON-ZERO by construction: a training anchor is a region, never an
#: invented exact point. ``k_sigma`` and the cell size are declared constants.
ANCHOR_POSITIONAL_SIGMA_M = 5.0e3
ANCHOR_K_SIGMA = 2.0
ANCHOR_CELL_SIZE_M = 1.0e3

#: A fixed, conventional epoch (decimal year) for the ledger binding. Passed in
#: everywhere; this constant is used only as a deterministic default (never a
#: wall-clock read).
DEFAULT_ANCHOR_EPOCH = 2020.0


class StonehengeAnchorError(ValueError):
    """Raised on a malformed anchor or an illegal promotion."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StonehengeAnchor:
    """The user-reported Stonehenge training anchor, sealed as a correspondence.

    Attributes
    ----------
    fixture_id:
        The opaque public id (:data:`STONEHENGE_FIXTURE_ID`).
    tokens:
        The sanitised five-token base-100 route shape (public).
    route_raw:
        The canonical even-length digit string of the route.
    route_hash:
        Immutable SHA-256 of ``route_raw``.
    public_lat_deg, public_lon_deg:
        The SYNTHETIC public anchor coordinate (a famous public place).
    uncertainty_region:
        A non-zero positional error region about the public coordinate.
    evidence_class:
        ``OPERATOR_SELECTION`` — an operator-selected input, not a measurement.
    source_status:
        ``SOURCE`` — the correspondence is user-reported and unverified.
    use:
        ``TRAINING_ANCHOR`` — never scored as a holdout prediction.
    """

    fixture_id: str
    tokens: Tuple[int, ...]
    route_raw: str
    route_hash: str
    public_lat_deg: float
    public_lon_deg: float
    uncertainty_region: uncertainty.ErrorRegion
    evidence_class: str = claims.EvidenceClass.OPERATOR_SELECTION.value
    source_status: str = claims.EvidenceClass.SOURCE.value
    use: str = source_import.RecordUse.TRAINING_ANCHOR.value

    def __post_init__(self) -> None:
        if self.fixture_id != STONEHENGE_FIXTURE_ID:
            raise StonehengeAnchorError(
                f"fixture_id must be the opaque {STONEHENGE_FIXTURE_ID!r}")
        if tuple(self.tokens) != EXPECTED_TOKENS:
            raise StonehengeAnchorError(
                f"anchor tokens {self.tokens} != expected {EXPECTED_TOKENS}")
        if self.route_hash != _sha256(self.route_raw):
            raise StonehengeAnchorError(
                "route_hash does not match route_raw (the original source "
                "string is immutable)")
        if not (-90.0 <= self.public_lat_deg <= 90.0):
            raise StonehengeAnchorError("public_lat_deg out of range")
        if not (-180.0 <= self.public_lon_deg <= 180.0):
            raise StonehengeAnchorError("public_lon_deg out of range")
        # Uncertainty never collapsed to a point.
        if self.uncertainty_region.area_m2 <= 0.0:
            raise StonehengeAnchorError(
                "the training anchor carries a non-zero positional uncertainty; "
                "a zero-area region asserts invented precision")

    def anchor_unit_vector(self) -> np.ndarray:
        """The public-coordinate direction as an ECEF unit vector (height 0)."""
        x, y, z = geodesy.geodetic_to_ecef(
            self.public_lat_deg, self.public_lon_deg, 0.0)
        v = np.array([x, y, z], dtype=float)
        return v / np.linalg.norm(v)

    def anchor_hash(self) -> str:
        """A stable content hash of the public projection of this anchor."""
        blob = json.dumps(self.public_projection(), sort_keys=True,
                          separators=(",", ":"), default=float)
        return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def public_projection(self) -> dict:
        """A narrative-free public projection (opaque id, route shape, coord).

        No private label or narrative is ever emitted — only the opaque id, the
        sanitised public route shape, the synthetic public coordinate, and the
        non-zero uncertainty footprint.
        """
        return {
            "fixture_id": self.fixture_id,
            "tokens": list(self.tokens),
            "route_wire": EXPECTED_WIRE,
            "route_hash": self.route_hash,
            "public_coordinate_deg": [self.public_lat_deg, self.public_lon_deg],
            "coordinate_status": "SYNTHETIC_PUBLIC_ANCHOR",
            "uncertainty": {
                "representation": self.uncertainty_region.kind.value,
                "area_m2": self.uncertainty_region.area_m2,
                "radius_m": self.uncertainty_region.radius_m,
                "collapsed_to_point": False,
            },
            "evidence_class": self.evidence_class,
            "source_status": self.source_status,
            "use": self.use,
        }

    def refuse_as_measured(self, *_a, **_k) -> None:
        """A user-reported training anchor is never a measured fact."""
        claims.refuse_candidate_as_measured()

    def promote_to(self, evidence_class: claims.EvidenceClass) -> None:
        """Refuse any promotion of the anchor to measurement-grade evidence."""
        if evidence_class in claims.MEASUREMENT_EVIDENCE:
            claims.refuse_candidate_as_measured()
        raise StonehengeAnchorError(
            "the anchor's evidence class is fixed at OPERATOR_SELECTION / "
            "SOURCE; it is not promoted in place")


@dataclass(frozen=True)
class StonehengeImport:
    """The imported anchor bound to a provenance ledger."""

    anchor: StonehengeAnchor
    anchor_record: source_import.AnchorRecord
    ledger_head: str
    ledger_event_id: str


def build_anchor() -> StonehengeAnchor:
    """Build the validated Stonehenge training anchor.

    Verifies the tokenisation ``01|65|87|65|23`` by parsing the sanitised route
    through the locked five-token parser (:mod:`cwatlas.r1082.route_core`), then
    seals the synthetic public coordinate with a non-zero uncertainty region.
    """
    route = route_core.parse_five_token(SANITIZED_ROUTE_DIGITS)
    if route.tokens != EXPECTED_TOKENS:
        raise StonehengeAnchorError(
            f"tokenisation check failed: {route.tokens} != {EXPECTED_TOKENS}")
    region = uncertainty.propagate_circle(
        center=(STONEHENGE_PUBLIC_LAT_DEG, STONEHENGE_PUBLIC_LON_DEG),
        input_sigma_m=ANCHOR_POSITIONAL_SIGMA_M,
        quantization_m=0.0,
        cell_size_m=ANCHOR_CELL_SIZE_M,
        k_sigma=ANCHOR_K_SIGMA,
        justification="synthetic public Stonehenge anchor positional sigma "
                      "(declared; user-reported correspondence)",
    )
    return StonehengeAnchor(
        fixture_id=STONEHENGE_FIXTURE_ID,
        tokens=route.tokens,
        route_raw=route.raw,
        route_hash=_sha256(route.raw),
        public_lat_deg=STONEHENGE_PUBLIC_LAT_DEG,
        public_lon_deg=STONEHENGE_PUBLIC_LON_DEG,
        uncertainty_region=region,
    )


def import_anchor(epoch: float = DEFAULT_ANCHOR_EPOCH,
                  ledger: Optional[pl.Ledger] = None) -> StonehengeImport:
    """Import the anchor and bind it to the hash-chained provenance ledger.

    Registers the anchor by its opaque id in a
    :class:`cwatlas.r1082.source_import.SourceImport` and appends a MESSAGE
    event binding the sanitised route string to the immutable hash chain. The
    private narrative is never touched — only the opaque id and the public route
    shape are recorded.
    """
    anchor = build_anchor()
    imp = source_import.SourceImport(ledger)
    record = imp.register_stonehenge_anchor()
    event = imp.ledger.append(
        kind=pl.EventKind.MESSAGE,
        source_id=anchor.fixture_id,
        epoch=epoch,
        raw=anchor.route_raw,
        operator_note="user-reported training anchor (opaque id only)",
    )
    return StonehengeImport(
        anchor=anchor,
        anchor_record=record,
        ledger_head=imp.ledger.head(),
        ledger_event_id=event.event_id,
    )


def stonehenge_anchor_report() -> dict:
    """P17 declaration receipt. Nothing measured; source origin not validated."""
    anchor = build_anchor()
    return {
        "phase_id": "P17",
        "tranche": "T05",
        "what_this_is": (
            "the user-reported Stonehenge training anchor, imported and "
            "validated as the second calibration correspondence: the sanitised "
            "route 01|65|87|65|23 bound to a SYNTHETIC public coordinate with a "
            "non-zero positional uncertainty, referenced by an opaque id and "
            "bound to the hash-chained provenance ledger."),
        "stonehenge_fixture_id": STONEHENGE_FIXTURE_ID,
        "tokenization": EXPECTED_WIRE,
        "tokens": list(EXPECTED_TOKENS),
        "public_coordinate_deg": [STONEHENGE_PUBLIC_LAT_DEG,
                                  STONEHENGE_PUBLIC_LON_DEG],
        "coordinate_status": "SYNTHETIC_PUBLIC_ANCHOR",
        "positional_sigma_m": ANCHOR_POSITIONAL_SIGMA_M,
        "uncertainty_area_m2": anchor.uncertainty_region.area_m2,
        "uncertainty_collapsed_to_point": False,
        "evidence_class": claims.EvidenceClass.OPERATOR_SELECTION.value,
        "source_status": claims.EvidenceClass.SOURCE.value,
        "never_measured": True,
        "use": source_import.RecordUse.TRAINING_ANCHOR.value,
        "scored_as_holdout": False,
        "bound_to_provenance_ledger": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "STONEHENGE_TRAINING_ANCHOR_IMPORTED_OPAQUE_ID_NEVER_MEASURED",
        "what_this_does_not_say": (
            "The anchor is a user-reported OPERATOR_SELECTION over a SOURCE "
            "claim, sealed against a synthetic public coordinate. It is not a "
            "measured fact, it validates no source origin, and it is a training "
            "anchor — never scored as a holdout prediction."),
    }
