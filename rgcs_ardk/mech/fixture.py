"""Mechanical-only fixture coordinates and OpenSCAD renderer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from rgcs_ardk.geometry import AnnularGeometry


@dataclass(frozen=True)
class FixtureModel:
    base_outer_diameter_mm: float = 320.0
    base_inner_clearance_mm: float = 180.0
    base_thickness_mm: float = 8.0
    spacer_height_mm: float = 12.0
    probe_hole_diameter_mm: float = 2.2
    sleeve_outer_diameter_mm: float = 18.0
    sleeve_inner_diameter_mm: float = 8.0
    sleeve_height_mm: float = 30.0
    geometry: AnnularGeometry = AnnularGeometry()

    def as_dict(self) -> dict:
        return {
            **asdict(self),
            "geometry": self.geometry.as_dict(),
            "mechanical_rotation": False,
            "electrical_features": False,
            "ptfe_sleeve_required": True,
            "dielectric_spacers_required": True,
            "clamp_torque": "TBD_MEASURED_PER_RUN",
        }


def render_openscad(model: FixtureModel | None = None) -> str:
    model = model or FixtureModel()
    geometry = model.geometry
    lines = [
        "// RGCS-ARDK-001 RevA fixture. Mechanical geometry only.",
        "// PUBLICATION_HOLD; no mechanical rotation.",
        f"base_outer_d = {model.base_outer_diameter_mm:g};",
        f"base_inner_clearance_d = {model.base_inner_clearance_mm:g};",
        f"base_thickness = {model.base_thickness_mm:g};",
        f"spacer_height = {model.spacer_height_mm:g};",
        f"probe_radius = {geometry.params.mean_radius_mm:g};",
        f"probe_hole_d = {model.probe_hole_diameter_mm:g};",
        f"sector_count = {geometry.params.sector_count};",
        f"pcb_mount_radius = {geometry.mounting_radius_mm:g};",
        f"pcb_mount_hole_d = {geometry.mounting_hole_diameter_mm:g};",
        "",
        "module base_plate() {",
        "    difference() {",
        "        cylinder(d=base_outer_d, h=base_thickness, $fn=256);",
        "        translate([0,0,-0.1]) cylinder(d=base_inner_clearance_d, h=base_thickness+0.2, $fn=256);",
        "        for (i=[0:sector_count-1]) {",
        "            rotate([0,0,360*i/sector_count])",
        "                translate([probe_radius,0,-0.1])",
        "                    cylinder(d=probe_hole_d, h=base_thickness+0.2, $fn=24);",
        "        }",
        "        for (a=[45,135,225,315]) {",
        "            rotate([0,0,a]) translate([pcb_mount_radius,0,-0.1])",
        "                cylinder(d=pcb_mount_hole_d, h=base_thickness+0.2, $fn=32);",
        "        }",
        "    }",
        "}",
        "",
        "module center_ptfe_sleeve() {",
        "    difference() {",
        f"        cylinder(d={model.sleeve_outer_diameter_mm:g}, h={model.sleeve_height_mm:g}, $fn=64);",
        f"        translate([0,0,-0.1]) cylinder(d={model.sleeve_inner_diameter_mm:g}, h={model.sleeve_height_mm + 0.2:g}, $fn=64);",
        "    }",
        "}",
        "",
        "module dielectric_spacer(angle_deg) {",
        "    rotate([0,0,angle_deg]) translate([pcb_mount_radius,0,base_thickness])",
        "        difference() {",
        "            cylinder(d=8, h=spacer_height, $fn=32);",
        "            translate([0,0,-0.1]) cylinder(d=pcb_mount_hole_d, h=spacer_height+0.2, $fn=32);",
        "        }",
        "}",
        "",
        "base_plate();",
        "center_ptfe_sleeve();",
        "for (a=[45,135,225,315]) dielectric_spacer(a);",
        "",
    ]
    return "\n".join(lines)


def fixture_manifest_json(model: FixtureModel | None = None) -> str:
    return json.dumps((model or FixtureModel()).as_dict(), indent=2, sort_keys=True) + "\n"
