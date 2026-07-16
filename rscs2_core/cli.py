"""rgcs-v4 command-line interface (Agent 12).

Makes the v4 work reproducible by another user:

    python -m rscs2_core.cli <command> [options]
    rgcs-v4 <command> [options]           (installed entry point)

Commands: devices, geometry, mesh, material, modes, sweep, piezo,
optical, coil, diagnostics, refsystems, proof-bundle, report,
verify-checksums. Every command prints JSON/CSV to stdout or writes
the named files — no hidden state; CPU float64 remains the numerical
authority (DV4-004) and no backend is silently substituted (DV4-007).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def _pj(obj):
    def enc(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        return str(o)
    print(json.dumps(obj, indent=2, default=enc, sort_keys=True))


def cmd_devices(args):
    from . import accel
    _pj(accel.capability_report())
    return 0


def cmd_geometry(args):
    from . import crystal110 as c110
    _pj(c110.build_crystal(args.variant).record())
    return 0


def cmd_mesh(args):
    from . import crystal110 as c110
    out = c110.mesh_crystal(c110.build_crystal(args.variant),
                            args.clmax, workdir=args.workdir)
    _pj(out["manifest"])
    return 0


def cmd_material(args):
    from . import quartz as qz
    _pj(qz.material_record())
    return 0


def _crystal_problem(variant, clmax, workdir):
    from skfem import MeshTet
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa)
    from rscs_core.propagation import voigt_to_tensor
    from . import crystal110 as c110, fem
    c = c110.build_crystal(variant)
    m = c110.mesh_crystal(c, clmax, workdir=workdir)
    C_FULL = voigt_to_tensor(alpha_quartz_stiffness_pa())
    prob = fem.assemble_anisotropic(
        MeshTet(m["nodes_m"].T, m["tets"].T), C_FULL,
        ALPHA_QUARTZ_DENSITY_KG_M3)
    return c, m, prob, C_FULL, ALPHA_QUARTZ_DENSITY_KG_M3


def cmd_modes(args):
    from . import fem
    c, m, prob, _, _ = _crystal_problem(args.variant, args.clmax,
                                        args.workdir)
    sol = fem.solve_modes(prob, args.n)
    print("mode,frequency_hz,is_rigid,residual")
    for k, f in enumerate(sol["frequencies_hz"]):
        r = sol["residuals"][k]
        print(f"{k + 1},{f:.6f},{f < 1.0},"
              f"{r:.3e}" if np.isfinite(r) else
              f"{k + 1},{f:.6f},{f < 1.0},nan(rigid)")
    print(f"# orthonormality_error={sol['orthonormality_error']:.3e} "
          f"ndof={sol['ndof']}", file=sys.stderr)
    return 0


def cmd_sweep(args):
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa)
    from rscs_core.propagation import voigt_to_tensor
    from . import accel
    C = voigt_to_tensor(alpha_quartz_stiffness_pa())
    rng = np.random.default_rng(args.seed)
    d = rng.normal(size=(args.n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    out = accel.sweep(C, ALPHA_QUARTZ_DENSITY_KG_M3, d,
                      backend=args.backend, device=args.device)
    meta = {k: v for k, v in out.items() if k != "speeds_m_s"}
    meta["backend"] = args.backend
    meta["speeds_minmax_m_s"] = [float(out["speeds_m_s"].min()),
                                 float(out["speeds_m_s"].max())]
    _pj(meta)
    return 0


def cmd_piezo(args):
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa)
    from rscs_core.propagation import voigt_to_tensor
    from skfem import MeshTet
    from . import crystal110 as c110, piezo, quartz as qz
    c = c110.build_crystal(args.variant)
    m = c110.mesh_crystal(c, args.clmax, workdir=args.workdir)
    pz = piezo.PiezoProblem(
        MeshTet(m["nodes_m"].T, m["tets"].T),
        voigt_to_tensor(alpha_quartz_stiffness_pa()),
        np.array(qz.quartz_piezo_tensor_c_m2()),
        np.array(qz.quartz_dielectric_f_m()),
        ALPHA_QUARTZ_DENSITY_KG_M3)
    L = c.length_mm * 1e-3
    els = [lambda x: (x[0] > 0) & (x[2] > 0.35 * L) & (x[2] < 0.65 * L),
           lambda x: (x[0] < 0) & (x[2] > 0.35 * L) & (x[2] < 0.65 * L)]
    sol = piezo.solve_piezo_modes(pz, args.n, els,
                                  condition=args.condition)
    print("mode,frequency_hz")
    for k, f in enumerate(sol["frequencies_hz"]):
        print(f"{k + 1},{f:.6f}")
    return 0


def cmd_optical(args):
    from . import crystal110 as c110, projections as pj
    pp = pj.probe_paths(c110.build_crystal(args.variant),
                        wavelength_nm=args.wavelength)
    _pj({"wavelength_nm": pp["wavelength_nm"], "n_o": pp["n_o"],
         "paths": {k: {kk: vv for kk, vv in v.items()}
                   for k, v in pp["paths"].items()}})
    return 0


def cmd_coil(args):
    from . import projections as pj
    zg = np.linspace(-args.zmax, args.zmax, args.points)
    pts = np.stack([np.zeros_like(zg), np.zeros_like(zg), zg], 1)
    out = pj.coil_pair_field(pts, args.radius, args.separation,
                             args.current, mode=args.mode,
                             counter_wound=not args.same_wound)
    print("z_m,Bz_re_T,Bz_im_T")
    for z, b in zip(zg, out["phasor_t"][:, 2]):
        print(f"{z:.5f},{b.real:.6e},{b.imag:.6e}")
    return 0


def cmd_diagnostics(args):
    from . import eye
    _, _, prob, C_FULL, _ = _crystal_problem(args.variant, args.clmax,
                                             args.workdir)
    from . import fem
    sol = fem.solve_modes(prob, 6 + args.mode + 2)
    flds = eye.evaluate_elastic_diagnostics(prob, sol, args.mode,
                                            C_FULL)
    print("diagnostic,raw_max,units,n_points")
    for did, f in sorted(flds.items()):
        print(f"{did},{f.raw_max:.6e},{f.units},{len(f.values)}")
    return 0


def cmd_refsystems(args):
    from . import refsystems as rs
    ana = rs.cavity_modes_analytic((0.5, 0.4, 0.3))[:6]
    out = rs.cavity_modes_fem((0.5, 0.4, 0.3), (8, 7, 6), n_modes=8)
    k0 = out["n_constant_modes"]
    print("cavity_mode,exact_hz,fem_hz")
    for i, (a, b) in enumerate(zip(ana,
                                   out["frequencies_hz"][k0:k0 + 6])):
        print(f"{i + 1},{a:.4f},{b:.4f}")
    return 0


def cmd_proof_bundle(args):
    if args.target != "canonical-110":
        print("only target 'canonical-110' is defined", file=sys.stderr)
        return 2
    from .proofbundle import build_bundle
    out = build_bundle(args.out, fast=args.fast)
    print(str(out))
    return 0


def cmd_report(args):
    bundle = Path(args.bundle)
    v = json.loads((bundle / "VERDICT.json").read_text())
    print((bundle / "reports" / "PROOF_BUNDLE_REPORT.md").read_text())
    print(f"# VERDICT: {v['verdict']}", file=sys.stderr)
    return 0


def cmd_verify_checksums(args):
    bundle = Path(args.bundle)
    sums = (bundle / "SHA256SUMS.txt").read_text().strip().splitlines()
    bad = 0
    for line in sums:
        h, rel = line.split("  ", 1)
        p = bundle / rel
        if not p.exists():
            print(f"MISSING {rel}")
            bad += 1
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != h:
            print(f"MISMATCH {rel}")
            bad += 1
    print(f"{len(sums) - bad}/{len(sums)} OK")
    return 1 if bad else 0


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rgcs-v4",
        description="RGCS v4 / RSCS 2.0 command-line interface")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, fn, **kw):
        sp = sub.add_parser(name, **kw)
        sp.set_defaults(fn=fn)
        return sp

    add("devices", cmd_devices,
        help="CPU/OpenCL device capability report (JSON)")
    sp = add("geometry", cmd_geometry, help="canonical geometry record")
    sp.add_argument("variant", choices=["ideal_n7", "nominal"])
    sp = add("mesh", cmd_mesh, help="gmsh mesh + manifest")
    sp.add_argument("variant", choices=["ideal_n7", "nominal"])
    sp.add_argument("--clmax", type=float, default=8.0)
    sp.add_argument("--workdir", default="cli_work")
    add("material", cmd_material, help="frozen alpha-quartz record")
    sp = add("modes", cmd_modes, help="anisotropic modal solve (CSV)")
    sp.add_argument("variant", choices=["ideal_n7", "nominal"])
    sp.add_argument("--clmax", type=float, default=8.0)
    sp.add_argument("--n", type=int, default=12)
    sp.add_argument("--workdir", default="cli_work")
    sp = add("sweep", cmd_sweep, help="Christoffel anisotropy sweep")
    sp.add_argument("--backend", default="auto",
                    choices=["cpu", "opencl", "cuda_interface", "auto"])
    sp.add_argument("--device", default=None)
    sp.add_argument("--n", type=int, default=10000)
    sp.add_argument("--seed", type=int, default=42)
    sp = add("piezo", cmd_piezo, help="piezoelectric coupled modes")
    sp.add_argument("variant", choices=["ideal_n7", "nominal"])
    sp.add_argument("--clmax", type=float, default=10.0)
    sp.add_argument("--n", type=int, default=8)
    sp.add_argument("--condition", default="short",
                    choices=["short", "open"])
    sp.add_argument("--workdir", default="cli_work")
    sp = add("optical", cmd_optical, help="probe-path projection")
    sp.add_argument("variant", choices=["ideal_n7", "nominal"])
    sp.add_argument("--wavelength", type=float, default=632.8)
    sp = add("coil", cmd_coil, help="coil-pair on-axis field (CSV)")
    sp.add_argument("--radius", type=float, default=0.03)
    sp.add_argument("--separation", type=float, default=0.044)
    sp.add_argument("--current", type=float, default=1.0)
    sp.add_argument("--mode", default="opposed",
                    choices=["opposed", "in_phase"])
    sp.add_argument("--same-wound", action="store_true")
    sp.add_argument("--zmax", type=float, default=0.08)
    sp.add_argument("--points", type=int, default=81)
    sp = add("diagnostics", cmd_diagnostics,
             help="eye diagnostic fields for one mode")
    sp.add_argument("variant", choices=["ideal_n7", "nominal"])
    sp.add_argument("--mode", type=int, default=0)
    sp.add_argument("--clmax", type=float, default=9.0)
    sp.add_argument("--workdir", default="cli_work")
    add("refsystems", cmd_refsystems,
        help="reference-system quick tables")
    sp = add("proof-bundle", cmd_proof_bundle,
             help="build the canonical-110 proof bundle")
    sp.add_argument("target", choices=["canonical-110"])
    sp.add_argument("--out", default=None)
    sp.add_argument("--fast", action="store_true")
    sp.add_argument("--backend", default="auto",
                    help="recorded; sweep backend policy (DV4-007)")
    sp.add_argument("--refinement", default="all",
                    help="recorded; bundle always runs all levels")
    sp = add("report", cmd_report, help="print a bundle's report")
    sp.add_argument("--bundle", default="proof_bundle_110mm")
    sp = add("verify-checksums", cmd_verify_checksums,
             help="verify a bundle's SHA256SUMS.txt")
    sp.add_argument("--bundle", default="proof_bundle_110mm")
    return p


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
