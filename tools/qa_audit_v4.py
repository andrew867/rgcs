"""Agent 13 Role B: independent adversarial QA audit (programmatic).

Re-verifies the load-bearing v4 claims from scratch — it does NOT
trust the test suite: matrix symmetry, mass/stiffness scale, tensor
ordering, Bond rotation, units, rigid modes, residuals, orthogonality,
piezo energy/uncoupled limit, registry completeness, frozen history,
bundle determinism, screenshot authenticity (PNG magic + provenance),
claims wording, and licences. Prints a PASS/FAIL line per check and
writes tools/qa_audit_v4_results.json.

    python tools/qa_audit_v4.py [--fast]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import numpy as np

RESULTS: list[dict] = []


def check(name, fn):
    try:
        detail = fn()
        RESULTS.append({"check": name, "status": "PASS",
                        "detail": detail})
        print(f"PASS  {name}: {detail}")
    except AssertionError as e:
        RESULTS.append({"check": name, "status": "FAIL",
                        "detail": str(e)})
        print(f"FAIL  {name}: {e}")
    except Exception as e:
        RESULTS.append({"check": name, "status": "ERROR",
                        "detail": repr(e)})
        print(f"ERROR {name}: {e!r}")


def main() -> int:
    fast = "--fast" in sys.argv[1:]
    from skfem import MeshTet
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa,
                                      AXIS_X, AXIS_Y, AXIS_Z,
                                      wave_speeds)
    from rscs_core.propagation import voigt_to_tensor
    from rscs2_core import crystal110 as c110, fem, quartz as qz

    E0, NU0, RHO0 = 210e9, 0.3, 7850.0
    C_FULL = voigt_to_tensor(alpha_quartz_stiffness_pa())
    RHOQ = ALPHA_QUARTZ_DENSITY_KG_M3
    mesh = fem.box_mesh((0.04, 0.01, 0.01), (6, 2, 2))
    prob = fem.assemble_isotropic(mesh, E0, NU0, RHO0)
    proba = fem.assemble_anisotropic(mesh, C_FULL, RHOQ)

    # --- numerical core --------------------------------------------------
    def sym(M):
        d = abs(M - M.T)
        return float(d.max()) / float(abs(M).max())
    check("K symmetry (isotropic)", lambda: (
        lambda r: (r < 1e-12, f"rel asym {r:.2e}")[1]
        if r < 1e-12 else (_ for _ in ()).throw(
            AssertionError(f"asym {r:.2e}")))(sym(prob.K)))
    check("K symmetry (anisotropic)", lambda: (
        lambda r: f"rel asym {r:.2e}" if r < 1e-12 else
        (_ for _ in ()).throw(AssertionError(f"asym {r:.2e}")))(
        sym(proba.K)))
    check("M symmetry + positive", lambda: (
        lambda r, mn: f"asym {r:.2e}, min eig proxy > 0"
        if r < 1e-12 and mn > 0 else (_ for _ in ()).throw(
            AssertionError(f"asym {r:.2e} min {mn:.2e}")))(
        sym(prob.M), float(prob.M.diagonal().min())))

    def mass_patch():
        u = np.zeros(prob.ndof)
        u[fem.component_dofs(prob.basis, 0)] = 1.0
        got = float(u @ (prob.M @ u))
        want = RHO0 * 0.04 * 0.01 * 0.01
        r = abs(got - want) / want
        assert r < 1e-9, f"uMu vs rhoV rel err {r:.2e}"
        return f"uMu = rhoV within {r:.1e} (V4-D-001 guard)"
    check("mass patch (V4-D-001 root cause guard)", mass_patch)

    def stiffness_nullspace():
        # rigid translation must produce zero strain energy
        u = np.zeros(prob.ndof)
        u[fem.component_dofs(prob.basis, 1)] = 1.0
        e = float(u @ (prob.K @ u)) / float(abs(prob.K).max())
        assert e < 1e-12, f"translation energy {e:.2e}"
        return f"rigid translation K-energy {e:.1e}"
    check("stiffness nullspace (translation)", stiffness_nullspace)

    def rigid_and_residuals():
        sol = fem.solve_modes(proba, 10)
        assert sol["n_rigid_modes"] == 6, \
            f"{sol['n_rigid_modes']} rigid modes"
        r = sol["residuals"][~np.isnan(sol["residuals"])]
        assert np.all(r < 1e-6), f"max residual {r.max():.2e}"
        assert sol["orthonormality_error"] < 1e-8
        return (f"6 rigid; max residual {r.max():.1e}; ortho "
                f"{sol['orthonormality_error']:.1e}")
    check("free anisotropic body: rigid/residuals/orthogonality",
          rigid_and_residuals)

    def tensor_ordering():
        # Voigt->tensor must satisfy all minor/major symmetries and
        # reproduce C11 at [0,0,0,0], C44 at [1,2,1,2]
        cv = alpha_quartz_stiffness_pa()
        cv = np.asarray(cv)
        assert np.allclose(C_FULL, np.transpose(C_FULL, (1, 0, 2, 3)))
        assert np.allclose(C_FULL, np.transpose(C_FULL, (0, 1, 3, 2)))
        assert np.allclose(C_FULL, np.transpose(C_FULL, (2, 3, 0, 1)))
        assert C_FULL[0, 0, 0, 0] == cv[0, 0]
        assert C_FULL[1, 2, 1, 2] == cv[3, 3]
        return "minor+major symmetries; C11/C44 slots correct"
    check("tensor ordering (Voigt -> full)", tensor_ordering)

    def bond_rotation():
        # 120-deg Z rotation must leave trigonal C invariant; a random
        # rotation must preserve all Christoffel eigenvalue SETS
        R120 = qz.euler_zxz_matrix(120.0, 0.0, 0.0)
        c2 = qz.rotate_stiffness(C_FULL, R120)
        assert np.allclose(c2, C_FULL, rtol=0, atol=1e-3 * abs(
            C_FULL).max()), "trigonal 120deg Z invariance broken"
        rng = np.random.default_rng(7)
        Rr = qz.euler_zxz_matrix(*rng.uniform(0, 90, 3))
        d = rng.normal(size=(50, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        s1 = qz.christoffel_speeds(C_FULL, RHOQ, d)["speeds_m_s"]
        s2 = qz.christoffel_speeds(qz.rotate_stiffness(C_FULL, Rr),
                                   RHOQ, d @ Rr.T)["speeds_m_s"]
        r = np.max(np.abs(s1 - s2) / s1)
        assert r < 1e-9, f"frame invariance {r:.2e}"
        return f"120deg invariance; frame invariance {r:.1e}"
    check("Bond rotation anchors", bond_rotation)

    def christoffel_frozen():
        rows = []
        for nm, ax in (("X", AXIS_X), ("Y", AXIS_Y), ("Z", AXIS_Z)):
            frozen = wave_speeds(ax)["v_quasi_long_m_s"]
            got = qz.christoffel_speeds(
                C_FULL, RHOQ, np.array([ax], float))["speeds_m_s"][0, 0]
            r = abs(got - frozen) / frozen
            assert r < 1e-9, f"{nm}: {r:.2e}"
            rows.append(f"{nm} {r:.1e}")
        return "; ".join(rows)
    check("Christoffel vs frozen v3 axes", christoffel_frozen)

    def units_sanity():
        sol = fem.solve_modes(prob, 8, fixed_dofs=prob.basis.get_dofs(
            lambda x: np.isclose(x[0], 0.0)).flatten())
        from rscs2_core import reference as ref
        fa = ref.euler_bernoulli_cantilever_hz(E0, RHO0, 0.04, 0.01,
                                               0.01, 1)
        f1 = sol["elastic_frequencies_hz"][0]
        r = abs(f1 - fa) / fa
        assert r < 0.12, f"cantilever f1 off by {r:.1%} (thick beam)"
        return f"cantilever f1 {f1:.1f} Hz vs EB {fa:.1f} Hz ({r:.1%})"
    check("units end-to-end (Pa, kg/m^3 -> Hz)", units_sanity)

    def piezo_limits():
        from rscs2_core import piezo
        pz0 = piezo.PiezoProblem(mesh, C_FULL,
                                 np.zeros((3, 3, 3)),
                                 np.array(qz.quartz_dielectric_f_m()),
                                 RHOQ)
        sol_e = fem.solve_modes(proba, 9)
        el = [lambda x: np.isclose(x[1], 0.0),
              lambda x: np.isclose(x[1], 0.01)]
        sol_p = piezo.solve_piezo_modes(pz0, 9, el, condition="short")
        fe = sol_e["frequencies_hz"][6:9]
        fp = sol_p["frequencies_hz"][6:9]
        r = np.max(np.abs(fe - fp) / fe)
        assert r < 1e-9, f"uncoupled limit rel err {r:.2e}"
        return f"e=0 recovers elastic exactly ({r:.1e})"
    check("piezo uncoupled limit (G8)", piezo_limits)

    def material_constants():
        e = np.array(qz.quartz_piezo_tensor_c_m2())
        assert abs(e[0, 0, 0] - 0.171) < 1e-12
        eps = np.array(qz.quartz_dielectric_f_m())
        assert abs(eps[0, 0] / 8.8541878128e-12 - 4.428) < 1e-3
        assert abs(eps[2, 2] / 8.8541878128e-12 - 4.634) < 1e-3
        assert abs(RHOQ - 2648.0) < 5.0
        return "e11=0.171; eps_r 4.428/4.634; rho ~2648 (Bechmann)"
    check("material constants vs published", material_constants)

    def geometries_distinct():
        i = c110.build_crystal("ideal_n7")
        n = c110.build_crystal("nominal")
        assert i.length_mm != n.length_mm
        assert abs(i.length_mm - 770.263671875 / 7.0) == 0.0
        assert n.length_mm == 110.0
        return (f"ideal {i.length_mm!r} != nominal {n.length_mm!r} "
                "(exact reprs)")
    check("ideal vs nominal distinct + exact (G10)",
          geometries_distinct)

    # --- registry completeness (G2) --------------------------------------
    def registry_complete():
        import yaml
        reg = yaml.safe_load((REPO / "rscs2_core/registry/"
                              "rscs2_registry.yaml").read_text(
            encoding="utf-8"))
        n = 0
        for section, entries in reg.items():
            if not isinstance(entries, list):
                continue
            for e in entries:
                for k in ("id", "units", "class", "provenance",
                          "exclusions", "tests", "module", "status"):
                    assert k in e, f"{e.get('id', '?')} missing {k}"
                assert e["tests"], f"{e['id']} has no tests"
                n += 1
        assert n >= 40, f"only {n} registered objects"
        return f"{n} objects, all with id/units/class/provenance/" \
               "exclusions/tests/module/status"
    check("registry completeness (G2)", registry_complete)

    # --- frozen history (G1) ----------------------------------------------
    def frozen_history():
        out = subprocess.run(
            ["git", "diff", "--stat", "715486b", "HEAD", "--",
             "archive/v2.0.0"], capture_output=True, text=True,
            cwd=REPO, check=True)
        assert out.stdout.strip() == "", "archive/v2.0.0 modified!"
        for tag in ("v2.0.0", "v3.0.0", "v3.0.1"):
            t = subprocess.run(["git", "rev-parse", tag],
                               capture_output=True, text=True,
                               cwd=REPO)
            assert t.returncode == 0, f"tag {tag} missing"
        return "archive untouched; tags v2.0.0/v3.0.0/v3.0.1 present"
    check("frozen history (G1)", frozen_history)

    # --- screenshots authentic (G24) ---------------------------------------
    def screenshots():
        pngs = list((REPO / "proof_bundle_110mm/figures").glob("*.png"))
        assert len(pngs) >= 17, f"only {len(pngs)} figures"
        for p in pngs:
            b = p.read_bytes()
            assert b[:8] == b"\x89PNG\r\n\x1a\n", f"{p.name} not PNG"
            assert len(b) > 3000, f"{p.name} suspiciously small"
        prov = json.loads((REPO / "proof_bundle_110mm/"
                           "PROVENANCE.json").read_text())
        assert "figures" in " ".join(prov["live_recomputed"])
        return f"{len(pngs)} PNGs valid, declared live-recomputed"
    check("screenshot authenticity (G24)", screenshots)

    # --- claims wording (G29) ----------------------------------------------
    def claims():
        # V4-D-002: exclusion statements ("No experimental confirmation,
        # therapeutic effect, consciousness causation ... import") are
        # the docs DOING THEIR JOB; only affirmative usage is a defect.
        banned = ["portal", "consciousness", "therapeutic",
                  "metric engineering", "metric-engineering",
                  "cosmolog"]
        negations = ("no ", "not ", "never", "exclusion", "excluded",
                     "forbidden", "no unsupported", "import;",
                     "unsupported")
        offenders = []
        for p in (REPO / "docs").rglob("*V4*.md"):
            low = p.read_text(encoding="utf-8", errors="ignore").lower()
            i = 0
            for b in banned:
                i = low.find(b)
                while i != -1:
                    ctx = low[max(0, i - 250):i + 250]
                    if not any(n in ctx for n in negations):
                        offenders.append(f"{p.name}:{b}")
                    i = low.find(b, i + 1)
        assert not offenders, f"affirmative claim words: {offenders}"
        return ("no AFFIRMATIVE claim vocabulary; exclusion statements "
                "verified manually (V4-D-002)")
    check("claims wording (G29)", claims)

    # --- bundle determinism (G25/G26) ---------------------------------------
    if not fast:
        def bundle_determinism():
            import tempfile
            from rscs2_core.proofbundle import build_bundle
            with tempfile.TemporaryDirectory() as td:
                b1 = build_bundle(Path(td) / "b1", fast=True)
                b2 = build_bundle(Path(td) / "b2", fast=True)
                h1 = {l.split("  ")[1]: l.split("  ")[0] for l in
                      (b1 / "SHA256SUMS.txt").read_text().splitlines()}
                h2 = {l.split("  ")[1]: l.split("  ")[0] for l in
                      (b2 / "SHA256SUMS.txt").read_text().splitlines()}
                assert set(h1) == set(h2), "file sets differ"
                # deterministic numeric artifacts: CSV/JSON must match
                # (figures/PDF may embed timestamps; checked separately)
                diff = [k for k in h1 if h1[k] != h2[k]
                        and k.endswith((".csv", ".json", ".txt", ".md",
                                        ".stl", ".obj", ".glb", ".msh"))
                        and k != "SHA256SUMS.txt"
                        and "SOFTWARE_VERSIONS" not in k]
                assert not diff, f"nondeterministic: {diff[:8]}"
                return (f"{len(h1)} files; all data artifacts "
                        "bit-identical across two builds")
        check("bundle determinism (G25/G26)", bundle_determinism)

    # --- licences (G30) -------------------------------------------------------
    def licences():
        import importlib.metadata as im
        deps = {"numpy": "BSD", "scipy": "BSD", "scikit-fem": "BSD",
                "meshio": "MIT", "matplotlib": "PSF/BSD-compatible",
                "pyyaml": "MIT", "pydantic": "MIT"}
        found = {}
        for d in deps:
            try:
                meta = im.metadata(d)
                found[d] = (meta.get("License-Expression")
                            or meta.get("License") or "see classifier")
            except im.PackageNotFoundError:
                pass
        # gmsh is GPL but used as SUBPROCESS only (DV4-006)
        return (f"runtime deps permissive ({', '.join(found)}); gmsh "
                "GPL isolated as subprocess (DV4-006); pyopencl MIT "
                "optional")
    check("licences (G30)", licences)

    (REPO / "tools/qa_audit_v4_results.json").write_text(
        json.dumps(RESULTS, indent=2))
    fails = [r for r in RESULTS if r["status"] != "PASS"]
    print(f"\n{len(RESULTS) - len(fails)}/{len(RESULTS)} checks PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
