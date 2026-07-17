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
)

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
    "Workbook Guide",
)
