"""P13 (A85-A94) — the root-space resolver, gauge contract, and
root-lock certificate.

The R3 correction: a root is NOT "the first place where the phase
residual is zero". wrap(phi_obs - phi_model) = 0 only means
phi_obs - phi_model = 2*pi*n for unknown integer n — every zero of the
wrapped residual is an alias candidate. A root is a typed, calibrated,
alias-resolved, gauge-declared, uncertainty-bounded RELATIONAL
reference state, and the certificate below refuses to say "locked"
until every criterion holds.

Absolute vacuum root and non-local preferred frames are UNSUPPORTED
by standing status, not by oversight.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import (ClaimBoundaryError, GaugeError, ROOT_CLASSES,
               ROOT_STATUSES, validate_root_class, validate_root_status)
from pmwr.phase_authority import PhaseAuthority
from pmwr.recovery import identifiability_gate

TWO_PI = 2.0 * math.pi


# --- zero-residual alias audit (A87) --------------------------------------

def zero_residual_aliases(frequency_hz: float, search_window_s: float
                          ) -> dict:
    """Every delay in the window whose wrapped residual is zero: one
    per carrier cycle. 'First zero' is an arbitrary member of this
    set, which is why R3 refuses to call it the root."""
    n = int(search_window_s * frequency_hz)
    return {"frequency_hz": frequency_hz,
            "search_window_s": search_window_s,
            "zero_residual_candidates": n + 1,
            "spacing_s": 1.0 / frequency_hz,
            "statement": "wrap(residual)=0 admits integer-cycle "
                         "aliases; a zero of the wrapped residual is "
                         "a candidate, never a root",
            "status": "ROOT_ALIAS_UNRESOLVED" if n > 0 else
                      "ROOT_LOCK_BOUNDED",
            "evidence_class": "DERIVED_ARITHMETIC"}


def dual_lattice_root_search(f_a_hz: float, f_b_hz: float,
                             window_s: float) -> dict:
    """A87: two incommensurate carriers thin the alias set to their
    beat period (reusing the v4.7 dual-lattice result at root level)."""
    if f_a_hz == f_b_hz:
        raise ClaimBoundaryError("identical carriers cannot "
                                 "disambiguate each other")
    beat = abs(f_a_hz - f_b_hz)
    survivors = int(window_s * beat) + 1
    return {"beat_hz": beat,
            "unambiguous_span_s": 1.0 / beat,
            "surviving_candidates": survivors,
            "resolved_within_window": survivors == 1,
            "evidence_class": "DERIVED_ARITHMETIC"}


# --- canonical root state (A86) --------------------------------------------

@dataclass(frozen=True)
class RootState:
    """The eleven-component canonical root (core/17). Every component
    must be declared; a root with missing components is refused at
    construction, which is the point."""
    root_class: str
    address_semantic: str                # S
    reference_frame: str                 # F
    anchor_event: tuple                  # x0^mu (t, x, y, z)
    epoch: str                           # t0
    reference_worldlines: tuple          # W (ids)
    phase_authority: PhaseAuthority      # A
    calibration_ref: str                 # C
    gauge_rule: str                      # G — canonical-rep selection
    integer_cycles: tuple | None         # N (None = unresolved)
    nuisance: dict = field(default_factory=dict)   # Theta
    covariance_diag: tuple = ()          # Sigma proxy

    def __post_init__(self):
        validate_root_class(self.root_class)
        for name in ("address_semantic", "reference_frame", "epoch",
                     "calibration_ref", "gauge_rule"):
            if not getattr(self, name):
                raise ClaimBoundaryError(
                    f"root state missing {name}; an undeclared "
                    "component makes the root untyped")
        if len(self.anchor_event) != 4:
            raise ClaimBoundaryError("anchor event needs (t,x,y,z)")
        if self.root_class == "PHYSICAL_REFERENCE_NETWORK_ROOT" and \
                len(self.reference_worldlines) < 4:
            raise ClaimBoundaryError(
                "a physical reference network needs >= 4 worldlines "
                "to define emission coordinates")

    @property
    def cycles_resolved(self) -> bool:
        return self.integer_cycles is not None


# --- gauge orbits (A88) ------------------------------------------------------

def gauge_orbit_audit(observations_equal_under: list,
                      canonical_rule: str | None) -> dict:
    """If transformations Q leave observations invariant, the
    recoverable object is the equivalence class [x] = {Qx}. Selecting
    a member requires a DECLARED rule; without one the orbit stands."""
    if not canonical_rule:
        raise GaugeError(
            "gauge orbit with no canonical-representative rule: the "
            f"class {{{', '.join(observations_equal_under)}}} has no "
            "distinguished member until a selection rule is declared")
    return {"invariances": list(observations_equal_under),
            "canonical_rule": canonical_rule,
            "recovered_object": "equivalence class with declared "
                                "representative",
            "collapse_refused":
                "the representative is a CONVENTION, not the one true "
                "state (forbidden collapse "
                "CANONICAL_REPRESENTATIVE_IS_UNIQUE_ONTOLOGY)",
            "evidence_class": "DERIVED_ARITHMETIC"}


# --- emission coordinates (A89) ----------------------------------------------

def emission_localize(emitters: list, ranges_m: list,
                      noise_m: float = 1.0) -> dict:
    """Localize an event from ranges to >= 4 reference worldlines
    (linearized GPS-style solve). The output frame is RELATIONAL —
    defined by those worldlines — and the audit says so."""
    if len(emitters) < 4:
        return {"solved": False,
                "status": "ROOT_PARTIALLY_IDENTIFIED",
                "reason": f"{len(emitters)} reference worldlines < 4: "
                          "emission coordinates undefined"}
    P = np.array(emitters, dtype=float)
    r = np.array(ranges_m, dtype=float)
    x0 = P.mean(axis=0)
    for _ in range(10):
        d = np.linalg.norm(P - x0, axis=1)
        J = (x0 - P) / d[:, None]
        dx, *_ = np.linalg.lstsq(J, r - d, rcond=None)
        x0 = x0 + dx
        if np.linalg.norm(dx) < 1e-9:
            break
    gate = np.linalg.svd(J, compute_uv=False)
    cond = float(gate[0] / gate[-1])
    return {"solved": True, "position_m": tuple(float(v) for v in x0),
            "geometry_condition": cond,
            "position_uncertainty_m": noise_m * cond,
            "frame": "RELATIONAL — defined by the reference "
                     "worldlines; not a preferred universal frame "
                     "(forbidden collapse "
                     "REFERENCE_NETWORK_IS_PREFERRED_FRAME)",
            "evidence_class": "NUMERICAL_SIMULATION"}


# --- root-lock certificate (A86/A93) -----------------------------------------

#: Registered thresholds, frozen with the evaluation contract.
COND_LIMIT = 1e8
POSTERIOR_LIMIT = 10.0


def root_lock_certificate(root: RootState, freqs_hz: list,
                          candidate_delays_s: list,
                          noise_sigma: float,
                          aliases_in_domain: int,
                          independent_channels_agree: bool,
                          holdout_passed: bool) -> dict:
    """Evaluate every root-lock criterion (core/17) and emit the
    honest status. The best available status is ROOT_LOCK_BOUNDED —
    'bounded relational lock' — and the two absolute readings are
    UNSUPPORTED by construction."""
    failures = []
    if not root.cycles_resolved:
        failures.append(("ROOT_ALIAS_UNRESOLVED",
                         "integer-cycle vector unresolved"))
    if aliases_in_domain > 1:
        failures.append(("ROOT_NON_UNIQUE",
                         f"{aliases_in_domain} observationally "
                         "equivalent candidates in the search domain"))
    gate = identifiability_gate(freqs_hz, candidate_delays_s,
                                noise_sigma, COND_LIMIT)
    if not gate["identifiable"]:
        failures.append(("ROOT_PARTIALLY_IDENTIFIED",
                         "; ".join(gate["refusal_reasons"])))
    if gate["posterior_width_proxy"] > POSTERIOR_LIMIT:
        failures.append(("ROOT_LOCK_REJECTED",
                         "posterior width exceeds the frozen limit"))
    if not independent_channels_agree:
        failures.append(("ROOT_LOCK_REJECTED",
                         "independent channels disagree"))
    if not holdout_passed:
        failures.append(("ROOT_LOCK_REJECTED",
                         "held-out / substitution test failed"))

    status = failures[0][0] if failures else "ROOT_LOCK_BOUNDED"
    validate_root_status(status)
    return {
        "root_class": root.root_class,
        "status": status,
        "failures": [f"{s}: {r}" for s, r in failures],
        "identifiability": gate,
        "gauge_rule": root.gauge_rule,
        "absolute_vacuum_root": "ABSOLUTE_VACUUM_ROOT_UNSUPPORTED",
        "nonlocal_frame": "NONLOCAL_REFERENCE_FRAME_UNSUPPORTED",
        "claim_boundary":
            "the strongest possible claim is a BOUNDED RELATIONAL "
            "lock against declared references; no vacuum origin, no "
            "preferred frame, no transport",
        "evidence_class": "NUMERICAL_SIMULATION",
    }
