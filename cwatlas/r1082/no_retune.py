"""P26 — No-retune enforcement.

After the calibration is frozen (P19) and a holdout is scored, adjusting any
frozen parameter is *result shopping*: it silently re-fits the model to make the
holdout look better. This module makes such a change **technically visible** and
**testably forbidden**.

Given a frozen profile's receipt (which seals the seven
:data:`cwatlas.r1082.claims.FROZEN_PARAMETERS`) and a proposed *after* set of
parameters, :func:`detect_retune`:

* diffs the frozen parameters and identifies the **specific** parameter(s) that
  changed (root, handedness, epoch, shell, token order, centroid, …);
* treats **moving a label between the training and holdout sets** as a retune
  too (it re-partitions the very data the freeze sealed);
* routes any detected change through
  :func:`cwatlas.r1082.claims.refuse_post_output_retuning` (``frozen=True``) and
  raises a red :class:`RetuneError` carrying the changed parameters and the
  ``RETUNED_AFTER_REVEAL`` verdict;
* invalidates the holdout comparison after a mutation
  (:func:`holdout_comparison_status`).

A clean *after* (no frozen parameter changed, no label moved) returns a typed
"no retune" report rather than raising. Any real change mints a **new** profile
id — the only honest way to express a different configuration.

Nothing here is measured or physical.

    SOURCE_ORIGIN_NOT_VALIDATED
    PHYSICAL_VALIDATION_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
import json
from typing import Iterable, Mapping, Optional, Tuple

from cwatlas.r1082 import claims

MODULE_ID = "CW-R1082-NO-RETUNE"
MODULE_VERSION = "1.0.0"

#: The red verdict shown when a post-reveal retune is detected.
RETUNED_AFTER_REVEAL = "RETUNED_AFTER_REVEAL"

#: The clean verdict when nothing frozen changed.
NO_RETUNE_DETECTED = "NO_RETUNE_DETECTED"

#: A synthetic sentinel naming the training/holdout membership axis. Moving a
#: label across it is a retune of the sealed partition, mapped onto the frozen
#: ``destination_label_split`` parameter for the refusal message.
LABEL_MEMBERSHIP_PARAMETER = "training_holdout_membership"


class RetuneError(claims.R1082ClaimError):
    """A post-reveal retune of one or more frozen parameters (red verdict).

    Carries the changed parameters and the :data:`RETUNED_AFTER_REVEAL` verdict
    so the red team and the UI can name exactly what was tampered with.
    """

    def __init__(self, message: str, *,
                 changed_parameters: Tuple[str, ...] = (),
                 moved_labels: Tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.changed_parameters = tuple(changed_parameters)
        self.moved_labels = tuple(moved_labels)
        self.verdict = RETUNED_AFTER_REVEAL


def _frozen_from_receipt(before) -> dict:
    """Extract the frozen-parameter mapping from a receipt or a bare mapping.

    Accepts a full ``calibration_receipt`` document (``parameters.frozen``), a
    ``{"frozen": {...}}`` wrapper, or a bare ``{parameter: value}`` mapping.
    """
    if not isinstance(before, Mapping):
        raise RetuneError("before_receipt must be a mapping (a freeze receipt)")
    params = before.get("parameters")
    if isinstance(params, Mapping) and isinstance(params.get("frozen"), Mapping):
        return dict(params["frozen"])
    if isinstance(before.get("frozen"), Mapping):
        return dict(before["frozen"])
    # A bare mapping of frozen parameters.
    return {k: before[k] for k in before if k in claims.FROZEN_PARAMETERS}


def parameter_hash(frozen_parameters: Mapping) -> str:
    """A deterministic hash over the seven frozen parameters (the seal check).

    Only the :data:`cwatlas.r1082.claims.FROZEN_PARAMETERS` participate, so the
    hash is a stable fingerprint of the frozen configuration.
    """
    seal = {k: frozen_parameters.get(k) for k in claims.FROZEN_PARAMETERS}
    blob = json.dumps(seal, sort_keys=True, separators=(",", ":"), default=float)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def diff_frozen_parameters(before: Mapping, after: Mapping) -> Tuple[str, ...]:
    """Return the frozen parameter names whose value differs between two sets.

    Pure and non-raising: only the seven frozen parameters are compared, in a
    stable order. A parameter present in one set and absent in the other counts
    as changed.
    """
    changed = []
    _missing = object()
    for key in claims.FROZEN_PARAMETERS:
        b = before.get(key, _missing)
        a = after.get(key, _missing)
        if b != a:
            changed.append(key)
    return tuple(changed)


def _normalise_moves(label_moves: Optional[Iterable]) -> Tuple[str, ...]:
    """Coerce a label-move spec into a tuple of moved opaque ids."""
    if not label_moves:
        return ()
    out = []
    for m in label_moves:
        if isinstance(m, Mapping):
            out.append(str(m.get("opaque_id") or m.get("label") or m))
        else:
            out.append(str(m))
    return tuple(out)


def detect_retune(before_receipt: Mapping, after_params: Mapping, *,
                  label_moves: Optional[Iterable] = None) -> dict:
    """Detect and refuse any post-reveal change to a frozen parameter.

    ``before_receipt`` is the frozen profile's receipt (or its frozen-parameter
    mapping); ``after_params`` is the proposed configuration. ``label_moves`` is
    an optional list of opaque ids moved between the training and holdout sets —
    each such move is itself a retune.

    Returns a clean report when nothing changed. Raises :class:`RetuneError`
    (routed through :func:`cwatlas.r1082.claims.refuse_post_output_retuning`)
    naming the specific changed parameter(s) otherwise.
    """
    before = _frozen_from_receipt(before_receipt)
    if not isinstance(after_params, Mapping):
        raise RetuneError("after_params must be a mapping of parameters")
    after = _frozen_from_receipt(after_params) if (
        "parameters" in after_params or "frozen" in after_params) else dict(
        after_params)

    changed = diff_frozen_parameters(before, after)
    moved = _normalise_moves(label_moves)

    if not changed and not moved:
        return {
            "retuned": False,
            "verdict": NO_RETUNE_DETECTED,
            "changed_parameters": [],
            "moved_labels": [],
            "before_hash": parameter_hash(before),
            "after_hash": parameter_hash(after),
            "holdout_comparison": "VALID",
            "measured_here": "nothing",
            "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        }

    # A moved label re-partitions the sealed data: name the label-split axis.
    named = list(changed)
    if moved:
        named.append(LABEL_MEMBERSHIP_PARAMETER)

    # Route through the canonical locked-root refusal, then re-raise with the
    # specific changed parameters attached (the red RETUNED_AFTER_REVEAL verdict).
    try:
        claims.refuse_post_output_retuning(", ".join(named), frozen=True)
    except claims.R1082ClaimError as exc:
        raise RetuneError(
            f"{RETUNED_AFTER_REVEAL}: {exc}",
            changed_parameters=tuple(changed),
            moved_labels=moved) from exc
    # Unreachable: refuse_post_output_retuning always raises when frozen=True.
    raise RetuneError(RETUNED_AFTER_REVEAL, changed_parameters=tuple(changed),
                      moved_labels=moved)


def refuse_label_move(opaque_id: str, *, frm: str = "training",
                      to: str = "holdout") -> None:
    """Refuse moving a label between the training and holdout sets after freeze.

    Moving a label re-partitions the sealed data — a retune. This is a thin
    wrapper that always refuses (post-freeze); it is the single-move counterpart
    of :func:`detect_retune`'s ``label_moves``.
    """
    try:
        claims.refuse_post_output_retuning(LABEL_MEMBERSHIP_PARAMETER,
                                           frozen=True)
    except claims.R1082ClaimError as exc:
        raise RetuneError(
            f"{RETUNED_AFTER_REVEAL}: moving {opaque_id!r} from {frm} to {to} "
            f"re-partitions the sealed data ({exc})",
            moved_labels=(str(opaque_id),)) from exc


def holdout_comparison_status(before_receipt: Mapping, after_params: Mapping, *,
                              label_moves: Optional[Iterable] = None) -> str:
    """``"VALID"`` if nothing frozen changed, else ``"INVALIDATED"``.

    Non-raising: use this to decide whether a prior holdout comparison still
    holds. Any frozen-parameter change or label move invalidates it.
    """
    before = _frozen_from_receipt(before_receipt)
    after = _frozen_from_receipt(after_params) if (
        isinstance(after_params, Mapping) and
        ("parameters" in after_params or "frozen" in after_params)) else dict(
        after_params or {})
    changed = diff_frozen_parameters(before, after)
    moved = _normalise_moves(label_moves)
    return "INVALIDATED" if (changed or moved) else "VALID"


def new_profile_required(changed_parameters: Iterable[str]) -> bool:
    """True iff a change mandates a *new* profile id (any frozen change does)."""
    return bool(tuple(changed_parameters))


def no_retune_report() -> dict:
    """P26 declaration receipt. Every frozen change is detected and refused."""
    return {
        "phase_id": "P26",
        "tranche": "T07",
        "what_this_is": (
            "the no-retune enforcer: given a frozen profile's receipt and a "
            "proposed parameter set, it identifies the specific frozen "
            "parameter(s) changed (root, handedness, epoch, shell, token order, "
            "centroid, …), treats moving a label between the training and "
            "holdout sets as a retune too, and routes any change through "
            "claims.refuse_post_output_retuning with a red RETUNED_AFTER_REVEAL "
            "verdict; a change mints a new profile id and invalidates the "
            "holdout comparison."),
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "frozen_parameters": list(claims.FROZEN_PARAMETERS),
        "label_membership_parameter": LABEL_MEMBERSHIP_PARAMETER,
        "violation_verdict": RETUNED_AFTER_REVEAL,
        "clean_verdict": NO_RETUNE_DETECTED,
        "label_move_is_retune": True,
        "post_freeze_retuning": "REFUSED",
        "new_profile_required_on_change": True,
        "claim_class": claims.EvidenceClass.SOFTWARE_RESULT.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_NO_RETUNE_ENFORCED_FROZEN_CHANGES_DETECTED_REFUSED",
        "what_this_does_not_say": (
            "This enforcer detects and refuses post-reveal retuning; it does not "
            "make any candidate a measured fact and validates no source origin. "
            "The only honest way to express a different configuration is a new "
            "profile id, scored against fresh holdouts."),
    }
