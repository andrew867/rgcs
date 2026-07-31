# Vela 5B adapter

**Status: IMPLEMENTED.** Catalog, estimate, resumable download, legacy `.Z`
decompression, FITS inspection, and stream recipes all run against the live
archive.

## What the product is

The public raw archive is the **All Sky Monitor X-ray detector** product in FITS.
It is **not** the original serial radio telemetry and **not** the gamma-ray
detector bitstream. Verified by inspection:

```
TELESCOP = VELA 5B      INSTRUME = XC      HDU 1 = RATE (BinTableHDU)
YEAR DOY SOD TIME L_PNT B_PNT C1CNTS C2CNTS L_SCZ B_SCZ STABFLAG PNTFLAG SPIN
```

`C1CNTS` and `C2CNTS` are the two X-ray energy channels; counts are one-second
accumulations. `SPIN` carries the ~64 s spin period.

## Layout

`raw/` holds `1969`-`1979` (time-ordered, ~5 mission days per file) and
`b00`-`b11` (coordinate-ordered), plus `all_bad.README` and `all_bad.dat`.
Files are legacy Unix `.Z`, detected by magic bytes.

Smallest file: `1971/26_31jan1971.raw.Z`, 3,276 B -> 11,520 B FITS, 3 rows.

## Phases

| phase | scope | gate |
|---|---|---|
| **V0** catalog only | crawl, count, estimate | done - 12,693 files, 4.912 GiB |
| **V1** minimal sample | README + smallest + typical file, schema report | done |
| **V2** one year | 1969, corrupt-row ledger respected, no silent row loss | not started |
| **V3** full archive | stream processing, checkpointed | **blocked on V2** |

Do not mirror before V0-V2 are green.

## Controls that must accompany any Vela finding

- channel 1 and channel 2 independently, then swapped
- time-shuffled and within-file row-shuffled
- synthetic Poisson counts at matched rates
- temperature and spin-period nuisance regressors
- corrupted rows included vs excluded (`all_bad.dat`)
- archive byte stream vs physical value stream

Instrument temperature and gain variation produce large artificial periodic
structure, and the spin (~64 s) and orbit (~112 h) periods are imprinted on
everything. Periodicity near those is `INSTRUMENT_ARTIFACT` until a control says
otherwise.

## Known gap

No `fvelalc` parity check - HEASoft is not required by this implementation and is
not installed. Optional parity remains unimplemented.
