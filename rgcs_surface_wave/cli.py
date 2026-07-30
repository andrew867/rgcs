"""R10.15 Phase F31/F32 — the ``rgcs surface-wave`` command family.

Every command emits JSON and a human-readable summary, and every one
carries a receipt with input hashes, versions, evidence class,
limitations, and the standing nonclaim.

This module is mounted by the unified ``rgcs`` CLI (r1013.cli) as the
``surface-wave`` subcommand, so the existing rgcs, rgcs-v4,
rgcs-workbook, and rgcs-workbench interfaces are unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rgcs_surface_wave import NONCLAIM
from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.receipts import make_receipt, verify_bundle

EXIT_OK, EXIT_USER, EXIT_REFUSAL = 0, 2, 3


def _geo_from_yaml(path):
    """Load a model file. YAML if available, JSON always."""
    from rgcs_surface_wave.geometry import (AnnularGeometry,
                                            DielectricSlab, Support,
                                            candidate_geometry)
    if path in (None, "candidate"):
        return candidate_geometry()
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(
            f"no model file at '{p}'. Pass 'candidate' to use the "
            "preregistered candidate geometry.")
    text = p.read_text(encoding="utf-8")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        import yaml
        doc = yaml.safe_load(text)
    g = doc.get("geometry", doc)
    slab = None
    if g.get("dielectric"):
        d = g["dielectric"]
        slab = DielectricSlab(d["gap_m"], d["thickness_m"],
                              d["epsilon_r"], d.get("loss_tangent", 0.0))
    return AnnularGeometry(
        inner_radius_m=g["inner_radius_m"],
        outer_radius_m=g["outer_radius_m"],
        thickness_m=g.get("thickness_m", 1.6e-3),
        cells=g.get("cells", 35),
        omitted_cells=tuple(g.get("omitted_cells", ())),
        dielectric=slab,
        supports=tuple(Support(s, (0.0, 0.0, -0.01))
                       for s in g.get("supports", ["support_a"])))


def _emit(args, receipt, human_lines):
    if getattr(args, "format", "human") == "json":
        text = json.dumps(receipt, indent=2, default=str, sort_keys=True)
    else:
        text = "\n".join(human_lines + ["", f"NONCLAIM: {NONCLAIM}"])
    out = getattr(args, "output", None)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)


def cmd_geometry_validate(args):
    from rgcs_surface_wave.geometry import validate
    geo = _geo_from_yaml(args.model)
    v = validate(geo)
    r = make_receipt("surface-wave geometry validate",
                     {"model": str(args.model)}, v,
                     ClaimClass.DERIVED.value,
                     ["geometry record only; no field is solved here"])
    lines = [f"Geometry OK: {geo.cells} cells, "
             f"{len(geo.active_cells)} active, omitted "
             f"{list(geo.omitted_cells)}",
             f"  radii {geo.inner_radius_m * 1e3:.3f} to "
             f"{geo.outer_radius_m * 1e3:.3f} mm, area ratio "
             f"{geo.area_ratio:.6f}"]
    lines += [f"  note: {n}" for n in v["notes"]]
    lines += [f"  warning: {w}" for w in v["warnings"]]
    _emit(args, r, lines)
    return EXIT_OK


def cmd_mask_analyze(args):
    from rgcs_surface_wave.masks import analyze
    geo = _geo_from_yaml(args.model)
    sp = analyze(geo, m_max=args.m_max)
    r = make_receipt("surface-wave mask analyze",
                     {"model": str(args.model), "m_max": args.m_max},
                     {k: v for k, v in sp.items()
                      if k not in ("coefficients", "phase_rad")},
                     ClaimClass.DERIVED.value,
                     ["exact discrete Fourier arithmetic; finite "
                      "aperture applied as an exact rect integral"])
    lines = [f"Mask spectrum ({geo.cells} cells, "
             f"{len(geo.active_cells)} active):",
             f"  m=0 amplitude: {sp['m0']:.6f}",
             f"  m=1 amplitude: {sp['m1']:.6f}   <- sets net lateral force",
             f"  Parseval residual: {sp['parseval_residual']:.2e}",
             f"  symmetry: {sp['symmetry']['class']}",
             "  comparison against controls:"]
    for name, e in sp["comparison_to_nulls"].items():
        lines.append(f"    {name:24s} m1={e['m1']:.6f}")
    _emit(args, r, lines)
    return EXIT_OK


def cmd_temporal_analyze(args):
    from rgcs_surface_wave.temporal import coefficients
    tc = coefficients(args.waveform, n_max=args.n_max, duty=args.duty,
                      depth=args.depth)
    r = make_receipt("surface-wave temporal analyze",
                     {"waveform": args.waveform, "duty": args.duty},
                     {k: v for k, v in tc.items()
                      if k != "coefficients"},
                     ClaimClass.DERIVED.value,
                     ["DFT quadrature error scales as 1/n_samples; "
                      "analytic cross-check reported where available"])
    lines = [f"Temporal spectrum ({args.waveform}):",
             f"  DC: {tc['dc']:.6f}",
             f"  effective modulation depth: "
             f"{tc['modulation_depth_effective']:.6f}",
             f"  Parseval residual: {tc['parseval_residual']:.2e}",
             f"  analytic max deviation: "
             f"{tc['analytic_max_deviation']:.2e}"]
    _emit(args, r, lines)
    return EXIT_OK


def cmd_eigenmodes_solve(args):
    from rgcs_surface_wave.eigenmodes import (annular_modes,
                                              test_candidate_carrier)
    geo = _geo_from_yaml(args.model)
    res = annular_modes(geo, m_values=tuple(range(args.m_max + 1)),
                        n_roots=args.n_roots)
    cand = test_candidate_carrier(geo, args.test_candidate_hz)
    r = make_receipt("surface-wave eigenmodes solve",
                     {"model": str(args.model),
                      "test_candidate_hz": args.test_candidate_hz},
                     {"modes": res["modes"][:12],
                      "f_surface_wave_derived_hz":
                          res["f_surface_wave_derived_hz"],
                      "candidate_test": cand},
                     ClaimClass.SIMULATED.value, res["limitations"])
    lines = ["Annular eigenmodes (declared eigenvalue problem):"]
    for m in res["modes"][:8]:
        lines.append(f"  m={m['m']} n={m['radial_index']}: "
                     f"{m['frequency_mhz']:10.3f} MHz  "
                     f"Q<={m['q_total_upper_bound']:.1f}")
    lines += ["",
              f"DERIVED f_SW = "
              f"{res['f_surface_wave_derived_hz'] / 1e6:.3f} MHz",
              f"Candidate {args.test_candidate_hz:.0f} Hz: "
              f"{cand['verdict']}",
              f"  {cand['interpretation']}"]
    _emit(args, r, lines)
    return EXIT_OK


def cmd_floquet_solve(args):
    from rgcs_surface_wave.eigenmodes import annular_modes
    from rgcs_surface_wave.floquet import nonreciprocity, solve_sidebands
    geo = _geo_from_yaml(args.model)
    res = annular_modes(geo, m_values=(0, 1, 2, 3), n_roots=1)
    mf = {m["m"]: m["frequency_hz"] for m in res["modes"]
          if m["radial_index"] == 1}
    q = res["modes"][0]["q_total_upper_bound"]
    f_d = mf.get(1, res["f_surface_wave_derived_hz"])
    sb = solve_sidebands(mf, q, f_d, args.f_mod, geo.cells,
                         geo.active_cells, args.waveform)
    nr = nonreciprocity(mf, q, f_d, args.f_mod, geo.cells,
                        geo.active_cells)
    r = make_receipt("surface-wave floquet solve",
                     {"model": str(args.model), "f_mod": args.f_mod,
                      "waveform": args.waveform},
                     {"sidebands": sb, "nonreciprocity": nr},
                     nr["claim_class"],
                     ["truncated harmonic balance on a reduced modal "
                      "basis", "no force is inferred from sidebands"])
    lines = [f"Floquet sidebands at f_drive={f_d / 1e6:.3f} MHz, "
             f"f_mod={args.f_mod} Hz:",
             f"  carrier amplitude: {sb['carrier_amplitude']:.4e}",
             f"  upper/lower totals: {sb['upper_sideband_total']:.4e} / "
             f"{sb['lower_sideband_total']:.4e}",
             f"  regime: {nr['regime']}",
             f"  verdict: {nr['verdict']}",
             f"  {nr['interpretation']}"]
    _emit(args, r, lines)
    return EXIT_OK


def cmd_stress_integrate(args):
    from rgcs_surface_wave.cem import mask_comparison
    geo = _geo_from_yaml(args.model)
    mc = mask_comparison(geo)
    r = make_receipt("surface-wave stress integrate",
                     {"model": str(args.model)}, mc,
                     ClaimClass.SIMULATED.value,
                     ["quasi-static exact-Coulomb source model",
                      "closed cylindrical surface, placement-invariant",
                      "a computed stress is not a measured force"])
    lines = ["Closed-surface Maxwell stress by mask:"]
    for row in mc["rows"]:
        lines.append(f"  {row['mask']:24s} m1={row['mask_m1']:.6f}  "
                     f"F_lateral={row['lateral_force_n']:.4e} N")
    lines.append(f"  m1-to-lateral-force correlation: "
                 f"{mc['m1_lateral_correlation']:.6f}")
    _emit(args, r, lines)
    return EXIT_OK


def cmd_momentum_close(args):
    from rgcs_surface_wave import momentum
    from rgcs_surface_wave.cem import ring_static_model
    geo = _geo_from_yaml(args.model)
    ring = ring_static_model(geo)
    f = ring["force_n"]
    bodies = {"annulus": f,
              "dielectric": [0.0, 0.0, 0.0],
              "supports": [-f[0], -f[1], -f[2]],
              "enclosure": [0.0, 0.0, 0.0]}
    led = momentum.close(bodies)
    r = make_receipt("surface-wave momentum close",
                     {"model": str(args.model)}, led,
                     ClaimClass.SIMULATED.value,
                     ["the support reaction is assigned as the "
                      "equilibrium closure of the quasi-static model"])
    lines = [f"Momentum ledger: {led['status']}",
             f"  annulus force: {f}",
             f"  relative residual: {led['relative_residual']:.2e}",
             f"  {led['interpretation']}"]
    _emit(args, r, lines)
    return EXIT_OK if led["status"] == "GREEN" else EXIT_USER


def cmd_energy_close(args):
    from rgcs_surface_wave import energy
    led = energy.close(args.source_w, args.switch_w, 0.0,
                       {"conductor": args.source_w * 0.6,
                        "dielectric": args.source_w * 0.35,
                        "radiated": args.source_w * 0.05,
                        "mechanical": 0.0, "thermal": args.switch_w})
    r = make_receipt("surface-wave energy close",
                     {"source_w": args.source_w}, led,
                     ClaimClass.SIMULATED.value,
                     ["loss split is a declared example partition"])
    lines = [f"Energy ledger: {led['status']}",
             f"  in {led['total_in_w']:.4f} W, out "
             f"{led['total_out_w']:.4f} W",
             f"  relative residual: {led['relative_residual']:.2e}"]
    _emit(args, r, lines)
    return EXIT_OK if led["status"] == "GREEN" else EXIT_USER


def cmd_artifacts_estimate(args):
    from rgcs_surface_wave.artifacts import budget
    b = budget(args.candidate_force_n)
    r = make_receipt("surface-wave artifacts estimate",
                     {"candidate_force_n": args.candidate_force_n}, b,
                     ClaimClass.DERIVED.value,
                     ["order-of-magnitude bench artifact estimates"])
    lines = ["Ordinary-artifact budget:"]
    for e in b["estimates"]:
        lines.append(f"  {e['mechanism']:28s} {e['force_n']:.4e} N")
    lines += [f"  candidate: {b['candidate_force_n']:.4e} N",
              f"  verdict: {b['verdict']}",
              "  required controls: " + "; ".join(b["required_controls"][:4])]
    _emit(args, r, lines)
    return EXIT_OK


def cmd_bundle_verify(args):
    v = verify_bundle(args.bundle_dir)
    print(json.dumps(v, indent=2))
    return EXIT_OK if v["ok"] else EXIT_USER


def cmd_privacy_scan(args):
    from rgcs_surface_wave.privacy import scan_tracked
    s = scan_tracked()
    print(f"Scanned {s['files_scanned']} tracked files: "
          + ("CLEAN" if s["clean"] else f"{len(s['findings'])} FINDINGS"))
    for f in s["findings"][:20]:
        print(f"  {f['kind']}: {f['file']}")
    return EXIT_OK if s["clean"] else EXIT_USER


def build_parser(sub=None):
    p = sub or argparse.ArgumentParser(prog="rgcs surface-wave")
    s = p.add_subparsers(dest="group", required=True)

    def add(group, name, fn, model=True):
        g = s.add_parser(group) if group not in getattr(
            build_parser, "_groups", {}) else build_parser._groups[group]
        build_parser._groups = getattr(build_parser, "_groups", {})
        build_parser._groups[group] = g
        gs = getattr(g, "_sub", None) or g.add_subparsers(
            dest="op", required=True)
        g._sub = gs
        sp = gs.add_parser(name)
        if model:
            sp.add_argument("model", nargs="?", default="candidate")
        sp.add_argument("--format", choices=("human", "json"),
                        default="human")
        sp.add_argument("--output", default=None)
        sp.set_defaults(fn=fn)
        return sp

    add("geometry", "validate", cmd_geometry_validate)
    sp = add("mask", "analyze", cmd_mask_analyze)
    sp.add_argument("--m-max", type=int, default=12, dest="m_max")
    sp = add("temporal", "analyze", cmd_temporal_analyze, model=False)
    sp.add_argument("--waveform", default="stepped")
    sp.add_argument("--n-max", type=int, default=8, dest="n_max")
    sp.add_argument("--duty", type=float, default=33.0 / 35.0)
    sp.add_argument("--depth", type=float, default=1.0)
    sp = add("eigenmodes", "solve", cmd_eigenmodes_solve)
    sp.add_argument("--m-max", type=int, default=3, dest="m_max")
    sp.add_argument("--n-roots", type=int, default=2, dest="n_roots")
    sp.add_argument("--test-candidate-hz", type=float, default=4096.0,
                    dest="test_candidate_hz")
    sp = add("floquet", "solve", cmd_floquet_solve)
    sp.add_argument("--f-mod", type=float, default=16.0, dest="f_mod")
    sp.add_argument("--waveform", default="sinusoidal")
    add("stress", "integrate", cmd_stress_integrate)
    add("momentum", "close", cmd_momentum_close)
    sp = add("energy", "close", cmd_energy_close, model=False)
    sp.add_argument("--source-w", type=float, default=1.0,
                    dest="source_w")
    sp.add_argument("--switch-w", type=float, default=0.01,
                    dest="switch_w")
    sp = add("artifacts", "estimate", cmd_artifacts_estimate,
             model=False)
    sp.add_argument("--candidate-force-n", type=float, default=1e-9,
                    dest="candidate_force_n")
    sp = add("bundle", "verify", cmd_bundle_verify, model=False)
    sp.add_argument("bundle_dir")
    add("privacy", "scan", cmd_privacy_scan, model=False)
    return p


def main(argv=None) -> int:
    build_parser._groups = {}
    p = build_parser()
    args = p.parse_args(argv if argv is not None else sys.argv[1:])
    try:
        return args.fn(args)
    except (FileNotFoundError, ValueError) as ex:
        print(f"{type(ex).__name__}: {ex}", file=sys.stderr)
        return EXIT_REFUSAL if "refused" in str(ex).lower() else EXIT_USER


if __name__ == "__main__":
    raise SystemExit(main())
