# network_byte_order_struct

Reads and writes multi-byte integers in network byte order (big-endian) from
plain `bytes`/`bytearray` buffers.

```python
from network_byte_order_struct import write_uint32, read_uint32, read_int16

buf, n = write_uint32(0x01020304)
assert bytes(buf) == b"\x01\x02\x03\x04"
assert n == 4

value, used = read_uint32(buf)
assert value == 0x01020304 and used == 4

# Signed and unsigned readers share the same shape:
negative, _ = read_int16(b"\xff\xff")
assert negative == -1
```

## Why this exists

`struct` already handles big-endian packing, but every call site has to
remember the format character and the width, and mixing up `>H` with `>h` (or
`>I` with `>i`) is a silent bug. This library fixes the widths and the byte
order in named functions so a call site says exactly what it means. The
trade-off is that only the six common integer widths are supported; if you
need floats or packed heterogeneous records, use `struct` directly.

## API

All read functions take a buffer (`bytes`, `bytearray`, or `memoryview`) and
an optional `offset`, and return `(value, bytes_consumed)`. All write
functions take a value, an optional `bytearray`/`memoryview` target, and an
optional `offset`, and return `(buffer, bytes_written)`. When the target is
`None`, a fresh `bytearray` is allocated and returned.

Exported names:

- `BYTE_ORDER` — the string `"big"`.
- `BufferError` — raised when a buffer is too short. Subclasses `ValueError`.
- `read_uint16`, `read_uint32`, `read_uint64`
- `read_int16`, `read_int32`, `read_int64`
- `write_uint16`, `write_uint32`, `write_uint64`
- `write_int16`, `write_int32`, `write_int64`

## The awkward edge

`bool` is a subclass of `int` in Python, so `write_uint16(True)` would happily
write `0x0001` if the range check only used `isinstance(value, int)`. The
write functions reject `bool` explicitly. If you genuinely want to write a
boolean as an integer, convert it first with `int(flag)`.

Out-of-range values raise `ValueError`, non-integer values raise `TypeError`,
and short buffers raise `BufferError`. Offsets are measured from the start of
the buffer and must be non-negative.
