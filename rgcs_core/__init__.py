"""rgcs_core — RGCS v2 computational core.

A deterministic, typed, tested library implementing the RGCS v2
mathematical model (docs/MATHEMATICAL_MODEL.md, equations RGCS-M.0..M.61;
machine-readable ids in docs/model_registry.yaml). Independent of the
desktop UI.

Subpackages
-----------
geometry       facets, frusta, terminations, spiral/cone path, nodes,
               density inverse (RGCS-M.1..M.7, M.30..M.41)
harmonics      axial estimates and the 4096 ladder with wave-speed
               uncertainty (RGCS-M.8..M.12)
compact_modes  compact phase-coordinate spectra, parity, zero-mode rule
               (RGCS-M.13..M.17)
resonance      epsilon offsets, detuning, linewidth, Q-derived classes
               (RGCS-M.18..M.22, M.26)
coupled_modes  2-mode and N-mode eigenproblems, avoided crossings,
               complex Stuart-Landau dynamics (RGCS-M.23..M.29, M.46..M.49)
loading        mass/stiffness/damping corrections, k_H vs k~_H
               (RGCS-M.42..M.45)
coherence      analytic signal, coherence, PLV, anisotropy, model
               comparison (COH-M1..M14)
drive          pulse timing, exact cycle families, microsecond pulses
experiments    schemas, control-subtracted analysis, merit score
provenance     model version, classification metadata, sha256, JSON

Units policy: every module docstring declares its units; unit conversions
(mm <-> m, mm^3 -> cm^3) appear exactly once per function. All epistemic
labels follow docs/SCIENTIFIC_CLASSIFICATION_POLICY.md; physical
correspondence is determined by measurement, not assumed by terminology.
"""

from .provenance import MODEL_VERSION
from .uncertainty import UncertainValue, default_wave_speed

__version__ = "3.0.0"
__all__ = ["MODEL_VERSION", "UncertainValue", "default_wave_speed",
           "__version__"]
