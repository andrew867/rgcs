"""LiNiPO4 ferrotoroidic IOME reference (Agent M11; RGCS-V4-EQ-001/
002/003; material reference.linipo4; primary source SRC-V4-01
metadata-only — numeric presets come from the pack, SRC-V4-00).

Reduced-order model of inverse optical magnetoelectric domain writing:
the writing bias is controlled by the light PROPAGATION DIRECTION
(k̂·T̂ channel), not polarization — with mandatory discriminators
against helicity (inverse Faraday) and thermal (optical annealing)
comparators. Never alpha quartz."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..multiphysics import applicability, get_material, make_result
from ..multiphysics import not_applicable_result

MODULE_ID = "rscs2.refmodels.iome_linipo4"

#: registered LiNiPO4 presets (pack-supplied, SRC-V4-00; the primary
#: paper SRC-V4-01 is metadata-only locally, DV4C-003)
TRANSITION_K = 20.8
DD_BANDS_NM = (1300.0, 1400.0, 1670.0)
PUMP_PRESET_NM = 1700.0
PROBE_PRESET_NM = 1450.0
BAND_WIDTH_NM = 120.0


# --- toroidal state (EQ-001) ----------------------------------------------

@dataclass(frozen=True)
class ToroidalState:
    """Magnetic toroidal moment T = 1/2 sum_i r_i x S_i.
    Frame: orthorhombic abc, toroidal axis || b (declared phase).
    Origin policy: sublattice-centered (declared; microscopic T is
    origin-dependent for uncompensated moments — LiNiPO4's AFM
    compensation makes the declared T origin-robust)."""
    t_vector_a_m2: tuple      # (Ta, Tb, Tc)
    frame: str = "orthorhombic abc; toroidal axis || b"
    origin_policy: str = "sublattice-centered (declared)"

    @staticmethod
    def from_spins(r_m: np.ndarray, s_a_m2: np.ndarray
                   ) -> "ToroidalState":
        t = 0.5 * np.cross(np.asarray(r_m, float),
                           np.asarray(s_a_m2, float)).sum(axis=0)
        return ToroidalState(tuple(t))

    def parity(self) -> "ToroidalState":
        """P: r -> -r, S (axial) invariant => T -> -T."""
        return ToroidalState(tuple(-np.asarray(self.t_vector_a_m2)),
                             self.frame, self.origin_policy)

    def time_reversal(self) -> "ToroidalState":
        """T-rev: S -> -S => T -> -T."""
        return self.parity()          # same sign action on T

    def pt(self) -> "ToroidalState":
        """PT: T -> +T (even)."""
        return self

    @property
    def magnitude(self) -> float:
        return float(np.linalg.norm(self.t_vector_a_m2))

    @property
    def unit(self) -> np.ndarray:
        m = self.magnitude
        return np.asarray(self.t_vector_a_m2) / m if m else \
            np.zeros(3)


def domain_states(t_mag: float) -> tuple:
    """The two time-reversed domains: +T b, -T b."""
    return (ToroidalState((0.0, +t_mag, 0.0)),
            ToroidalState((0.0, -t_mag, 0.0)))


# --- resonance + coupling ---------------------------------------------------

def eta_resonant(wavelength_nm: float, eta0: float = 1.0) -> float:
    """Directional-response strength: sum of Lorentzian-in-wavelength
    d-d band factors (registered bands). Off-resonance -> ~0."""
    s = 0.0
    for b in DD_BANDS_NM:
        x = (wavelength_nm - b) / BAND_WIDTH_NM
        s += 1.0 / (1.0 + x * x)
    return eta0 * s / len(DD_BANDS_NM)


def iome_bias(k_hat, t_state: ToroidalState, fluence_j_m2: float,
              lam_coupling: float, wavelength_nm: float) -> float:
    """Free-energy writing bias per EQ-002: b = lambda * f *
    eta(wl) * (k_hat . T_hat) * |T|. Depends ONLY on the propagation
    direction channel — polarization does not enter this model."""
    k = np.asarray(k_hat, float)
    k = k / np.linalg.norm(k)
    return (lam_coupling * fluence_j_m2 * eta_resonant(wavelength_nm)
            * float(k @ t_state.unit) * t_state.magnitude)


SATURATION_LAWS = {
    "tanh": lambda b: math.tanh(b),
    "logistic": lambda b: 2.0 / (1.0 + math.exp(
        -2.0 * max(-350.0, min(350.0, b)))) - 1.0,
    "linear_clip": lambda b: max(-1.0, min(1.0, b)),
}


def written_alignment(bias: float, law: str = "tanh") -> float:
    """Bounded domain alignment A = p+ - p- in [-1, 1]."""
    return SATURATION_LAWS[law](bias)


def populations(alignment: float) -> tuple:
    a = max(-1.0, min(1.0, alignment))
    return (0.5 * (1 + a), 0.5 * (1 - a))     # p+ + p- = 1 always


def retention(alignment: float, temperature_k: float) -> float:
    """Nonvolatile below the registered transition; thermal erasure
    above it (alignment -> 0)."""
    return alignment if temperature_k < TRANSITION_K else 0.0


# --- directional complex index (EQ-003) --------------------------------------

def directional_complex_index(k_hat, t_state: ToroidalState,
                              wavelength_nm: float,
                              eta_re: float = 1e-4,
                              eta_im: float = 4e-4) -> dict:
    """dn = (eta_re + i eta_im) * eta(wl) * (k_hat.T_hat) |T|.
    Real (dispersive) and imaginary (absorptive/optical-diode)
    channels are serialized SEPARATELY."""
    k = np.asarray(k_hat, float)
    k = k / np.linalg.norm(k)
    proj = float(k @ t_state.unit) * t_state.magnitude
    r = eta_resonant(wavelength_nm)
    return {"dn_real": eta_re * r * proj,
            "dn_imag": eta_im * r * proj,
            "note": "Re/Im channels separate; Re channel is a "
                    "registered PREDICTION partner, not an observed "
                    "value (source values unavailable locally)"}


# --- writing model + discriminators ------------------------------------------

def write_domains(material_id: str, k_hat, t_mag: float,
                  fluence_j_m2: float, lam_coupling: float,
                  wavelength_nm: float = PUMP_PRESET_NM,
                  temperature_k: float = 15.0,
                  jones=(1.0, 0.0), law: str = "tanh") -> dict:
    """Capability-gated IOME writing. `jones` is ACCEPTED and
    deliberately UNUSED by this mechanism (polarization invariance is
    the source model's claim — the ablation tests assert it)."""
    mat = get_material(material_id)
    app = applicability(mat, "domain_writing")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID, material_id,
                                     app["reason_code"], app["reason"])
    plus, _ = domain_states(t_mag)
    bias = iome_bias(k_hat, plus, fluence_j_m2, lam_coupling,
                     wavelength_nm)
    align = retention(written_alignment(bias, law), temperature_k)
    p_plus, p_minus = populations(align)
    dn = directional_complex_index(k_hat, ToroidalState(
        (0.0, align * t_mag, 0.0)), wavelength_nm)
    return make_result(
        MODULE_ID, material_id, "REDUCED_ORDER_VALIDATED",
        ["DER"],
        {"bias": bias, "alignment": align,
         "p_plus": p_plus, "p_minus": p_minus,
         "dn_real": dn["dn_real"], "dn_imag": dn["dn_imag"],
         "temperature_k": temperature_k,
         "erased": temperature_k >= TRANSITION_K},
        {"bias": "dimensionless", "alignment": "[-1,1]",
         "dn": "dimensionless"},
        source_ids=["SRC-V4-01", "SRC-V4-00"],
        equation_ids=["RGCS-V4-EQ-001", "RGCS-V4-EQ-002",
                      "RGCS-V4-EQ-003"],
        assumptions=["propagation-direction channel only; "
                     "polarization deliberately unused",
                     "S_omega = ExH = f k_hat declared approximation",
                     "SOURCE_VALUE_COMPARISON_PENDING_LOCAL_SOURCE "
                     "(DV4C-003)"])


def compare_saturation_laws(bias_train: np.ndarray,
                            align_train: np.ndarray,
                            bias_test: np.ndarray,
                            align_test: np.ndarray) -> dict:
    """Held-out model comparison: fit a scale per law on train data,
    rank by TEST residual. No aesthetic selection (gate H5)."""
    from scipy.optimize import minimize_scalar
    scores = {}
    for name, law in SATURATION_LAWS.items():
        def loss(s, b=bias_train, a=align_train, f=law):
            return float(np.sum((np.array([f(s * x) for x in b])
                                 - a) ** 2))
        r = minimize_scalar(loss, bounds=(1e-3, 1e3),
                            method="bounded")
        s = float(r.x)
        test_resid = float(np.sqrt(np.mean(
            (np.array([law(s * x) for x in bias_test])
             - align_test) ** 2)))
        scores[name] = {"scale": s, "heldout_rmse": test_resid}
    best = min(scores, key=lambda k: scores[k]["heldout_rmse"])
    return {"scores": scores, "selected_by_heldout_rmse": best}


def scanned_writing_profile(x_mm: np.ndarray, beam_center_mm: float,
                            beam_waist_mm: float, k_sign: int,
                            peak_bias: float) -> np.ndarray:
    """Spatial writing: Gaussian-beam local bias -> alignment profile
    (overlap/convolution of scanned spots is additive in bias)."""
    b = peak_bias * k_sign * np.exp(
        -2 * ((np.asarray(x_mm) - beam_center_mm)
              / beam_waist_mm) ** 2)
    return np.tanh(b)


# --- comparator mechanisms (channel discrimination, gate H3) ------------------

def inverse_faraday_comparator(jones, fluence_j_m2: float,
                               scale: float = 1.0) -> float:
    """IFE responds to HELICITY (sigma = 2 Im(Ex* Ey)/|E|^2), not to
    propagation reversal."""
    ex, ey = complex(jones[0]), complex(jones[1])
    den = abs(ex) ** 2 + abs(ey) ** 2
    hel = 2 * (ex.conjugate() * ey).imag / den if den else 0.0
    return scale * fluence_j_m2 * hel


def thermal_annealing_comparator(jones, intensity_w_m2: float,
                                 absorption_anisotropy: float = 0.3,
                                 scale: float = 1.0) -> float:
    """MnF2-style optical annealing: polarization-ANGLE-dependent
    absorption heating; direction- and helicity-blind."""
    ex, ey = complex(jones[0]), complex(jones[1])
    den = abs(ex) ** 2 + abs(ey) ** 2
    lin = (abs(ex) ** 2 - abs(ey) ** 2) / den if den else 0.0
    return scale * intensity_w_m2 * (1 + absorption_anisotropy * lin)
