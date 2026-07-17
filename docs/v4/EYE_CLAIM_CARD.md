# Eye claim card — versioned, with correction trail (Agent V02)

This card is the ONLY approved compact wording for sharing the Eye
finding. If a sentence is quoted anywhere, it should be a sentence
from the current version of this card, with its version number.
Corrections append; nothing is deleted.

---

## CLAIM CARD v4 (current — emergent programme, after the
## independent census)

**What was computed.** (1) The v4.2.1 mesh ladder (below, card v3),
and (2) an **independent, unbiased full-domain cluster census** with
eigenspace tracking (`tools/v4x2_eye_census.py`), which removes the
nearest-to-candidate selection that every earlier analysis used.

**What the census found.**

1. **One apex feature, two estimates.** The v4.1 coordinate
   (z = 102.24 mm) and the v4.2.1 coordinate (z = 99.78 mm) are
   2.53 mm apart — and the census shows a **single persistent
   strain-energy concentration near the male apex** whose centroid
   estimate moves from ~102 mm (coarse mesh) toward ~99.8 mm (finer
   mesh). The two recorded coordinates are **resolution-dependent
   estimates of the same feature**, not two features. Card v3's
   framing ("the v4.1 coordinate does not survive refinement") was
   technically true of the coordinate but misleading about the
   feature; this card corrects it.
2. **The station comparison stands.** The apex feature sits
   5.1–6.7 mm from the conventional station across meshes and
   diagnostics, with ~1.8 mm halfwidth at the finest level:
   `NEAR_CONVENTIONAL_NODE_BUT_DISTINCT` for the implemented
   idealized model.
3. **The feature is not unique.** The unbiased census also finds a
   mirror concentration near the FEMALE apex (z ≈ 3.7–4.2 mm) and a
   symmetric mid-shaft pair (D2, z ≈ 58 mm). The strain-energy field
   has a structured, symmetric FAMILY of concentrations, which any
   'unique special point' narrative must now contend with.
4. **Mode identity is clean.** The first elastic eigenspace tracks
   across meshes with principal angles < 2.7° — the drift is not a
   mode switch.

**What this is NOT.** Everything in card v3's list, unchanged: not a
measurement, not evidence of a physical Eye, not about any real
crystal, and memory-limited at the finest level.

**Reproduce:** `python tools/v4x2_eye_census.py` →
`docs/v4/proof/C02/independent_census.json`.

---

## CLAIM CARD v3 (superseded by v4 — kept verbatim)

**What was computed.** A finite-element modal analysis of an
**idealized** 110 mm alpha-quartz geometry (ideal N=7 body, assumed
orientation, first elastic mode pair) locates a strain-energy
concentration whose position was tracked across mesh resolutions of
3.4, 2.4, and 1.8 mm element spacing.

**What was found.** At the finest tested resolution the feature sits
at (−0.048, −0.020, 99.78) mm, **6.30 mm** from the nearest
conventional mounting-station comparator, with a localization
halfwidth of **1.80 mm** — so the two positions are numerically
distinguishable, and the implemented conventional model **does not
explain** the feature's location. Classification:
`NEAR_CONVENTIONAL_NODE_BUT_DISTINCT`.

**What changed from earlier versions.** The refined pipeline did not
identify a persistent corresponding cluster near the previously
recorded z = 102.24 mm **under the tested mode, mesh, interpolation,
and clustering configuration**; the earlier coordinate is understood
as resolution-limited (it was computed at ~4 mm spacing, comparable
to the distances under discussion).

**What this is NOT.**
- Not a physical measurement — no crystal has ever been measured.
- Not evidence that any physical "Eye" exists.
- Not a claim about your crystal, any commercial crystal, or quartz
  in general. The geometry is idealized and the orientation assumed.
- Not final: the finest solve was memory-limited (13.9 GB at 30,816
  DOF on a 31.6 GB machine); one level finer needs ~48+ GB or an
  iterative solver.

**Reproduce it.**
```
python tools/v4x_eye_refinement_v5.py --budget 400
python tools/v4x2_eye_census.py
```

**Independent replication status.** An unbiased full-domain cluster
census with eigenspace (MAC/subspace) tracking is recorded in
`docs/v4/proof/C02/independent_census.json`; see
[EYE_REFINEMENT_V5.md](EYE_REFINEMENT_V5.md).

---

## Correction trail (append-only)

| Card | Date | Claim | Superseded by | Why |
|---|---|---|---|---|
| v1 | 2026-07-16 (v4.1) | candidate at (−0.295, −0.205, 102.240) mm, separation 3.906 mm, `UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE` — "the conventional model may explain it within uncertainty" | v2 | halfwidth (3.08 mm) was comparable to the separation; the comparison carried no information |
| v2 | 2026-07-16 (v4.2.0) | "sub-millimetre refinement": `INSUFFICIENT_RESOLUTION` at 8.0/5.5/4.5 mm | v3 | the title overstated the resolution by ~10×(defect V4X-D-011); the ladder could not decide the question |
| v3 | 2026-07-17 (v4.2.1) | separation resolved; "the v4.1 coordinate does not survive refinement" | v4 | the census shows ONE apex feature with resolution-dependent estimates; the coordinate framing conflated the estimate with the feature |
| v4 | 2026-07-17 (emergent) | one apex feature (two estimates), station comparison stands, feature has a symmetric family (female apex + mid-shaft pair), eigenspace cleanly tracked | — | current |

## Rules for sharing (V02)

1. Quote the card, cite the version. "RGCS found X" without a card
   version is not a supported statement.
2. The caveats travel with the claim. A screenshot of the bold text
   without "What this is NOT" misrepresents the work, and this card
   is the reference to point to when that happens.
3. Corrections are news: when a future version changes the claim,
   the change is announced with the same prominence as the original.
4. The physical Eye hypothesis is **open and untested**. Anyone
   presenting this computation as physical evidence — for or
   against — is beyond the card.
