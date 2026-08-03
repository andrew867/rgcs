"""Deterministic reference codec for the RevA SPI frame."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct
import zlib


MAGIC = 0xA74D
VERSION = 1
_HEADER = struct.Struct(">HBBHH")
_CHECKSUM = struct.Struct(">I")


class Operation(IntEnum):
    READ_REG = 1
    WRITE_REG = 2
    STREAM_SENSE = 3
    LOAD_DRIVE_TABLE = 4
    ARM = 5
    DISARM = 6
    GET_RECEIPT_HASH = 7


@dataclass(frozen=True)
class Frame:
    operation: Operation
    address: int
    payload: bytes = b""
    version: int = VERSION


def encode_frame(frame: Frame) -> bytes:
    if not 0 <= frame.address <= 0xFFFF:
        raise ValueError("address out of range")
    if len(frame.payload) > 0xFFFF:
        raise ValueError("payload too large")
    body = _HEADER.pack(
        MAGIC,
        frame.version,
        int(frame.operation),
        frame.address,
        len(frame.payload),
    ) + bytes(frame.payload)
    return body + _CHECKSUM.pack(zlib.crc32(body) & 0xFFFFFFFF)


def decode_frame(data: bytes) -> Frame:
    if len(data) < _HEADER.size + _CHECKSUM.size:
        raise ValueError("frame is truncated")
    magic, version, operation, address, length = _HEADER.unpack_from(data)
    if magic != MAGIC or version != VERSION:
        raise ValueError("frame header is invalid")
    expected = _HEADER.size + length + _CHECKSUM.size
    if len(data) != expected:
        raise ValueError("frame length is invalid")
    body = data[:-_CHECKSUM.size]
    supplied = _CHECKSUM.unpack_from(data, len(body))[0]
    if zlib.crc32(body) & 0xFFFFFFFF != supplied:
        raise ValueError("frame checksum mismatch")
    return Frame(Operation(operation), address, data[_HEADER.size : -_CHECKSUM.size], version)
