# Frames, Epochs, Calendars, and Galactic Directions

---

## 1. Epoch is gated, not removed

V1 can structurally decode direct 9-digit vectors and variable-length envelopes
**without solving the full epoch system**, because the codec and spatial path are
parseable before dynamic projection.

Epoch is **mandatory** for:

- moving planetary/body frames;
- the SAA magnetic phase hand;
- shell radius, where shell surfaces are epoch-dependent;
- barycentric or interstellar coordinates;
- astronomical proper motion and ephemeris reconciliation;
- reproducible public certificates.

```
STRUCTURAL_DECODE:  epoch optional / may remain unresolved
DYNAMIC_PROJECTION: epoch required
PUBLIC_RECEIPT:     declared epoch metadata required
```

Encoded as `r1053.certificate.EPOCH_GATING` and emitted in every
`address_certificate()`, so a receipt always says which of the three regimes it is in.

---

## 2. Ba-130 and UTC/TAI

```
Ba-130  = long-origin source candidate
UTC/TAI = conventional metadata and reproducibility layer
Cs-133  = possible downstream fine-phase implementation only
```

Do not reopen Cs-133/Cs-137/UTC/TAI as competing long-origin roots unless explicitly
requested. UTC/TAI metadata remains **mandatory** on public receipts regardless — it
is the reproducibility layer, not a rival root.

---

## 3. OA Tranquility Calendar — audit

The Orion's Arm Tranquility Calendar defines:

- 13 months of 28 days;
- Armstrong Day between Mendel 28 and Archimedes 1;
- Aldrin Day in leap years;
- Archimedes 1 = 21 July Gregorian;
- Moon Landing Day / 20 July 1969 as the central historical date in OA lore.

**Current RGCS vectors show no direct active bit-level match to this calendar.** The
token values in direct vectors do not map to a month index 1–13 plus a day 1–28
without arbitrary transforms. Classification:

```
OA_TRANQUILITY_CALENDAR: CALENDAR_CONVERGENCE_LEAD
ACTIVE_CODEC_ROLE:       NONE_YET
EPOCH_ROLE:              POSSIBLE_EXTERNAL_DISPLAY_OR_REFERENCE_LAYER
```

It is a **lead**, not an active codec component. Nothing in V1 depends on it.

---

## 4. Galactic directions

OA's Galactic Directions page states:

```
x = coreward     y = spinward     z = Galactic North
```

This is consistent in shape with real Galactic Cartesian usage: Astropy's `Galactic`
frame has positive *x* toward the Milky Way centre and *z* toward the North Galactic
Pole under the IAU 1958 convention (finalised 1959).

OA also notes a Communion convention in which "up" can mean Galactic **South** and
"down" Galactic **North**. This is striking next to RGCS's South-Up / Antarctica-top
Earth display — but it remains **lore convergence only**. Two projects independently
choosing an inverted vertical convention is a weak coincidence, not a shared source;
inverted-vertical conventions are common wherever a display has no privileged "up".

---

## 5. SPICE influence on RGCS frame hygiene

The NAIF/SPICE model is the external engineering reference for public RGCS frame
discipline:

```
reference frame ≠ coordinate system
frames have centers
frames can be time-dependent
coordinate systems locate points inside a frame
state/orientation data require both
```

RGCS therefore emits `FrameManifest` and `AddressCertificate` objects rather than
unlabeled coordinates. See [`r1053/certificate.py`](../r1053/certificate.py) and
[Earth Root Final Spec](RGCS_V1_EARTH_ROOT_FINAL_SPEC.md) §1.

A worked receipt is shown in the [User Manual](USER_MANUAL.md).
