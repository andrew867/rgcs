"""Eye diagnostic and consensus engine (Agent 09, RSCS2-D.1..D.16).

Determines whether a body possesses a stable, computationally special
interaction region ("eye"). THE ENGINE DOES NOT ASSUME AN EYE EXISTS:
a null result (NO_STABLE_CANDIDATE) is a passing scientific outcome,
and per DV4-010 no eye claim is ever classified Established — every
diagnostic here is Derived machinery applied to solved fields.

Architecture (deliberate):
  * field evaluators — compute the D1..D12 diagnostic FIELDS from a
    solved FEM problem (or an explicitly supplied solved EM/complex
    field; D5/D9/D10/D12 refuse to run without their inputs);
  * candidate extraction — top-quantile clustering of one field into
    candidate REGIONS (centroid + bounding box + score), never
    unjustified point precision;
  * consensus — a documented multi-criterion procedure over many
    diagnostic fields with agreement, null-comparison, mesh-persistence
    (D14), boundary-sensitivity (D13), mode-dependence, and
    uncertainty-persistence (D15) gates. Consensus is NOT an average of
    unrelated normalized fields: each gate is a separate pass/fail
    check with its own tolerance, and every rejection is recorded with
    its reason.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

__all__ = ["DIAGNOSTIC_SPECS", "DiagnosticField", "Candidate",
           "EyeConsensusResult", "ALLOWED_STATUSES",
           "evaluate_elastic_diagnostics", "electric_energy_density_field",
           "phase_coherence_field",
           "phase_singularities_on_plane", "em_circulation",
           "extract_candidates", "eye_consensus"]

# --- registered diagnostic specifications ------------------------------

def _spec(did, name, definition, units, normalization, conventional,
          failure, artifacts, classification, provenance):
    return {"id": did, "name": name, "field_definition": definition,
            "units": units, "normalization": normalization,
            "conventional_interpretation": conventional,
            "failure_conditions": failure, "artifact_risks": artifacts,
            "classification": classification, "provenance": provenance,
            "tests": ["tests/v4/test_rscs2_eye.py"]}


#: All sixteen registered diagnostics. Classifications follow DV4-010:
#: eye-related quantities are Derived machinery, NEVER Established
#: claims about a special region.
DIAGNOSTIC_SPECS: dict[str, dict] = {
    "D1": _spec("D1", "displacement amplitude", "|u(x)| of a mass-"
                "orthonormal mode", "m (mode-normalized)",
                "max-normalized to [0,1]",
                "antinodes of ordinary modes; maxima at free surfaces "
                "for bending", "mode not converged; rigid mode passed",
                "coarse-mesh interpolation error at caps",
                "DER (eye claims never EST, DV4-010)",
                "standard modal analysis"),
    "D2": _spec("D2", "strain-energy density", "w_s = 1/2 eps:C:eps",
                "J/m^3 (mode-normalized)", "max-normalized",
                "stress concentration at geometric transitions "
                "(cap/shaft junctions) is CONVENTIONAL",
                "requires C tensor; garbage on rigid modes",
                "singular corners exaggerate w_s under refinement",
                "DER (DV4-010)", "linear elasticity"),
    "D3": _spec("D3", "kinetic-energy density", "w_k = 1/2 rho w^2 |u|^2",
                "J/m^3 (mode-normalized)", "max-normalized",
                "co-located with D1 antinodes by construction",
                "meaningless for omega=0 (rigid) modes",
                "same interpolation risks as D1", "DER (DV4-010)",
                "standard modal analysis"),
    "D4": _spec("D4", "stress concentration (von Mises)",
                "sigma_vm of sigma = C:eps", "Pa (mode-normalized)",
                "max-normalized",
                "peaks at reentrant features/junctions — conventional",
                "requires C tensor", "corner singularities grow with "
                "refinement (classic non-persistent artifact)",
                "DER (DV4-010)", "von Mises (standard)"),
    "D5": _spec("D5", "piezoelectric/electric-energy density",
                "w_e = 1/2 grad(phi) . eps_diel . grad(phi)", "J/m^3",
                "max-normalized",
                "concentrates where strain drives potential (piezo)",
                "REFUSES to run without a solved potential field",
                "gauge choice affects phi but not grad(phi)",
                "DER (DV4-010)", "rscs2_core.piezo (IEEE 176)"),
    "D6": _spec("D6", "optical-path sensitivity",
                "|eps_pp(x)| along probe direction p (photoelastic "
                "kernel of RSCS2-E.9)", "strain (mode-normalized)",
                "max-normalized",
                "large where the probe crosses high axial strain — "
                "ordinary standing-wave structure",
                "probe direction must be declared",
                "path discretization aliasing", "DER (DV4-010)",
                "frozen rgcs_core.optics photoelastic model"),
    "D7": _spec("D7", "coil/drive-mode overlap density",
                "|b(x) . u_n(x)| for a declared drive pattern b",
                "N/m^3 * m (normalized)", "max-normalized",
                "reflects drive addressability, not specialness",
                "drive pattern must be declared",
                "uniform-b trivially mirrors D1 component",
                "DER (DV4-010)", "RSCS2-E.11 projection"),
    "D8": _spec("D8", "cross-modal overlap",
                "|u_i(x)||u_j(x)| for a near-degenerate mode pair",
                "m^2 (normalized)", "max-normalized",
                "large where two modes share amplitude — the coupled-"
                "two-mode interaction region (RGCS-M.24 language)",
                "needs >= 2 elastic modes; pair choice declared",
                "degenerate pairs mix arbitrarily (basis ambiguity)",
                "DER (DV4-010)", "frozen coupled-mode framework"),
    "D9": _spec("D9", "phase coherence",
                "local |mean(e^{i arg u})| over a neighborhood of a "
                "COMPLEX response field", "dimensionless [0,1]",
                "intrinsic [0,1]",
                "undamped real modes have global phase 0/pi: coherence "
                "trivially 1 (declared degenerate case) — only a "
                "damped/driven complex response is informative",
                "REFUSES real fields", "damping model changes phases",
                "DER (DV4-010)", "standard signal coherence"),
    "D10": _spec("D10", "phase singularity",
                 "2*pi winding of arg(w) on plaquettes of a plane "
                 "slice of a COMPLEX scalar field",
                 "integer winding per plaquette", "count",
                 "phase vortices in complex scalar fields are ordinary "
                 "wave phenomena, NOT evidence of a physical vortex",
                 "REFUSES real fields (mathematically invalid)",
                 "grid aliasing creates spurious +/- pairs",
                 "DER (DV4-010)", "Nye & Berry 1974 (standard)"),
    "D11": _spec("D11", "displacement vorticity/circulation",
                 "|curl u(x)| of the mode shape", "1/1 (normalized)",
                 "max-normalized",
                 "nonzero curl is ordinary in bending/torsion modes; "
                 "a plotted circulation is NOT a physical vortex "
                 "(frozen D6-003 exclusion)",
                 "requires displacement gradients", "coarse-mesh curl "
                 "noise", "DER (DV4-010)", "vector calculus"),
    "D12": _spec("D12", "electromagnetic circulation",
                 "loop circulation of a SOLVED EM field (e.g. the "
                 "RSCS2-E.10 Biot-Savart field)", "T*m", "raw",
                 "Ampere's law: circulation reflects enclosed current, "
                 "zero off-current loops — a null control",
                 "REFUSES to run without an explicitly solved field "
                 "(never inferred from geometry)", "discretization of "
                 "the loop integral", "DER (DV4-010)",
                 "Ampere's law (standard)"),
    "D13": _spec("D13", "boundary-condition sensitivity",
                 "candidate centroid shift across declared BC variants",
                 "mm", "compared to boundary_tol_mm",
                 "a real interior feature should not move when the "
                 "mounting changes", "needs >= 2 BC variants",
                 "all-variant artifacts pass this gate (limitation "
                 "declared)", "DER (DV4-010)", "sensitivity analysis"),
    "D14": _spec("D14", "mesh-refinement persistence",
                 "candidate centroid shift coarse -> refined",
                 "mm", "compared to persistence_tol_mm",
                 "artifacts (corner singularities, interpolation "
                 "hotspots) move or vanish under refinement",
                 "needs a refined solve", "two coarse meshes sharing "
                 "an artifact (use >= 2x refinement)",
                 "DER (DV4-010)", "FEM verification practice"),
    "D15": _spec("D15", "uncertainty persistence",
                 "candidate recurrence fraction and centroid cloud "
                 "over material/parameter perturbation draws",
                 "fraction [0,1]; cloud rms mm",
                 "compared to uncertainty_min_fraction",
                 "a feature that collapses under 1% material "
                 "uncertainty is not a stable claim",
                 "needs >= 3 draws", "correlated draws underestimate "
                 "spread", "DER (DV4-010)", "Monte-Carlo sensitivity"),
    "D16": _spec("D16", "cross-physics consensus",
                 "count of DISTINCT diagnostic families agreeing on a "
                 "region (elastic energy / optical / drive / piezo / "
                 "kinematic)", "count", "compared to min_agree",
                 "co-location of unrelated fields is the entire claim; "
                 "one field alone is never special",
                 "consensus is NOT averaging (documented procedure)",
                 "double-counting correlated diagnostics (D1/D3, "
                 "D1/uniform-D7) — families deduplicated",
                 "DER (DV4-010)", "this engine (documented procedure)"),
}

#: Diagnostic families for D16: members are correlated by construction
#: and count ONCE toward agreement (anti-double-counting).
_FAMILIES = {"D1": "kinematic", "D3": "kinematic", "D7": "kinematic",
             "D2": "elastic_energy", "D4": "elastic_energy",
             "D5": "piezo", "D6": "optical", "D8": "cross_modal",
             "D9": "phase", "D10": "phase", "D11": "rotational",
             "D12": "em"}

ALLOWED_STATUSES = ("STABLE_CANDIDATE_REGION", "MODE_SPECIFIC_CANDIDATE",
                    "BOUNDARY_SENSITIVE_CANDIDATE",
                    "CONVENTIONAL_NODE_EXPLAINS_RESULT",
                    "MESH_ARTIFACT_REJECTED", "NO_STABLE_CANDIDATE")


@dataclass
class DiagnosticField:
    """One evaluated diagnostic: values at points, max-normalized with
    the raw scale kept. mode_indices records which modes produced it
    (for the mode-dependence gate)."""
    diagnostic_id: str
    points_mm: np.ndarray          # (N, 3)
    values: np.ndarray             # (N,) normalized [0, 1]
    raw_max: float
    units: str
    mode_indices: tuple = ()
    note: str = ""

    def __post_init__(self):
        if self.diagnostic_id not in DIAGNOSTIC_SPECS:
            raise ValueError(f"unregistered diagnostic "
                             f"{self.diagnostic_id}")
        self.points_mm = np.atleast_2d(np.asarray(self.points_mm, float))
        self.values = np.asarray(self.values, float)
        if self.points_mm.shape[0] != self.values.shape[0]:
            raise ValueError("points/values length mismatch")


@dataclass
class Candidate:
    centroid_mm: np.ndarray
    bbox_mm: np.ndarray            # (2, 3) min/max corners
    score: float
    contributing: list = field(default_factory=list)
    families: list = field(default_factory=list)
    mode_indices: tuple = ()
    status: str = ""
    gates: dict = field(default_factory=dict)
    distances_mm: dict = field(default_factory=dict)
    uncertainty: dict = field(default_factory=dict)


@dataclass
class EyeConsensusResult:
    status: str
    candidates: list
    rejected: list
    procedure: dict
    null_comparison: dict

    def __post_init__(self):
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"status {self.status} not allowed")

    def to_json(self) -> str:
        def enc(o):
            if isinstance(o, np.ndarray):
                return o.tolist()
            if isinstance(o, (np.floating, np.integer)):
                return o.item()
            if isinstance(o, (Candidate,)):
                return o.__dict__
            return str(o)
        return json.dumps({"status": self.status,
                           "candidates": [c.__dict__ for c in
                                          self.candidates],
                           "rejected": self.rejected,
                           "procedure": self.procedure,
                           "null_comparison": self.null_comparison},
                          default=enc, indent=2)


# --- FEM field evaluators (D1-D4, D6-D8, D11) --------------------------

def _element_centroids_mm(mesh) -> np.ndarray:
    return np.mean(mesh.p[:, mesh.t], axis=1).T * 1000.0


def _mode_at_quadrature(problem, mode):
    """Interpolate a nodal mode to quadrature points: values (3, E, Q)
    and gradients (3, 3, E, Q)."""
    ifield = problem.basis.interpolate(mode)
    return np.asarray(ifield.value), np.asarray(ifield.grad)


def evaluate_elastic_diagnostics(problem, sol, mode_index: int,
                                 c_full_pa: np.ndarray,
                                 probe_direction=(0.0, 0.0, 1.0),
                                 drive_pattern=(1.0, 0.0, 0.0),
                                 pair_index: int | None = None
                                 ) -> dict[str, DiagnosticField]:
    """Evaluate the elastic-field diagnostics D1-D4, D6, D7, D11 (and
    D8 if pair_index is given) for one elastic mode, at element
    centroids. All values max-normalized with the raw scale recorded."""
    nr = sol["n_rigid_modes"]
    i = nr + mode_index
    mode = sol["modes"][:, i]
    f_hz = sol["frequencies_hz"][i]
    if f_hz < 1.0:
        raise ValueError("rigid mode passed to elastic diagnostics")
    pts = _element_centroids_mm(problem.mesh)
    u, g = _mode_at_quadrature(problem, mode)
    eps = 0.5 * (g + np.transpose(g, (1, 0, 2, 3)))
    sig = np.einsum("ijkl,kl...->ij...", np.asarray(c_full_pa), eps)

    def per_elem(x):
        return np.mean(x, axis=-1)               # average over quad pts

    out: dict[str, DiagnosticField] = {}

    def add(did, raw, units, note=""):
        v = per_elem(raw)
        m = float(np.max(v))
        out[did] = DiagnosticField(did, pts, v / m if m > 0 else v, m,
                                   units, (mode_index,), note)

    amp = np.sqrt(np.sum(u * u, axis=0))
    add("D1", amp, "m (mode-normalized)")
    add("D2", 0.5 * np.einsum("ij...,ij...->...", sig, eps), "J/m^3")
    w = 2 * math.pi * f_hz
    add("D3", 0.5 * problem.density_kg_m3 * w * w * amp ** 2, "J/m^3")
    dev = sig - (np.trace(sig) / 3.0) * np.eye(3)[:, :, None, None]
    add("D4", np.sqrt(1.5 * np.einsum("ij...,ij...->...", dev, dev)),
        "Pa")
    p = np.asarray(probe_direction, float)
    p = p / np.linalg.norm(p)
    add("D6", np.abs(np.einsum("i,ij...,j->...", p, eps, p)),
        "strain", note=f"probe direction {p.tolist()}")
    b = np.asarray(drive_pattern, float)
    add("D7", np.abs(np.einsum("i,i...->...", b, u)), "overlap",
        note=f"drive pattern {b.tolist()}")
    curl = np.stack([g[2, 1] - g[1, 2], g[0, 2] - g[2, 0],
                     g[1, 0] - g[0, 1]])
    add("D11", np.sqrt(np.sum(curl * curl, axis=0)), "1/1",
        note="plotted circulation is NOT a physical vortex (D6-003)")
    if pair_index is not None:
        u2, _ = _mode_at_quadrature(problem,
                                    sol["modes"][:, nr + pair_index])
        amp2 = np.sqrt(np.sum(u2 * u2, axis=0))
        v = per_elem(amp * amp2)
        m = float(np.max(v))
        out["D8"] = DiagnosticField(
            "D8", pts, v / m if m > 0 else v, m, "m^2",
            (mode_index, pair_index),
            note=f"pair ({mode_index},{pair_index})")
    return out


def electric_energy_density_field(p_basis, phi: np.ndarray | None,
                                  eps_diel_f_m: np.ndarray
                                  ) -> DiagnosticField:
    """D5: electric-energy density w_e = 1/2 grad(phi).eps.grad(phi)
    from a SOLVED potential (rscs2_core.piezo). REFUSES to run without
    one — the eye engine never invents an electric field."""
    if phi is None:
        raise ValueError("D5 requires a SOLVED potential field "
                         "(rscs2_core.piezo); it is never inferred")
    g = np.asarray(p_basis.interpolate(np.asarray(phi, float)).grad)
    we = 0.5 * np.einsum("i...,ij,j...->...", g,
                         np.asarray(eps_diel_f_m, float), g)
    v = np.mean(we, axis=-1)
    pts = _element_centroids_mm(p_basis.mesh)
    m = float(np.max(v))
    return DiagnosticField("D5", pts, v / m if m > 0 else v, m, "J/m^3")


# --- complex-field diagnostics (D9, D10) and EM (D12) ------------------

def phase_coherence_field(points_mm: np.ndarray,
                          complex_values: np.ndarray,
                          radius_mm: float) -> DiagnosticField:
    """D9: local phase coherence |<e^{i arg w}>| over a neighborhood.
    REFUSES real input — an undamped real mode has trivial coherence
    (declared degenerate case in the spec)."""
    w = np.asarray(complex_values)
    if not np.iscomplexobj(w) or np.allclose(w.imag, 0.0):
        raise ValueError("D9 requires a genuinely COMPLEX field "
                         "(damped/driven response); real modes are the "
                         "declared degenerate case")
    pts = np.atleast_2d(np.asarray(points_mm, float))
    ph = np.exp(1j * np.angle(w))
    coh = np.zeros(len(pts))
    for k in range(len(pts)):
        d = np.linalg.norm(pts - pts[k], axis=1)
        nbr = ph[d <= radius_mm]
        coh[k] = np.abs(np.mean(nbr))
    return DiagnosticField("D9", pts, coh, 1.0, "dimensionless")


def phase_singularities_on_plane(grid_x_mm: np.ndarray,
                                 grid_z_mm: np.ndarray,
                                 complex_grid: np.ndarray) -> dict:
    """D10: plaquette winding numbers of arg(w) on a plane slice.
    Returns singular plaquette centers and their charges. REFUSES real
    input (winding of a real field is mathematically invalid)."""
    w = np.asarray(complex_grid)
    if not np.iscomplexobj(w) or np.allclose(w.imag, 0.0):
        raise ValueError("D10 requires a COMPLEX scalar field")
    ph = np.angle(w)

    def dwrap(a):
        return (a + np.pi) % (2 * np.pi) - np.pi
    # plaquette circulation, counterclockwise in (x, z): +x, +z, -x, -z
    # (rows index z, columns index x)
    circ = (dwrap(ph[:-1, 1:] - ph[:-1, :-1])
            + dwrap(ph[1:, 1:] - ph[:-1, 1:])
            + dwrap(ph[1:, :-1] - ph[1:, 1:])
            + dwrap(ph[:-1, :-1] - ph[1:, :-1]))
    charge = np.round(circ / (2 * np.pi)).astype(int)
    iy, ix = np.nonzero(charge)
    xs = 0.5 * (grid_x_mm[ix] + grid_x_mm[ix + 1])
    zs = 0.5 * (grid_z_mm[iy] + grid_z_mm[iy + 1])
    return {"singularities_mm": np.stack([xs, zs], axis=1),
            "charges": charge[iy, ix],
            "note": "phase vortices are ordinary wave phenomena, not "
                    "physical vortices (D6-003 exclusion)"}


def em_circulation(field_fn: Callable[[np.ndarray], np.ndarray] | None,
                   loop_points_m: np.ndarray) -> dict:
    """D12: circulation of a SOLVED EM field around a closed loop.
    REFUSES to run without an explicit field (never inferred)."""
    if field_fn is None:
        raise ValueError("D12 requires an explicitly SOLVED EM field "
                         "(e.g. RSCS2-E.10 Biot-Savart); it is never "
                         "inferred from geometry")
    lp = np.atleast_2d(np.asarray(loop_points_m, float))
    if not np.allclose(lp[0], lp[-1]):
        lp = np.vstack([lp, lp[0]])
    B = field_fn(lp)
    dl = np.diff(lp, axis=0)
    mid = 0.5 * (B[1:] + B[:-1])
    return {"circulation_t_m": float(np.sum(mid * dl)),
            "n_segments": len(dl)}


# --- candidate extraction ----------------------------------------------

def extract_candidates(fld: DiagnosticField, quantile: float = 0.95,
                       link_radius_mm: float = 5.0,
                       min_points: int = 3) -> list[dict]:
    """Top-quantile clustering of one diagnostic field into candidate
    REGIONS. Greedy union-find linkage of above-threshold points within
    link_radius. Score = cluster share of above-threshold field mass."""
    thr = np.quantile(fld.values, quantile)
    idx = np.nonzero(fld.values >= thr)[0]
    if len(idx) == 0:
        return []
    pts = fld.points_mm[idx]
    vals = fld.values[idx]
    parent = np.arange(len(idx))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a in range(len(idx)):
        d = np.linalg.norm(pts - pts[a], axis=1)
        for b in np.nonzero(d <= link_radius_mm)[0]:
            ra, rb = find(a), find(int(b))
            if ra != rb:
                parent[rb] = ra
    roots = np.array([find(a) for a in range(len(idx))])
    total = float(np.sum(vals))
    out = []
    for r in np.unique(roots):
        m = roots == r
        if np.sum(m) < min_points:
            continue
        w = vals[m]
        c = np.average(pts[m], axis=0, weights=w)
        out.append({"diagnostic_id": fld.diagnostic_id,
                    "centroid_mm": c,
                    "bbox_mm": np.stack([pts[m].min(0), pts[m].max(0)]),
                    "score": float(np.sum(w) / total),
                    "n_points": int(np.sum(m)),
                    "mode_indices": fld.mode_indices})
    return sorted(out, key=lambda d: -d["score"])


# --- consensus ----------------------------------------------------------

def _cluster_across(cands: list[dict], link_radius_mm: float):
    """Union-find on per-diagnostic candidate centroids."""
    n = len(cands)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a in range(n):
        for b in range(a + 1, n):
            if np.linalg.norm(cands[a]["centroid_mm"]
                              - cands[b]["centroid_mm"]) <= link_radius_mm:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[rb] = ra
    groups: dict[int, list] = {}
    for a in range(n):
        groups.setdefault(find(a), []).append(cands[a])
    return list(groups.values())


def _match(centroid, cand_list, tol_mm):
    """Nearest candidate within tol, else None."""
    best, bd = None, np.inf
    for c in cand_list:
        d = np.linalg.norm(np.asarray(c["centroid_mm"]) - centroid)
        if d < bd:
            best, bd = c, d
    return (best, bd) if bd <= tol_mm else (None, bd)


def eye_consensus(fields: list[DiagnosticField],
                  geometry: dict,
                  refined_fields: list[DiagnosticField] | None = None,
                  boundary_fields: dict[str, list[DiagnosticField]]
                  | None = None,
                  uncertainty_fields: list[list[DiagnosticField]]
                  | None = None,
                  quantile: float = 0.95,
                  link_radius_mm: float = 5.0,
                  min_agree_families: int = 3,
                  persistence_tol_mm: float = 5.0,
                  boundary_tol_mm: float = 5.0,
                  node_tol_mm: float = 3.0,
                  uncertainty_min_fraction: float = 0.6,
                  min_modes: int = 2,
                  max_extent_fraction: float = 0.35) -> EyeConsensusResult:
    """Documented multi-criterion consensus (RSCS2-D.16).

    geometry dict keys:
      length_mm, inside_fn(points (N,3) mm -> bool array),
      geometric_centre_mm (3,), shaft_midpoint_mm (3,),
      node_prior_mm (3,), conventional_features_mm (F,3)
      (ordinary node/antinode locations of the modes examined).

    Gate order (each recorded, never averaged):
      1. per-diagnostic candidate extraction (top-quantile regions);
      2. cross-diagnostic clustering; agreement counted over
         DEDUPLICATED diagnostic FAMILIES (anti-double-counting);
      2b. localization: the merged region's bbox diagonal must not
          exceed max_extent_fraction of the body length (a flat or
          body-spanning field is NOT an interaction region);
      3. inside-body validity;
      4. null comparison vs conventional node/antinode locations;
      5. mesh persistence (D14) against refined_fields;
      6. boundary sensitivity (D13) across boundary_fields variants;
      7. mode dependence (>= min_modes distinct modes);
      8. uncertainty persistence (D15) across draws.
    """
    procedure = {
        "quantile": quantile, "link_radius_mm": link_radius_mm,
        "min_agree_families": min_agree_families,
        "persistence_tol_mm": persistence_tol_mm,
        "boundary_tol_mm": boundary_tol_mm, "node_tol_mm": node_tol_mm,
        "uncertainty_min_fraction": uncertainty_min_fraction,
        "min_modes": min_modes,
        "max_extent_fraction": max_extent_fraction,
        "note": "gates are sequential pass/fail checks; consensus is "
                "NOT an average of normalized fields",
    }
    per_diag = []
    for f in fields:
        per_diag.extend(extract_candidates(f, quantile, link_radius_mm))
    rejected: list[dict] = []
    groups = _cluster_across(per_diag, link_radius_mm)
    candidates: list[Candidate] = []
    conv = np.atleast_2d(np.asarray(
        geometry.get("conventional_features_mm", np.empty((0, 3)))))

    def refined_cands():
        out = []
        for f in (refined_fields or []):
            out.extend(extract_candidates(f, quantile, link_radius_mm))
        return out

    rc = refined_cands() if refined_fields is not None else None
    bc = {name: [c for f in flds for c in
                 extract_candidates(f, quantile, link_radius_mm)]
          for name, flds in (boundary_fields or {}).items()}
    uc = [[c for f in flds for c in
           extract_candidates(f, quantile, link_radius_mm)]
          for flds in (uncertainty_fields or [])]

    for grp in groups:
        diags = sorted({c["diagnostic_id"] for c in grp})
        fams = sorted({_FAMILIES.get(d, d) for d in diags})
        w = np.array([c["score"] for c in grp])
        cen = np.average(np.stack([c["centroid_mm"] for c in grp]),
                         axis=0, weights=w)
        bbox = np.stack([np.min(np.stack([c["bbox_mm"][0] for c in grp]),
                                axis=0),
                         np.max(np.stack([c["bbox_mm"][1] for c in grp]),
                                axis=0)])
        modes = tuple(sorted({m for c in grp
                              for m in c["mode_indices"]}))
        cand = Candidate(cen, bbox, float(np.mean(w)), diags, fams,
                         modes)
        # distances to the declared references
        for key in ("geometric_centre_mm", "shaft_midpoint_mm",
                    "node_prior_mm"):
            if key in geometry:
                cand.distances_mm[key] = float(np.linalg.norm(
                    cen - np.asarray(geometry[key], float)))
        if len(conv):
            dmin = float(np.min(np.linalg.norm(conv - cen, axis=1)))
            cand.distances_mm["nearest_conventional_feature"] = dmin

        # gate 2: family agreement
        cand.gates["agreement_families"] = len(fams)
        if len(fams) < min_agree_families:
            rejected.append({"centroid_mm": cen.tolist(),
                             "reason": "insufficient diagnostic-family "
                                       f"agreement ({len(fams)} < "
                                       f"{min_agree_families})",
                             "diagnostics": diags})
            continue
        # gate 2b: localization (a body-spanning field is not a region)
        extent = float(np.linalg.norm(bbox[1] - bbox[0]))
        cand.gates["extent_mm"] = extent
        if extent > max_extent_fraction * geometry["length_mm"]:
            rejected.append({"centroid_mm": cen.tolist(),
                             "reason": "not localized: extent "
                                       f"{extent:.1f} mm > "
                                       f"{max_extent_fraction:.2f} x "
                                       "body length",
                             "diagnostics": diags})
            continue
        # gate 3: inside body
        inside = bool(np.all(geometry["inside_fn"](cen[None, :])))
        cand.gates["inside_body"] = inside
        if not inside:
            rejected.append({"centroid_mm": cen.tolist(),
                             "reason": "candidate centroid outside the "
                                       "body (invalid)",
                             "diagnostics": diags})
            continue
        # gate 4: null comparison
        d_conv = cand.distances_mm.get("nearest_conventional_feature",
                                       np.inf)
        cand.gates["null_comparison_mm"] = d_conv
        if d_conv <= node_tol_mm:
            cand.status = "CONVENTIONAL_NODE_EXPLAINS_RESULT"
            candidates.append(cand)
            continue
        # gate 5: mesh persistence (D14)
        if rc is not None:
            m, dist = _match(cen, rc, persistence_tol_mm)
            cand.gates["mesh_persistence_shift_mm"] = float(dist)
            if m is None:
                cand.status = "MESH_ARTIFACT_REJECTED"
                candidates.append(cand)
                continue
        # gate 6: boundary sensitivity (D13)
        if bc:
            shifts = {}
            stable = True
            for name, lst in bc.items():
                m, dist = _match(cen, lst, boundary_tol_mm)
                shifts[name] = float(dist)
                stable &= m is not None
            cand.gates["boundary_shifts_mm"] = shifts
            if not stable:
                cand.status = "BOUNDARY_SENSITIVE_CANDIDATE"
                candidates.append(cand)
                continue
        # gate 7: mode dependence
        cand.gates["n_modes"] = len(modes)
        if len(modes) < min_modes:
            cand.status = "MODE_SPECIFIC_CANDIDATE"
            candidates.append(cand)
            continue
        # gate 8: uncertainty persistence (D15)
        if uc:
            hits, cloud = 0, []
            for lst in uc:
                m, _ = _match(cen, lst, persistence_tol_mm)
                if m is not None:
                    hits += 1
                    cloud.append(np.asarray(m["centroid_mm"]))
            frac = hits / len(uc)
            cand.uncertainty = {
                "recurrence_fraction": frac,
                "n_draws": len(uc),
                "cloud_mm": [c.tolist() for c in cloud],
                "cloud_rms_mm": (float(np.sqrt(np.mean(np.sum(
                    (np.stack(cloud) - cen) ** 2, axis=1))))
                    if cloud else None),
            }
            cand.gates["uncertainty_fraction"] = frac
            if frac < uncertainty_min_fraction:
                rejected.append({"centroid_mm": cen.tolist(),
                                 "reason": "collapsed under parameter "
                                           f"uncertainty (recurrence "
                                           f"{frac:.2f} < "
                                           f"{uncertainty_min_fraction})",
                                 "diagnostics": diags})
                continue
        cand.status = "STABLE_CANDIDATE_REGION"
        candidates.append(cand)

    candidates.sort(key=lambda c: -c.score)
    null_cmp = {"conventional_features_mm": conv.tolist(),
                "node_tol_mm": node_tol_mm}
    stable = [c for c in candidates
              if c.status == "STABLE_CANDIDATE_REGION"]
    if stable:
        status = "STABLE_CANDIDATE_REGION"
        procedure["competing_candidates"] = len(stable) > 1
    elif candidates:
        # most informative surviving classification, by gate order
        order = ["CONVENTIONAL_NODE_EXPLAINS_RESULT",
                 "MESH_ARTIFACT_REJECTED",
                 "BOUNDARY_SENSITIVE_CANDIDATE",
                 "MODE_SPECIFIC_CANDIDATE"]
        status = sorted((c.status for c in candidates),
                        key=order.index)[0]
    else:
        status = "NO_STABLE_CANDIDATE"
    return EyeConsensusResult(status, candidates, rejected, procedure,
                              null_cmp)
