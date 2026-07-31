# Stream recipes

Every recipe records source, columns, rows, scaling, serialization width,
endianness, bit order, missing-data policy, a **lossy flag**, an **inverse** where
one exists, and an output hash.

| id | recipe | lossy | inverse |
|---|---|---|---|
| A | `ARCHIVE_BYTES` | no | identity |
| B | `DECOMPRESSED_FILE_BYTES` | no | recompress |
| C | `FITS_HDU_RAW_STORAGE` | no | documented padding/endianness |
| D | `FITS_COLUMN_RAW` | no | `numpy.frombuffer` with recorded dtype |
| E | `FITS_COLUMN_PHYSICAL` | no | inverse scale/zero |
| F | `TIME_ORDERED_ROWS` | no | recorded permutation |
| G | `COUNT_CHANNEL_STREAM` | **yes** | none |
| H | `EVENT_TIME_STREAM` | depends | deltas reversible; ranks not |
| I | `BITPLANE_STREAM` | **yes** | none |
| J | `MARK_SPACE_STREAM` | **yes** | none |
| K | `FRAME_OR_PACKET_BYTES` | no | identity |

## Declared, never searched

`COUNT_CHANNEL_STREAM` accepts only: `channel_1_only`, `channel_2_only`,
`alternating`, `channel_major`, `row_major`, `difference`, `sum`. Anything else
raises.

`MARK_SPACE_STREAM` accepts only quantiles on the frozen grid
`(0.25, 0.5, 0.75)`. Searching thresholds until something looks interesting is
hypothesis inflation, and it is refused in code rather than discouraged in prose.

## Why lossy matters

A lossy stream cannot be inverted, so a pattern found in it cannot be traced back
to source values. `COUNT_CHANNEL_STREAM` rounds and clips to uint16 - sub-count
precision and anything above 65535 are gone. That is recorded in `lossy_reason`
on every receipt.
