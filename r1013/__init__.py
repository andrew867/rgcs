"""RGCS R10.13 — normal-user custom crystal workflow + unified CLI.

Consolidates the R10.13 release: crystal-specimen schema and API over
the frozen rgcs_core/rscs2_core engines, quick estimates, Christoffel,
custom FEM, fixtures, result certificates, the unified ``rgcs`` CLI
(codec subcommands delegate to r1012 unchanged), and the research-only
models (timing compiler, aperture ring, dynamic-boundary ledger,
two-sided variable codec, 19-wire exact cover, state-dependent edge
law). Publication remains on HOLD; no measurement is ever fabricated:
every computed number carries an evidence class and a computed
frequency is never a measured resonance.
"""

__version__ = "0.10.13"
SPECIMEN_SCHEMA_VERSION = "rgcs.crystal-specimen/1.0"
FIXTURE_SCHEMA_VERSION = "rgcs.fixture/1.0"
CERTIFICATE_SCHEMA_VERSION = "rgcs.result-certificate/1.0"
RUN_CONFIG_SCHEMA_VERSION = "rgcs.run-config/1.0"
PUBLICATION_STATUS = "HOLD"

#: Evidence classes for user-facing results. Software output can never
#: be MEASUREMENT; that class is reserved for imported instrument data.
EVIDENCE_CLASSES = ("ESTIMATE", "ANALYTIC", "NUMERICAL_SIMULATION",
                    "SYNTHETIC_OBSERVATION", "MEASUREMENT",
                    "SOURCE_PROVENANCE_ONLY")
SOFTWARE_EMITTABLE = ("ESTIMATE", "ANALYTIC", "NUMERICAL_SIMULATION",
                      "SYNTHETIC_OBSERVATION", "SOURCE_PROVENANCE_ONLY")
