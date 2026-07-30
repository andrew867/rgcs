"""R10.13 Phase 24 — stable error codes with normal-language repair.

Every user-facing failure carries a stable code, a plain-language
message, and a repair step. ``rgcs help error CODE`` prints the entry.
"""

from __future__ import annotations

ERROR_CODES = {
    "RGCS-E001": {
        "title": "Specimen file not found",
        "meaning": "The path you gave does not point to a file.",
        "repair": "Check the spelling and folder. On Windows use "
                  "quotes around paths with spaces, for example "
                  '"C:\\My Crystals\\my-crystal.json". On Linux use '
                  'quotes too: "~/my crystals/my-crystal.json".',
    },
    "RGCS-E002": {
        "title": "Specimen file is not valid JSON",
        "meaning": "The file could not be read as JSON, so nothing "
                   "else can be checked yet.",
        "repair": "Open the file in a text editor and look for a "
                  "missing comma, quote, or bracket near the line the "
                  "error names. 'rgcs crystal new FILE' writes a "
                  "known-good starting file.",
    },
    "RGCS-E003": {
        "title": "Wrong or missing schema_version",
        "meaning": "The file does not declare "
                   "'rgcs.crystal-specimen/1.0'.",
        "repair": "Add \"schema_version\": "
                  "\"rgcs.crystal-specimen/1.0\" at the top level, or "
                  "run 'rgcs crystal migrate FILE --out NEW_FILE' for "
                  "an older record.",
    },
    "RGCS-E004": {
        "title": "Required field missing",
        "meaning": "A field the calculation needs is absent.",
        "repair": "The error names the field. Add it with a real "
                  "value, or null if the quantity was not measured "
                  "(null is only allowed where documented).",
    },
    "RGCS-E005": {
        "title": "Value out of physical range",
        "meaning": "A number is zero, negative, or outside its "
                   "documented range.",
        "repair": "Re-check the measurement and the unit. Lengths and "
                  "diameters are millimetres and must be positive; "
                  "angles are degrees between 0 and 180 exclusive.",
    },
    "RGCS-E006": {
        "title": "Unit or mode not recognized",
        "meaning": "diameter_mode must be across_vertices or "
                   "across_flats; angle_mode must be face_slope, "
                   "axis_to_face, or apex_included.",
        "repair": "Pick the mode that matches how you measured. "
                  "See MEASURING_YOUR_CRYSTAL in the manual.",
    },
    "RGCS-E007": {
        "title": "Contradictory geometry",
        "meaning": "Two values cannot both be true, for example a "
                   "narrow diameter larger than the wide diameter, or "
                   "termination caps taller than the crystal.",
        "repair": "Swap or re-measure the named values. The error "
                  "lists both numbers so you can see the conflict.",
    },
    "RGCS-E008": {
        "title": "Not enough data for this calculation",
        "meaning": "The record is valid but a required value for "
                   "THIS model is null or missing.",
        "repair": "The error names what to measure next. A quick "
                  "estimate needs only the length; a full mesh needs "
                  "both diameters and both termination angles.",
    },
    "RGCS-E009": {
        "title": "Density mismatch",
        "meaning": "Measured mass divided by computed volume "
                   "disagrees with the declared material density "
                   "beyond tolerance.",
        "repair": "Re-check mass, dimensions, and material. A large "
                  "gap usually means an inclusion, a different "
                  "material, or a diameter measured across flats but "
                  "recorded as across vertices.",
    },
    "RGCS-E010": {
        "title": "Fixture not compatible",
        "meaning": "The chosen fixture cannot be applied to this "
                   "specimen or model.",
        "repair": "Use 'rgcs crystal modes ... --fixture free' first; "
                  "then add the real mount. Custom fixtures need "
                  "contact positions inside the specimen bounds.",
    },
    "RGCS-E011": {
        "title": "Mesh generation failed",
        "meaning": "gmsh was not found or exited with an error.",
        "repair": "Install gmsh and ensure the 'gmsh' command runs in "
                  "the same terminal. 'rgcs doctor' checks this.",
    },
    "RGCS-E012": {
        "title": "Imported mesh failed audit",
        "meaning": "The supplied mesh is not a closed, manifold, "
                   "consistently oriented solid at the declared "
                   "scale, so results from it would not be "
                   "trustworthy.",
        "repair": "The audit names the failing check. Re-export from "
                  "your CAD tool as a watertight solid in "
                  "millimetres, or let RGCS mesh the specimen "
                  "from dimensions instead.",
    },
    "RGCS-E013": {
        "title": "Capability refused",
        "meaning": "The requested computation is not available in "
                   "this installation or is refused by policy (for "
                   "example an unresolved research quantity).",
        "repair": "This is intentional, not a crash. The refusal "
                  "record names what evidence or component would be "
                  "needed. Nothing is guessed in its place.",
    },
    "RGCS-E014": {
        "title": "Result directory not found or incomplete",
        "meaning": "A report or bundle step could not find a prior "
                   "result to package.",
        "repair": "Run the calculation first and pass its --out "
                  "directory. 'latest' only works after at least one "
                  "run in the current directory.",
    },
    "RGCS-E015": {
        "title": "Evidence class violation",
        "meaning": "Something attempted to label computed output as "
                   "a measurement, or to use a source claim as data.",
        "repair": "No repair from the user side; this is a software "
                  "firewall. Report it if you see it in normal use.",
    },
}


class UserError(ValueError):
    """Typed user-facing failure: stable code + plain message + repair."""

    def __init__(self, code: str, message: str, field: str | None = None):
        if code not in ERROR_CODES:
            raise KeyError(f"unknown error code {code}")
        self.code = code
        self.field = field
        self.repair = ERROR_CODES[code]["repair"]
        super().__init__(message)

    def record(self) -> dict:
        return {"code": self.code, "field": self.field,
                "message": str(self), "title": ERROR_CODES[self.code]["title"],
                "repair": self.repair}


def explain(code: str) -> dict:
    if code not in ERROR_CODES:
        raise UserError("RGCS-E004",
                        f"'{code}' is not a known error code. Known codes "
                        f"run RGCS-E001 to RGCS-E{len(ERROR_CODES):03d}.")
    return {"code": code, **ERROR_CODES[code]}
