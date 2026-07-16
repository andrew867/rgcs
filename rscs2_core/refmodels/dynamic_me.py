"""Dynamic magnetoelectric response reference (Agent M5;
RGCS-V4-EQ-011; material reference.dynamic_magnetoelectric or
reference.linipo4). Never alpha quartz (capability firewall).

Delta P_i(omega) = alpha_ij(omega) Delta H_j(omega), with a
transparent Lorentz reduced form
alpha_ij(omega) = a_ij * w0^2 / (w0^2 - w^2 - i w gamma).
Units: alpha [s/m] (P [C/m^2] per H [A/m]); amplitude and quadrature
are separate outputs and are never collapsed into one unsigned score."""

from __future__ import annotations

import numpy as np

from ..multiphysics import applicability, get_material, make_result
from ..multiphysics import not_applicable_result

MODULE_ID = "rscs2.refmodels.dynamic_me"


class METensor:
    """Complex dynamical ME tensor with declared symmetry mask,
    frame, and reciprocity METADATA (never inferred from shape)."""

    def __init__(self, material_id: str, a_ij_s_m: np.ndarray,
                 f0_hz: float, gamma_hz: float,
                 allowed_mask: np.ndarray | None = None,
                 coordinate_frame: str = "tensor frame (declared)",
                 reciprocity: str = "DECLARED_NONRECIPROCAL",
                 handedness: int = +1):
        self.material = get_material(material_id)
        app = applicability(self.material, "magnetoelectric_dynamic")
        self._blocked = app["applicability"] == "NOT_APPLICABLE"
        self._app = app
        a = np.asarray(a_ij_s_m, float)
        if a.shape != (3, 3):
            raise ValueError("a_ij must be 3x3")
        mask = np.ones((3, 3), bool) if allowed_mask is None \
            else np.asarray(allowed_mask, bool)
        if np.any(a[~mask] != 0):
            raise ValueError("symmetry-forbidden component nonzero")
        self.a, self.mask = a, mask
        self.f0, self.gamma = float(f0_hz), float(gamma_hz)
        self.frame = coordinate_frame
        self.reciprocity = reciprocity
        self.handedness = int(handedness)

    def alpha(self, f_hz) -> np.ndarray:
        """alpha_ij(omega): complex (…,3,3)."""
        w = 2 * np.pi * np.atleast_1d(np.asarray(f_hz, float))
        w0 = 2 * np.pi * self.f0
        g = 2 * np.pi * self.gamma
        lor = w0 ** 2 / (w0 ** 2 - w ** 2 - 1j * w * g)
        return (self.handedness * self.a)[None, :, :] \
            * lor[:, None, None]

    def response(self, f_hz, dh_a_m: np.ndarray) -> dict:
        """Delta P(omega) = alpha(omega) @ Delta H, with in-phase and
        quadrature parts serialized separately."""
        if self._blocked:
            return not_applicable_result(
                MODULE_ID, self.material.material_id,
                self._app["reason_code"], self._app["reason"])
        al = self.alpha(f_hz)
        dh = np.asarray(dh_a_m, float)
        p = np.einsum("fij,j->fi", al, dh)
        return make_result(
            MODULE_ID, self.material.material_id,
            "REDUCED_ORDER_VALIDATED", ["DER"],
            {"n_freqs": int(len(np.atleast_1d(f_hz)))},
            {"alpha": "s/m", "P": "C/m^2", "H": "A/m"},
            source_ids=list(self.material.source_ids),
            equation_ids=["RGCS-V4-EQ-011"],
            assumptions=[f"Lorentz reduced form; frame {self.frame}",
                         f"reciprocity metadata: {self.reciprocity} "
                         "(declared, never inferred from tensor "
                         "shape)"]) | {
            "f_hz": np.atleast_1d(np.asarray(f_hz, float)),
            "p_inphase_c_m2": p.real, "p_quadrature_c_m2": p.imag,
            "p_amplitude_c_m2": np.abs(p),
            "p_phase_rad": np.angle(p)}

    def reversed_handedness(self) -> "METensor":
        out = METensor.__new__(METensor)
        out.__dict__.update(self.__dict__)
        out.handedness = -self.handedness
        return out

    def kramers_kronig_check(self, f_hz: np.ndarray,
                             component=(0, 1)) -> dict:
        """Consistency of Re/Im via the Hilbert transform when the
        provided grid covers the resonance; sparse spectral support
        returns a limitation record, never invented dispersion."""
        f = np.asarray(f_hz, float)
        if len(f) < 64 or f.max() < 4 * self.f0 or f.min() > \
                0.25 * self.f0:
            return {"status": "INSUFFICIENT_SPECTRAL_SUPPORT",
                    "classification": "INTERFACE_ONLY",
                    "note": "KK check needs broad coverage around the "
                            "resonance; no dispersion is invented"}
        al = self.alpha(f)[:, component[0], component[1]]
        # KK: Re(a)(w) = (2/pi) P∫ w' Im(a)/(w'^2 - w^2) dw'
        w = 2 * np.pi * f
        re_kk = np.empty_like(w)
        im = al.imag
        for i, wi in enumerate(w):
            den = w ** 2 - wi ** 2
            den[i] = np.inf                      # principal value
            re_kk[i] = (2 / np.pi) * np.trapezoid(
                w * im / den, w)
        resid = np.linalg.norm(al.real - re_kk) / \
            np.linalg.norm(al.real)
        return {"status": "CHECKED", "relative_residual": float(resid)}


def optical_rotation_observable(me: METensor, f_hz: float,
                                path_m: float,
                                scale_rad_per_alpha: float) -> dict:
    """Declared observable: rotation angle proportional to the
    REAL (dispersive) part of alpha_xy times path; ellipticity to the
    IMAGINARY (absorptive) part. Assumptions are explicit; the two
    channels are never merged."""
    if me._blocked:
        return not_applicable_result(
            "rscs2.refmodels.dynamic_me.rotation",
            me.material.material_id, me._app["reason_code"],
            me._app["reason"])
    a = me.alpha(f_hz)[0, 0, 1]
    return {"rotation_rad": float(scale_rad_per_alpha * a.real
                                  * path_m),
            "ellipticity_rad": float(scale_rad_per_alpha * a.imag
                                     * path_m),
            "assumptions": ["linear-in-alpha small-rotation regime",
                            "declared proportionality scale",
                            "dispersive->rotation, absorptive->"
                            "ellipticity kept separate"]}
