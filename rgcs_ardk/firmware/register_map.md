# Firmware register map RevA

## Transport

Reference transport: SPI or USB CDC. Final interface selected by embedded implementation.

## Registers

| Address | Name | Type | Description |
|---:|---|---|---|
| 0x0000 | FW_VERSION | u32 | firmware version |
| 0x0004 | CONFIG_HASH | u128 | active configuration hash, read in chunks |
| 0x0010 | ENABLE | bool | default false |
| 0x0014 | CARRIER_HZ | u32 | 1,683,456 |
| 0x0018 | ENVELOPE_HZ | u32 | 4096 |
| 0x0020 | MOD_CMD | float32 | clamped 0..0.5 |
| 0x0024 | LAG_CMD_RAD | float32 | clamped -pi..pi |
| 0x0028 | ACTIVE_FLOOR | float32 | must be >=0.5 |
| 0x0030 | COMMAND_ANGLE_RAD | float32 | commanded DeltaB angle |
| 0x0034 | COMMAND_MAG | float32 | commanded normalized DeltaB magnitude |
| 0x0100.. | SECTOR_AMP_00..36 | float32 | sector amplitude weights |
| 0x0200.. | SECTOR_PHASE_00..36 | float32 | sector phase offsets |
| 0x0300.. | SECTOR_LOAD_00..36 | float32 | sector loading values |
| 0x0400.. | SENSE_COMPLEX_00..36 | complex float32 | sector pickup samples |
| 0x0500.. | COMPASS_COMPLEX_0..7 | complex float32 | coarse compass pickups |
| 0x0600 | FAULT_FLAGS | u32 | latched faults |

## Forbidden registers

No `force`, `thrust`, `lift`, `propulsion`, or wall-power performance registers may exist.
