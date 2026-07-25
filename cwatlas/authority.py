"""P06 — Frame, epoch, and root authority registry.

A registry of *typed, versioned, hashed* certificates naming the authorities a
decode rests on: the body, its root/frame, the epoch, the time scale, the
orientation profile, and the ephemeris. System Contract invariant 2 requires
every decode to record codec id/version/params, frame, epoch, orientation
profile, shell law, and software commit; this registry is where those frame /
epoch / orientation / ephemeris authorities are declared, looked up, and
pinned so a decode can state *exactly which ones it used*.

The registry is deliberately independent of the concrete frame math
(``cwatlas.frames`` / ``earth_frame`` / ``mars_frame``): it names those
authorities by *concept* — a typed id, a version, and a payload — and never
hard-imports them, so it can record which frame/epoch/orientation a decode
used without being able to silently rewrite that math. Frame and epoch
certificate payloads conform to ``cwatlas/schemas/frame_epoch.schema.json``.

Refusals, not guesses (invariant: underdetermined inputs get explicit result
states):

* an unregistered body/root/frame/epoch/orientation/ephemeris is refused
  (``AuthorityError``), never silently defaulted;
* a lookup with no version is refused when more than one version is
  registered — hidden defaults are rejected, legacy versions are preserved
  side by side;
* a tampered certificate fails its hash check on registration and on lookup.

Nothing here measures anything or claims any geographic or physical
semantics.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
    PHYSICAL_VALIDATION_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from cwatlas import claims

#: Path to the frame/epoch certificate schema this registry validates against
#: for FRAME and EPOCH authority payloads.
_SCHEMA_PATH = Path(__file__).with_name("schemas") / "frame_epoch.schema.json"


class AuthorityError(RuntimeError):
    """Raised on an unregistered/ambiguous authority or a tampered certificate."""


class AuthorityType(Enum):
    """The kinds of authority a decode must be able to pin by reference."""

    BODY = "BODY"
    ROOT = "ROOT"
    FRAME = "FRAME"
    EPOCH = "EPOCH"
    TIME_SCALE = "TIME_SCALE"
    ORIENTATION = "ORIENTATION"
    EPHEMERIS = "EPHEMERIS"


#: Authority types whose certificate payload must satisfy the frame/epoch
#: certificate schema.
_SCHEMA_TYPES = frozenset({AuthorityType.FRAME, AuthorityType.EPOCH})


def _frame_epoch_required() -> Tuple[str, ...]:
    """The ``required`` field list from the frame/epoch certificate schema."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return tuple(schema.get("required", ()))


def _canonical(
    authority_type: AuthorityType,
    authority_id: str,
    version: str,
    payload: Dict[str, object],
) -> str:
    """Deterministic canonical JSON over a certificate's identifying material."""
    material = {
        "authority_type": authority_type.value,
        "authority_id": authority_id,
        "version": version,
        "payload": payload,
    }
    return json.dumps(material, sort_keys=True, separators=(",", ":"))


def compute_hash(
    authority_type: AuthorityType,
    authority_id: str,
    version: str,
    payload: Dict[str, object],
) -> str:
    """A stable ``sha256:`` digest over the certificate's identifying fields."""
    blob = _canonical(authority_type, authority_id, version, payload)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthorityCertificate:
    """A typed, versioned, hashed authority reference.

    The ``hash`` is excluded from equality (``compare=False``) so two
    certificates built from the same inputs compare equal; tamper detection
    goes through :meth:`verify`, which recomputes the digest.
    """

    authority_type: AuthorityType
    authority_id: str
    version: str
    payload: Dict[str, object]
    hash: str = field(default="", compare=False)

    def digest(self) -> str:
        """Recompute the digest from the current identifying fields."""
        return compute_hash(
            self.authority_type, self.authority_id, self.version, self.payload)

    def verify(self) -> bool:
        """True iff the stored hash matches the recomputed digest."""
        return bool(self.hash) and self.hash == self.digest()

    def to_dict(self) -> dict:
        return {
            "authority_type": self.authority_type.value,
            "authority_id": self.authority_id,
            "version": self.version,
            "payload": dict(self.payload),
            "hash": self.hash,
        }


def make_certificate(
    authority_type: AuthorityType,
    authority_id: str,
    version: str,
    payload: Optional[Dict[str, object]] = None,
) -> AuthorityCertificate:
    """Build a hashed :class:`AuthorityCertificate`.

    FRAME and EPOCH payloads are validated against the frame/epoch schema's
    required fields; a missing field is refused rather than silently defaulted.
    """
    if not authority_id:
        raise AuthorityError("authority_id must be a non-empty string")
    if not version:
        raise AuthorityError("version must be a non-empty string")
    body = dict(payload or {})
    if authority_type in _SCHEMA_TYPES:
        missing = [k for k in _frame_epoch_required() if k not in body]
        if missing:
            raise AuthorityError(
                f"refused: {authority_type.value} certificate payload is "
                f"missing schema-required fields {missing} "
                f"(schema: frame_epoch.schema.json)")
    digest = compute_hash(authority_type, authority_id, version, body)
    return AuthorityCertificate(authority_type, authority_id, version, body, digest)


@dataclass
class AuthorityRegistry:
    """A register/lookup store of authority certificates.

    Keyed by ``(type, id, version)`` so legacy versions of an authority live
    side by side and are never overwritten. A lookup without a version is
    refused when more than one version exists — no hidden default.
    """

    _certs: Dict[Tuple[AuthorityType, str, str], AuthorityCertificate] = field(
        default_factory=dict)

    def register(self, cert: AuthorityCertificate) -> AuthorityCertificate:
        """Register a certificate after verifying it is untampered."""
        if not cert.verify():
            raise AuthorityError(
                f"refused: certificate for {cert.authority_type.value} "
                f"{cert.authority_id!r} v{cert.version} fails its hash check "
                f"(tampered or unhashed); it will not be registered")
        key = (cert.authority_type, cert.authority_id, cert.version)
        existing = self._certs.get(key)
        if existing is not None and existing.hash != cert.hash:
            raise AuthorityError(
                f"refused: a different certificate is already registered for "
                f"{cert.authority_type.value} {cert.authority_id!r} "
                f"v{cert.version}; register a new version rather than "
                f"overwriting a pinned authority")
        self._certs[key] = cert
        return cert

    def register_new(
        self,
        authority_type: AuthorityType,
        authority_id: str,
        version: str,
        payload: Optional[Dict[str, object]] = None,
    ) -> AuthorityCertificate:
        """Build and register a certificate in one step."""
        return self.register(
            make_certificate(authority_type, authority_id, version, payload))

    def versions(self, authority_type: AuthorityType, authority_id: str) -> List[str]:
        """The registered versions for one authority, sorted."""
        return sorted(
            v for (t, i, v) in self._certs if t is authority_type and i == authority_id)

    def is_registered(
        self,
        authority_type: AuthorityType,
        authority_id: str,
        version: Optional[str] = None,
    ) -> bool:
        if version is not None:
            return (authority_type, authority_id, version) in self._certs
        return bool(self.versions(authority_type, authority_id))

    def lookup(
        self,
        authority_type: AuthorityType,
        authority_id: str,
        version: Optional[str] = None,
    ) -> AuthorityCertificate:
        """Return the pinned certificate, or refuse.

        Refuses an unregistered authority, an unknown version, and an
        ambiguous version-less lookup when several versions exist.
        """
        vs = self.versions(authority_type, authority_id)
        if not vs:
            raise AuthorityError(
                f"refused: no {authority_type.value} authority registered "
                f"under {authority_id!r}; a decode may not proceed on an "
                f"unregistered frame/epoch/orientation")
        if version is None:
            if len(vs) != 1:
                raise AuthorityError(
                    f"refused: {authority_type.value} {authority_id!r} has "
                    f"versions {vs}; specify one — no hidden default")
            version = vs[0]
        cert = self._certs.get((authority_type, authority_id, version))
        if cert is None:
            raise AuthorityError(
                f"refused: {authority_type.value} {authority_id!r} has no "
                f"version {version!r}; registered versions are {vs}")
        if not cert.verify():
            raise AuthorityError(
                f"refused: registered certificate for {authority_type.value} "
                f"{authority_id!r} v{version} fails its hash check (tampered)")
        return cert

    def require_frame_epoch(
        self,
        frame_id: str,
        epoch_id: str,
        frame_version: Optional[str] = None,
        epoch_version: Optional[str] = None,
    ) -> Tuple[AuthorityCertificate, AuthorityCertificate]:
        """Look up the frame and epoch a decode intends to use, or refuse."""
        return (
            self.lookup(AuthorityType.FRAME, frame_id, frame_version),
            self.lookup(AuthorityType.EPOCH, epoch_id, epoch_version),
        )

    def certificates(self) -> List[AuthorityCertificate]:
        """All registered certificates, in a deterministic order."""
        return [
            self._certs[k]
            for k in sorted(self._certs, key=lambda t: (t[0].value, t[1], t[2]))
        ]


def default_registry() -> AuthorityRegistry:
    """A registry preloaded with a small *synthetic* authority set.

    These are declared references, not measurements: a synthetic Earth/Mars
    body, a root, a schema-valid frame and epoch, a time scale, an orientation
    profile, and an ephemeris. Downstream code can build its own registry;
    this one keeps the module reachable and exercised without private data.
    """
    reg = AuthorityRegistry()
    reg.register_new(AuthorityType.BODY, "EARTH", "1.0.0",
                     {"kind": "planet", "convention": "geodetic_or_geocentric"})
    reg.register_new(AuthorityType.BODY, "MARS", "1.0.0",
                     {"kind": "planet", "convention": "IAU_body_fixed"})
    reg.register_new(AuthorityType.ROOT, "EARTH_BODY_FIXED_ROOT", "1.0.0",
                     {"body_id": "EARTH", "kind": "body_fixed_root"})
    reg.register_new(AuthorityType.TIME_SCALE, "TT_DECIMAL_YEAR", "1.0.0",
                     {"unit": "decimal_year"})
    reg.register_new(AuthorityType.ORIENTATION, "SYNTH_ORIENT_A", "1.0.0",
                     {"body_id": "EARTH", "kind": "orientation_profile"})
    reg.register_new(AuthorityType.EPHEMERIS, "SYNTH_EPHEM_0", "1.0.0",
                     {"kind": "ephemeris", "note": "synthetic placeholder"})
    reg.register_new(AuthorityType.FRAME, "ITRF2020", "1.0.0", {
        "body_id": "EARTH",
        "frame_id": "ITRF2020",
        "epoch": "2020.0",
        "time_scale": "TT_DECIMAL_YEAR",
        "orientation_profile_id": "SYNTH_ORIENT_A",
        "ephemeris_id": None,
    })
    reg.register_new(AuthorityType.EPOCH, "EPOCH_2020_0", "1.0.0", {
        "body_id": "EARTH",
        "frame_id": "ITRF2020",
        "epoch": "2020.0",
        "time_scale": "TT_DECIMAL_YEAR",
        "orientation_profile_id": "SYNTH_ORIENT_A",
        "ephemeris_id": None,
    })
    return reg


def authority_report() -> dict:
    """What this module registers — and what it refuses to claim."""
    reg = default_registry()
    return {
        "module": "cwatlas.authority",
        "phase_id": "P06",
        "authority_types": [t.value for t in AuthorityType],
        "schema_validated_types": sorted(t.value for t in _SCHEMA_TYPES),
        "registered_certificates": [
            {
                "authority_type": c.authority_type.value,
                "authority_id": c.authority_id,
                "version": c.version,
            }
            for c in reg.certificates()
        ],
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "note": (
            "certificates name authorities by typed id + version + hash so a "
            "decode records exactly which frame/epoch/orientation it used "
            "(contract invariant 2). Unregistered authorities are refused; "
            "legacy versions are preserved, never overwritten."),
        "verdict": "GREEN_R10_8_1_P06_FRAME_EPOCH_AND_ROOT_AUTHORITY_REGISTRY",
    }
