"""Optical excitation channels + ablation engine (Agent M14).

Independent, individually replaceable channels. A response model
DECLARES which channels it consumes and mechanically receives ONLY
those (undeclared channels cannot affect the output by construction).
Comparator mechanisms are registered so channel ablation can separate
IOME (direction), inverse Faraday (helicity), inverse Cotton-Mouton /
optical annealing (polarization angle), photothermal (intensity), and
vortex diagnostics (phase/OAM). Spatial-pattern comparison never
implies physical identity (M3 registry)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

CHANNELS = ("propagation", "hbar_k", "jones", "helicity",
            "polarization_angle", "sam", "oam_index", "intensity",
            "intensity_gradient", "e_waveform", "b_waveform", "phase",
            "group_delay", "spectrum", "beam_geometry", "envelope")


@dataclass(frozen=True)
class OpticalExcitation:
    propagation: tuple = (0.0, 0.0, 1.0)
    wavelength_nm: float = 1064.0
    jones: tuple = (1.0 + 0j, 0.0 + 0j)
    oam_index: int = 0
    intensity_w_m2: float = 1.0
    intensity_gradient: tuple = (0.0, 0.0, 0.0)
    e_waveform: str = "cw"
    b_waveform: str = "cw"
    phase_rad: float = 0.0
    group_delay_s: float = 0.0
    spectrum: str = "monochromatic"
    beam_geometry: str = "gaussian"
    envelope: str = "cw"

    def channel(self, name: str):
        if name not in CHANNELS:
            raise KeyError(f"unregistered optical channel '{name}'")
        if name == "hbar_k":
            hbar = 1.054571817e-34
            k = 2 * math.pi / (self.wavelength_nm * 1e-9)
            n = np.asarray(self.propagation, float)
            return hbar * k * n / np.linalg.norm(n)
        if name == "helicity":
            ex, ey = self.jones
            den = abs(ex) ** 2 + abs(ey) ** 2
            return 2 * (np.conj(ex) * ey).imag / den if den else 0.0
        if name == "polarization_angle":
            ex, ey = self.jones
            return 0.5 * math.atan2(2 * (np.conj(ex) * ey).real,
                                    abs(ex) ** 2 - abs(ey) ** 2)
        if name == "sam":
            return self.channel("helicity")     # per-photon units
        return getattr(self, {"propagation": "propagation",
                              "jones": "jones",
                              "oam_index": "oam_index",
                              "intensity": "intensity_w_m2",
                              "intensity_gradient":
                                  "intensity_gradient",
                              "e_waveform": "e_waveform",
                              "b_waveform": "b_waveform",
                              "phase": "phase_rad",
                              "group_delay": "group_delay_s",
                              "spectrum": "spectrum",
                              "beam_geometry": "beam_geometry",
                              "envelope": "envelope"}[name])

    def ablate(self, channel: str, **replacement) -> "OpticalExcitation":
        """Replace exactly the fields backing one channel; all other
        channels stay fixed."""
        allowed = {
            "propagation": ("propagation",),
            "jones": ("jones",), "helicity": ("jones",),
            "polarization_angle": ("jones",),
            "oam_index": ("oam_index",),
            "intensity": ("intensity_w_m2",),
            "intensity_gradient": ("intensity_gradient",),
            "phase": ("phase_rad",),
            "group_delay": ("group_delay_s",),
            "spectrum": ("spectrum", "wavelength_nm"),
            "beam_geometry": ("beam_geometry",),
            "envelope": ("envelope", "e_waveform", "b_waveform"),
        }
        if channel not in allowed:
            raise KeyError(f"cannot ablate channel '{channel}'")
        bad = set(replacement) - set(allowed[channel])
        if bad:
            raise ValueError(f"ablation of '{channel}' may only touch "
                             f"{allowed[channel]}, got {sorted(bad)}")
        return replace(self, **replacement)


@dataclass(frozen=True)
class ResponseDeclaration:
    """A mechanism declares its consumed channels; respond() passes
    ONLY those values, so undeclared channels cannot leak in."""
    name: str
    consumes: frozenset
    fn: object                       # callable(dict) -> float

    def respond(self, exc: OpticalExcitation) -> float:
        visible = {c: exc.channel(c) for c in self.consumes}
        return float(self.fn(visible))


def _iome(v):
    k = np.asarray(v["propagation"], float)
    k = k / np.linalg.norm(k)
    return v["intensity"] * k[1]                # k . b_hat channel


def _ife(v):
    return v["intensity"] * v["helicity"]


def _icm(v):
    return v["intensity"] * math.cos(2 * v["polarization_angle"])


def _thermal(v):
    return v["intensity"]


def _vortex(v):
    return float(v["oam_index"])


MECHANISMS = {
    "iome_linipo4": ResponseDeclaration(
        "iome_linipo4", frozenset({"propagation", "intensity"}),
        _iome),
    "inverse_faraday": ResponseDeclaration(
        "inverse_faraday", frozenset({"helicity", "intensity"}), _ife),
    "inverse_cotton_mouton": ResponseDeclaration(
        "inverse_cotton_mouton",
        frozenset({"polarization_angle", "intensity"}), _icm),
    "photothermal": ResponseDeclaration(
        "photothermal", frozenset({"intensity"}), _thermal),
    "mnf2_annealing": ResponseDeclaration(
        "mnf2_annealing",
        frozenset({"polarization_angle", "intensity"}),
        lambda v: v["intensity"] * (1 + 0.3 * math.cos(
            2 * v["polarization_angle"]))),
    "vortex_diagnostic": ResponseDeclaration(
        "vortex_diagnostic", frozenset({"oam_index", "phase"}),
        _vortex),
}


def ablation_matrix(exc: OpticalExcitation,
                    variations: dict) -> dict:
    """Response change of every mechanism under every single-channel
    variation (all other channels fixed)."""
    base = {m: MECHANISMS[m].respond(exc) for m in MECHANISMS}
    out = {"baseline": base, "ablations": {}}
    for label, (channel, repl) in variations.items():
        exc2 = exc.ablate(channel, **repl)
        out["ablations"][label] = {
            m: MECHANISMS[m].respond(exc2) - base[m]
            for m in MECHANISMS}
    return out


def hidden_order_report(alignment: float, t_mag: float,
                        temperature_k: float, k_hat,
                        wavelength_nm: float,
                        beam_waist_mm: float,
                        penetration_depth_mm: float,
                        sample_thickness_mm: float) -> dict:
    """Typed hidden-order diagnostic family built on the M11 model."""
    from .refmodels import iome_linipo4 as io
    plus, _ = io.domain_states(t_mag * max(alignment, 0)
                               or t_mag * alignment)
    eff = io.ToroidalState((0.0, alignment * t_mag, 0.0))
    dn = io.directional_complex_index(k_hat, eff, wavelength_nm)
    p_plus, p_minus = io.populations(alignment)
    return {
        "toroidal_moment": {"quantity_id": "toroidal_moment.magnetic",
                            "macroscopic_b_component":
                                alignment * t_mag,
                            "pt": "P:-1 T:-1 PT:+1"},
        "afm_order_parameter": abs(alignment),
        "domain_populations": {"p_plus": p_plus, "p_minus": p_minus},
        "domain_walls_expected": p_plus not in (0.0, 1.0),
        "directional_index_contrast": {"re": 2 * dn["dn_real"],
                                       "im": 2 * dn["dn_imag"]},
        "nonreciprocal_directional_dichroism": 2 * dn["dn_imag"],
        "writing_bias_retained": io.retention(alignment,
                                              temperature_k),
        "spatial_resolution_mm": beam_waist_mm,
        "penetration_uniformity": min(
            1.0, penetration_depth_mm / sample_thickness_mm),
        "identity_note": "toroidal order, mechanical vortex, optical "
                         "vortex, and the quartz eye are DISTINCT "
                         "typed quantities (M3 registry)",
    }


def compare_patterns(pattern_a: np.ndarray, pattern_b: np.ndarray,
                     qid_a: str, qid_b: str) -> dict:
    """Spatial-pattern correlation with the identity prohibition
    embedded (frozen boundary 7)."""
    from .quantity_registry import compare_geometric
    a = np.asarray(pattern_a, float).ravel()
    b = np.asarray(pattern_b, float).ravel()
    ac, bc = a - a.mean(), b - b.mean()
    den = np.linalg.norm(ac) * np.linalg.norm(bc)
    corr = float(ac @ bc / den) if den else 0.0
    rec = compare_geometric(qid_a, qid_b)
    rec["spatial_correlation"] = corr
    return rec
