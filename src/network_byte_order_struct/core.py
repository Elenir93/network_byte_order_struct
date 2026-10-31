"""Read and write multi-byte integers in network byte order.

Network byte order is big-endian: the most significant byte comes first.
This module deliberately works on plain ``bytes``/``bytearray`` buffers rather
than streams so that it stays dependency-free and usable in contexts where a
file object is not available.

All read functions return the integer and the number of bytes consumed
(always the width of the type). All write functions return the number of
bytes written (always the width of the type).
"""

import struct

#: Canonical name for the byte order used throughout this module.
BYTE_ORDER = "big"


class BufferError(ValueError):
    """Raised when a buffer is too short for the requested integer width.

    Subclassing ``ValueError`` keeps compatibility with callers that already
    catch ``ValueError`` for malformed input.
    """


def _check_buffer(buf, offset, width):
    """Validate that ``buf`` has ``width`` bytes available at ``offset``.

    Returns the memoryview slice so callers do not repeat the bounds check.
    """
    if not isinstance(buf, (bytes, bytearray, memoryview)):
        raise TypeError("buffer must be bytes, bytearray, or memoryview")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    end = offset + width
    if end > len(buf):
        raise BufferError(
            "buffer of length %d is too short for %d bytes at offset %d"
            % (len(buf), width, offset)
        )
    return memoryview(buf)[offset:end]


def read_uint16(buf, offset=0):
    """Read an unsigned 16-bit integer. Returns ``(value, 2)``."""
    view = _check_buffer(buf, offset, 2)
    return struct.unpack(">H", view)[0], 2


def read_uint32(buf, offset=0):
    """Read an unsigned 32-bit integer. Returns ``(value, 4)``."""
    view = _check_buffer(buf, offset, 4)
    return struct.unpack(">I", view)[0], 4


def read_uint64(buf, offset=0):
    """Read an unsigned 64-bit integer. Returns ``(value, 8)``."""
    view = _check_buffer(buf, offset, 8)
    return struct.unpack(">Q", view)[0], 8


def read_int16(buf, offset=0):
    """Read a signed 16-bit integer. Returns ``(value, 2)``."""
    view = _check_buffer(buf, offset, 2)
    return struct.unpack(">h", view)[0], 2


def read_int32(buf, offset=0):
    """Read a signed 32-bit integer. Returns ``(value, 4)``."""
    view = _check_buffer(buf, offset, 4)
    return struct.unpack(">i", view)[0], 4


def read_int64(buf, offset=0):
    """Read a signed 64-bit integer. Returns ``(value, 8)``."""
    view = _check_buffer(buf, offset, 8)
    return struct.unpack(">q", view)[0], 8


def _check_range(value, lo, hi, name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("%s must be an int" % name)
    if value < lo or value > hi:
        raise ValueError("%s out of range: %d not in [%d, %d]" % (name, value, lo, hi))


def write_uint16(value, buf=None, offset=0):
    """Write an unsigned 16-bit integer.

    If ``buf`` is ``None`` a new ``bytearray`` is allocated and returned as
    ``(buf, 2)``. Otherwise the value is written into ``buf`` at ``offset``
    and ``(buf, 2)`` is returned; the buffer must be large enough.
    """
    _check_range(value, 0, 0xFFFF, "uint16")
    return _write(">H", value, buf, offset, 2)


def write_uint32(value, buf=None, offset=0):
    """Write an unsigned 32-bit integer. See :func:`write_uint16`."""
    _check_range(value, 0, 0xFFFFFFFF, "uint32")
    return _write(">I", value, buf, offset, 4)


def write_uint64(value, buf=None, offset=0):
    """Write an unsigned 64-bit integer. See :func:`write_uint16`."""
    _check_range(value, 0, 0xFFFFFFFFFFFFFFFF, "uint64")
    return _write(">Q", value, buf, offset, 8)


def write_int16(value, buf=None, offset=0):
    """Write a signed 16-bit integer. See :func:`write_uint16`."""
    _check_range(value, -0x8000, 0x7FFF, "int16")
    return _write(">h", value, buf, offset, 2)


def write_int32(value, buf=None, offset=0):
    """Write a signed 32-bit integer. See :func:`write_uint16`."""
    _check_range(value, -0x80000000, 0x7FFFFFFF, "int32")
    return _write(">i", value, buf, offset, 4)


def write_int64(value, buf=None, offset=0):
    """Write a signed 64-bit integer. See :func:`write_uint16`."""
    _check_range(value, -0x8000000000000000, 0x7FFFFFFFFFFFFFFF, "int64")
    return _write(">q", value, buf, offset, 8)


def _write(fmt, value, buf, offset, width):
    if buf is None:
        return bytearray(struct.pack(fmt, value)), width
    if not isinstance(buf, (bytearray, memoryview)):
        raise TypeError("buf must be a bytearray, memoryview, or None")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    if offset + width > len(buf):
        raise BufferError(
            "buffer of length %d is too short for %d bytes at offset %d"
            % (len(buf), width, offset)
        )
    struct.pack_into(fmt, buf, offset, value)
    return buf, width
