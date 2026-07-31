# VELA_GRB_1969_1972_RECOVERY

**Status: RECOVERY LANE OPEN. No original gamma-ray stream located.**

The Vela 5B archive currently implemented is the **All-Sky Monitor X-ray detector**
archive. It is **not** the original Vela gamma-ray burst stream. This lane exists to
find out whether that stream survives anywhere, and to be honest if it does not.

**No claim is made that the original raw stream exists online.** Until a record is
located and verified, this lane holds a search plan and an evidence taxonomy, not
data.

---

## First target

The 16-burst corpus reported by **Klebesadel, Strong & Olson (1973)**,
*Observations of Gamma-Ray Bursts of Cosmic Origin*, ApJ 182, L85.

What is sought, in order of value:

1. machine-readable time-tagged count histories
2. spacecraft identifiers and detector channels per burst
3. bin widths and background estimates
4. clock corrections between spacecraft
5. telemetry or recorder format documentation
6. burst dates, durations, and spacecraft pairs
7. plotted time profiles (figures) as a last resort

## Recovery order

| step | action | status |
|---|---|---|
| 1 | Obtain the 1973 paper, figures, tables, dates, durations, pairs, profiles | not started |
| 2 | Search HEASARC, NTRS, LANL public archives, NSSDC metadata, later Vela catalogs, conference proceedings, technical reports, instrument documentation | not started |
| 3 | Locate machine-readable count histories if they exist | not started |
| 4 | If only plots survive, create `PLOT_DIGITIZED` evidence with calibration uncertainty and image provenance | not started |
| 5 | Keep digitized curves strictly separate from original event or count data | enforced by class |
| 6 | Issue the external-archive request below | template ready |

## Evidence classes for this lane

| class | meaning |
|---|---|
| `ORIGINAL_EVENT_DATA` | time-tagged counts as recorded. Not known to exist publicly. |
| `ORIGINAL_COUNT_HISTORY` | binned counts from mission-era processing |
| `PLOT_DIGITIZED` | curves recovered from a published figure |
| `LITERATURE_TABULATED` | values quoted in a paper, not re-derivable |
| `NOT_LOCATED` | sought, not found — recorded, not hidden |

**`PLOT_DIGITIZED` never merges with `ORIGINAL_*`.** A digitized curve carries its
image provenance, the digitiser used, axis-calibration points, and an explicit
calibration uncertainty. It is a measurement *of a figure*, not of the sky.

---

## External-archive request template

> **Subject:** Request for Vela gamma-ray burst detector records, 1969–1972
>
> I am seeking archival records underlying the gamma-ray burst detections reported
> in Klebesadel, Strong & Olson (1973), ApJ 182, L85, for a reproducible-analysis
> research project. Specifically:
>
> 1. **Time-tagged count histories** for the reported bursts — counts per bin with
>    absolute timestamps, in any surviving machine-readable form.
> 2. **Spacecraft identifiers** for each detection, including which pair or
>    triangulation set contributed.
> 3. **Detector channels** and their energy responses.
> 4. **Bin widths** and any variable-binning scheme used.
> 5. **Background estimates** and the method by which they were derived.
> 6. **Clock corrections** applied between spacecraft, and residual timing
>    uncertainty.
> 7. **Telemetry or recorder format documentation** — frame structure, word
>    layout, encoding, and any error-control coding used on the downlink.
>
> If original event data are not retained, I would value knowing that explicitly,
> along with any pointer to the most primitive surviving representation. A negative
> answer is a useful result and will be recorded as such.
>
> Media, formats and access restrictions are not a barrier; I can work from any
> surviving representation and will document provenance fully.

Send to: NSSDC / HEASARC archive scientists, LANL public archives, and the NTRS
technical-report contacts, separately.

---

## Boundaries

- Do **not** describe the X-ray ASM archive as gamma-ray burst data.
- Do **not** claim the original stream is online until a record is located and
  verified.
- Do **not** merge digitized figures with count data.
- A `NOT_LOCATED` result is published like any other.

See [SOURCE_AND_REPRESENTATION_BOUNDARIES](SOURCE_AND_REPRESENTATION_BOUNDARIES.md).
