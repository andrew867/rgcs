"""RGCS R15 — Experimental Phase Infrastructure.

R15 turns the completed R13 software/simulation architecture into an
instrument-ready, calibration-bound, uncertainty-aware experimental
platform. It adds seven authorities above R13 -- instrument, calibration,
specimen, fixture, protocol, observation, and evidence -- and the pipeline
that runs a frozen protocol through an authorized configuration, a
calibration/specimen/fixture binding, an acquisition, an immutable raw
artifact, a derivation graph, the ordinary-explanation attacks, residual
classification, and finally an evidence receipt.

Three laws carry across everything here.

**No purchase.** No operator is required to own or buy laboratory
equipment. Every hardware-facing lane ships a REAL_DEVICE interface, a
deterministic SYNTHETIC_DEVICE, a REPLAY_DEVICE, and a
FAULT_INJECTION_DEVICE, plus schemas, protocols, error budgets, tests, and
docs. Only physical acquisition may be blocked.

**Evidence, not assertion.** No observation enters evidence without an
instrument, a calibration, a specimen, a fixture, a protocol, a clock, an
environment, timestamps, an uncertainty budget, immutable artifacts,
hashes, and a derivation lineage. Missing any of these caps the evidence
below a physical measurement. The strongest an unreplicated residual can
be is ``UNEXPLAINED_INSTRUMENT_RESIDUAL`` -- there is no ``PHRYLL_DETECTED``
state, and a residual below combined uncertainty is not anomalous.

**No promotion.** A synthetic observation is not a physical measurement; a
source is not a measurement; a model is not a measurement; noise is not a
resonance; and an unexplained instrument residual is not new physics.

No physical measurement is performed by any module here.
"""

from __future__ import annotations
