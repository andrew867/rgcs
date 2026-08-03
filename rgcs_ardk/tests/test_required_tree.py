from pathlib import Path


def test_required_high_level_tree_and_reports_exist():
    root = Path("rgcs_ardk")
    for name in (
        "params",
        "geometry",
        "pcb",
        "drive",
        "sense",
        "firmware",
        "bench",
        "mech",
        "reports",
        "tests",
    ):
        assert (root / name).is_dir()
    reports = Path("docs/proofs/r1074-annular-devkit")
    expected = {
        "r1074_summary_for_ag.md",
        "pcb_design_spec.md",
        "parametric_geometry_report.md",
        "sensor_feedback_report.md",
        "firmware_reference_report.md",
        "manufacturing_readiness_report.md",
        "safety_and_claim_firewall.md",
    }
    assert {path.name for path in reports.iterdir() if path.is_file()} == expected
