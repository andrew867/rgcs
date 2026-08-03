"""Deterministic KiCad PCB writer for the two RevA board variants."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from rgcs_ardk.drive import AuthorityBundle, load_authority
from rgcs_ardk.geometry import AnnularGeometry, CircleFeature, Point2D, SectorPolygon
from rgcs_ardk.params import LOCKS
from rgcs_ardk.pcb.model import (
    BoardDefinition,
    BoardVariant,
    board_definition,
    net_registry,
    validate_net_registry,
)


@dataclass(frozen=True)
class GeneratedBoard:
    variant: BoardVariant
    board_path: Path
    metadata_path: Path
    board_sha256: str
    metadata_sha256: str


def _number(value: float) -> str:
    rendered = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if rendered in {"", "-0"} else rendered


def _point(point: Point2D) -> str:
    return f"(xy {_number(point.x_mm)} {_number(point.y_mm)})"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _net_names(definition: BoardDefinition) -> tuple[str, ...]:
    names: list[str] = []
    for index in range(LOCKS.sector_count):
        names.extend(f"{prefix}_{index:02d}" for prefix in definition.sector_access_prefixes)
    names.extend(definition.global_nets)
    registry_order = {record.name: position for position, record in enumerate(net_registry())}
    return tuple(sorted(set(names), key=registry_order.__getitem__))


def _zone(net_number: int, name: str, polygon: SectorPolygon) -> str:
    points = " ".join(_point(point) for point in polygon.points)
    return (
        "  (zone\n"
        f"    (net {net_number}) (net_name \"{name}\") (layer \"F.Cu\")\n"
        "    (hatch edge 0.5)\n"
        "    (connect_pads (clearance 0.25))\n"
        "    (min_thickness 0.25)\n"
        "    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))\n"
        f"    (polygon (pts {points}))\n"
        "  )"
    )


def _test_point(reference: str, point: Point2D, net_number: int, net_name: str) -> str:
    return (
        f"  (footprint \"RGCS_ARDK:TestPoint\" (layer \"F.Cu\") "
        f"(at {_number(point.x_mm)} {_number(point.y_mm)})\n"
        f"    (property \"Reference\" \"{reference}\" (at 0 -2 0) (layer \"F.SilkS\"))\n"
        "    (fp_circle (center 0 0) (end 1.2 0) (stroke (width 0.2) (type default)) "
        "(fill none) (layer \"F.SilkS\"))\n"
        f"    (pad \"1\" thru_hole circle (at 0 0) (size 2 2) (drill 1) "
        f"(layers \"*.Cu\" \"*.Mask\") (net {net_number} \"{net_name}\"))\n"
        "  )"
    )


def _mounting_hole(feature: CircleFeature) -> str:
    return (
        f"  (footprint \"MountingHole:{feature.feature_id}\" (layer \"F.Cu\") "
        f"(at {_number(feature.center.x_mm)} {_number(feature.center.y_mm)})\n"
        f"    (property \"Reference\" \"H_{feature.feature_id}\" (at 0 -3 0) (layer \"F.SilkS\"))\n"
        f"    (pad \"\" np_thru_hole circle (at 0 0) "
        f"(size {_number(feature.diameter_mm)} {_number(feature.diameter_mm)}) "
        f"(drill {_number(feature.diameter_mm)}) (layers \"*.Cu\" \"*.Mask\"))\n"
        "  )"
    )


def _two_pad_footprint(
    reference: str,
    point: Point2D,
    net_a_number: int,
    net_a: str,
    net_b_number: int,
    net_b: str,
) -> str:
    return (
        f"  (footprint \"RGCS_ARDK:Optional_0603\" (layer \"F.Cu\") "
        f"(at {_number(point.x_mm)} {_number(point.y_mm)})\n"
        f"    (property \"Reference\" \"{reference}\" (at 0 -1.5 0) (layer \"F.SilkS\"))\n"
        f"    (pad \"1\" smd roundrect (at -0.85 0) (size 1 1.2) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") "
        f"(roundrect_rratio 0.2) (net {net_a_number} \"{net_a}\"))\n"
        f"    (pad \"2\" smd roundrect (at 0.85 0) (size 1 1.2) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") "
        f"(roundrect_rratio 0.2) (net {net_b_number} \"{net_b}\"))\n"
        "  )"
    )


def _board_a_items(
    geometry: AnnularGeometry, net_numbers: dict[str, int]
) -> Iterable[str]:
    polygons = geometry.sector_ring(110.0, 128.0)
    for index, polygon in enumerate(polygons):
        name = f"SENSE_{index:02d}"
        yield _zone(net_numbers[name], name, polygon)
        yield _test_point(f"TP{name}", geometry.sector_center(index, 119.0), net_numbers[name], name)
    for index, point in enumerate(geometry.compass_pickups()):
        name = f"COMPASS_{index}"
        yield _test_point(f"TP{name}", point, net_numbers[name], name)
    # The annular aperture precludes center copper; this pad terminates the fixture probe.
    yield _test_point("TPCENTER_REF", Point2D(99.0, 0.0), net_numbers["CENTER_REF"], "CENTER_REF")


def _board_b_items(
    geometry: AnnularGeometry, net_numbers: dict[str, int]
) -> Iterable[str]:
    drive_polygons = geometry.sector_ring(126.0, 140.0)
    load_polygons = geometry.sector_ring(98.0, 108.0)
    for index, (drive_polygon, load_polygon) in enumerate(zip(drive_polygons, load_polygons)):
        drive = f"DRV_{index:02d}"
        load = f"LOAD_{index:02d}"
        sense = f"SENSE_{index:02d}"
        kelvin_p = f"KELVIN_P_{index:02d}"
        kelvin_n = f"KELVIN_N_{index:02d}"
        yield _zone(net_numbers[drive], drive, drive_polygon)
        yield _zone(net_numbers[load], load, load_polygon)
        yield _test_point(f"TP{drive}", geometry.sector_center(index, 134.0), net_numbers[drive], drive)
        yield _test_point(f"TP{load}", geometry.sector_center(index, 103.0), net_numbers[load], load)
        yield _test_point(f"TP{sense}", geometry.sector_center(index, 116.0), net_numbers[sense], sense)
        yield _test_point(f"TP{kelvin_p}", geometry.sector_center(index, 121.0), net_numbers[kelvin_p], kelvin_p)
        yield _test_point(f"TP{kelvin_n}", geometry.sector_center(index, 112.0), net_numbers[kelvin_n], kelvin_n)
        yield _two_pad_footprint(
            f"RLOAD_{index:02d}",
            geometry.sector_center(index, 131.0),
            net_numbers[drive],
            drive,
            net_numbers[load],
            load,
        )
        yield _two_pad_footprint(
            f"CLOAD_{index:02d}",
            geometry.sector_center(index, 101.0),
            net_numbers[load],
            load,
            net_numbers["GUARD_INNER"],
            "GUARD_INNER",
        )


def render_board(
    variant: BoardVariant,
    authority: AuthorityBundle,
    geometry: AnnularGeometry | None = None,
) -> str:
    """Render one deterministic `.kicad_pcb` design scaffold."""
    del authority  # Validation happens before render; values do not change physical geometry.
    validate_net_registry()
    geometry = geometry or AnnularGeometry()
    definition = board_definition(variant)
    names = _net_names(definition)
    net_numbers = {name: index + 1 for index, name in enumerate(names)}
    lines = [
        "(kicad_pcb (version 20240108) (generator \"rgcs_ardk_r1074\")",
        "  (general (thickness 1.6))",
        "  (paper \"A3\")",
        "  (layers",
        "    (0 \"F.Cu\" signal)",
        "    (31 \"B.Cu\" signal)",
        "    (36 \"B.SilkS\" user \"b.silkscreen\")",
        "    (37 \"F.SilkS\" user \"f.silkscreen\")",
        "    (44 \"Edge.Cuts\" user)",
        "  )",
        "  (setup (pad_to_mask_clearance 0))",
        "  (net 0 \"\")",
    ]
    lines.extend(f"  (net {number} \"{name}\")" for name, number in net_numbers.items())
    lines.extend(
        (
            f"  (property \"BOARD_VARIANT\" \"{variant.value}\")",
            "  (property \"STATUS\" \"DESIGN_SCAFFOLD_PUBLICATION_HOLD\")",
            f"  (property \"SECTOR_COUNT\" \"{LOCKS.sector_count}\")",
            "  (gr_circle (center 0 0) (end 144 0) "
            "(stroke (width 0.2) (type default)) (fill none) (layer \"Edge.Cuts\"))",
            "  (gr_circle (center 0 0) (end 94 0) "
            "(stroke (width 0.2) (type default)) (fill none) (layer \"Edge.Cuts\"))",
        )
    )
    lines.extend(_mounting_hole(hole) for hole in geometry.mounting_holes())
    for fiducial in geometry.fiducials():
        lines.append(
            f"  (gr_circle (center {_number(fiducial.center.x_mm)} {_number(fiducial.center.y_mm)}) "
            f"(end {_number(fiducial.center.x_mm + fiducial.diameter_mm / 2)} {_number(fiducial.center.y_mm)}) "
            "(stroke (width 0.2) (type default)) (fill none) (layer \"F.SilkS\"))"
        )
    items = _board_a_items(geometry, net_numbers) if definition.passive_only else _board_b_items(geometry, net_numbers)
    lines.extend(items)
    lines.append(")")
    return "\n".join(lines) + "\n"


def _metadata(
    definition: BoardDefinition,
    geometry: AnnularGeometry,
    authority: AuthorityBundle,
    board_sha256: str,
) -> dict:
    return {
        "schema_version": 1,
        "board": definition.variant.value,
        "revision": "RevA",
        "status": "DESIGN_SCAFFOLD_PUBLICATION_HOLD",
        "fabrication_ready": False,
        "purpose": definition.purpose,
        "passive_only": definition.passive_only,
        "features": list(definition.features),
        "geometry": geometry.as_dict(),
        "authority": {
            "source_commit": authority.source_commit,
            "hashes": authority.hashes,
            "seed_used": False,
        },
        "board_sha256": board_sha256,
        "drc_profile": "safe_low_power_revA",
        "drc_executed": False,
        "manufacturing_stackup_approved": False,
    }


def generate_boards(
    output_dir: str | Path,
    *,
    authority_root: str | Path | None = None,
) -> tuple[GeneratedBoard, GeneratedBoard]:
    """Generate both separate boards after validating R10.73 authority."""
    authority = load_authority(authority_root)
    geometry = AnnularGeometry()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    generated: list[GeneratedBoard] = []
    for variant in BoardVariant:
        definition = board_definition(variant)
        board_path = output / f"{variant.value}.kicad_pcb"
        metadata_path = output / f"{variant.value}.metadata.json"
        board_bytes = render_board(variant, authority, geometry).encode("utf-8")
        board_hash = _sha256_bytes(board_bytes)
        metadata = _metadata(definition, geometry, authority, board_hash)
        metadata_bytes = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")
        board_path.write_bytes(board_bytes)
        metadata_path.write_bytes(metadata_bytes)
        generated.append(
            GeneratedBoard(
                variant,
                board_path,
                metadata_path,
                board_hash,
                _sha256_bytes(metadata_bytes),
            )
        )
    manifest = {
        "schema_version": 1,
        "status": "DESIGN_SCAFFOLD_PUBLICATION_HOLD",
        "fabrication_ready": False,
        "authority_source_commit": authority.source_commit,
        "outputs": [
            {
                **asdict(item),
                "variant": item.variant.value,
                "board_path": item.board_path.name,
                "metadata_path": item.metadata_path.name,
            }
            for item in generated
        ],
    }
    (output / "generation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return generated[0], generated[1]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="build/kicad/r1074")
    parser.add_argument("--authority-root")
    args = parser.parse_args(argv)
    generated = generate_boards(args.output, authority_root=args.authority_root)
    for board in generated:
        print(f"{board.variant.value}: {board.board_sha256}")
    print("status: DESIGN_SCAFFOLD_PUBLICATION_HOLD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
