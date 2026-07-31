# Source and representation boundaries

The single most important distinction in the archive lane:

> **A FITS file's bytes are an archive encoding. They are not necessarily the
> spacecraft's original transmitted bitstream.**

Everything below follows from that.

---

## What the Vela 5B public archive actually is

| it **is** | it is **not** |
|---|---|
| the All Sky Monitor **X-ray** detector product, in FITS | the original serial radio telemetry |
| one-second count accumulations, two energy channels | the gamma-ray detector bitstream |
| reduced and re-serialised decades after the fact | a bit-faithful record of what the antenna received |

Confirmed by inspection of a real file — `TELESCOP = VELA 5B`,
`INSTRUME = XC`, columns `YEAR DOY SOD TIME L_PNT B_PNT C1CNTS C2CNTS
L_SCZ B_SCZ STABFLAG PNTFLAG SPIN`.

Those are **derived physical quantities**, not a captured downlink. Anything found
in them is a property of the archive product unless proven otherwise.

## Instrument facts that generate false structure

- Spin period **≈ 64 s**, orbital period **≈ 112 h**. Both imprint strong
  periodicity that has nothing to do with content.
- Instrument **temperature and gain variation** produce large artificial periodic
  structure. This is stated in the mission documentation, not inferred.
- About **0.1 %** of the historical data was corrupted during a computer transfer.
  `all_bad.README` and `all_bad.dat` are the ledger and must be respected.
- Files use legacy Unix **`.Z`** (LZW) compression. Not gzip. Detected by magic
  bytes, never by extension.

Any periodicity near 64 s or 112 h is an `INSTRUMENT_ARTIFACT` until a control
says otherwise.

---

## The representation ladder

Each rung is a different object. Confusing two of them is the core error this
lane exists to prevent.

```
1  transmitted bitstream          NOT PRESENT in the public archive
2  ground-processed telemetry     NOT PRESENT
3  archive product (FITS)         what you can actually download
4  decompressed file bytes        recipe DECOMPRESSED_FILE_BYTES
5  HDU storage bytes              recipe FITS_HDU_RAW_STORAGE
6  column raw storage values      recipe FITS_COLUMN_RAW
7  column physical values         recipe FITS_COLUMN_PHYSICAL
8  re-serialised derived stream   recipes G, H, I, J -- ALL DERIVED
```

**Rungs 7 and 8 are constructions.** Re-serialising numeric columns into a
bitstream is something *we* do; it is not something the spacecraft did. Every such
recipe records columns, rows, scaling, width, endianness, bit order, missing-data
policy, a lossy flag, and its inverse where one exists.

## Lossy recipes, named

| recipe | why it is lossy |
|---|---|
| `COUNT_CHANNEL_STREAM` | rounding and clipping to uint16 discard sub-count precision and any value above 65535 |
| `BITPLANE_STREAM` | one plane of many; the rest are discarded |
| `MARK_SPACE_STREAM` | thresholding discards magnitude |

A lossy stream has **no inverse** and is marked `inverse: null`.

## Thresholds are frozen, not searched

`MARK_SPACE_STREAM` accepts only quantiles on the frozen grid
`(0.25, 0.5, 0.75)`. Searching thresholds until a stream looks interesting is
hypothesis inflation, and the module raises rather than allowing it.

The same applies to interleavings: `COUNT_CHANNEL_STREAM` accepts only the seven
declared orderings and refuses anything else.

## Rules that are enforced in code, not just written here

1. Source artifacts are never mutated. Decompression produces a new artifact and
   both byte strings are hashed.
2. Compression is detected by magic bytes. A `.Z` file that is really gzip is
   reported as gzip.
3. Only official mission roots are reachable; `..` cannot escape a root.
4. Decompressed size is capped, so an archive bomb is refused.
5. Remote filenames are sanitised before touching the filesystem.
6. Nothing downloaded is ever executed.

## What a result may claim

A finding in rung 3–8 data is a statement about **the archive product**. To become
a statement about the *spacecraft*, it would need rung 1 or 2 data, which the
public archive does not contain.

There is no `DISCOVERY` result class and no `MESSAGE_CONFIRMED` result class.

See [CLAIM_BOUNDARIES](CLAIM_BOUNDARIES.md) and
[NULL_AND_SIGNIFICANCE_POLICY](NULL_AND_SIGNIFICANCE_POLICY.md).
