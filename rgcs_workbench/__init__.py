"""RGCS Workbench canonical data model and Master Evidence Workbook
generator (v4.5 pack, phases P01/P05).

The canonical store is the authority; the workbook is a one-way,
formula-visible export from it (canonical -> workbook). Workbook cells
are never the database. Every record and every visible value carries
an evidence class from the fixed set, and no export may hide it.

    Lore proposes. Mathematics translates. Software attacks.
    Evidence decides. Provenance remembers.
"""

SCHEMA_VERSION = "1.0.0"

# The fixed evidence ladder (product-and-science contract). Ordered
# weakest -> strongest; nothing may launder upward without a record.
EVIDENCE_CLASSES = (
    "LORE",
    "SOURCE_CLAIM",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "SYNTHETIC_RUN",
    "BENCH_MEASUREMENT",
    "INDEPENDENT_REPLICATION",
    # v4.6 (CSCP) additions: a claim may be recorded as having no
    # supporting mechanism, or as lying outside a model's domain.
    # These are NOT rungs of the ladder — they are terminal statuses.
    "UNSUPPORTED",
    "NOT_APPLICABLE",
    # v4.7 (PMWR) additions (core/08)
    "METAPHOR",
    "GEOMETRY_IDENTITY",
    "CALIBRATED_MEASUREMENT",
    "ANTHROPOGENIC_STRUCTURE",
    "REPRESENTATION_ARTIFACT",
    "CIRCULAR_DERIVATION",
    "UNEXPLAINED_INSTRUMENT_RESIDUAL",
    "REPLICATED_ANOMALY",
    "PROSPECTIVE_PREDICTION",
    # v4.9 (R6) additions: the remaining rungs of the Phryll ladder
    # (core/07). SOURCE_CLAIM, UNEXPLAINED_INSTRUMENT_RESIDUAL and
    # REPLICATED_ANOMALY are already present above. There is no
    # detection class and adding one is a test failure.
    "OPERATIONAL_HYPOTHESIS",
    "ORDINARY_CHANNEL_RESULT",
    "CANDIDATE_NEW_MECHANISM",
)

#: Classes that assert something about the physical world. A
#: software-only lane may never emit these.
PHYSICAL_EVIDENCE_CLASSES = ("BENCH_MEASUREMENT",
                             "INDEPENDENT_REPLICATION")

PRIVACY_CLASSES = ("PUBLIC", "PUBLIC_SAFE", "PRIVATE")

# Sheets the workbook contract requires (04_WORKBOOK_CONTRACT +
# 01 orchestrator). Order is the tab order.
REQUIRED_SHEETS = (
    "Dashboard",
    "Frequency Keys",
    "Harmonic Relations",
    "Specimens",
    "Mode Estimates",
    "Timing Recipes",
    "Hypotheses",
    "Evidence Ledger",
    "Eye Results",
    "Resonator Platform",
    "Hardware BOM",
    "Experiment Queue",
    "Corrections",
    "Source Registry",
    "Lore Registry",
    "Installer Metadata",
    "CSCP Candidates",
    "CSCP Tetrahedron",
    "CSCP Spacetime",
    "CSCP Experiments",
    "PMWR Recovery",
    "PMWR Crystal",
    "PMWR Phryll",
    "R3 Root Space",
    "R3 Lanes",
    "R4 Codec",
    "R4 Platforms",
    "R6 Claims",
    "R6 Apparatus",
    "R6 Witness",
    "R6 Mailbox",
    "R6 Grid",
    "Workbook Guide",
)
