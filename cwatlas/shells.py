"""P16 — Body-relative shell registry and nonliteral ontology labels.

The source corpus describes a nested set of "shells" numbered 0 through 8:
shell 0 is the body-relative surface datum and shells 1 through 8 are ordered
body-relative altitude bands. This module makes that ontology *representable*
without endorsing it.

The two governance rules that shape the design:

* **The labels are nonliteral.** A shell label is SOURCE ontology — at most a
  ``SOURCE_CLAIM`` (what a source reported) or a ``MATHEMATICAL_TRANSLATION``
  (an arithmetic re-expression). It is never a physical or geographic claim.
  The registry records the label; it does not assert the label is real.

* **The ``8 <-> 0`` closure is stored, not applied.** System Contract
  invariant 8: "``8 <-> 0`` shell closure is stored as source ontology, not
  silently applied to every codec." The corpus asserts shell 8 "wraps back" to
  shell 0. The atlas keeps that assertion as data, exposes it behind an
  explicit opt-in flag (default off), and refuses any attempt to auto-apply it
  to a codec.

Shell state conforms to the ``ShellState`` architecture concept: a shell index
bound to a body, carrying its ontology label and its claim class.

Pure data and typed refusals. Nothing here measures anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from cwatlas.claims import ClaimClass, ClaimError

#: The number of shells in the source ontology, indices 0..8 inclusive.
SHELL_MIN = 0
SHELL_MAX = 8


@dataclass(frozen=True)
class ShellDefinition:
    """One shell in the source ontology.

    ``literal`` is always ``False``: the label is a nonliteral source-ontology
    label, never a physical claim. ``altitude_band`` edges are declared in
    source-ontology band-ordinal units (dimensionless), *not* measured metres.
    """

    index: int
    ontology_label: str
    surface_semantics: str
    altitude_band_lower: float
    altitude_band_upper: float
    claim_class: ClaimClass
    literal: bool = False

    def __post_init__(self) -> None:
        if self.literal:
            raise ClaimError(
                "a shell ontology label is nonliteral; literal=True would "
                "assert a physical shell, which is not claimed.")
        if self.claim_class not in (
            ClaimClass.SOURCE_CLAIM, ClaimClass.MATHEMATICAL_TRANSLATION):
            raise ClaimError(
                f"a shell label may only be SOURCE_CLAIM or "
                f"MATHEMATICAL_TRANSLATION, not {self.claim_class.value}.")


@dataclass(frozen=True)
class ShellState:
    """A shell index bound to a body — the ShellState concept.

    Carries the nonliteral ontology label and its claim class so a downstream
    receipt can record what shell law was in effect without promoting it.
    """

    shell_index: int
    body_id: str
    ontology_label: str
    claim_class: ClaimClass

    def __post_init__(self) -> None:
        if not SHELL_MIN <= self.shell_index <= SHELL_MAX:
            raise ClaimError(
                f"shell_index {self.shell_index} out of range "
                f"[{SHELL_MIN}, {SHELL_MAX}].")


def _shell(index: int, label: str, semantics: str,
           lower: float, upper: float) -> ShellDefinition:
    return ShellDefinition(
        index=index,
        ontology_label=label,
        surface_semantics=semantics,
        altitude_band_lower=lower,
        altitude_band_upper=upper,
        claim_class=ClaimClass.SOURCE_CLAIM,
    )


#: The shell registry, 0..8. Labels and bands are SOURCE ontology (nonliteral).
#: Band edges are source-ontology band ordinals, not measured altitudes.
SHELL_REGISTRY: dict[int, ShellDefinition] = {
    0: _shell(0, "SHELL_0_SURFACE_DATUM",
              "body-relative surface datum (shell zero)", 0.0, 0.0),
    1: _shell(1, "SHELL_1_BAND", "first body-relative altitude band", 0.0, 1.0),
    2: _shell(2, "SHELL_2_BAND", "second body-relative altitude band", 1.0, 2.0),
    3: _shell(3, "SHELL_3_BAND", "third body-relative altitude band", 2.0, 3.0),
    4: _shell(4, "SHELL_4_BAND", "fourth body-relative altitude band", 3.0, 4.0),
    5: _shell(5, "SHELL_5_BAND", "fifth body-relative altitude band", 4.0, 5.0),
    6: _shell(6, "SHELL_6_BAND", "sixth body-relative altitude band", 5.0, 6.0),
    7: _shell(7, "SHELL_7_BAND", "seventh body-relative altitude band", 6.0, 7.0),
    8: _shell(8, "SHELL_8_OUTER_BAND",
              "eighth (outermost) body-relative altitude band", 7.0, 8.0),
}


#: The 8 <-> 0 closure, stored as source ontology. NOT auto-applied (invariant
#: 8). ``auto_apply`` is permanently False; applying it requires the explicit
#: opt-in flag on :func:`apply_shell_closure`.
SHELL_CLOSURE = {
    "from_shell": 8,
    "to_shell": 0,
    "claim_class": ClaimClass.SOURCE_CLAIM.value,
    "auto_apply": False,
    "description": (
        "the source ontology asserts shell 8 wraps back to shell 0; this is "
        "stored as SOURCE ontology and is never silently applied to a codec."),
}


def get_shell(index: int) -> ShellDefinition:
    """Return a shell definition, or refuse an unknown index."""
    try:
        return SHELL_REGISTRY[index]
    except (KeyError, TypeError):
        raise ClaimError(
            f"unknown shell {index!r}; the source ontology defines shells "
            f"{SHELL_MIN}..{SHELL_MAX}.") from None


def make_shell_state(index: int, body_id: str) -> ShellState:
    """Bind a shell index to a body, refusing an unknown index or empty body."""
    definition = get_shell(index)  # refuses unknown index
    if not body_id:
        raise ClaimError("a shell state must declare a body_id.")
    return ShellState(
        shell_index=definition.index,
        body_id=body_id,
        ontology_label=definition.ontology_label,
        claim_class=definition.claim_class,
    )


def refuse_auto_closure(*_a, **_k) -> None:
    """Any auto-application of the 8 <-> 0 closure is refused (invariant 8)."""
    raise ClaimError(
        "refused: the 8 <-> 0 shell closure is SOURCE ontology and may not be "
        "auto-applied to a codec. It is stored, and applied only through the "
        "explicit opt-in flag on apply_shell_closure(apply_closure=True).")


def apply_shell_closure(index: int, apply_closure: bool = False) -> int:
    """Resolve a shell index under the 8 <-> 0 closure.

    The closure is **opt-in and default off**. With ``apply_closure=False``
    (the default) the index is returned unchanged and the closure is refused
    for the 8 -> 0 case; the caller cannot silently benefit from it. With
    ``apply_closure=True`` the caller has explicitly opted in and shell 8
    resolves to shell 0.
    """
    get_shell(index)  # refuses unknown index
    if index == SHELL_CLOSURE["from_shell"]:
        if not apply_closure:
            raise ClaimError(
                "refused: shell 8 -> 0 closure is opt-in and off by default; "
                "pass apply_closure=True to opt in explicitly. It is never "
                "applied silently (invariant 8).")
        return int(SHELL_CLOSURE["to_shell"])
    return index


def shells_report() -> dict:
    """P16 declaration receipt. Labels are nonliteral; nothing is measured."""
    return {
        "phase_id": "P16",
        "what_this_is": (
            "a body-relative shell registry (shells 0..8) with surface "
            "semantics, altitude bands, and nonliteral SOURCE ontology "
            "labels; the 8 <-> 0 closure stored as source ontology and never "
            "auto-applied."),
        "claim_class": ClaimClass.SOURCE_CLAIM.value,
        "shell_range": [SHELL_MIN, SHELL_MAX],
        "shells": {
            i: {
                "ontology_label": s.ontology_label,
                "surface_semantics": s.surface_semantics,
                "altitude_band": [s.altitude_band_lower, s.altitude_band_upper],
                "claim_class": s.claim_class.value,
                "literal": s.literal,
            }
            for i, s in SHELL_REGISTRY.items()
        },
        "shell_closure": SHELL_CLOSURE,
        "labels_are_nonliteral": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": (
            "SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED"),
        "verdict": "SHELL_ONTOLOGY_STORED_NONLITERAL_NO_AUTO_CLOSURE",
    }
