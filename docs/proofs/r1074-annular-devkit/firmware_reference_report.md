# Firmware Reference Report

**Status:** `PASS_REFERENCE_CONTROL_PUBLICATION_HOLD`

The firmware model controls only `DeltaB` direction and magnitude. Its command
surface is modulation, lag, per-sector/group amplitude balance, and thermal
derating. It clamps modulation to `0..0.5`, lag to `-pi..pi`, group balance to
`0.9..1.1`, and refuses any derating that would take an active cell below 0.5.
It begins from the hash-validated R10.73 rows and never synthesizes a substitute
fabrication table.

The runtime is default-off. Arming requires the exact authority configuration
hash, closed enclosure, valid sensors, and a hardware current limiter. Missed
heartbeat, enclosure opening, invalid sensors, or overtemperature disarms and
latches a fault. The SPI reference codec implements the declared magic,
version, operation, address, payload length, and CRC32 fields.

## Locked inputs

- Source authority commit: `710e5947c80ea7a2299dc0a40fd63a4262891e39`.
- Carrier: 1,683,456 Hz, exactly `4096 * 411`.
- Envelope/reference: 4096 Hz.
- Constrained point: `mod=0.5`, `lag=pi`, `|d_eff|=0.4124`, offset about 12.46 degrees.

## Boundary and pending work

There is no force/thrust executable namespace, wall-power performance path,
hardware abstraction layer, driver timing implementation, or high-power
authorization. Hardware-in-loop timing, current-limit behavior, EMI,
watchdog, thermal response, and fault injection remain physical acceptance
work.
