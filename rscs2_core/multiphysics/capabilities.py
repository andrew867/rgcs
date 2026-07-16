"""MaterialCapabilities: typed, schema-backed capability records
(Agent M2; shared schema section 1). UNKNOWN is not permission."""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = "rgcs.v4.material_capabilities.1"

#: the 24 required capability keys (shared schema)
CAPABILITY_KEYS = (
    "elasticity_isotropic", "elasticity_anisotropic", "piezoelectric",
    "dielectric_anisotropic", "photoelastic", "optical_birefringent",
    "magnetic_order", "spin_orbit_coupling", "magnon_modes",
    "exciton_frenkel", "exciton_wannier", "exciton_charge_transfer",
    "exciton_magnon_coupling", "spin_phonon_coupling",
    "chiral_phonons", "magnetoelectric_dynamic", "nonlinear_optical",
    "plasmonic_near_field", "quantum_statistical_response",
    "microscopic_tunnelling_model", "ferrotoroidic_order",
    "directional_optical_response", "domain_writing",
    "thermal_domain_selection",
)

ALLOWED_STATUS = ("SUPPORTED", "REFERENCE_ONLY", "INTERFACE_ONLY",
                  "UNSUPPORTED", "UNKNOWN")
ALLOWED_CLASS = ("CORE_VALIDATED", "REDUCED_ORDER_VALIDATED",
                 "INTERFACE_ONLY", "SOURCE_HYPOTHESIS",
                 "NOT_APPLICABLE")


@dataclass(frozen=True)
class CapabilityRecord:
    status: str = "UNSUPPORTED"
    classification: str = "NOT_APPLICABLE"
    parameter_set_ids: tuple = ()
    source_ids: tuple = ()
    temperature_constraints: dict = field(default_factory=dict)
    field_constraints: dict = field(default_factory=dict)
    reason: str | None = None

    def __post_init__(self):
        if self.status not in ALLOWED_STATUS:
            raise ValueError(f"bad capability status {self.status}")
        if self.classification not in ALLOWED_CLASS:
            raise ValueError(
                f"bad classification {self.classification}")

    def to_dict(self) -> dict:
        return {"status": self.status,
                "classification": self.classification,
                "parameter_set_ids": list(self.parameter_set_ids),
                "source_ids": list(self.source_ids),
                "temperature_constraints": dict(
                    self.temperature_constraints),
                "field_constraints": dict(self.field_constraints),
                "reason": self.reason}


@dataclass(frozen=True)
class MaterialCapabilities:
    material_id: str
    display_name: str
    material_family: str
    reference_only: bool
    source_ids: tuple
    symmetry: str
    coordinate_frame: str
    temperature_range: dict
    notes: tuple = ()
    capabilities: dict = field(default_factory=dict)

    def __post_init__(self):
        missing = set(CAPABILITY_KEYS) - set(self.capabilities)
        if missing:
            raise ValueError(
                f"{self.material_id}: missing capability keys "
                f"{sorted(missing)}")
        extra = set(self.capabilities) - set(CAPABILITY_KEYS)
        if extra:
            raise ValueError(
                f"{self.material_id}: unknown capability keys "
                f"{sorted(extra)}")
        for k, v in self.capabilities.items():
            if not isinstance(v, CapabilityRecord):
                raise ValueError(f"{self.material_id}.{k}: capability "
                                 "must be a CapabilityRecord")

    def capability(self, key: str) -> CapabilityRecord:
        if key not in CAPABILITY_KEYS:
            raise KeyError(f"unregistered capability '{key}' — aliases"
                           " are rejected, not guessed")
        return self.capabilities[key]

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "material_id": self.material_id,
            "display_name": self.display_name,
            "material_family": self.material_family,
            "reference_only": self.reference_only,
            "source_ids": list(self.source_ids),
            "symmetry": self.symmetry,
            "coordinate_frame": self.coordinate_frame,
            "temperature_range": dict(self.temperature_range),
            "notes": list(self.notes),
            "capabilities": {k: v.to_dict()
                             for k, v in sorted(
                                 self.capabilities.items())},
        }

    def what_is_not_supported(self) -> list[str]:
        return sorted(k for k, v in self.capabilities.items()
                      if v.status == "UNSUPPORTED")


def applicability(material: "MaterialCapabilities",
                  capability_key: str) -> dict:
    """The applicability service: APPLICABLE / NOT_APPLICABLE /
    INTERFACE_ONLY / REFERENCE_ONLY with reason codes. UNKNOWN status
    is NOT permission to run (returns NOT_APPLICABLE with reason)."""
    rec = material.capability(capability_key)
    if rec.status == "SUPPORTED":
        return {"applicability": "APPLICABLE",
                "classification": rec.classification,
                "reason_code": None, "reason": None}
    if rec.status == "REFERENCE_ONLY":
        return {"applicability": "REFERENCE_ONLY",
                "classification": rec.classification,
                "reason_code": "REFERENCE_SYSTEM_ONLY",
                "reason": rec.reason or
                "reduced-order reference system, not the material's "
                "microscopic physics"}
    if rec.status == "INTERFACE_ONLY":
        return {"applicability": "INTERFACE_ONLY",
                "classification": "INTERFACE_ONLY",
                "reason_code": "INTERFACE_ONLY",
                "reason": rec.reason or
                "schema/adapter exists; computation not implemented"}
    if rec.status == "UNKNOWN":
        return {"applicability": "NOT_APPLICABLE",
                "classification": "NOT_APPLICABLE",
                "reason_code": "CAPABILITY_UNKNOWN_NOT_PERMISSION",
                "reason": "capability status UNKNOWN — execution "
                          "refused until a registered record exists"}
    # UNSUPPORTED: RGCS has no VALIDATED implementation of this
    # mechanism for this material. This is a statement about the
    # SOFTWARE, never proof that the mechanism is physically absent,
    # impossible, or incapable of producing an observable effect
    # (binding scope statement, V4C corrective integration).
    return {"applicability": "NOT_APPLICABLE",
            "classification": "NOT_APPLICABLE",
            "reason_code": "MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL",
            "reason": (rec.reason or
                       f"{material.material_id} has no registered "
                       f"{capability_key} capability")
            + " [no validated implementation exists; this is not "
              "evidence of physical nonexistence]"}
