# SPI protocol sketch

## Frame

```text
MAGIC u16 = 0xA74D
VERSION u8
OP u8
ADDR u16
LEN u16
PAYLOAD bytes
CRC32 u32
```

## Operations

- READ_REG
- WRITE_REG
- STREAM_SENSE
- LOAD_DRIVE_TABLE
- ARM
- DISARM
- GET_RECEIPT_HASH

## Safety

- Device powers up disabled.
- ENABLE requires valid config hash and active floor check.
- Watchdog disables output on missed heartbeat.
- Hardware current limit is mandatory; software is not the only protection.
