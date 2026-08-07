"""Hyperbolic-material benchmark lane, isotopically enriched hBN (V5).

hBN is a comparison material teaching loss variables, isotopic
purity, launch-type separation, and wide-scan measurement
discipline. It is a benchmark, not a replacement for quartz, and
not RGCS validation (ledger P024).
"""

from __future__ import annotations

BENCHMARK_REQUIRED_FIELDS = (
    "material", "isotope_fraction", "thickness_nm", "reststrahlen_band",
    "branch_id", "propagation_length_um", "lifetime_ps", "q_factor",
    "launch_type", "scan_width_um", "incidence_angle_alpha",
    "edge_angle_beta",
)

LAUNCH_TYPES = ("edge_launch", "tip_launch")

ROLE = "BENCHMARK_MATERIAL_NOT_QUARTZ_REPLACEMENT"


def validate_benchmark(row: dict) -> list[str]:
    problems = [f"hBN benchmark missing field '{field}'"
                for field in BENCHMARK_REQUIRED_FIELDS
                if field not in row]
    if row.get("launch_type") is not None \
            and row.get("launch_type") not in LAUNCH_TYPES:
        problems.append(f"launch_type must be one of {LAUNCH_TYPES}; "
                        f"edge and tip launches never mix in one row")
    scan = row.get("scan_width_um")
    length = row.get("propagation_length_um")
    if scan is not None and length is not None and scan < length:
        problems.append("a long-lifetime claim needs a scan at least as "
                        "wide as the propagation length; narrow scans "
                        "cannot support it")
    return problems


def benchmark_row(**fields) -> dict:
    row = dict(fields)
    row.setdefault("claim_status", "BENCHMARK_SOURCE")
    row["role"] = ROLE
    problems = validate_benchmark(row)
    if problems:
        raise ValueError(f"invalid hBN benchmark row: {problems}")
    return row


__all__ = ["BENCHMARK_REQUIRED_FIELDS", "LAUNCH_TYPES", "ROLE",
           "validate_benchmark", "benchmark_row"]
