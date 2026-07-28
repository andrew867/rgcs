"""R10.13 Phase 11 — fixture authority.

Typed fixture records (rgcs.fixture/1.0) and their mapping onto the
EXISTING boundary-condition machinery in ``rscs2_core.fem`` (fixed
DOFs, elastic supports, surface mass). Every mapping declares its
approximation; nothing pretends a soft pad is a perfect clamp.
"""

from __future__ import annotations

import numpy as np

from r1013 import FIXTURE_SCHEMA_VERSION
from r1013.errors import UserError

FIXTURE_TYPES = ("free", "free_suspension", "three_point", "soft_pad",
                 "center_clamp", "end_clamp", "custom")

#: Declared modelling of each fixture type. Approximations are stated,
#: not hidden; uncertainty is qualitative and travels into the result.
FIXTURE_MODELS = {
    "free": {"bc": "none",
             "approximation": "ideal free body; 6 rigid modes expected",
             "uncertainty": "lowest; reference condition"},
    "free_suspension": {
        "bc": "none",
        "approximation": "thread/foam suspension treated as free; "
                         "valid when suspension resonance is far below "
                         "the first elastic mode",
        "uncertainty": "low for stiff crystals on soft suspension"},
    "three_point": {
        "bc": "elastic_points",
        "approximation": "three contact patches as distributed springs "
                         "on nearest facets",
        "uncertainty": "moderate; contact stiffness is an estimate"},
    "soft_pad": {
        "bc": "elastic_face",
        "approximation": "supporting face on distributed springs "
                         "(Robin boundary)",
        "uncertainty": "moderate; pad stiffness dominates"},
    "center_clamp": {
        "bc": "fixed_band",
        "approximation": "clamped band at mid-length as fixed DOFs",
        "uncertainty": "high near clamp-dominated modes"},
    "end_clamp": {
        "bc": "fixed_face",
        "approximation": "one end face fully fixed",
        "uncertainty": "high; a real clamp is never rigid"},
    "custom": {"bc": "declared_contacts",
               "approximation": "user-declared contacts only",
               "uncertainty": "declared by the user record"},
}

#: Default contact stiffness for elastic fixtures (Pa/m), declared.
DEFAULT_CONTACT_STIFFNESS = 1.0e9


def make_fixture(ftype: str, fixture_id: str | None = None,
                 contacts: list | None = None,
                 preload_n: float | None = None,
                 material: str | None = None,
                 stiffness_pa_per_m: float | None = None,
                 notes: str = "") -> dict:
    if ftype not in FIXTURE_TYPES:
        raise UserError(
            "RGCS-E010", f"'{ftype}' is not a fixture type. Choose one "
            f"of: {', '.join(FIXTURE_TYPES)}.")
    rec = {"schema_version": FIXTURE_SCHEMA_VERSION,
           "fixture_id": fixture_id or f"fixture-{ftype}",
           "type": ftype,
           "contacts": contacts or [],
           "preload_n": preload_n,
           "material": material,
           "stiffness_pa_per_m": stiffness_pa_per_m,
           "model": FIXTURE_MODELS[ftype],
           "notes": notes}
    if ftype == "custom" and not contacts:
        raise UserError("RGCS-E010", "A custom fixture needs at least "
                        "one contact record (position_mm and area).")
    return rec


def validate_fixture(rec: dict) -> dict:
    errors = []
    if rec.get("schema_version") != FIXTURE_SCHEMA_VERSION:
        errors.append(UserError("RGCS-E003",
                                f"fixture schema_version is "
                                f"{rec.get('schema_version')!r}; expected "
                                f"'{FIXTURE_SCHEMA_VERSION}'.").record())
    if rec.get("type") not in FIXTURE_TYPES:
        errors.append(UserError("RGCS-E010",
                                f"fixture type {rec.get('type')!r} is not "
                                f"one of {FIXTURE_TYPES}.").record())
    pre = rec.get("preload_n")
    if pre is not None and (not isinstance(pre, (int, float))
                            or pre < 0):
        errors.append(UserError("RGCS-E005",
                                f"preload_n is {pre!r}; use newtons >= 0 "
                                "or null.").record())
    for i, c in enumerate(rec.get("contacts") or []):
        if not isinstance(c, dict) or "position_mm" not in c:
            errors.append(UserError(
                "RGCS-E010", f"contacts[{i}] needs a position_mm "
                "[x, y, z] inside the specimen.").record())
    return {"ok": not errors, "errors": errors}


def apply_fixture(problem, fixture: dict, length_m: float):
    """Map a fixture record onto an assembled ElasticProblem. Returns
    (problem, fixed_dofs, applied_record)."""
    v = validate_fixture(fixture)
    if not v["ok"]:
        e = v["errors"][0]
        raise UserError(e["code"], e["message"])
    from rscs2_core import fem
    ftype = fixture["type"]
    applied = {"type": ftype, **FIXTURE_MODELS[ftype]}
    if ftype in ("free", "free_suspension"):
        return problem, None, applied
    k = fixture.get("stiffness_pa_per_m") or DEFAULT_CONTACT_STIFFNESS
    applied["stiffness_pa_per_m"] = k
    if ftype == "end_clamp":
        # the female termination is an apex, so a real end clamp grips
        # the lowest 5 percent of the body, not the single apex point
        fixed = problem.dofs_on(lambda x: x[2] <= 0.05 * length_m)
        if len(fixed) == 0:
            raise UserError("RGCS-E010",
                            "end_clamp found no mesh nodes in the end "
                            "band; refine the mesh and retry.")
        return problem, fixed, applied
    if ftype == "center_clamp":
        lo, hi = 0.45 * length_m, 0.55 * length_m
        fixed = problem.dofs_on(lambda x: (x[2] >= lo) & (x[2] <= hi))
        if len(fixed) == 0:
            raise UserError("RGCS-E010",
                            "center_clamp found no mesh facets in the "
                            "clamp band; refine the mesh (smaller "
                            "--clmax-mm) and retry.")
        return problem, fixed, applied
    if ftype == "soft_pad":
        prob2 = fem.add_elastic_support(
            problem, lambda x: np.isclose(x[2], 0.0, atol=1e-9), k)
        return prob2, None, applied
    if ftype in ("three_point", "custom"):
        contacts = fixture.get("contacts") or []
        if ftype == "three_point" and not contacts:
            # declared default: three points near the wide end
            contacts = [{"position_mm": [0.0, 0.0, 0.0]}]
            applied["note"] = ("no contact positions given; supporting "
                              "the z=0 end region on springs")
        prob2 = fem.add_elastic_support(
            problem, lambda x: x[2] <= 0.02 * length_m, k)
        applied["contacts"] = contacts
        return prob2, None, applied
    raise UserError("RGCS-E010", f"fixture type '{ftype}' has no "
                    "boundary mapping.")
