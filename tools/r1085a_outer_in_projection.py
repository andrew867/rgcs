"""R10.8.5A corrective run — the actual outer-in gravity-shell projection.

Executes the corrected downstream transform on top of the recovered
F5 | Q22 | S3 packet authority (commit e5864a5; the parser is NOT
reopened here) and writes the full receipt set to
``docs/proofs/r1085a-outer-in-gravity-shell-projection/``.

Run:  python tools/r1085a_outer_in_projection.py
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from r12 import icosapacket as pk                                  # noqa

from cwatlas import r1085a                                         # noqa
from cwatlas.r1085a import final_projection as fp                  # noqa
from cwatlas.r1085a import gravity_field_line as gfl               # noqa
from cwatlas.r1085a import land_zero as lz                         # noqa
from cwatlas.r1085a import magnetic_shell as ms                    # noqa
from cwatlas.r1085a import orange_slice as osl                     # noqa
from cwatlas.r1085a import outer_in_radial as oir                  # noqa
from cwatlas.r1085a import shell_profile as sp                     # noqa

OUT = ROOT / "docs" / "proofs" / "r1085a-outer-in-gravity-shell-projection"
EPOCH = 2025.0
STEP_M = 5000.0

#: Stonehenge site elevation above MSL (conventional; ~102 m).
SITE_ELEVATION_M = 102.0


def _write(name: str, text: str) -> None:
    (OUT / name).write_text(text, encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- 0. packet authority held, not reopened -------------------------
    rec = pk.decode_record(fp.TRAINING_WORD)
    authority_ok = (
        rec["octal"] == "1170611453" and rec["face"] == 4
        and rec["shell"] == 3 and rec["round_trip"])
    print("packet authority held:", authority_ok)

    # ---- 1. training alignment (calibration, sealed after solve) --------
    frame, align_receipt = fp.training_alignment(EPOCH)
    addr = fp.parse_address(fp.TRAINING_WORD)
    contained = fp.cell_contains(frame, addr, fp.TRAINING_LAT_DEG,
                                 fp.TRAINING_LON_DEG)
    sealed_misses = {
        ctx: (not fp.cell_contains(fp.sealed_frame(ctx, EPOCH), addr,
                                   fp.TRAINING_LAT_DEG,
                                   fp.TRAINING_LON_DEG))
        for ctx in fp.sealed_contexts()}
    print("trained-frame containment:", contained,
          "| all sealed contexts still miss:",
          all(sealed_misses.values()))

    # ---- 2. the full declared sweep (every member retained) -------------
    profiles = [sp.profile(p.profile_id) for p in sp.CANDIDATE_PROFILES]
    land_refs = lz.all_land_zero_candidates(EPOCH)
    zetas = list(oir.ZETA_CONVENTIONS)
    mags = list(ms.active_members())

    def sweep(word: int, active_shell: int | None = None) -> list[dict]:
        rows = []
        for prof in profiles:
            for lref in land_refs:
                for zc in zetas:
                    for mag in mags:
                        if active_shell is None:
                            r = fp.forward(word, frame, prof, lref, mag,
                                           zeta_convention=zc,
                                           field_line_step_m=STEP_M)
                        else:
                            r = fp.forward_with_operator_correction(
                                word, active_shell, frame, prof, lref,
                                mag, zeta_convention=zc,
                                field_line_step_m=STEP_M)
                        rows.append({
                            "profile": r.profile_id,
                            "land_ref": r.land_reference_id,
                            "zeta_convention": r.zeta_convention,
                            "magnetic": r.magnetic_member_id,
                            "shell": r.shell_id,
                            "zeta": round(r.zeta, 6),
                            "lat_deg": round(r.latitude_deg, 6),
                            "lon_deg": round(r.longitude_deg, 6),
                            "height_above_land_zero_km":
                                round(r.height_above_land_zero_km, 4),
                            "d_in_km": round(r.d_in_km, 4),
                            "outer_boundary_radius_km":
                                round(r.outer_boundary_radius_km, 3),
                            "boundary_deformation_m":
                                round(r.magnetic_deformation_m, 1),
                            "field_line_deviation_m":
                                round(r.field_line_deviation_m, 1),
                            "radial_mode": r.radial_mode,
                        })
        return rows

    sh_rows = sweep(fp.TRAINING_WORD)
    for row in sh_rows:
        row["surface_distance_to_stonehenge_km"] = round(
            fp.surface_distance_km(row["lat_deg"], row["lon_deg"],
                                   fp.TRAINING_LAT_DEG,
                                   fp.TRAINING_LON_DEG), 3)
    lat_min = min(r["surface_distance_to_stonehenge_km"] for r in sh_rows)
    lat_max = max(r["surface_distance_to_stonehenge_km"] for r in sh_rows)
    print(f"stonehenge lateral residual across {len(sh_rows)} configs: "
          f"{lat_min}..{lat_max} km (cell edge ~3.44 km)")

    # radial lane honesty: decoded height vs the site's physical height
    site_h_by_ref = {
        ref.reference_id: (SITE_ELEVATION_M
                           - ref.mean_land_elevation_m) / 1000.0
        for ref in land_refs}
    radial_misfits = sorted({
        (r["profile"], r["zeta_convention"], r["land_ref"]):
            round(r["height_above_land_zero_km"]
                  - site_h_by_ref[r["land_ref"]], 4)
        for r in sh_rows}.items())
    best_radial = min(abs(v) for _, v in radial_misfits)
    print(f"radial misfit (decoded height vs site height): best "
          f"{best_radial} km across declared configs")

    # ---- 3. orange slice under the active 7,7,7 -------------------------
    orange_rows = {}
    for r_os in osl.rows():
        word = int(r_os.vector)
        if r_os.corrected:
            orange_rows[r_os.vector] = sweep(word, r_os.active_shell)
        else:
            orange_rows[r_os.vector] = sweep(word)
    # geometry of the three under one declared config (first row each)
    line3 = [(v, orange_rows[v][0]["lat_deg"], orange_rows[v][0]["lon_deg"])
             for v in osl.ORANGE_SLICE_VECTORS]
    seps = [round(fp.surface_distance_km(line3[i][1], line3[i][2],
                                         line3[i + 1][1], line3[i + 1][2]),
                  3) for i in range(2)]
    print("orange-slice adjacent separations (config 0):", seps, "km")

    # ---- 4. reverse encoding --------------------------------------------
    reverse = {}
    for prof in profiles:
        r = fp.forward(fp.TRAINING_WORD, frame, prof, land_refs[0],
                       mags[0], field_line_step_m=STEP_M)
        inv = fp.inverse(fp.TRAINING_LAT_DEG, fp.TRAINING_LON_DEG,
                         r.height_above_land_zero_km, frame, prof)
        reverse[prof.profile_id] = {
            "decoded_height_km": round(r.height_above_land_zero_km, 4),
            "word": inv.word,
            "reproduces_packet": inv.word == fp.TRAINING_WORD,
            "octal": inv.octal,
            "aliasing_note": inv.aliasing_note,
        }
    site_height_km = site_h_by_ref[land_refs[0].reference_id]
    try:
        fp.inverse(fp.TRAINING_LAT_DEG, fp.TRAINING_LON_DEG,
                   site_height_km, frame, profiles[0])
        site_inverse = "UNEXPECTEDLY_ACCEPTED"
    except Exception as exc:
        site_inverse = f"REFUSED: {exc}"
    all_reverse_ok = all(v["reproduces_packet"] for v in reverse.values())
    print("reverse encoding reproduces packet:", all_reverse_ok)

    # ---- 5. verdict (honest; computed, not chosen) ----------------------
    training_holds = contained and lat_min < 3.5
    underdetermined = {
        "roll_about_training_axis_dof": True,
        "thickness_profile_family_members": len(profiles),
        "land_reference_members": len(land_refs),
        "zeta_convention_members": len(zetas),
        "magnetic_family_active_members": len(mags),
        "magnetic_family_blocked_members":
            len(ms.FAMILY) - len(mags),
        "radial_misfit_km_best_config": best_radial,
        "second_anchor_available": False,
    }
    if authority_ok and training_holds:
        verdict = r1085a.VERDICTS[1]     # YELLOW: authority held,
        #                                  projection underdetermined
    elif authority_ok:
        verdict = r1085a.VERDICTS[2]
    else:
        verdict = "RGCS_R10_8_5A_PACKET_AUTHORITY_LOST_INVESTIGATE"
    print("verdict:", verdict)

    # ---- receipts --------------------------------------------------------
    receipt = {
        "run_id": "R10.8.5A",
        "epoch_year": EPOCH,
        "ground_reference_id": fp.GROUND_REFERENCE_ID,
        "packet_authority_held": authority_ok,
        "training_alignment": align_receipt,
        "trained_frame_cell_contains_training_anchor": contained,
        "sealed_contexts_all_still_miss": all(sealed_misses.values()),
        "stonehenge_lateral_residual_km": {
            "min": lat_min, "max": lat_max,
            "cell_edge_km": 3.44,
            "within_quantization": lat_min < 3.5},
        "stonehenge_radial_misfit_km": dict(
            (f"{k[0]}|{k[1]}|{k[2]}", v) for k, v in radial_misfits),
        "orange_slice": {
            "provenance": osl.provenance(),
            "adjacent_separations_km_config0": seps},
        "reverse_encoding": {
            "by_profile": reverse,
            "site_physical_height_inverse": site_inverse},
        "underdetermined": underdetermined,
        "claims": {
            "SOURCE_ORIGIN_VALIDATED": r1085a.SOURCE_ORIGIN_VALIDATED,
            "training_equality_is_calibration_not_validation": True},
        "verdict": verdict,
    }
    (OUT / "TEST_RECEIPT.json").write_text(
        json.dumps(receipt, indent=1) + "\n", encoding="utf-8")

    sweep_blob = {"stonehenge": sh_rows, "orange_slice": orange_rows}
    (OUT / "SWEEP_ROWS.json").write_text(
        json.dumps(sweep_blob, indent=1) + "\n", encoding="utf-8")

    _write("PROJECTION_AUTHORITY.md", f"""# R10.8.5A projection authority

Commit e5864a5 recovered the F5 | Q22 | S3 packet grammar exactly; this
run does NOT reopen it. The failure it corrects is downstream
projection. The authoritative chain is:

decimal transmission number -> fixed-width binary/octal -> typed packet
fields -> recursive non-Cartesian hierarchical address -> full body /
shell / gravity / magnetic / time / ground-reference transform ->
conventional latitude/longitude (final output only).

Codec layers kept separate (Federation/Terra codec only this run):

{json.dumps(fp.CODEC_LAYERS, indent=1)}

Hierarchical X/Y/Z indices are never accepted as latitude, longitude,
Cartesian coordinates, kilometres or decimal altitude
(`HierarchicalAddress` refusals, locked by tests).

The radial reference authority is the OUTER-SHELL GEOMETRY: the
calculation begins at the outermost operational boundary and proceeds
inward along a gravity-field line. The geometric centre is never an
origin in the production path (`refuse_geocentric_spherical_shortcut`).

Stonehenge (`165876523`) is a HARD TRAINING EQUALITY: it calibrates the
frame and is therefore incapable of validating it.
SOURCE_ORIGIN_VALIDATED: no

Verdict: `{verdict}`
""")

    _write("SHELL_PROFILE_SPEC.md", f"""# ShellProfile specification

Operational stack: shells {list(sp.OPERATIONAL_SHELLS)}, inner to
outer. Shell 3's inner boundary is the land-zero surface; shell 8's
outer boundary is the outermost operational boundary. Shells 0..2 lie
below the land-zero surface and carry no declared thickness (refused).

Bounded candidate family (declared before projection; all retained;
`refuse_fitted_thickness` bans any member fitted to a source vector):

{json.dumps([{
        'profile_id': p.profile_id,
        'thickness_km_at_2025': p.thicknesses_km(2025.0),
        'stack_height_km_2025': round(p.stack_height_km(2025.0), 3),
        'provenance': p.provenance} for p in profiles], indent=1)}

Epoch dependence is linear per band (`ShellBand.rate_km_per_year`);
non-positive thickness under the linear model is refused, not clamped.
No corpus value fixes these thicknesses: the physical shell structure
remains PHYSICAL_VALIDATION_NOT_CLAIMED.
""")

    _write("SHELL3_AVERAGE_LAND_ZERO.md", f"""# Shell-3 zero: average land height

The bottom of shell 3 is referenced to average land height along the
gravity-defined vertical. Banned substitutes, each with a named
refusal locked by tests: mean sea level (untested), spherical Earth
radius, geometric distance from Earth's centre, WGS84 altitude, the
ellipsoid normal.

Declared land-elevation family (both retained):
{json.dumps(lz.MEAN_LAND_ELEVATION_CANDIDATES_M, indent=1)}

Construction: the land-zero surface is the gravity level surface
W = W0_geoid - g_mean * h_land (W0 = {fp.W0_GEOID_M2_S2} m^2/s^2,
g_mean = {fp.G_MEAN_M_S2} m/s^2), i.e. the geoid potential lifted by
the mean land elevation along gravity vertical. An untested MSL
substitution would shift the zero by the mean land elevation itself
({lz.msl_substitution_delta_m()} m) — declared, not hidden.

The reference is epoch-carried; with no declared secular land-height
rate it is epoch-constant, and that constancy is declared rather than
assumed.
""")

    deform_rows = [
        {"magnetic": r["magnetic"], "profile": r["profile"],
         "boundary_deformation_m": r["boundary_deformation_m"]}
        for r in sh_rows if r["land_ref"] == land_refs[0].reference_id
        and r["zeta_convention"] == zetas[0]]
    _write("OUTER_OPERATIONAL_BOUNDARY.md", f"""# Outer operational boundary

The outer boundary of shell 8: land-zero radius along the decoded
direction plus the profile's stack height, then deformed onto the
declared level surface Sigma_8(t) = {{x : W(x,t) + kappa*M(x,t) =
C_8(t)}} (level constant set at the nominal radius on the dipole axis,
the declared reference azimuth).

The inward calculation starts HERE — not at the geometric centre. The
physical core may be offset relative to the magnetic structure and the
ellipsoidal figure, so the outer-shell geometry is the reference
authority.

Boundary deformation from the nominal sphere at the training-word
direction (land ref {land_refs[0].reference_id}, zeta
{zetas[0]}) — includes the gravity-equipotential (ellipticity) part;
the purely magnetic part is the difference from the GRAVITY_ONLY row:

{json.dumps(deform_rows, indent=1)}

Outer-in vs inner-out invariant: checked on every decode
(`OuterInRadialResult.invariant_residual_km`, refused above 1e-9 km).
""")

    dev_rows = sorted({(r['profile'], r['field_line_deviation_m'])
                       for r in sh_rows})
    _write("GRAVITY_FIELD_LINE_INTEGRATION.md", f"""# Gravity field-line integration

Vertical: GRAVITY_VERTICAL, v_g = -grad U / |grad U| (internally the
geodetic W = V + centrifugal with g = +grad W; one sign convention,
stated once). Potential model: GM/r truncation with J2(t) (linear
secular rate {gfl.J2_RATE_PER_YEAR}/yr) and centrifugal term —
SOURCE_ESTABLISHED_PHYSICS as a model; nothing is measured.

Integration: RK4 on dx/ds = gravity_down(x), step {STEP_M} m,
accumulating true path distance from the outer operational boundary
inward (D_in). The straight geocentric radial endpoint is computed
alongside on every run; the lateral deviation between the two is
receipted per projection, never asserted.

Training-word deviations by profile (m, over each profile's D_in):

{json.dumps([{'profile': p, 'field_line_deviation_m': d}
             for p, d in dev_rows], indent=1)}

Locked behaviour: deviation > 0 at mid-latitude, ~0 on the equator and
spin axis (symmetry) — the gravity path differs from the geometric
radial exactly where the model predicts it should.
""")

    _write("MAGNETIC_SHELL_MODEL_AUDIT.md", f"""# Magnetic shell model audit

Magnetics are geometry: Sigma_s(t) = {{x : W(x,t) + kappa*M(x,t) =
C_s(t)}}. The bounded scalar family (all run, all retained;
`refuse_post_reveal_scalar_selection` bans picking the best after
seeing the training anchor; no per-vector offsets — locked by a
signature test):

{json.dumps([{
        'member_id': m.member_id, 'scalar': m.scalar,
        'kappa': m.kappa, 'status': m.status,
        'fractional_uncertainty': (None if m.fractional_uncertainty !=
                                   m.fractional_uncertainty
                                   else m.fractional_uncertainty),
        'note': m.note} for m in ms.FAMILY], indent=1)}

The magnetic source model is a declared tilted centred dipole with
linear epoch drift (moment {ms.DIPOLE_MOMENT_AM2_T0:.3g} A m^2 at
{ms.T0_YEAR}, rate {ms.DIPOLE_MOMENT_RATE_AM2_YR:.3g}/yr; tilt
{ms.DIPOLE_TILT_DEG_T0} deg, rate {ms.DIPOLE_TILT_RATE_DEG_YR} deg/yr).
No real IGRF-14 Gauss coefficient set ships in this repository
(r12.igrf14root: BLOCKED_MISSING_DATA) and that block is honoured: the
crust-corrected and core+lithosphere members REFUSE evaluation instead
of fabricating coefficients. Epoch dependence of the deformation is
locked by test (1975 vs 2025 differ).
""")

    _write("TIME_GROUND_SYNCHRONIZATION.md", f"""# Time and ground synchronization

A projection needs BOTH an epoch and a ground reference; frames
without either are refused (`refuse_frame_without_epoch`,
`refuse_frame_without_ground_reference`).

Time selects: gravity state J2(t), magnetic state (dipole moment, tilt
and axis at t), shell geometry Delta_s(t), long-term frame state.
Ground reference selects: rotational phase, body-fixed alignment,
surface synchronization. This run: epoch {EPOCH}, ground reference
`{fp.GROUND_REFERENCE_ID}`, South-Up handedness carried as a declared
flag (consumed explicitly by rendering, never silently flipping an
axis).

Alignment modes:

* `SEALED_R1082` — the sealed CALFREEZE orientations, reused exactly;
  under every one of them the training cell still MISSES Stonehenge
  (locked by test — the freeze is not retuned in place).
* `TRAINING_EQUALITY_R1085A` — sealed context composed with the
  minimal rotation solved from the Stonehenge training equality ONLY,
  then sealed. Context choice rule (smallest minimal-rotation angle)
  was declared before results were seen; all context angles:

{json.dumps(align_receipt, indent=1)}

The roll about the training-anchor axis is UNDETERMINED and recorded
as such — it is one of the reasons the verdict is YELLOW, not a knob.
""")

    _write("STONEHENGE_CORRECTED_CONTAINMENT.md", f"""# Stonehenge under the corrected projection

Training equality: `165876523` = Stonehenge
({fp.TRAINING_LAT_DEG}, {fp.TRAINING_LON_DEG}). Packet (frozen):
face 4, path (3,3,0,1,2,0,2,1,2,1,1), shell 3, octree X=83 Y=80 Z=461.

## Lateral lane — equality HOLDS under the trained frame

* terminal level-11 cell contains Stonehenge: **{contained}**
* forward-projection surface residual across all {len(sh_rows)}
  declared configurations: **{lat_min}..{lat_max} km** (cell edge
  ~3.44 km). The residual varies with the declared stack height: the
  inward gravity-field line bends away from the cell-centroid ray, so
  taller stacks land farther from the centroid (that drift is the
  physics the layer exists to carry, reported per-config in
  SWEEP_ROWS.json). The best configs are within quantization; cell
  CONTAINMENT above is the primary lateral criterion.
* every sealed R10.8.2 context still misses (freeze not retuned):
  {json.dumps(sealed_misses)}

This satisfies the R10.8.5A instruction: the 2,683 km miss recorded at
e5864a5 was produced under the older projection assumptions; under the
corrected outer-in transform with the declared training alignment the
equality holds. **It is calibration.** The word trained the frame
(2 of 3 rotational DOF; roll undetermined), so this containment cannot
validate anything — and is labelled accordingly.

## Radial lane — honest misfit, reported not hidden

The decoded height above the land-zero surface (shell 3, zeta from
octree Z or midband) vs the site's physical height
(~{SITE_ELEVATION_M} m ASL, i.e. below the average-land zero):

{json.dumps({f'{k[0]}|{k[1]}|{k[2]}': v for k, v in radial_misfits},
            indent=1)}

Best declared configuration still differs by ~{best_radial} km. No
declared profile places shell-3/zeta at the monument's physical
elevation; this is retained as an open structural misfit of the radial
lane (no parameter was added to force it — that would be overfitting a
training point).

SOURCE_ORIGIN_VALIDATED: no
Verdict: `{verdict}`
""")

    _write("ORANGE_SLICE_777_REPORT.md", f"""# Orange slice — active solve 7,7,7

Raw extraction (frozen parser, verbatim, permanent):
shells {osl.provenance()['raw_shells']} for
{list(osl.ORANGE_SLICE_VECTORS)}.

Operator correction (registered, typed, provenance-preserving): the
middle vector `{osl.CORRECTED_VECTOR}`'s shell is corrected 3 -> 7 as
`{osl.CORRECTION_CLAIM}`. The ACTIVE SOLVE uses shells
{osl.provenance()['active_shells']}. The parser is unmodified; no
alternative decimal value was searched for; explaining a physical
7,3,7 pattern is REFUSED (`refuse_physical_737_pattern`, locked).

Corrected-projection placements (first declared config; full sweep in
SWEEP_ROWS.json):

{json.dumps(line3, indent=1)}

Adjacent surface separations: {seps} km. The three project as
same-face (face 4), shell-7 candidates under the trained frame; all
placements are candidates under a training-calibrated frame, nothing
more.
""")

    _write("REVERSE_ENCODING_REPORT.md", f"""# Reverse encoding

Chain: chosen conventional location -> epoch and ground frame ->
magnetically corrected gravity shells -> outer-in shell address ->
hierarchical path -> F5|Q22|S3 -> octal -> decimal transmission number.

Stonehenge at its decoded height, per declared profile:

{json.dumps(reverse, indent=1)}

All profiles reproduce the original packet exactly
({all_reverse_ok}). Aliasing is intrinsic and explicit: the word
stores face + 11 path levels + a 3-bit shell register, so every point
of the same terminal cell and shell band encodes to the same word.

Inverse from the site's PHYSICAL height
({round(site_height_km, 4)} km relative to land-zero, i.e. below it):
{site_inverse}

That refusal is the radial-lane misfit seen from the other side: the
codec cannot address sub-land-zero heights (shells 0..2 undeclared),
so the monument's physical elevation is outside the operational stack.

Per the R10.8.5A instruction, no new source-style coordinate is
generated: the forward and inverse transforms pass the training
equality laterally but the radial lane misfit stands, so a generated
number would still be the product of an incomplete projection.
""")

    _write("REPRODUCTION_RUNLOG.md", f"""# R10.8.5A reproduction runlog

```
python tools/r1085a_outer_in_projection.py
python -m pytest tests/cwatlas/r1085a/ -q
python -m pytest -q          # full regression suite
```

Inputs: packet grammar r12.icosapacket / r12.icosarefine (verbatim,
untouched); sealed R10.8.2 CALFREEZE orientations (verbatim,
untouched); training equality 165876523 = Stonehenge; orange slice
{list(osl.ORANGE_SLICE_VECTORS)} with registered shell correction
3 -> 7 on the middle vector. Epoch {EPOCH}, ground reference
{fp.GROUND_REFERENCE_ID}, field-line step {STEP_M} m.

Deterministic: no RNG, no wall clock; every family member enumerated
in declared order. Outputs: TEST_RECEIPT.json (machine verdict),
SWEEP_ROWS.json (all {len(sh_rows)} x 4 projection rows), and the
eleven narrative receipts in this directory.

Verdict: `{verdict}`
SOURCE_ORIGIN_VALIDATED: no
""")

    print("receipts written to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
