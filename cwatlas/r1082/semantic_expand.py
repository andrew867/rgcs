"""P10 — Seven-field semantic expansion of the compact route.

Locked Decision 14: the semantic address has **seven logical fields** —
``namespace``, ``stellar_system``, ``body``, ``root_face``, ``recursive_path``,
``barycentric``, and ``shell_epoch`` (shell and epoch permitted to share a
compressed wire field). This module expands a compact base-100 route (P09) into
those seven fields and compacts them back, exactly.

The expansion is driven by :class:`TokenSemanticResolver` plugins that each
declare an **explicit token count** — one token does *not* equal one semantic
field:

* ``namespace`` / ``stellar_system`` / ``body`` consume **0** tokens; they are
  absent in a short local address and fall back to declared defaults (Locked
  Decision, "body and system prefixes may be absent in short local addresses");
* ``root_face`` consumes **1** token (icosahedral face 0..19);
* ``recursive_path`` consumes **3** tokens, each decomposed into three octal
  digits (0..7) — nine path steps from three tokens;
* ``shell_epoch`` consumes **1** token: the packed shell + coarse-epoch field.

A decoded **certificate** expands every available field. A **variable-depth**
packet with fewer tokens omits unused epoch components (the compressed epoch is
``None`` and, for even shorter packets, the recursive path shrinks).

Expansion is lossless: ``compact(expand(route)) == route`` for the token-bearing
fields. ``barycentric`` is a derived display coordinate (a deterministic
function of face/path/shell); it is reproduced on every expansion and is not
consulted when compacting.

Evidence class ``DERIVED_MATHEMATICS`` / claim class ``MATHEMATICAL_TRANSLATION``.
The seven fields are an arithmetic re-expression of the route, **not** a decoded
location and **not** a validated source origin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from cwatlas.claims import ClaimClass
from cwatlas.r1082 import claims as _r1082
from cwatlas.r1082.route_core import (
    CODEC_ID, FIVE_TOKEN, RouteCore, RouteError, parse_five_token,
)

# -- defaults for absent short-address prefixes -----------------------------

DEFAULT_NAMESPACE = "CW"
DEFAULT_STELLAR_SYSTEM = "SOL"
DEFAULT_BODY = "EARTH"

#: Face range (icosahedral 20-face partition), shell range, path-step range.
FACE_MIN, FACE_MAX = 0, 19
SHELL_MIN, SHELL_MAX = 0, 8
PATH_STEP_MIN, PATH_STEP_MAX = 0, 7

#: Each recursive-path token expands to this many octal digits (99 < 8**3).
OCTAL_DIGITS_PER_TOKEN = 3
_PATH_TOKEN_COUNT = 3

#: Packed shell+coarse-epoch field: token = coarse * (SHELL_MAX+1) + shell.
_SHELL_BASE = SHELL_MAX + 1  # 9

#: A fixed, deterministic conventional epoch used when the caller supplies none.
#: This is a passed-in constant, never a wall-clock read (determinism rule).
DEFAULT_CONVENTIONAL_EPOCH = {"timescale": "UTC", "value": "2000-01-01T00:00:00Z"}

#: Body-relative shell radii (metres), Earth reference. These are **declared
#: ontology representatives** (DERIVED / SOURCE ontology), not measured values;
#: they exist so the shell always supplies a radius (never "altitude missing").
SHELL_RADIUS_M: dict[int, float] = {
    0: 0.0,          # infinite centre / recursive closure
    1: 1.2215e6,     # core
    2: 3.480e6,      # mantle
    3: 6.371e6,      # surface datum (mean Earth radius)
    4: 6.381e6,      # low-aircraft regime
    5: 6.391e6,      # higher-aircraft regime
    6: 6.771e6,      # satellite-orbit regime
    7: 2.6571e7,     # high-satellite regime
    8: 4.2164e7,     # equal-pull / effective-potential boundary (8<->0)
}


def resolve_shell_radius_m(shell_index: int) -> float:
    """The body-relative shell radius (declared ontology representative)."""
    try:
        return SHELL_RADIUS_M[shell_index]
    except KeyError:
        raise RouteError(
            f"shell index {shell_index} out of range "
            f"[{SHELL_MIN}, {SHELL_MAX}]; no radius profile.") from None


@dataclass(frozen=True)
class TokenSemanticResolver:
    """A semantic-field resolver plugin with an explicit token count.

    ``token_count`` is the number of base-100 tokens the field consumes — 0 for
    absent short-address prefixes, so one token never silently equals one field.
    """

    field_name: str
    token_count: int
    description: str


#: The ordered resolver plan for the locked five-token route. The token counts
#: sum to FIVE_TOKEN; the three zero-count prefixes are absent in a short local
#: address and take declared defaults.
RESOLVER_PLAN: tuple[TokenSemanticResolver, ...] = (
    TokenSemanticResolver("namespace", 0, "absent in short local address"),
    TokenSemanticResolver("stellar_system", 0, "absent in short local address"),
    TokenSemanticResolver("body", 0, "absent in short local address"),
    TokenSemanticResolver("root_face", 1, "icosahedral face 0..19"),
    TokenSemanticResolver("recursive_path", _PATH_TOKEN_COUNT,
                          "three tokens -> nine octal path steps (0..7)"),
    TokenSemanticResolver("barycentric", 0,
                          "derived display coordinate (function of face/path/"
                          "shell); consumes no tokens"),
    TokenSemanticResolver("shell_epoch", 1, "packed shell + coarse epoch"),
)


@dataclass(frozen=True)
class SemanticAddress:
    """The seven logical fields, conforming to ``semantic_address.schema.json``.

    ``unresolved`` records fields left at a default because their prefix was
    absent (short local address) — every intermediate/unresolved field is
    exposed, never silently invented.
    """

    namespace: str
    stellar_system: str
    body: str
    root_face: int
    recursive_path: tuple[int, ...]
    barycentric: tuple[float, float, float]
    shell_epoch: dict
    unresolved: tuple[str, ...] = field(default=(), compare=False)

    def to_dict(self) -> dict:
        return {
            "namespace": self.namespace,
            "stellar_system": self.stellar_system,
            "body": self.body,
            "root_face": self.root_face,
            "recursive_path": list(self.recursive_path),
            "barycentric": list(self.barycentric),
            "shell_epoch": self.shell_epoch,
        }


def _token_to_octal(value: int) -> tuple[int, ...]:
    """Decompose a 0..99 token into three octal digits (0..7)."""
    return (value // 64, (value // 8) % 8, value % 8)


def _octal_to_token(digits: Sequence[int]) -> int:
    """Recompose three octal digits (0..7) into a base-100 token."""
    if len(digits) != OCTAL_DIGITS_PER_TOKEN:
        raise RouteError(
            f"a path token needs exactly {OCTAL_DIGITS_PER_TOKEN} octal "
            f"digits, got {len(digits)}.")
    d0, d1, d2 = digits
    for d in (d0, d1, d2):
        if not PATH_STEP_MIN <= d <= PATH_STEP_MAX:
            raise RouteError(
                f"path step {d} out of range "
                f"[{PATH_STEP_MIN}, {PATH_STEP_MAX}].")
    return d0 * 64 + d1 * 8 + d2


def _pack_shell_epoch_token(shell: int, coarse: int) -> int:
    return coarse * _SHELL_BASE + shell


def _unpack_shell_epoch_token(token: int) -> tuple[int, int]:
    return token % _SHELL_BASE, token // _SHELL_BASE  # (shell, coarse)


def _barycentric(face: int, path: Sequence[int], shell: int
                 ) -> tuple[float, float, float]:
    """A deterministic display coordinate in [0,1]^3 (derived, not measured)."""
    p0 = path[0] if path else 0
    return (
        face / FACE_MAX if FACE_MAX else 0.0,
        p0 / PATH_STEP_MAX if PATH_STEP_MAX else 0.0,
        shell / SHELL_MAX if SHELL_MAX else 0.0,
    )


def _shell_epoch_dict(shell: int, coarse: int | None,
                      conventional_epoch: dict) -> dict:
    """Build a ``shell_epoch`` object; omit the compressed epoch when absent."""
    if shell not in SHELL_RADIUS_M:
        raise RouteError(
            f"shell index {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")
    ce = dict(conventional_epoch)
    if "timescale" not in ce or "value" not in ce:
        raise RouteError(
            "conventional_epoch must carry a timescale and a value "
            "(UTC/TAI/TT/TDB); it is mandatory even with a compressed epoch.")
    out: dict = {
        "shell": {
            "index": shell,
            "profile_id": f"EARTH_SHELL_R_V1:{shell}",
            "radius_m": resolve_shell_radius_m(shell),
            "altitude_m": None,
            "effective_potential": None,
        },
        "conventional_epoch": ce,
    }
    if coarse is None:
        out["compressed_epoch"] = None  # variable depth: unused epoch omitted
    else:
        out["compressed_epoch"] = {
            "profile": "COMPOSITE_VARIABLE_DEPTH",
            "payload": {"coarse": coarse},
        }
    return out


def expand(route: RouteCore | str, *,
           conventional_epoch: dict | None = None,
           namespace: str = DEFAULT_NAMESPACE,
           stellar_system: str = DEFAULT_STELLAR_SYSTEM,
           body: str = DEFAULT_BODY) -> SemanticAddress:
    """Expand a compact route into the seven semantic fields.

    Accepts a :class:`RouteCore` or a route string (parsed as five-token).
    ``conventional_epoch`` is mandatory metadata; a fixed deterministic default
    is used if the caller omits it (never a wall-clock read). Short packets omit
    unused epoch components; ``unresolved`` lists fields left at a default.
    """
    if isinstance(route, str):
        route = parse_five_token(route)
    if not isinstance(route, RouteCore):
        raise RouteError(f"expand expects a RouteCore or str, got {route!r}.")

    ce = DEFAULT_CONVENTIONAL_EPOCH if conventional_epoch is None \
        else conventional_epoch
    tokens = route.tokens
    depth = len(tokens)
    if depth < 1:
        raise RouteError("cannot expand an empty route.")

    unresolved: list[str] = []
    for name, present in (("namespace", namespace != DEFAULT_NAMESPACE),
                          ("stellar_system",
                           stellar_system != DEFAULT_STELLAR_SYSTEM),
                          ("body", body != DEFAULT_BODY)):
        if not present:
            unresolved.append(name)  # absent prefix -> declared default

    face = tokens[0]
    if not FACE_MIN <= face <= FACE_MAX:
        raise RouteError(
            f"root_face token {face} out of range [{FACE_MIN}, {FACE_MAX}]; "
            f"refused (not a valid icosahedral face).")

    # recursive path: as many of the middle 3 tokens as are present
    path_tokens = tokens[1:1 + _PATH_TOKEN_COUNT]
    path: list[int] = []
    for tok in path_tokens:
        path.extend(_token_to_octal(tok))

    # shell+epoch: the final token when the full five-token route is present.
    shell = 0
    coarse: int | None = None
    if depth >= FIVE_TOKEN:
        shell, coarse = _unpack_shell_epoch_token(tokens[FIVE_TOKEN - 1])
    else:
        unresolved.append("shell_epoch.compressed_epoch")  # variable depth

    shell_epoch = _shell_epoch_dict(shell, coarse, ce)
    bary = _barycentric(face, path, shell)

    return SemanticAddress(
        namespace=namespace,
        stellar_system=stellar_system,
        body=body,
        root_face=face,
        recursive_path=tuple(path),
        barycentric=bary,
        shell_epoch=shell_epoch,
        unresolved=tuple(unresolved),
    )


def compact(address: SemanticAddress) -> RouteCore:
    """Recover the exact compact route from a semantic address (lossless)."""
    tokens: list[int] = [address.root_face]

    path = list(address.recursive_path)
    if len(path) % OCTAL_DIGITS_PER_TOKEN != 0:
        raise RouteError(
            f"recursive_path length {len(path)} is not a multiple of "
            f"{OCTAL_DIGITS_PER_TOKEN}; cannot recompose path tokens.")
    for i in range(0, len(path), OCTAL_DIGITS_PER_TOKEN):
        tokens.append(_octal_to_token(path[i:i + OCTAL_DIGITS_PER_TOKEN]))

    ce = address.shell_epoch.get("compressed_epoch")
    if ce is not None:
        shell = address.shell_epoch["shell"]["index"]
        coarse = ce["payload"]["coarse"]
        tokens.append(_pack_shell_epoch_token(shell, coarse))

    raw = "".join(f"{t:02d}" for t in tokens)
    return RouteCore(raw=raw, tokens=tuple(tokens), codec_id=CODEC_ID,
                     leading_zero_policy="LEFT_PAD_TO_EVEN",
                     variable_depth=ce is None)


def semantic_expand_report() -> dict:
    """P10 declaration receipt. Arithmetic expansion; nothing located."""
    return {
        "phase_id": "P10",
        "tranche": "T03",
        "what_this_is": (
            "a seven-field semantic expansion (namespace, stellar_system, "
            "body, root_face, recursive_path, barycentric, shell_epoch) driven "
            "by TokenSemanticResolver plugins with explicit token counts; "
            "one token does not equal one field; lossless expand<->compact."),
        "seven_fields": [r.field_name for r in RESOLVER_PLAN],
        "resolver_token_counts": {r.field_name: r.token_count
                                  for r in RESOLVER_PLAN},
        "total_tokens": sum(r.token_count for r in RESOLVER_PLAN),
        "codec_id": CODEC_ID,
        "evidence_class": _r1082.EvidenceClass.DERIVED_MATHEMATICS.value,
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "variable_depth_omits_unused_epoch": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "GREEN_R10_8_2_P10_SEVEN-FIELD_SEMANTIC_EXPANSION",
        "what_this_does_not_say": (
            "The seven fields are an arithmetic re-expression of the route, "
            "not a decoded location; barycentric is a derived display "
            "coordinate; source origin remains NOT_VALIDATED."),
    }
