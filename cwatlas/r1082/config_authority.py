"""P02 -- the locked-decision ADR and configuration authority.

The operator selected the ``EARTH_ROOT_D_V1`` root, topology, orientation,
codec, and anchor choices. This module encodes those choices as an
**architecture-decision record in code**: an immutable, versioned, hashed
configuration object. It is the single authority for what the locked profile
*is*, and it refuses any silent mutation of a locked decision.

The discipline (Locked Decisions / System Contract "No result shopping"):

* every locked decision is typed as an :class:`LockedDecision` and carried in
  the frozen :data:`LOCKED_DECISIONS` tuple -- an ADR-in-code, one entry per
  operator selection;
* the authority *loads and validates* the public fixture
  ``fixtures/earth_root_D_v1.json`` against those decisions, so the shipped
  config can never drift from the ADR without a validation failure;
* the whole ADR hashes to a deterministic :meth:`ConfigurationAuthority.freeze_hash`
  -- changing any locked decision changes the hash and therefore mints a new
  profile id;
* attempting to mutate a locked decision is refused through
  :func:`cwatlas.r1082.claims.refuse_post_output_retuning`; there is no setter
  that quietly rotates the grid, flips handedness, swaps topology, or moves the
  tokenization.

Nothing here measures anything or validates the source's origin. The decisions
are ``OPERATOR_SELECTION`` evidence: operator-selected inputs, not measured
facts. Epochs are never read from a wall clock -- this module holds no time.

    SOURCE_ORIGIN_NOT_VALIDATED
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

from cwatlas.r1082 import claims

#: The frozen profile id. Any change to a locked decision mints a NEW id.
PROFILE_ID = "EARTH_ROOT_D_V1"

#: Version of the ADR encoding itself (bumped only with a new profile id).
ADR_VERSION = "R10.8.2-ADR-1"

#: The public config fixture the authority validates against the ADR.
FIXTURE_PATH = Path(__file__).with_name("fixtures") / "earth_root_D_v1.json"


class ConfigAuthorityError(RuntimeError):
    """Raised when the fixture drifts from the ADR or a decision is unknown."""


@dataclass(frozen=True)
class LockedDecision:
    """One operator-selected decision, recorded as an ADR entry.

    ``number`` is the Locked-Decisions contract ordinal; ``key`` is the stable
    machine name; ``value`` is the frozen selection; ``rationale`` states why
    it is locked. ``evidence_class`` is always ``OPERATOR_SELECTION`` -- these
    are selected inputs, never measured facts.
    """

    number: int
    key: str
    title: str
    value: str
    rationale: str
    evidence_class: str = claims.EvidenceClass.OPERATOR_SELECTION.value

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "key": self.key,
            "title": self.title,
            "value": self.value,
            "rationale": self.rationale,
            "evidence_class": self.evidence_class,
        }


#: The ADR-in-code: the fifteen operator-selected locked decisions, verbatim
#: from ``01_CONTRACTS/LOCKED_DECISIONS.md``. This tuple is the authority.
LOCKED_DECISIONS: Tuple[LockedDecision, ...] = (
    LockedDecision(
        1, "origin", "Origin", "EARTH_CENTER_OF_MASS",
        "The root frame origin is the Earth centre of mass."),
    LockedDecision(
        2, "axis", "Body axis", "MEAN_ROTATION_AXIS_SOUTH_UP",
        "The body axis is the mean rotation axis, expressed South-Up."),
    LockedDecision(
        3, "partition", "Partition", "SPHERICAL_ICOSAHEDRON_20_FACES",
        "The sphere is partitioned into 20 spherical icosahedral faces."),
    LockedDecision(
        4, "dual_graph", "Active adjacency graph", "DODECAHEDRAL_20_VERTEX_DUAL",
        "The active adjacency graph is the dodecahedral dual of the icosahedron."),
    LockedDecision(
        5, "root_feature", "Root feature", "ICOSAHEDRAL_FACE_CENTER",
        "The root feature is one icosahedral face centre, equivalently the "
        "matching dodecahedral-dual vertex."),
    LockedDecision(
        6, "fixed_anchor", "Fixed spatial anchor",
        "WILKES_GRAVITY_ANOMALY_CENTROID",
        "The fixed spatial anchor is the Wilkes Land gravity-anomaly centroid, "
        "a versioned centroid-and-uncertainty profile."),
    LockedDecision(
        7, "dynamic_zero", "Dynamic phase-zero direction",
        "SAA_FIELD_MAGNITUDE_MINIMUM",
        "The dynamic phase-zero direction is the South Atlantic Anomaly "
        "field-magnitude minimum, evaluated at the encoded epoch and encoded "
        "body-relative shell radius."),
    LockedDecision(
        8, "orientation_pole", "Orientation", "SOUTH_UP",
        "The orientation is South-Up."),
    LockedDecision(
        9, "positive_rotation", "Positive rotation",
        "CLOCKWISE_FROM_ABOVE_ANTARCTICA",
        "Positive rotation is clockwise when viewed externally from above "
        "Antarctica."),
    LockedDecision(
        10, "opposite_view", "Opposite view",
        "ANTICLOCKWISE_FROM_NORTH_DOWN",
        "The same rotation appears anticlockwise from the North-down viewpoint."),
    LockedDecision(
        11, "second_anchor", "Second geographic calibration anchor",
        "STONEHENGE_PRIVATE_001",
        "The second calibration anchor is the user-reported Stonehenge training "
        "anchor, referenced by an opaque private fixture id (never the raw "
        "vector or narrative in public artifacts)."),
    LockedDecision(
        12, "local_coordinate", "Local coordinate", "BARYCENTRIC",
        "The local coordinate within a face is barycentric."),
    LockedDecision(
        13, "route_core", "Route core", "FIVE_TOKEN_BASE_100",
        "The source route core is a five-token base-100 representation, "
        "for example 01|65|87|65|23."),
    LockedDecision(
        14, "semantic_address", "Semantic address",
        "SEVEN_LOGICAL_FIELDS_PACKED_SHELL_EPOCH",
        "The semantic address has seven logical fields, with shell and epoch "
        "permitted to share a compressed wire field."),
    LockedDecision(
        15, "variable_depth", "Variable depth", "VARIABLE_DEPTH_EXPANDING_CERTIFICATE",
        "Packets may omit unused epoch components while a decoded certificate "
        "expands every available semantic component."),
)

#: Index the decisions by their stable key.
_BY_KEY: Dict[str, LockedDecision] = {d.key: d for d in LOCKED_DECISIONS}

#: The subset of decision keys that map onto the shipped public fixture and
#: therefore must agree with it exactly.
_FIXTURE_CHECKS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("origin", ("origin",)),
    ("axis", ("axis",)),
    ("partition", ("partition",)),
    ("dual_graph", ("dual_graph",)),
    ("root_feature", ("root_feature",)),
    ("fixed_anchor", ("fixed_anchor", "type")),
    ("dynamic_zero", ("dynamic_zero", "type")),
    ("orientation_pole", ("orientation", "pole")),
    ("second_anchor", ("training_anchor",)),
)


def _dig(data: dict, path: Tuple[str, ...]):
    """Follow a key path into a nested mapping, or return a sentinel miss."""
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return _MISS
        cur = cur[key]
    return cur


_MISS = object()


@dataclass(frozen=True)
class ConfigurationAuthority:
    """The immutable, validated authority for ``EARTH_ROOT_D_V1``.

    Build it with :meth:`load`. It carries the frozen ADR decisions and the
    validated public config, and exposes a deterministic :meth:`freeze_hash`.
    It has no setters: :meth:`refuse_change` routes every mutation attempt
    through the governance refusal, so a locked decision can never be changed
    silently -- only a new profile id can express a different configuration.
    """

    profile_id: str
    adr_version: str
    decisions: Tuple[LockedDecision, ...]
    config: Dict = field(default_factory=dict)

    @classmethod
    def load(cls, fixture_path: Optional[Path] = None) -> "ConfigurationAuthority":
        """Load and validate the public config fixture against the ADR."""
        path = Path(fixture_path) if fixture_path is not None else FIXTURE_PATH
        config = json.loads(path.read_text(encoding="utf-8"))
        auth = cls(
            profile_id=PROFILE_ID,
            adr_version=ADR_VERSION,
            decisions=LOCKED_DECISIONS,
            config=config,
        )
        auth.validate()
        return auth

    def decision(self, key: str) -> LockedDecision:
        """Return the locked decision for ``key``, or raise."""
        if key not in _BY_KEY:
            raise ConfigAuthorityError(f"no such locked decision {key!r}")
        return _BY_KEY[key]

    def validate(self) -> None:
        """Verify the loaded config agrees with every ADR fixture check.

        Raises :class:`ConfigAuthorityError` on any drift between the shipped
        public fixture and the encoded ADR -- the fixture can never quietly
        diverge from the locked decisions.
        """
        if self.config.get("profile_id") != PROFILE_ID:
            raise ConfigAuthorityError(
                f"fixture profile_id {self.config.get('profile_id')!r} != "
                f"{PROFILE_ID!r}")
        for key, path in _FIXTURE_CHECKS:
            expected = _BY_KEY[key].value
            actual = _dig(self.config, path)
            if actual is _MISS:
                raise ConfigAuthorityError(
                    f"fixture is missing {'/'.join(path)} required by locked "
                    f"decision {key!r}")
            if actual != expected:
                raise ConfigAuthorityError(
                    f"fixture {'/'.join(path)}={actual!r} contradicts locked "
                    f"decision {key!r}={expected!r}: the locked profile may not "
                    f"be silently altered")

    def canonical(self) -> dict:
        """The canonical ADR mapping used for hashing (deterministic order)."""
        return {
            "profile_id": self.profile_id,
            "adr_version": self.adr_version,
            "decisions": [d.to_dict() for d in self.decisions],
        }

    def freeze_hash(self) -> str:
        """Deterministic SHA-256 of the canonical ADR.

        Independent of wall-clock time and of dict ordering. Changing any
        locked decision changes this hash, which is what mints a new profile
        id under the no-result-shopping rule.
        """
        blob = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def refuse_change(self, decision_key: str) -> None:
        """Refuse any attempt to mutate a locked decision.

        Routes through :func:`cwatlas.r1082.claims.refuse_post_output_retuning`
        so the refusal is the same governance rule the red team indexes. A
        different configuration is only expressible as a new profile id.
        """
        if decision_key not in _BY_KEY:
            raise ConfigAuthorityError(
                f"no such locked decision {decision_key!r}")
        claims.refuse_post_output_retuning(decision_key, frozen=True)

    # The dataclass is ``frozen=True``: any attribute assignment raises
    # ``dataclasses.FrozenInstanceError``. There is deliberately no setter --
    # a different configuration is only expressible as a new profile id.


def config_authority_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    auth = ConfigurationAuthority.load()
    return {
        "module": "cwatlas.r1082.config_authority",
        "phase_id": "P02",
        "profile_id": auth.profile_id,
        "adr_version": auth.adr_version,
        "locked_decision_count": len(auth.decisions),
        "locked_decisions": [d.key for d in auth.decisions],
        "freeze_hash": auth.freeze_hash(),
        "fixture_validated": True,
        "claim": "the locked EARTH_ROOT_D_V1 decisions, encoded as an "
                 "immutable hashed ADR and validated against the public config",
        "claim_class": claims.EvidenceClass.OPERATOR_SELECTION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "LOCKED_DECISION_ADR_HASHED_AND_IMMUTABLE",
        "what_this_does_not_say": (
            "The locked decisions are operator-selected inputs, not measured "
            "facts. Encoding and hashing them validates neither the source's "
            "origin nor any physical effect; it only fixes the configuration "
            "so it cannot be silently retuned."),
    }
