"""Malformed-input tests: every public entry point rejects bad inputs
with ValueError (or pydantic ValidationError), never silent nonsense."""

from __future__ import annotations

import math

import numpy as np
import pytest
from pydantic import ValidationError

from rgcs_core.geometry import (CrystalGeometry, polygon_area_mm2,
                                apothem_mm, termination_height_mm,
                                crystal_geometry, SpiralGeometry,
                                spiral_curve, node_prior_mm, node_positions,
                                node_alignment_factor,
                                solve_diameter_scale_for_mass)
from rgcs_core.harmonics import axial_half_wave, ladder_length_mm
from rgcs_core.compact_modes import parity_index_set, compact_mode_spectrum
from rgcs_core.resonance import resonance_offset, classify_resonance
from rgcs_core.coupled_modes import (coupled_two_mode, n_mode_eigenproblem,
                                     integrate_stuart_landau)
from rgcs_core.loading import loading_factor, added_modal_mass_g
from rgcs_core.drive import drive_sequence, micro_pulse_metrics
from rgcs_core.coherence import (coherence_series, phase_locking_value,
                                 rayleigh_test, windowed_phase_rates,
                                 spatial_phase_anisotropy,
                                 fit_exponential_decay, model_comparison,
                                 threshold_detect_bootstrap)
from rgcs_core.experiments import control_subtracted_metrics, merit_score


def test_geometry_rejects_nonpositive_and_nan():
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            polygon_area_mm2(bad, 6)
        with pytest.raises(ValueError):
            apothem_mm(bad, 6)
        with pytest.raises(ValueError):
            axial_half_wave(bad)
    with pytest.raises(ValueError):
        polygon_area_mm2(10.0, 2)                     # facets < 3
    with pytest.raises(ValueError):
        polygon_area_mm2(10.0, 6, "sideways")         # bad mode
    with pytest.raises(ValueError):
        termination_height_mm(10.0, 0.0)              # bad angle
    with pytest.raises(ValueError):
        termination_height_mm(10.0, 190.0)


def test_crystal_geometry_model_validation():
    with pytest.raises(ValidationError):
        CrystalGeometry(length_mm=-5, wide_diameter_mm=30,
                        narrow_diameter_mm=25)
    with pytest.raises(ValidationError):
        CrystalGeometry(length_mm=100, wide_diameter_mm=20,
                        narrow_diameter_mm=25)        # inverted taper
    with pytest.raises(ValidationError):
        CrystalGeometry(length_mm=100, wide_diameter_mm=30,
                        narrow_diameter_mm=25, facets=2)
    # Caps exceeding length caught at computation time.
    tiny = CrystalGeometry(length_mm=5.0, wide_diameter_mm=30,
                           narrow_diameter_mm=25)
    with pytest.raises(ValueError):
        crystal_geometry(tiny)


def test_density_inverse_rejects_bad_mass():
    g = CrystalGeometry(length_mm=154.0, wide_diameter_mm=31.6,
                        narrow_diameter_mm=26.9)
    for bad in (0.0, -1.0, float("nan")):
        with pytest.raises(ValueError):
            solve_diameter_scale_for_mass(g, bad)


def test_spiral_validation():
    with pytest.raises(ValidationError):
        SpiralGeometry(q_per_turn=0.9)                # must be > 1
    with pytest.raises(ValueError):
        spiral_curve(SpiralGeometry(), samples=8)     # too few samples


def test_node_validation():
    with pytest.raises(ValueError):
        node_prior_mm(100.0, 60.0, 50.0)              # caps exceed length
    with pytest.raises(ValueError):
        node_positions(100.0, 10.0, 10.0, measured_from_female_mm=150.0)
    with pytest.raises(ValueError):
        node_positions(100.0, 10.0, 10.0,
                       measured_from_female_mm=float("nan"))
    with pytest.raises(ValueError):
        node_alignment_factor(50.0, 40.0, 0.0)        # sigma must be > 0


def test_harmonics_validation():
    with pytest.raises(ValueError):
        ladder_length_mm(0)
    with pytest.raises(ValueError):
        ladder_length_mm(5, base_frequency_hz=-1.0)
    with pytest.raises(ValueError):
        axial_half_wave(100.0, wave_speed=-6310.0)


def test_compact_modes_validation():
    with pytest.raises(ValueError):
        parity_index_set("weird", 5)
    with pytest.raises(ValueError):
        parity_index_set("odd", -1)
    with pytest.raises(ValueError):
        compact_mode_spectrum(-1.0)
    with pytest.raises(ValueError):
        compact_mode_spectrum(0.0, n_max=0)
    with pytest.raises(ValueError):
        compact_mode_spectrum(0.0, compact_radius_mm=-100.0)


def test_resonance_validation():
    with pytest.raises(ValueError):
        resonance_offset(-1.0, 20480.0)
    with pytest.raises(ValueError):
        resonance_offset(40960.0, 20480.0, pair_multiple=0.0)
    with pytest.raises(ValueError):
        classify_resonance(float("nan"), 1000, 800, u_eps=1e-4)
    with pytest.raises(ValueError):
        classify_resonance(1e-3, 1000, 800, u_eps=-1.0)


def test_coupled_modes_validation():
    with pytest.raises(ValueError):
        coupled_two_mode(0.0, 1000.0, 10.0)
    with pytest.raises(ValueError):
        coupled_two_mode(1000.0, 1000.0, -5.0)
    with pytest.raises(ValueError):
        n_mode_eigenproblem([1000.0, 1100.0],
                            [[0.0, 5.0], [7.0, 0.0]])   # asymmetric
    with pytest.raises(ValueError):
        n_mode_eigenproblem([1000.0, 1100.0],
                            [[1.0, 5.0], [5.0, 0.0]])   # nonzero diagonal
    with pytest.raises(ValueError):
        n_mode_eigenproblem([1000.0], [[0.0, 1.0]])     # shape mismatch
    with pytest.raises(ValueError):
        integrate_stuart_landau([1.0], [0.0], [1.0], [[0.0]], [[0.0]],
                                [1.0], -100.0, 10)      # bad fs


def test_loading_validation():
    with pytest.raises(ValueError):
        loading_factor(-1.0, 4096.0)
    with pytest.raises(ValueError):
        added_modal_mass_g(0.98, 154.0, modal_mass_fraction=1.5)


def test_drive_validation():
    with pytest.raises(ValueError):
        drive_sequence(carrier_hz=0.0)
    with pytest.raises(ValueError):
        micro_pulse_metrics(pulse_width_us=-1.0)
    with pytest.raises(ValueError):
        micro_pulse_metrics(pulses_per_period=0)


def test_coherence_validation():
    with pytest.raises(ValueError):
        coherence_series(np.array([]), 1000.0)
    with pytest.raises(ValueError):
        coherence_series(np.ones(10, complex), 1000.0, window_s=1.0)  # short
    with pytest.raises(ValueError):
        phase_locking_value(np.array([]), np.array([]))
    with pytest.raises(ValueError):
        phase_locking_value(np.ones(5), np.ones(6))
    with pytest.raises(ValueError):
        rayleigh_test(np.array([]))
    with pytest.raises(ValueError):
        windowed_phase_rates(np.ones(100), 1000.0)      # not 2-D
    with pytest.raises(ValueError):
        spatial_phase_anisotropy(np.ones((1, 100)), 1000.0)  # M < 2
    with pytest.raises(ValueError):
        fit_exponential_decay(np.array([0.0, 1.0]),
                              np.array([-1.0, -2.0]))   # no positive samples
    with pytest.raises(ValueError):
        model_comparison(np.array([0.0, 1.0]), np.array([1.0, 2.0]))  # < 4
    with pytest.raises(ValueError):
        threshold_detect_bootstrap(np.array([1.0]), np.ones((1, 3)))


def test_experiments_validation():
    with pytest.raises(ValueError):
        control_subtracted_metrics([1.0], [1.0, 2.0])   # too few samples
    with pytest.raises(ValueError):
        control_subtracted_metrics([1.0, float("nan")], [1.0, 2.0])
    with pytest.raises(ValueError):
        merit_score(1.5, 1000, 1000, 1000, 1000)        # overlap > 1
    with pytest.raises(ValueError):
        merit_score(0.5, 1000, 1000, 1000, 1000, control_gain=-1.0)
