"""R10.15A — ``rgcs scale-a`` command family (mechanical lane)."""

from __future__ import annotations

import argparse
import json
import sys

from r1015a import DESIGN_ID, EM_NEGATIVE_RESULT, STATUS, ScaleAError

NONCLAIM = ("Geometry and analytic proxy only. 463.8671875 mm is an "
            "exact first-order half-wave path candidate, not a "
            "measured resonance and not a final cut length. This lane "
            "is mechanical/acoustic and does not reopen the R10.15 "
            "electromagnetic negative result. No claim of propulsion, "
            "anomalous force, gravity modification, free energy, or "
            "measured Phryll is made.")


def _out(args, payload, lines):
    if getattr(args, "format", "human") == "json":
        print(json.dumps(payload, indent=2, default=str, sort_keys=True))
    else:
        print("\n".join(lines + ["", f"NONCLAIM: {NONCLAIM}"]))


def cmd_design(args):
    from r1015a.design import half_wave_proxy, scale_a_geometry
    p = half_wave_proxy(args.branch, args.frequency)
    g = scale_a_geometry(args.branch, args.frequency)
    r = g.record()
    _out(args, {"proxy": p, "geometry": r},
         [f"{DESIGN_ID}  [{STATUS}]",
          f"  branch: {args.branch} ({p['role']})",
          f"  v = {p['velocity_m_s']} m/s, f = {p['frequency_hz']} Hz",
          f"  half-wave path: {p['length_mm']} mm "
          f"(exact {p['length_m_exact'][0]}/{p['length_m_exact'][1]} m)",
          f"  wide/narrow diameter: {r['wide_diameter_mm']:.6f} / "
          f"{r['narrow_diameter_mm']:.6f} mm",
          f"  caps rx/tx: {r['rx_cap_height_mm']:.6f} / "
          f"{r['tx_cap_height_mm']:.6f} mm, shaft "
          f"{r['shaft_height_mm']:.6f} mm",
          f"  volume {r['idealized_volume_cm3']:.6f} cm3, mass "
          f"{r['idealized_mass_g_at_2p65']:.3f} g at 2.65 g/cm3",
          f"  evidence: {p['evidence_class']}; measured resonance: "
          f"{p['is_measured_resonance']}; final cut length: "
          f"{p['is_final_cut_length']}"])
    return 0


def cmd_length_budget(args):
    from r1015a.design import half_wave_proxy, physical_length_budget
    p = half_wave_proxy(args.branch, args.frequency)
    b = physical_length_budget(p["length_mm"])
    _out(args, b,
         [f"Physical length budget: {b['status']}",
          f"  effective path: {b['effective_length_mm']} mm",
          f"  unknown terms: {', '.join(b['unknown_terms'])}",
          f"  {b['refusal']}"])
    return 0


def cmd_modes(args):
    from r1015a.design import scale_a_geometry
    from r1015a.modes import crowding_report
    r = crowding_report(scale_a_geometry(args.branch, args.frequency),
                        target_hz=args.frequency)
    lines = [f"Mode screen near {args.frequency} Hz "
             f"({r['modes_in_window_count']} in +-25% window):"]
    for m in r["modes_in_window"]:
        lines.append(f"  {m['family']:20s} n={m['index']}  "
                     f"{m['frequency_hz']:9.1f} Hz  "
                     f"({m['separation_fraction']:+.2%})")
    lines += [f"  mode identity risk: {r['mode_identity_risk']}",
              f"  {r['interpretation']}",
              f"  proxy artifact: {r['proxy_artifact_warning']['warning']}"]
    _out(args, r, lines)
    return 0


def cmd_sweep(args):
    from r1015a.fem_profile import branch_comparison, velocity_sweep
    s = velocity_sweep(args.branch, args.frequency, args.uncertainty)
    b = branch_comparison(args.frequency)
    lines = [f"Velocity sweep ({args.branch}, "
             f"+-{args.uncertainty}%):",
             f"  nominal {s['nominal_length_mm']:.6f} mm",
             f"  span {s['length_span_mm']:.3f} mm "
             f"({s['length_span_pct']:.2f}%)",
             f"  {s['dominant_uncertainty']}", "", "Branches:"]
    for row in b["rows"]:
        lines.append(f"  {row['branch']:22s} {row['length_mm']:12.6f} mm"
                     f"   [{row['role']}]")
    _out(args, {"sweep": s, "branches": b}, lines)
    return 0


def cmd_fem(args):
    from r1015a.design import scale_a_geometry
    from r1015a.fem_profile import ScaleAFemProfile
    p = ScaleAFemProfile(geometry=scale_a_geometry(args.branch,
                                                   args.frequency))
    rec = p.record()
    _out(args, rec,
         ["Anisotropic FEM profile:",
          f"  solvable: {rec['solvable']}",
          f"  unresolved mandatory inputs "
          f"({len(rec['unresolved_inputs'])}): "
          + ", ".join(rec["unresolved_inputs"]),
          "  The half-wave proxy stands until these are supplied and "
          "a converged 3D anisotropic eigenmode solve is run."])
    return 0


def cmd_verify(args):
    from r1015a.scad import validate_design_json, verify_render
    s = verify_render()
    v = validate_design_json()
    _out(args, {"scad": s, "json": v},
         ["Reference model verification:",
          f"  level: {s['verification_level']}",
          f"  openscad available: {s['openscad_available']}, "
          f"render claimed: {s['render_claimed']}",
          f"  delimiters balanced: "
          f"{s['delimiter_balance']['balanced']}, presets present: "
          f"{s['all_presets_present']}, ascii clean: {s['ascii_clean']}",
          f"  sha256: {s['sha256']}",
          f"  design JSON valid: {v['ok']}, max cross-check deviation: "
          f"{v['cross_check_max_deviation']}"])
    return 0 if v["ok"] else 2


def cmd_boundary(args):
    _out(args, EM_NEGATIVE_RESULT,
         ["R10.15 electromagnetic result (FROZEN):",
          f"  annular eigenmode: "
          f"{EM_NEGATIVE_RESULT['annular_eigenmode_hz'] / 1e9:.6f} GHz",
          f"  4096 Hz as EM carrier: "
          f"{EM_NEGATIVE_RESULT['4096_hz_as_em_carrier']}",
          f"  sidebands: {EM_NEGATIVE_RESULT['sideband_resolution']}",
          f"  reversed modulation: "
          f"{EM_NEGATIVE_RESULT['reversed_modulation']}",
          f"  lateral force: {EM_NEGATIVE_RESULT['lateral_force']}",
          "  This mechanical lane does not modify any of the above."])
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="rgcs scale-a",
        description="Scale A mechanical bulk-acoustic crystal "
                    "candidate (separate from the surface-wave lane)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, extra in (
            ("design", cmd_design, True),
            ("length-budget", cmd_length_budget, True),
            ("modes", cmd_modes, True),
            ("sweep", cmd_sweep, True),
            ("fem-profile", cmd_fem, True),
            ("verify", cmd_verify, False),
            ("em-boundary", cmd_boundary, False)):
        p = sub.add_parser(name)
        if extra:
            p.add_argument("--branch", default="shear_proxy")
            p.add_argument("--frequency", type=float, default=4096.0)
        if name == "sweep":
            p.add_argument("--uncertainty", type=float, default=5.0)
        p.add_argument("--format", choices=("human", "json"),
                       default="human")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])
    try:
        return args.fn(args)
    except ScaleAError as ex:
        print(f"[REFUSED] {ex}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
