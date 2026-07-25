# Locked Decision ADR — `EARTH_ROOT_D_V1`

**Status:** Accepted and frozen (R10.8.2, tranche T01, phase P02)
**Authority in code:** `cwatlas/r1082/config_authority.py`
**Public config validated against this ADR:** `cwatlas/r1082/fixtures/earth_root_D_v1.json`
**Evidence class of every decision below:** `OPERATOR_SELECTION` (operator-selected inputs, not measured facts)

## Context

The R10.8.1 CW Atlas is a general bidirectional geocoder. R10.8.2 *locks* one
operator-selected Earth-root configuration so the source-map calibration
experiment cannot be tuned after the fact. These decisions are operator inputs.
The implementation must not reopen them merely because another configuration is
easier to code or produces a prettier map (`01_CONTRACTS/LOCKED_DECISIONS.md`,
`SYSTEM_CONTRACT.md` "No result shopping").

This ADR is encoded in code as an immutable, versioned, hashed configuration
object (`ConfigurationAuthority`). The fifteen decisions are carried in
`config_authority.LOCKED_DECISIONS`; the authority loads and validates the
public fixture against them and exposes a deterministic `freeze_hash()`.

## Decisions

| # | Key | Decision |
|---|-----|----------|
| 1 | `origin` | Origin is the Earth centre of mass. |
| 2 | `axis` | Body axis is the mean rotation axis, expressed South-Up. |
| 3 | `partition` | 20 spherical icosahedral faces. |
| 4 | `dual_graph` | Active adjacency graph is the dodecahedral dual. |
| 5 | `root_feature` | Root feature is one icosahedral face centre (equivalently the matching dodecahedral-dual vertex). |
| 6 | `fixed_anchor` | Fixed spatial anchor is the Wilkes Land gravity-anomaly centroid, as a versioned centroid-and-uncertainty profile. |
| 7 | `dynamic_zero` | Dynamic phase-zero direction is the South Atlantic Anomaly field-magnitude minimum, evaluated at the encoded epoch and body-relative shell radius. |
| 8 | `orientation_pole` | Orientation is South-Up. |
| 9 | `positive_rotation` | Positive rotation is clockwise viewed externally from above Antarctica. |
| 10 | `opposite_view` | The same rotation appears anticlockwise from the North-down viewpoint. |
| 11 | `second_anchor` | Second calibration anchor is the user-reported Stonehenge training anchor, referenced by the opaque fixture id `STONEHENGE_PRIVATE_001`. |
| 12 | `local_coordinate` | Local coordinate within a face is barycentric. |
| 13 | `route_core` | Route core is a five-token base-100 representation, e.g. `01|65|87|65|23`. |
| 14 | `semantic_address` | Semantic address has seven logical fields; shell and epoch may share a compressed wire field. |
| 15 | `variable_depth` | Packets may omit unused epoch components; a decoded certificate expands every available semantic component. |

## Consequences

* **Immutable and hashed.** `ConfigurationAuthority` is a frozen dataclass;
  `freeze_hash()` is a deterministic SHA-256 of the canonical ADR. Changing any
  decision changes the hash and therefore mints a **new profile id** — the old
  `EARTH_ROOT_D_V1` holdout comparisons are invalidated.
* **No silent mutation.** There is no setter. `refuse_change(key)` routes every
  mutation attempt through `cwatlas.r1082.claims.refuse_post_output_retuning`,
  the same governance refusal the red team indexes. Attribute assignment on the
  frozen object raises `dataclasses.FrozenInstanceError`.
* **The fixture cannot drift.** `validate()` compares the shipped public config
  to the encoded decisions and raises `ConfigAuthorityError` on any divergence,
  so the fixture can never quietly contradict this ADR.
* **The UI cannot silently alter the profile.** Any UI or API change to a
  locked field must go through a new profile id; the authority exposes no
  in-place edit path.

## What this ADR does *not* say

The locked decisions are operator-selected inputs. Encoding and hashing them
validates neither the source's origin nor any physical effect. The Wilkes
centroid profile/covariance, the source token-to-geometry semantics, the
isotope-derived epoch compression, and the body assignment of unlabeled vectors
remain **inferred or uncertain** (`SYSTEM_CONTRACT.md`) and are held as
registries or explicit refusal states, not silently guessed.

    SOURCE_ORIGIN_NOT_VALIDATED
    PHYSICAL_EFFECTS_NOT_CLAIMED
