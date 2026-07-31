# NASA archive codec workbench — quickstart

```bash
python -m rgcs_archive mission-list
python -m rgcs_archive estimate vela5b
python -m rgcs_archive catalog vela5b --out manifest.json
python -m rgcs_archive download <url> --quota-mib 32
python -m rgcs_archive inspect <file.Z>
python -m rgcs_archive derive <file> --recipe COUNT_CHANNEL_STREAM
python -m rgcs_archive parse-long 1687549873523387598456323376543328567433
python -m rgcs_archive route      1687549873523387598456323376543328567433
python -m rgcs_archive verify
```

`--dry-run` blocks all network access.

## Mission status

| mission | status | notes |
|---|---|---|
| `vela5b` | **IMPLEMENTED** | catalog, estimate, download, `.Z`, FITS, streams |
| `voyager2_pws` | ADAPTER_STUB | PDS4 label reader not implemented |
| `batse` | ADAPTER_STUB | trigger package reader not implemented |
| `fermi_gbm` | ADAPTER_STUB | trigger package reader not implemented |

A stub declares its blocker and does nothing else. It never pretends to work.

## Measured Vela 5B archive

```
files                12,693
total                5,274,187,869 bytes = 4.912 GiB
mean file            415,519 bytes
largest              all_bad.dat, 8 MiB
subdirectories       1969..1979, b00..b11
```

Estimation uses reported index sizes and HEAD; the archive is never downloaded to
measure it. **Do not mirror the whole archive** before the phased checks in
[VELA5B_ADAPTER](VELA5B_ADAPTER.md) are green.

## Politeness

Concurrency 2, 0.5 s delay, exponential backoff, 4 retries, resumable ranges,
per-download quota, identifying user agent. This is shared public infrastructure.

## Boundaries

Read
[SOURCE_AND_REPRESENTATION_BOUNDARIES](SOURCE_AND_REPRESENTATION_BOUNDARIES.md)
before interpreting anything. The short version: **a FITS file's bytes are an
archive encoding, not the spacecraft's transmitted bitstream**, and the Vela 5B
public archive is the X-ray ASM product — not the gamma-ray detector bitstream and
not the original serial telemetry.

There is no `DISCOVERY` result class.
