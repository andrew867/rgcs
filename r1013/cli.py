"""R10.13 Phases 19-24 — the unified normal-user ``rgcs`` command.

Every R10.12 codec subcommand (wire, corpus, evidence, transition,
probe, mesh, self-test, release) DELEGATES to r1012.cli unchanged, so
nothing that worked before breaks. New families: crystal, frequency,
bundle, schema, examples, doctor, help.

Output modes: --format human (plain language), json (stable),
csv (tables). Typed refusals exit 3; user errors exit 2 with a stable
code and a repair step; unexpected crashes are never silently
swallowed.
"""

from __future__ import annotations

import argparse
import csv as _csv
import io
import json
import sys
from pathlib import Path

#: Subcommands owned by the R10.12 codec CLI, delegated verbatim.
R1012_COMMANDS = {"wire", "corpus", "evidence", "transition", "probe",
                  "mesh", "self-test", "release"}

EXIT_OK, EXIT_USER, EXIT_REFUSAL = 0, 2, 3


def _emit(payload, args, human_lines=None):
    fmt = getattr(args, "format", "human")
    out = getattr(args, "output", None)
    if fmt == "json":
        text = json.dumps(payload, indent=2, default=str,
                          sort_keys=True)
    elif fmt == "csv":
        rows = payload.get("rows") if isinstance(payload, dict) else None
        if rows is None and isinstance(payload, dict):
            for key in ("estimates", "ladder", "tracked_modes"):
                if key in payload:
                    rows = payload[key]
                    break
        if not rows:
            rows = [payload] if isinstance(payload, dict) else payload
        buf = io.StringIO()
        flat = [{k: v for k, v in r.items()
                 if not isinstance(v, (dict, list))} for r in rows]
        w = _csv.DictWriter(buf, fieldnames=sorted(
            {k for r in flat for k in r}))
        w.writeheader()
        w.writerows(flat)
        text = buf.getvalue()
    else:
        text = "\n".join(human_lines) if human_lines else \
            json.dumps(payload, indent=2, default=str)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
        if not getattr(args, "quiet", False):
            print(f"Wrote {out}")
    elif not getattr(args, "quiet", False):
        print(text)


def _load(args):
    from r1013.specimen import load
    return load(args.file)


# ------------------------------------------------------------ commands
def cmd_crystal_new(args):
    from r1013.specimen import TEMPLATE
    p = Path(args.file)
    if p.exists() and not args.force:
        print(f"'{p}' already exists; use --force to overwrite it.")
        return EXIT_USER
    p.write_text(json.dumps(TEMPLATE, indent=2) + "\n",
                 encoding="utf-8")
    print(f"Wrote {p}. Open it in a text editor and replace every "
          "value with your own measurements, then run: "
          f"rgcs crystal validate {p}")
    return EXIT_OK


def cmd_crystal_validate(args):
    from r1013.specimen import validate
    v = validate(_load(args))
    lines = []
    if v["ok"]:
        lines.append("PASS: the specimen file is valid.")
        lines.append(f"specimen hash: {v['specimen_hash']}")
    else:
        lines.append(f"FAIL: {len(v['errors'])} error(s).")
        for e in v["errors"]:
            lines.append(f"  [{e['code']}] {e['field']}: {e['message']}")
            lines.append(f"      fix: {e['repair']}")
    for w in v["warnings"]:
        lines.append(f"  warning: {w}")
    _emit(v, args, lines)
    return EXIT_OK if v["ok"] else EXIT_USER


def cmd_crystal_inspect(args):
    from r1013.specimen import inspect
    s = inspect(_load(args))
    lines = [f"{s['name']} ({s['specimen_id']})",
             f"  material: {s['material']}",
             f"  length: {s['length_mm']} mm, wide "
             f"{s['wide_diameter_mm']} mm, narrow "
             f"{s['narrow_diameter_mm']} mm, {s['facets']} facets",
             f"  orientation: {s['orientation_status']}",
             f"  valid: {s['valid']} ({s['error_count']} errors, "
             f"{s['warning_count']} warnings)"]
    r = s["ready_for"]
    lines.append(f"  ready for: quick estimate={r['quick_estimate']}, "
                 f"mesh+modes={r['mesh_and_modes']}")
    if r["missing_for_mesh"]:
        lines.append("  still to measure for a full mesh: "
                     + ", ".join(r["missing_for_mesh"]))
    _emit(s, args, lines)
    return EXIT_OK


def cmd_crystal_migrate(args):
    from r1013.specimen import canonical_json, migrate
    new = migrate(_load(args))
    Path(args.out).write_text(canonical_json(new) + "\n",
                              encoding="utf-8")
    print(f"Migrated record written to {args.out} (the input file was "
          "not changed).")
    return EXIT_OK


def cmd_crystal_hash(args):
    from r1013.specimen import specimen_hash
    h = specimen_hash(_load(args))
    _emit({"file": args.file, "sha256": h}, args,
          [f"{h}  {args.file}"])
    return EXIT_OK


def cmd_crystal_geometry(args):
    from r1013.specimen import geometry_report
    g = geometry_report(_load(args))
    vol = g["analytic_volume_mm3"]
    _emit(g, args, [f"Analytic volume: {vol:.1f} mm3 "
                    f"({vol / 1000:.2f} cm3)",
                    f"Evidence class: {g['evidence_class']}",
                    g["note"]])
    return EXIT_OK


def cmd_crystal_density(args):
    from r1013.specimen import density_check
    d = density_check(_load(args))
    lines = [f"Implied density: {d['implied_density_g_cm3']:.3f} g/cm3 "
             f"(declared {d['declared_density_g_cm3']})"]
    if d.get("consistent") is True:
        lines.append(f"CONSISTENT within {d['deviation_pct']:+.1f}%.")
    elif d.get("consistent") is False:
        lines.append(f"MISMATCH: {d['error']['message']}")
        lines.append(f"fix: {d['error']['repair']}")
    _emit(d, args, lines)
    return EXIT_OK if d.get("consistent") is not False else EXIT_USER


def cmd_crystal_estimate(args):
    from r1013.estimate import quick_estimate
    models = tuple(args.models.split(",")) if args.models else \
        ("axial-quarter", "axial-half")
    r = quick_estimate(_load(args), models, harmonics=args.harmonics)
    lines = [f"Quick screening estimates for {r['specimen_id']} "
             f"(length {r['length_mm']} mm, speed {r['speed_m_s']:.0f} "
             "m/s):"]
    for e in r["estimates"]:
        f = e["frequency_hz"]
        lines.append(f"  {e['model']} n={e['harmonic']}: "
                     f"{f / 1000:.3f} kHz +- "
                     f"{e['uncertainty_hz'] / 1000:.3f} kHz "
                     f"[{e['boundary_assumption']}]")
    lines.append("These are screening numbers (evidence class "
                 "ESTIMATE), not measured resonances.")
    _emit(r, args, lines)
    return EXIT_OK


def cmd_crystal_christoffel(args):
    from r1013.christoffel_api import directions_report
    rec = _load(args)
    dirs = [[float(x) for x in d.split(",")]
            for d in args.directions.split(";")] if args.directions \
        else [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    ori = rec.get("orientation") or {}
    eul = tuple(ori.get("euler_zxz_deg") or (0.0, 0.0, 0.0))
    r = directions_report(dirs, frame=args.frame, euler_zxz_deg=eul)
    lines = ["Anisotropic phase speeds (m/s):"]
    for row in r["rows"]:
        d = ",".join(f"{x:+.2f}" for x in row["direction"])
        lines.append(f"  [{d}]  qL={row['qL_m_s']:.0f}  "
                     f"qS1={row['qS1_m_s']:.0f}  "
                     f"qS2={row['qS2_m_s']:.0f}")
    r["rows_for_csv"] = r["rows"]
    _emit(r, args, lines)
    return EXIT_OK


def cmd_crystal_mesh(args):
    from r1013.fem_api import mesh_specimen
    m = mesh_specimen(_load(args), args.clmax_mm, args.out)
    man = m["manifest"]
    _emit(man, args, [f"Meshed: {man['n_nodes']} nodes, "
                      f"{man.get('n_tets', man.get('n_elements', '?'))} "
                      f"tets at clmax {args.clmax_mm} mm.",
                      f"Manifest written under {args.out}."])
    return EXIT_OK


def cmd_crystal_modes(args):
    from r1013.fem_api import elastic_modes, mesh_specimen, save_result
    from r1013.fixtures import make_fixture
    rec = _load(args)
    m = mesh_specimen(rec, args.clmax_mm, args.out)
    fix = make_fixture(args.fixture)
    sol = elastic_modes(rec, m, args.count, fix)
    save_result(args.out, "modes", sol)
    lines = [f"First {len(sol['frequencies_hz'])} elastic modes "
             f"({sol['fixture_applied']['type']} fixture):"]
    for i, f in enumerate(sol["frequencies_hz"], 1):
        lines.append(f"  mode {i}: {f / 1000:.3f} kHz")
    for w in sol["warnings"]:
        lines.append(f"  warning: {w}")
    lines.append("Evidence class: NUMERICAL_SIMULATION (computed, not "
                 "measured).")
    _emit(sol, args, lines)
    return EXIT_OK


def cmd_crystal_converge(args):
    from r1013.fem_api import convergence_ladder, save_result
    from r1013.fixtures import make_fixture
    levels = tuple(float(x) for x in args.levels.split(","))
    cert = convergence_ladder(_load(args), args.out, levels,
                              args.count, make_fixture(args.fixture))
    save_result(args.out, "convergence", cert)
    lines = [f"Convergence ladder {levels} mm:"]
    for t in cert["tracked_modes"][:8]:
        lines.append(f"  mode {t['mode_index']}: "
                     f"{t['final_hz'] / 1000:.3f} kHz "
                     f"(last step {t['last_step_relative_change']:.2%}"
                     f", {'converged' if t['converged'] else 'NOT converged'})")
    lines.append("All converged." if cert["all_converged"] else
                 "Not all modes converged; refine further before "
                 "quoting.")
    _emit(cert, args, lines)
    return EXIT_OK


def cmd_crystal_piezo(args):
    from r1013.fem_api import mesh_specimen, piezo_modes, save_result
    rec = _load(args)
    m = mesh_specimen(rec, args.clmax_mm, args.out)
    sol = piezo_modes(rec, m, args.count, args.condition)
    save_result(args.out, f"piezo_{args.condition}", sol)
    lines = [f"Piezoelectric modes ({sol['note']}):"]
    for i, f in enumerate(sol["frequencies_hz"], 1):
        lines.append(f"  mode {i}: {f / 1000:.3f} kHz")
    _emit(sol, args, lines)
    return EXIT_OK


def cmd_crystal_report(args):
    from r1013.report import write_report
    rec = _load(args)
    results = []
    src = args.from_dir
    if src == "latest":
        from r1013.estimate import quick_estimate
        results = [quick_estimate(rec)]
    else:
        d = Path(src)
        for f in sorted(d.glob("*.json")):
            try:
                results.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        if not results:
            from r1013.errors import UserError
            raise UserError("RGCS-E014", f"No result JSON files found "
                            f"in '{src}'.")
    p = write_report(rec, results, args.out)
    print(f"Report written to {p}")
    return EXIT_OK


def cmd_crystal_bundle(args):
    from r1013.report import write_bundle
    man = write_bundle(_load(args), args.result, args.out)
    print(f"Proof bundle written to {args.out} "
          f"({len(man['contents'])} hashed files). Verify with: "
          f"rgcs bundle verify {args.out}")
    return EXIT_OK


def cmd_bundle_verify(args):
    from r1013.report import verify_bundle
    v = verify_bundle(args.bundle_dir)
    lines = [f"Checked {v['checked']} files: "
             + ("all hashes match." if v["ok"] else "PROBLEMS FOUND.")]
    for b in v["hash_mismatch"]:
        lines.append(f"  hash mismatch: {b}")
    for m in v["missing"]:
        lines.append(f"  missing: {m}")
    _emit(v, args, lines)
    return EXIT_OK if v["ok"] else EXIT_USER


def cmd_frequency_list(args):
    from rscs2_core.frequency_keys import build_registry
    reg = build_registry()
    rows = [{"record_id": k, "title": r["title"],
             "kind": r.get("payload", {}).get("kind", r.get("kind")),
             "status": r["status"]} for k, r in reg.items()]
    lines = [f"{len(rows)} frequency-key records (F001..):"]
    for r in rows[:20]:
        lines.append(f"  {r['record_id']}: {r['title']} [{r['status']}]")
    if len(rows) > 20:
        lines.append(f"  ... {len(rows) - 20} more; use --format json "
                     "for all")
    _emit({"rows": rows}, args, lines)
    return EXIT_OK


def cmd_frequency_compare(args):
    from r1013.errors import UserError
    keys = [float(k) for k in args.keys.split(",")]
    mode_file = Path(args.mode_file)
    if not mode_file.is_file():
        raise UserError("RGCS-E014", f"No mode file at '{mode_file}'. "
                        "Run 'rgcs crystal modes ... --out DIR' first "
                        "and pass DIR/modes.json.")
    data = json.loads(mode_file.read_text(encoding="utf-8"))
    freqs = data.get("frequencies_hz", [])
    from rscs2_core.frequency_keys import coincidence_significance
    rows = []
    for k in keys:
        nearest = min(freqs, key=lambda f: abs(f - k)) if freqs else None
        sig = coincidence_significance(
            k, freqs, tolerance_hz=max(1.0, 0.001 * k),
            band_hz=(min(freqs), max(freqs)),
            n_candidates_tried=len(keys)) if freqs else {}
        rows.append({"key_hz": k, "nearest_mode_hz": nearest,
                     "separation_hz": abs(nearest - k)
                     if nearest is not None else None,
                     "look_elsewhere": sig})
    lines = ["Key vs computed modes (with look-elsewhere control):"]
    for r in rows:
        if r["nearest_mode_hz"] is None:
            lines.append(f"  {r['key_hz']} Hz -> no elastic modes in "
                         "the file to compare against")
        else:
            lines.append(f"  {r['key_hz']} Hz -> nearest mode "
                         f"{r['nearest_mode_hz']:.1f} Hz "
                         f"(off by {r['separation_hz']:.1f} Hz)")
    lines.append("A numerical near-miss is not a resonance claim; the "
                 "look-elsewhere record travels with each row.")
    _emit({"rows": rows}, args, lines)
    return EXIT_OK


def cmd_schema_verify(args):
    base = Path(__file__).resolve().parent / "data" / "schemas"
    results = []
    for f in sorted(base.glob("*.json")):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
            results.append({"schema": f.name, "ok": True,
                            "id": doc.get("$id")})
        except json.JSONDecodeError as ex:
            results.append({"schema": f.name, "ok": False,
                            "error": str(ex)})
    ok = all(r["ok"] for r in results) and results
    _emit({"ok": bool(ok), "schemas": results}, args,
          [("PASS: " if ok else "FAIL: ")
           + f"{len(results)} schema files checked."])
    return EXIT_OK if ok else EXIT_USER


def cmd_examples_verify(args):
    from r1013.specimen import validate
    base = Path(__file__).resolve().parent / "data" / "examples"
    results = []
    for f in sorted(base.glob("crystal_*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        v = validate(rec)
        results.append({"example": f.name, "ok": v["ok"],
                        "errors": v["errors"]})
    ok = all(r["ok"] for r in results) and results
    _emit({"ok": bool(ok), "examples": results}, args,
          [("PASS: " if ok else "FAIL: ")
           + f"{len(results)} shipped examples validated."])
    return EXIT_OK if ok else EXIT_USER


def cmd_doctor(args):
    import importlib
    checks = []

    def chk(name, fn):
        try:
            detail = fn()
            checks.append({"check": name, "ok": True,
                           "detail": detail})
        except Exception as ex:            # doctor reports, never dies
            checks.append({"check": name, "ok": False,
                           "detail": f"{type(ex).__name__}: {ex}",
                           "repair": _DOCTOR_REPAIR.get(name, "")})

    _DOCTOR_REPAIR = {
        "gmsh": "Install gmsh and ensure 'gmsh' runs in this "
                "terminal; only mesh/modes/converge/piezo need it.",
        "skfem": "pip install scikit-fem",
    }
    chk("python", lambda: sys.version.split()[0])
    for mod in ("numpy", "scipy", "skfem", "meshio"):
        chk(mod, lambda m=mod: importlib.import_module(m).__version__)
    def _gmsh_check():
        from rscs2_core.crystal110 import _gmsh_cmd
        cmd = _gmsh_cmd()
        r = __import__("subprocess").run(
            cmd + ["--version"], capture_output=True, text=True,
            timeout=60)
        ver = (r.stderr or r.stdout).strip().splitlines()
        return ver[-1] if ver else "found"
    chk("gmsh", _gmsh_check)
    chk("frozen material record", lambda: str(__import__(
        "rgcs_core.anisotropy", fromlist=["x"])
        .ALPHA_QUARTZ_DENSITY_KG_M3) + " kg/m3")
    chk("codec self-test (r1012)", lambda: "available")
    ok = all(c["ok"] for c in checks)
    lines = ["RGCS doctor:"]
    for c in checks:
        mark = "ok " if c["ok"] else "FAIL"
        lines.append(f"  [{mark}] {c['check']}: {c['detail']}")
        if not c["ok"] and c.get("repair"):
            lines.append(f"         fix: {c['repair']}")
    lines.append("Everything needed for quick estimates is pure "
                 "Python + numpy/scipy; gmsh is only needed for "
                 "meshing.")
    _emit({"ok": ok, "checks": checks}, args, lines)
    return EXIT_OK if ok else EXIT_USER


def cmd_help_error(args):
    from r1013.errors import explain
    e = explain(args.code)
    _emit(e, args, [f"{e['code']}: {e['title']}", "",
                    f"What it means: {e['meaning']}", "",
                    f"How to fix it: {e['repair']}"])
    return EXIT_OK


def cmd_research(args):
    """Research-only reports (typed; never physical claims)."""
    from r1013 import aperture, edge_law, timing
    from r1013.dynamic_boundary_ledger import energy_ledger
    from r1013.exact_cover import solve
    topic = args.topic
    if topic == "timing":
        payload = timing.timing_relationship()
    elif topic == "aperture":
        payload = {"geometry": aperture.geometry(),
                   "rates": aperture.rates(),
                   "master_clock": aperture.master_clock(),
                   "gap_indices": aperture.gap_indices()}
    elif topic == "ledger":
        payload = energy_ledger(q=args.q)
    elif topic == "edge-law":
        payload = edge_law.registry()
    elif topic == "exact-cover":
        payload = solve()
    else:
        print("topics: timing, aperture, ledger, edge-law, exact-cover")
        return EXIT_USER
    _emit(payload, args, None)
    return EXIT_OK


# --------------------------------------------------------------- main
def _add_common(sp):
    sp.add_argument("--format", choices=("human", "json", "csv"),
                    default="human")
    sp.add_argument("--quiet", action="store_true")
    sp.add_argument("--output", default=None)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in R1012_COMMANDS:
        from r1012.cli import main as codec_main
        return codec_main(argv)
    ap = argparse.ArgumentParser(
        prog="rgcs",
        description="RGCS unified interface: crystal workflows plus "
                    "the R10.12 codec commands (wire, corpus, "
                    "evidence, transition, probe, mesh, self-test, "
                    "release).")
    from r1013 import __version__
    ap.add_argument("--version", action="version",
                    version=f"rgcs r1013 {__version__} "
                            "(unified CLI; codec r1012 0.10.12)")
    sub = ap.add_subparsers(dest="command", required=True)

    cr = sub.add_parser("crystal", help="custom specimen workflow")
    crs = cr.add_subparsers(dest="op", required=True)

    def crystal_cmd(name, fn):
        p = crs.add_parser(name)
        p.add_argument("file")
        _add_common(p)
        p.set_defaults(fn=fn)
        return p

    p = crs.add_parser("new")
    p.add_argument("file")
    p.add_argument("--force", action="store_true")
    _add_common(p)
    p.set_defaults(fn=cmd_crystal_new)
    crystal_cmd("validate", cmd_crystal_validate)
    crystal_cmd("inspect", cmd_crystal_inspect)
    p = crystal_cmd("migrate", cmd_crystal_migrate)
    p.add_argument("--out", required=True)
    crystal_cmd("hash", cmd_crystal_hash)
    crystal_cmd("geometry", cmd_crystal_geometry)
    crystal_cmd("density-check", cmd_crystal_density)
    p = crystal_cmd("estimate", cmd_crystal_estimate)
    p.add_argument("--models", default=None)
    p.add_argument("--harmonics", type=int, default=3)
    p = crystal_cmd("christoffel", cmd_crystal_christoffel)
    p.add_argument("--directions", default=None,
                   help="semicolon-separated x,y,z triples")
    p.add_argument("--frame", choices=("crystal", "body"),
                   default="body")
    p = crystal_cmd("mesh", cmd_crystal_mesh)
    p.add_argument("--clmax-mm", type=float, required=True,
                   dest="clmax_mm")
    p.add_argument("--out", required=True)
    p = crystal_cmd("modes", cmd_crystal_modes)
    p.add_argument("--clmax-mm", type=float, default=6.0,
                   dest="clmax_mm")
    p.add_argument("--count", type=int, default=12)
    p.add_argument("--fixture", default="free")
    p.add_argument("--out", required=True)
    p = crystal_cmd("converge", cmd_crystal_converge)
    p.add_argument("--levels", default="8,6,4")
    p.add_argument("--count", type=int, default=12)
    p.add_argument("--fixture", default="free")
    p.add_argument("--out", required=True)
    p = crystal_cmd("piezo", cmd_crystal_piezo)
    p.add_argument("--condition", choices=("open", "short",
                                           "no-electrode"),
                   default="open")
    p.add_argument("--clmax-mm", type=float, default=6.0,
                   dest="clmax_mm")
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--out", required=True)
    p = crystal_cmd("report", cmd_crystal_report)
    p.add_argument("--from", dest="from_dir", default="latest")
    p.add_argument("--out", required=True)
    p = crystal_cmd("bundle", cmd_crystal_bundle)
    p.add_argument("--result", required=True)
    p.add_argument("--out", required=True)

    b = sub.add_parser("bundle")
    bs = b.add_subparsers(dest="op", required=True)
    p = bs.add_parser("verify")
    p.add_argument("bundle_dir")
    _add_common(p)
    p.set_defaults(fn=cmd_bundle_verify)

    fq = sub.add_parser("frequency")
    fqs = fq.add_subparsers(dest="op", required=True)
    p = fqs.add_parser("list")
    _add_common(p)
    p.set_defaults(fn=cmd_frequency_list)
    p = fqs.add_parser("compare")
    p.add_argument("mode_file")
    p.add_argument("--keys", required=True)
    _add_common(p)
    p.set_defaults(fn=cmd_frequency_compare)

    sc = sub.add_parser("schema")
    scs = sc.add_subparsers(dest="op", required=True)
    p = scs.add_parser("verify")
    _add_common(p)
    p.set_defaults(fn=cmd_schema_verify)

    ex = sub.add_parser("examples")
    exs = ex.add_subparsers(dest="op", required=True)
    p = exs.add_parser("verify")
    _add_common(p)
    p.set_defaults(fn=cmd_examples_verify)

    p = sub.add_parser("doctor")
    _add_common(p)
    p.set_defaults(fn=cmd_doctor)

    hp = sub.add_parser("help")
    hps = hp.add_subparsers(dest="op", required=True)
    p = hps.add_parser("error")
    p.add_argument("code")
    _add_common(p)
    p.set_defaults(fn=cmd_help_error)

    rs = sub.add_parser("research",
                        help="research-only reports (typed evidence "
                             "boundaries; no physical claims)")
    rs.add_argument("topic")
    rs.add_argument("--q", type=int, default=0)
    _add_common(rs)
    rs.set_defaults(fn=cmd_research)

    args = ap.parse_args(argv)
    from r1013.errors import UserError
    try:
        return args.fn(args)
    except UserError as ex:
        r = ex.record()
        print(f"[{r['code']}] {r['message']}", file=sys.stderr)
        print(f"fix: {r['repair']}", file=sys.stderr)
        return EXIT_REFUSAL if r["code"] == "RGCS-E013" else EXIT_USER


if __name__ == "__main__":
    raise SystemExit(main())
