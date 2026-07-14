#!/usr/bin/env python3
"""Generate every numeric table of the RGCS v2 manuscript from rgcs_core.

Emits .tex include files into manuscript/tables/ plus generated_values.tex,
a macro file giving the manuscript its inline numbers, so that no number in
the text is hand-copied. Golden coherence datasets are re-analysed from the
CSVs with rgcs_core.coherence.

Run AFTER tools/make_figures.py (it merges fig_values.json):
    python3 tools/make_figures.py && python3 tools/make_tables.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from rgcs_core.uncertainty import default_wave_speed
from rgcs_core.geometry import (
    CrystalGeometry,
    SpiralGeometry,
    angle_audit,
    crystal_geometry,
    node_positions,
    spiral_metrics,
)
from rgcs_core.harmonics import (
    axial_half_wave,
    harmonic_classification,
    ladder_length_mm,
)
from rgcs_core.compact_modes import compact_mode_spectrum
from rgcs_core.resonance import (
    classify_resonance,
    corrected_resonance_offset,
    epsilon_q,
    resonance_offset,
    sweep_span_hz,
)
from rgcs_core.coupled_modes import coupled_two_mode
from rgcs_core.loading import added_modal_mass_g, loading_factor
from rgcs_core.drive import (
    drive_sequence,
    micro_pulse_metrics,
    phase_residue_cycles,
    sound_key_macro,
)
from rgcs_core.coherence import (
    DEFAULT_WINDOW_S,
    coherence_series,
    initial_phase_estimate,
    instantaneous_frequency,
    instantaneous_phase,
    noise_baseline_theory,
    phase_linearity,
    phase_locking_value,
    phase_rate_shear_scalar,
    rayleigh_test,
)
from rgcs_core.experiments import current_to_electron_rate

TAB_DIR = REPO_ROOT / "manuscript" / "tables"
TAB_DIR.mkdir(parents=True, exist_ok=True)
GOLDEN_DIR = REPO_ROOT / "experiments" / "sample_data" / "golden_coherence"
FIG_VALUES = REPO_ROOT / "manuscript" / "figures" / "fig_values.json"

MACROS: dict[str, str] = {}


def macro(name: str, value: str) -> None:
    assert name.isalpha(), f"macro names must be alphabetic: {name}"
    MACROS[name] = value


def write(name: str, content: str) -> None:
    out = TAB_DIR / name
    out.write_text(content)
    print(f"wrote {out.relative_to(REPO_ROOT)}")


def uvd(x) -> dict:
    return x if isinstance(x, dict) else x.to_dict()


def latex_sci(x: float, digits: int = 1) -> str:
    """Format a float as LaTeX scientific notation, e.g. 6.4 \\times
    10^{-35}, for use inside math mode (QA-D-15: never emit raw
    e-notation into a math environment)."""
    s = f"{x:.{digits}e}"
    mant, exp = s.split("e")
    return f"{mant} \\times 10^{{{int(exp)}}}"


def load_iq(path: Path):
    d = np.genfromtxt(path, delimiter=",", names=True)
    return d


# ----------------------------------------------------------------------
# Table 1 — golden reference values (ledger Part E) recomputed live
# ----------------------------------------------------------------------
def tab_golden_values() -> None:
    v = default_wave_speed()
    ladder_const = ladder_length_mm(1)
    l5 = ladder_length_mm(5)
    l7 = ladder_length_mm(7)
    f110 = axial_half_wave(110.0)
    err110_hz = f110.mean - 7 * 4096.0
    err110_pct = err110_hz / (7 * 4096.0) * 100.0
    h116 = harmonic_classification(116.0)
    spec = compact_mode_spectrum(v_chi=v, compact_radius_mm=100.0, n_max=1)
    fc1 = uvd(spec["modes"][0]["frequency"])["mean"]
    eps0 = resonance_offset(40960.0, 20480.0)
    two = coupled_two_mode(1000.0, 1000.0, 10.0)
    kh = loading_factor(152.0 / (2 * 0.152) * 2 * 0.152, 1.0)  # placeholder; real below
    kh = 152.0 / 154.052734375  # length route shown separately in loading table
    kh_meas = loading_factor(4041.398, 4096.0)  # not used in table
    kh = loading_factor(f_loaded_hz=axial_half_wave(154.052734375).mean * (152.0 / 154.052734375) ** -1, f_free_hz=1.0)
    # -- the golden k_H is defined as the ratio 152/154.052734375 (RG-10):
    kh = 152.0 / 154.052734375
    dm = added_modal_mass_g(kh, 154.0, 0.5)
    sp = spiral_metrics(SpiralGeometry())
    aud = angle_audit(51.843)
    seq = {m: drive_sequence(m) for m in ("standard", "half_spacing", "double_rate")}
    coil = micro_pulse_metrics(pulse_width_us=1.3, voltage_v=60.0, peak_current_a=3.0,
                               rise_time_us=1.3)
    erate = current_to_electron_rate(1e-14)
    shear = phase_rate_shear_scalar(1.0, 1.0, 1.0)

    def cyc(m):
        d = seq[m]
        return d

    rows = []
    rows.append(("G-01", r"ladder constant $v_L/(2f_0)$",
                 f"{ladder_const.mean:.9f} mm $\\pm{ladder_const.u_rel*100:.0f}\\%$", "Derived"))
    rows.append(("G-02", r"$L_5$", f"{l5.mean:.9f} mm $\\pm{l5.u_rel*100:.0f}\\%$", "Derived"))
    rows.append(("G-03", r"$L_7$", f"{l7.mean:.9f} mm $\\pm{l7.u_rel*100:.0f}\\%$", "Derived"))
    rows.append(("G-04", r"$f_{ax}(110\,\mathrm{mm})$",
                 f"{f110.mean:.4f} Hz $\\pm{f110.u_rel*100:.0f}\\%$; $+{err110_hz:.5f}$ Hz $=+{err110_pct:.5f}\\%$ vs $7f_0$",
                 "Derived-from-Hypothesis"))
    rows.append(("G-05", r"$f_{ax}(116\,\mathrm{mm})$; class set",
                 f"{uvd(h116['axial_frequency_hz'])['mean']:.4f} Hz; $N_{{\\rm eff}}={h116['n_eff']:.6f}$; $\\mathcal{{N}}=\\{{{', '.join(str(x) for x in h116['harmonic_class_set'])}\\}}$",
                 "Derived"))
    rows.append(("G-06", r"compact term $n{=}1$ ($v_\chi{=}\bar v_L$, $R_\chi{=}100$ mm)",
                 f"{fc1:.7f} Hz $\\pm5\\%$", "Hypothesis-conditioned"))
    rows.append(("G-07", r"$\epsilon_R^{(f)}(40960, 20480, p{=}2)$", f"{eps0:.1f} (exact)", "Derived"))
    rows.append(("G-08", r"hybrids for $f_A{=}f_B{=}1000$ Hz, $g{=}10$ Hz",
                 f"{two['lower_hybrid_hz']:.0f} / {two['upper_hybrid_hz']:.0f} Hz", "Established"))
    rows.append(("G-09", r"$k_H(152/154.052734375)$; $\Delta M_H(154\,\mathrm{g},\eta{=}0.5)$",
                 f"{kh:.10f}; {dm['added_modal_mass_g']:.7f} g", "Hypothesis-conditioned"))
    rows.append(("G-10", r"$a(q{=}e)$; $r\kappa$",
                 f"{sp['pitch_parameter_a']:.11f}; {sp['curvature_invariant_rkappa']:.11f}", "Established"))
    rows.append(("G-11", r"$\arctan\sqrt{\varphi}$ vs $51.843^\circ$",
                 f"{aud['atan_sqrt_phi_deg']:.7f}$^\\circ$; $\\Delta = {aud['atan_sqrt_phi_deg']-51.843:+.6f}^\\circ$",
                 "Established arithmetic"))
    rows.append(("G-12", r"exact-cycle drive families (cycles)",
                 " / ".join(f"{seq[m]['exact_cycles']}" for m in ("standard", "half_spacing", "double_rate")),
                 "Derived"))
    rows.append(("G-13", r"coil inference (60 V, 1.3 \si{\micro s}, 3 A)",
                 f"$L \\approx {coil['inferred_inductance_uh']:.0f}$ \\si{{\\micro H}}; $E \\approx {coil['stored_energy_uj']:.0f}$ \\si{{\\micro J}}",
                 "Derived (resistance neglected)"))
    rows.append(("G-14", r"electron-count correction ($10^{-14}$ A)",
                 f"{erate:,.2f} e/s (not 2,000)", "Established arithmetic"))
    rows.append(("G-15", r"shear-scalar identity $\sigma_\phi^2(\Omega,\Omega,\Omega)$",
                 f"{shear['sigma_phi2_s2']:.1f} (exact)", "Established"))
    half_nominal = seq["half_spacing"]["nominal_cycles"]
    rows.append(("D-13", rf"phase residue $r_\phi({half_nominal:.3f})$",
                 f"{phase_residue_cycles(half_nominal):+.3f} cycles",
                 "Derived"))

    body = "\n".join(f"{i} & {d} & {val} & {cl} \\\\" for i, d, val, cl in rows)
    write("tab_golden_values.tex", GOLDEN_TEMPLATE.format(body=body))

    # macros used inline
    macro("gvLadderConst", f"{ladder_const.mean:.9f}")
    macro("gvLfive", f"{l5.mean:.6f}")
    macro("gvLseven", f"{l7.mean:.6f}")
    macro("gvFaxOneTen", f"{f110.mean:.3f}")
    macro("gvFaxOneTenErrHz", f"{err110_hz:.3f}")
    macro("gvFaxOneTenErrPct", f"{err110_pct:.4f}")
    macro("gvFaxOneTenSigma", f"{f110.sigma:.0f}")
    macro("gvCompactN", f"{fc1:.4f}")
    macro("gvKH", f"{kh:.7f}")
    macro("gvDMH", f"{dm['added_modal_mass_g']:.4f}")
    macro("gvSpiralA", f"{sp['pitch_parameter_a']:.8f}")
    macro("gvRkappa", f"{sp['curvature_invariant_rkappa']:.8f}")
    macro("gvAngleGolden", f"{aud['atan_sqrt_phi_deg']:.6f}")
    macro("gvAngleDelta", f"{aud['atan_sqrt_phi_deg']-51.843:+.6f}")
    macro("gvCoilL", f"{coil['inferred_inductance_uh']:.0f}")
    macro("gvCoilE", f"{coil['stored_energy_uj']:.0f}")
    macro("gvElectronRate", f"{erate:,.0f}")
    macro("gvResidueHalf", f"{phase_residue_cycles(half_nominal):+.3f}")
    macro("gvHalfNominal", f"{half_nominal:.3f}")  # QA-D-26: generated,
    # not hand-typed, from rgcs_core.drive.drive_sequence
    macro("gvHybridLo", f"{two['lower_hybrid_hz']:.0f}")
    macro("gvHybridHi", f"{two['upper_hybrid_hz']:.0f}")


GOLDEN_TEMPLATE = r"""% Auto-generated by tools/make_tables.py from rgcs_core — do not edit.
\small
\begin{{longtable}}{{@{{}}l p{{0.30\linewidth}} p{{0.37\linewidth}} p{{0.15\linewidth}}@{{}}}}
\caption{{Golden reference values (evidence-ledger Part E), recomputed at build
time by \texttt{{rgcs\_core}} 2.0.0. Ladder and compact values carry the
$\pm u_v$ systematic band of RGCS-M.10.}}\label{{tab:golden}}\\
\toprule
ID & quantity & value (live) & label \\
\midrule
\endfirsthead
\toprule
ID & quantity & value (live) & label \\
\midrule
\endhead
{body}
\bottomrule
\end{{longtable}}
\normalsize
"""


# ----------------------------------------------------------------------
# Table 2 — worked harmonic-classification examples
# ----------------------------------------------------------------------
def tab_worked_examples() -> None:
    rows = []
    for L in (154.052734375, 110.0, 116.0):
        h = harmonic_classification(L)
        f = uvd(h["axial_frequency_hz"])
        cls = "\\{" + ", ".join(str(x) for x in h["harmonic_class_set"]) + "\\}"
        amb = "yes" if h["ambiguous"] else "no"
        rows.append(
            f"{L:.6f} & {f['mean']:.1f} & [{f['lo_1sigma']:.0f}, {f['hi_1sigma']:.0f}] & "
            f"{h['n_eff']:.4f} & {h['nearest_harmonic']} & {cls} & {amb} & "
            f"{h['frequency_error_fraction']*100:+.3f}\\% \\\\")
        if L == 116.0:
            macro("gvNeffOneSixteen", f"{h['n_eff']:.4f}")
            macro("gvFaxOneSixteen", f"{f['mean']:.1f}")
            macro("gvClassSetOneSixteen", "\\{" + ", ".join(str(x) for x in h["harmonic_class_set"]) + "\\}")
    body = "\n".join(rows)
    write("tab_worked_examples.tex", rf"""% Auto-generated by tools/make_tables.py from rgcs_core — do not edit.
\begin{{table}}[t]
\centering\small
\caption{{Set-valued harmonic classification (RGCS-M.12) at $u_v = 0.05$,
$f_0 = 4096$ Hz. Fractional error is quoted against $N_{{\rm nearest}} f_0$;
by the interpretation rule (RGCS-M.11, D-04) every value here is
Derived-from-Hypothesis arithmetic, never confirmation.}}
\label{{tab:worked}}
\begin{{tabular}}{{@{{}}rrrrrccr@{{}}}}
\toprule
$L$ (mm) & $f_{{ax}}$ (Hz) & $\pm1\sigma$ band (Hz) & $N_{{\rm eff}}$ &
nearest $N$ & class set $\mathcal{{N}}$ & ambiguous & error \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
""")


# ----------------------------------------------------------------------
# Table 3 — compact spectrum with parity and intervals
# ----------------------------------------------------------------------
def tab_compact_spectrum() -> None:
    spec = compact_mode_spectrum(base_frequency_hz=0.0, v_chi=default_wave_speed(),
                                 compact_radius_mm=100.0, n_max=6,
                                 parity="all", include_zero_mode=True)
    kap = uvd(spec["kappa_chi_hz"])
    macro("gvKappaChi", f"{kap['mean']:.2f}")
    rows = []
    for m in spec["modes"]:
        f = uvd(m["frequency"])
        rows.append(f"{m['n']} & {m['parity']} & {f['mean']:.2f} & "
                    f"[{f['lo_1sigma']:.0f}, {f['hi_1sigma']:.0f}] \\\\")
    body = "\n".join(rows)
    write("tab_compact_spectrum.tex", rf"""% Auto-generated by tools/make_tables.py from rgcs_core — do not edit.
\begin{{table}}[t]
\centering\small
\caption{{Compact-coordinate spectrum for $f_b = 0$,
$\kappa_\chi = {kap['mean']:.2f}$ Hz $\pm{kap['u_rel']*100:.0f}\%$
($v_\chi = \bar v_L$, $R_\chi = 100$ mm placeholder, D-21). The $n = 0$
member is excluded unconditionally at $f_b = 0$ (RGCS-M.17). Intervals are
the mandatory $\pm u_v$ propagation of RGCS-M.15.}}
\label{{tab:compact}}
\begin{{tabular}}{{@{{}}rlrr@{{}}}}
\toprule
$n$ & parity & $f_n$ (Hz) & $\pm1\sigma$ band (Hz) \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
""")


# ----------------------------------------------------------------------
# Table 4 — resonance-offset classes with uncertainty
# ----------------------------------------------------------------------
def tab_resonance_classes() -> None:
    f_x, q_m, q_x = 20480.0, 1000.0, 800.0
    eq = epsilon_q(q_m, q_x)
    macro("gvEpsQ", f"{eq:.4e}".replace("e-0", r"\times 10^{-") + "}")
    macro("gvEpsQPlain", f"{eq*1e3:.3f}")
    rows = []
    for fm, ueps in ((40960.0, 2e-4), (40970.0, 2e-4), (41100.0, 2e-4),
                     (41800.0, 3e-4), (45000.0, 5e-4), (61440.0, 1e-3)):
        eps = resonance_offset(fm, f_x)
        c = classify_resonance(eps, q_m, q_x, u_eps=ueps)
        span = sweep_span_hz(fm, f_x, q_m, q_x)
        cls = str(c.get("resonance_class", c.get("class", "?"))).replace("_", " ")
        rows.append(f"{fm:.0f} & {eps:+.5f} & \\num{{{ueps:.0e}}} & {cls.lower()} & {span:.0f} \\\\")
    body = "\n".join(rows)
    corr = corrected_resonance_offset(40960.0, 20480.0,
                                      deltas_m={"loading": -0.004, "T": 0.0008},
                                      deltas_x={"fixture": 0.001},
                                      u_f_m_hz=2.0, u_f_x_hz=1.5)
    macro("gvCorrEps", f"{corr['epsilon_corrected']:+.5f}")
    macro("gvCorrEpsU", f"{corr['u_epsilon']:.5f}")
    write("tab_resonance_classes.tex", rf"""% Auto-generated by tools/make_tables.py from rgcs_core — do not edit.
\begin{{table}}[t]
\centering\small
\caption{{$Q$-derived resonance classes (RGCS-M.20) for a target mode
$f_x = 20480$ Hz, $p = 2$, $Q_m = 1000$, $Q_x = 800$
($\epsilon_Q = 1/Q_{{\rm eff}} = \num{{{eq:.3e}}}$). A class string without
$u(\epsilon_R)$ is non-compliant (policy \S3.4). Sweep spans include the
six-linewidth floor of RGCS-M.21 (engineering heuristic).}}
\label{{tab:classes}}
\begin{{tabular}}{{@{{}}rrrlr@{{}}}}
\toprule
$f_m$ (Hz) & $\epsilon_R^{{(f)}}$ & $u(\epsilon_R)$ & class & sweep span (Hz) \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
""")


# ----------------------------------------------------------------------
# Table 5 — drive timing families (exact-cycle engineering)
# ----------------------------------------------------------------------
def tab_drive_families() -> None:
    rows = []
    for mode in ("standard", "half_spacing", "double_rate"):
        d = drive_sequence(mode)
        p = d
        rows.append(
            f"{mode.replace('_', ' ')} & {p['on_ms']:.0f} / {p['spacing_ms']:.0f} / {p['pause_ms']:.0f} & "
            f"{p['macro_ms']:.6g} & {p['duty']:.4f} & {p['nominal_cycles']:.3f} & "
            f"{p['exact_cycles']} = {p['on_total_cycles']}+{p['spacing_total_cycles']}+{p['pause_cycles']} & "
            f"{p['phase_residue_cycles']:+.3f} \\\\")
    body = "\n".join(rows)
    write("tab_drive_families.tex", rf"""% Auto-generated by tools/make_tables.py from rgcs_core — do not edit.
\begin{{table}}[t]
\centering\small
\caption{{Opposed-coil envelope families at the 4096 Hz carrier (RG-12).
Millisecond values are Source claims from the JH log; the exact-cycle
allocations are Derived engineering refinements that do not replace the
source-stated values. The phase residue $r_\phi$ is defined on cycle counts
only (D-13).}}
\label{{tab:drive}}
\begin{{tabular}}{{@{{}}lcccccc@{{}}}}
\toprule
family & ON/spacing/pause (ms) & macro (ms) & duty & nominal cycles &
exact allocation & $r_\phi$ \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
""")
    d = drive_sequence("half_spacing")
    macro("gvHalfMacroMs", f"{d['macro_ms']:.6g}")
    macro("gvHalfCycles", str(d["exact_cycles"]))


# ----------------------------------------------------------------------
# Table 6 — spiral / node worked example
# ----------------------------------------------------------------------
def tab_spiral_node() -> None:
    sp = spiral_metrics(SpiralGeometry())
    per_turn = np.asarray(sp["per_turn_compact_radius_mm"], dtype=float)
    g = CrystalGeometry(length_mm=154.052734375, wide_diameter_mm=32.0,
                        narrow_diameter_mm=25.0)
    cg = crystal_geometry(g)
    # Node worked example uses the corpus default cap heights (RGCS-M.39
    # reference values: h_f = 17.415434 mm, h_m = 14.812763 mm — Source-claim
    # dimensions of the default N=5 specimen).
    npos = node_positions(154.052734375, 17.415434, 14.812763)
    macro("gvXm", f"{npos['metric_center_mm']:.4f}")
    macro("gvXg", f"{npos['node_prior_mm']:.4f}")
    macro("gvXgMale", f"{npos['node_prior_male_frame_mm']:.4f}")
    macro("gvHf", f"{17.415434:.6f}")
    macro("gvHm", f"{14.812763:.6f}")
    macro("gvMass", f"{cg['mass_g']:.2f}")
    macro("gvVolume", f"{cg['volume_cm3']:.3f}")
    macro("gvEllThreeD", f"{sp['path_length_3d_mm']:.3f}")
    macro("gvEllPl", f"{sp['planar_arc_length_mm']:.3f}")
    macro("gvRchiPrior", f"{sp['compact_radius_prior_mm']:.3f}")
    macro("gvClosedForm", f"{sp['retired_closed_form_mm']:.3f}")
    macro("gvClosedFormErrPct", f"{sp['retired_closed_form_rel_error']*100:.2f}")
    macro("gvPerTurnRadii", ", ".join(f"{x:.2f}" for x in per_turn))
    kap_prior = uvd(compact_mode_spectrum(
        v_chi=default_wave_speed(),
        compact_radius_mm=sp["compact_radius_prior_mm"], n_max=1)["kappa_chi_hz"])
    macro("gvKappaPrior", f"{kap_prior['mean']:.0f}")

    rows = [
        (r"pitch parameter $a = \ln q/2\pi$", f"{sp['pitch_parameter_a']:.9f}", "Established"),
        (r"curvature invariant $r\kappa$", f"{sp['curvature_invariant_rkappa']:.9f}", "Established"),
        (r"exact planar arc length $\ell_{pl}$", f"{sp['planar_arc_length_mm']:.3f} mm", "Established"),
        (r"\textbf{numeric 3D path length $\ell_{3D}$ (authoritative)}",
         f"\\textbf{{{sp['path_length_3d_mm']:.3f} mm}} (converged to $10^{{-6}}$)", "Derived"),
        (r"retired closed form $\ell_{pl}\sqrt{1+(H/\ell_{pl})^2}$",
         f"{sp['retired_closed_form_mm']:.3f} mm ({sp['retired_closed_form_rel_error']*100:+.2f}\\% vs $\\ell_{{3D}}$)",
         "labelled approximation"),
        (r"mean compact-radius prior $R_\chi^{(s)} = \ell_{3D}/2\pi T$",
         f"{sp['compact_radius_prior_mm']:.3f} mm", "Hypothesis (A-07)"),
        (r"per-turn radii $R_{\chi,k} = \ell_k/2\pi$",
         ", ".join(f"{x:.2f}" for x in per_turn) + " mm", "Hypothesis (alt.)"),
        (r"metric centre $x_m = L/2$", f"{npos['metric_center_mm']:.4f} mm", "Established"),
        (r"node prior $x_g = (L + h_f - h_m)/2$ (female frame)",
         f"{npos['node_prior_mm']:.4f} mm", "Derived (prior only)"),
        (r"same point, male frame $L - x_g$",
         f"{npos['node_prior_male_frame_mm']:.4f} mm", "frame conversion"),
    ]
    body = "\n".join(f"{a} & {b} & {c} \\\\" for a, b, c in rows)
    write("tab_spiral_node.tex", rf"""% Auto-generated by tools/make_tables.py from rgcs_core — do not edit.
\begin{{table}}[t]
\centering\small
\caption{{Spiral-path and node-coordinate worked example. Spiral defaults
$q = e$, $T = 4$, $R_0 = 60$ mm, $H = 80$ mm, $p_z = 1.5$; crystal
$L = 154.052734$ mm, $D_w/D_n = 32/25$ mm, $N_f = 6$,
$\alpha_f/\alpha_m = 51.843^\circ/60^\circ$ (angle values are Source claims);
node rows use the corpus default cap heights $h_f = 17.415434$ mm,
$h_m = 14.812763$ mm. Node coordinates are in the female-apex frame
($x$ measured from the wide apex).}}
\label{{tab:spiralnode}}
\begin{{tabular}}{{@{{}}p{{0.47\linewidth}} p{{0.30\linewidth}} l@{{}}}}
\toprule
quantity & value (live) & status \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
""")


# ----------------------------------------------------------------------
# Table 7 — golden coherence datasets re-analysed
# ----------------------------------------------------------------------
def tab_coherence_golden() -> None:
    fs = 100000.0
    nw = int(round(DEFAULT_WINDOW_S * fs))
    bw = noise_baseline_theory(nw)
    macro("gvBaselineNw", f"{bw:.4f}")
    macro("gvNw", str(nw))
    rows = []

    # case a — white noise
    d = load_iq(GOLDEN_DIR / "case_a_white_noise.csv")
    z = d["I"] + 1j * d["Q"]
    _, c = coherence_series(z, fs)
    macro("gvCaseACoh", f"{np.mean(c):.4f}")
    rows.append(("(a) circular white noise",
                 f"$\\langle\\mathcal{{C}}_w\\rangle = {np.mean(c):.3f}$ vs theory $b_w = {bw:.3f}$",
                 "baseline, not zero"))

    # case b — pure tone
    d = load_iq(GOLDEN_DIR / "case_b_pure_sinusoid.csv")
    z = d["I"] + 1j * d["Q"]
    _, c = coherence_series(z, fs)
    pl = phase_linearity(z)
    fmean = float(np.mean(instantaneous_frequency(z, fs)))
    macro("gvCaseBCoh", f"{np.min(c):.6f}")
    macro("gvCaseBFreq", f"{fmean:.1f}")
    rows.append(("(b) pure tone 5 kHz",
                 f"$\\min\\mathcal{{C}}_w = {np.min(c):.4f}$; PL $= {pl:.4f}$; $\\langle f_{{\\rm inst}}\\rangle = {fmean:.1f}$ Hz",
                 "unity coherence"))

    # case c — decaying tone
    d = load_iq(GOLDEN_DIR / "case_c_decaying_sinusoid.csv")
    z = d["I"] + 1j * d["Q"]
    t = d["t_s"]
    _, c = coherence_series(z, fs)
    amp = np.abs(z)
    late = slice(int(0.8 * c.size), None)
    macro("gvCaseCCohLate", f"{np.mean(c[late]):.3f}")
    macro("gvCaseCAmpLatePct", f"{np.mean(amp[int(0.8*amp.size):])/amp.max()*100:.1f}")
    rows.append(("(c) decaying tone in noise",
                 f"late-window $\\langle\\mathcal{{C}}_w\\rangle = {np.mean(c[late]):.3f} > b_w$ while amplitude $\\to {np.mean(amp[int(0.8*amp.size):])/amp.max()*100:.1f}\\%$ of peak",
                 "order outlives amplitude"))

    # case d — random-phase runs
    d = np.genfromtxt(GOLDEN_DIR / "case_d_random_phase_runs.csv", delimiter=",", names=True)
    runs = np.unique(d["run"].astype(int))
    # Unified per-run initial-phase estimator (QA-D-03): arg z(0) mod 2pi,
    # shared with tools/make_figures.py via rgcs_core.coherence.
    phases, cohs = [], []
    for r in runs:
        m = d["run"].astype(int) == r
        z = d["I"][m] + 1j * d["Q"][m]
        phases.append(initial_phase_estimate(z))
        _, c = coherence_series(z, fs)
        cohs.append(float(np.mean(c)))
    rt = rayleigh_test(np.asarray(phases))
    macro("gvCaseDRuns", str(len(runs)))
    macro("gvCaseDRayP", f"{rt['p']:.2f}")
    macro("gvCaseDRayZ", f"{rt['Z']:.2f}")
    macro("gvCaseDCoh", f"{np.mean(cohs):.3f}")
    rows.append((f"(d) {len(runs)} random-phase runs",
                 f"per-run $\\langle\\mathcal{{C}}_w\\rangle = {np.mean(cohs):.3f}$; ensemble Rayleigh $Z_R = {rt['Z']:.2f}$, $p = {rt['p']:.2f}$",
                 "spontaneous-order signature"))

    # case f — pump leakage trap
    d = np.genfromtxt(GOLDEN_DIR / "case_f_pump_leakage.csv", delimiter=",", names=True,
                      dtype=None, encoding="utf-8")
    cond = np.asarray([str(x) for x in d["condition"]])
    msk = cond == "sample"
    runs = np.unique(d["run"][msk].astype(int))
    phs = []
    for r in runs:
        m = msk & (d["run"].astype(int) == r)
        z = d["I"][m] + 1j * d["Q"][m]
        phs.append(initial_phase_estimate(z))
    rtf = rayleigh_test(np.asarray(phs))
    macro("gvCaseFRayP", f"{rtf['p']:.2e}")
    rows.append(("(f) pump-leakage trap",
                 f"ensemble Rayleigh $p = {latex_sci(rtf['p'], 1)}$ (uniformity rejected): drive-imprinted, Stage-III claim blocked",
                 "driven, not spontaneous"))

    body = "\n".join(f"{a} & {b} & {c} \\\\" for a, b, c in rows)
    write("tab_coherence_golden.tex", rf"""% Auto-generated by tools/make_tables.py from rgcs_core — do not edit.
\begin{{table}}[t]
\centering\small
\caption{{Golden coherence datasets re-analysed at build time with
\texttt{{rgcs\_core.coherence}} ($w = 2$ ms, $N_w = {nw}$, hop 0.5 ms;
$b_w = (2\sqrt{{\pi}}/3)/\sqrt{{N_w}} = {bw:.4f}$). Per-run initial phases
are the unified estimator $\varphi_0 = \arg z(0) \bmod 2\pi$
(\texttt{{initial\_phase\_estimate}}). All datasets are Derived
synthetic records with known ground truth; none are measurements.}}
\label{{tab:goldencoh}}
\begin{{tabular}}{{@{{}}p{{0.22\linewidth}} p{{0.52\linewidth}} p{{0.17\linewidth}}@{{}}}}
\toprule
case & recomputed metrics & lesson \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
""")


# ----------------------------------------------------------------------
# Table 8 — protocol summary (branches, hypotheses, gates)
# ----------------------------------------------------------------------
def tab_protocol_summary() -> None:
    rows = [
        ("1 modal survey", "H-01, H-01a, H-03, H-04, H-07, H-09 (partial)",
         r"$f_n$, $Q_n$, $\gamma_n$, $\hat x_e$, parity phases",
         "fixture-only; glass dummy; reference resonator"),
        ("2 electrode pulse", "H-14 (primary), H-12, H-13, H-11",
         r"$G_c$, $d_c$, $(\mathcal{C}_w, w, b_w)$, $Z_R$, $\tau_c$",
         "shielded RC dummy; dummy electrodes; sham; injection"),
        ("3 sound key", "H-02 (primary), H-12, H-14, H-11",
         r"$\epsilon$-resolved $d_c$; key vs matched off-key",
         "speaker-only; matched-SPL off-key; muted sham"),
        ("4 opposed coil", "H-14 (primary), H-09, H-10, H-12, H-13, H-11",
         r"mode-band I/Q; ring-up/ringdown envelopes; $\tau_c$",
         "no-crystal coils; resistor dummy; rotated coil"),
        ("5 human loading", "H-08, H-08b",
         r"$k_H$ per mode; repeatability variance; $\Delta M_H$",
         "fixture/surrogate loads; calibrated masses; ethics gate"),
        ("6 spiral cone", "H-06, H-06a, H-05",
         r"apex-band $G_c$, $d_c$; fitted $\kappa_\chi$ vs priors",
         "disk, plain cone, Archimedean, flat log spiral"),
        ("7 water", "none (exploratory)",
         "pre/post chemistry deltas; blinded photo scoring",
         "sham; thermal; evaporation; crystal-absent; ultrasonic"),
        ("8 spatial mapping", "H-03, H-10, H-11, H-13",
         r"$\sigma_\phi^2(t)$, $\Sigma_\phi$, $\bar\Sigma_\phi(t)$; PLV",
         "rigid dummy bar; common injection; channel scrambling"),
    ]
    body = "\n".join(f"{a} & {b} & {c} & {d} \\\\" for a, b, c, d in rows)
    write("tab_protocol_summary.tex", rf"""% Auto-generated by tools/make_tables.py from rgcs_core — do not edit.
\begin{{table}}[t]
\centering\small
\caption{{Pre-registered experimental branches (EXPERIMENT\_PROTOCOL v1.0.0).
Every branch inherits the \S0 contract: shared reference clock, single-shot
I/Q, $N \geq 100$ runs before ensemble-phase claims, acquisition
$\geq 2.5\times$ past drive-off, controls before attribution, coherence
triplet reporting, per-run sensor geometry, artifact register,
apparatus-specific thresholds.}}
\label{{tab:protocol}}
\begin{{tabular}}{{@{{}}p{{0.13\linewidth}} p{{0.24\linewidth}} p{{0.27\linewidth}} p{{0.27\linewidth}}@{{}}}}
\toprule
branch & hypotheses & primary observables & key controls \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
""")


# ----------------------------------------------------------------------
# Macro file
# ----------------------------------------------------------------------
def write_macros() -> None:
    # merge figure-derived values
    if FIG_VALUES.exists():
        fv = json.loads(FIG_VALUES.read_text())
        macro("gvAnisoTauMs", f"{fv['aniso_tau_s']*1e3:.1f}")
        macro("gvAnisoTauTruthMs", f"{fv['aniso_tau_truth_ms']:.0f}")
        daic = fv["aniso_aic"]["no_change"] - fv["aniso_aic"]["exponential"]
        macro("gvAnisoDAICNull", f"{daic:.0f}")
        daic2 = fv["aniso_aic"]["damped_oscillatory"] - fv["aniso_aic"]["exponential"]
        macro("gvAnisoDAICDamped", f"{daic2:.0f}")
        macro("gvAnisoBest", fv["aniso_best_model"].replace("_", " "))
        macro("gvACSplit", f"{fv['ac_splitting_hz']:.0f}")
        macro("gvACRg", f"{fv['ac_rg']:.2f}")
        macro("gvACGamma", f"{fv['ac_linewidth_hz']:.2f}")
    v = default_wave_speed()
    macro("gvVL", f"{v.mean:.0f}")
    macro("gvUv", f"{v.u_rel*100:.0f}")
    lines = ["% Auto-generated by tools/make_tables.py from rgcs_core — do not edit."]
    for k, val in sorted(MACROS.items()):
        lines.append(f"\\newcommand{{\\{k}}}{{{val}}}")
    write("generated_values.tex", "\n".join(lines) + "\n")


def main() -> None:
    tab_golden_values()
    tab_worked_examples()
    tab_compact_spectrum()
    tab_resonance_classes()
    tab_drive_families()
    tab_spiral_node()
    tab_coherence_golden()
    tab_protocol_summary()
    write_macros()


if __name__ == "__main__":
    main()
