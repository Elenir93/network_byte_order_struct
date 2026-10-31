import unittest

from network_byte_order_struct import (
    BYTE_ORDER,
    BufferError,
    read_int16,
    read_int32,
    read_int64,
    read_uint16,
    read_uint32,
    read_uint64,
    write_int16,
    write_int32,
    write_int64,
    write_uint16,
    write_uint32,
    write_uint64,
)


class TestByteOrderConstant(unittest.TestCase):
    def test_byte_order_is_big(self):
        self.assertEqual(BYTE_ORDER, "big")


class TestReadUnsigned(unittest.TestCase):
    def test_uint16_known_bytes(self):
        self.assertEqual(read_uint16(b"\x12\x34"), (0x1234, 2))

    def test_uint32_known_bytes(self):
        self.assertEqual(read_uint32(b"\x00\x01\x00\x00"), (0x00010000, 4))

    def test_uint64_max(self):
        self.assertEqual(
            read_uint64(b"\xff\xff\xff\xff\xff\xff\xff\xff"),
            (0xFFFFFFFFFFFFFFFF, 8),
        )

    def test_read_with_offset(self):
        buf = b"\x00\x00\x12\x34\x99"
        self.assertEqual(read_uint16(buf, offset=2), (0x1234, 2))

    def test_read_from_bytearray(self):
        self.assertEqual(read_uint32(bytearray(b"\x00\x00\x00\x2a")), (42, 4))

    def test_read_from_memoryview(self):
        mv = memoryview(b"\x00\x2a")
        self.assertEqual(read_uint16(mv), (42, 2))


class TestReadSigned(unittest.TestCase):
    def test_int16_negative(self):
        self.assertEqual(read_int16(b"\xff\xff"), (-1, 2))

    def test_int32_min(self):
        self.assertEqual(read_int32(b"\x80\x00\x00\x00"), (-2147483648, 4))

    def test_int64_negative(self):
        self.assertEqual(read_int64(b"\xff\xff\xff\xff\xff\xff\xff\xfe"), (-2, 8))

    def test_int16_positive(self):
        self.assertEqual(read_int16(b"\x7f\xff"), (32767, 2))


class TestReadErrors(unittest.TestCase):
    def test_short_buffer_uint16(self):
        with self.assertRaises(BufferError):
            read_uint16(b"\x12")

    def test_short_buffer_uint32(self):
        with self.assertRaises(BufferError):
            read_uint32(b"\x00\x00\x00")

    def test_offset_past_end(self):
        with self.assertRaises(BufferError):
            read_uint16(b"\x00\x00", offset=1)

    def test_negative_offset(self):
        with self.assertRaises(ValueError):
            read_uint16(b"\x00\x00", offset=-1)

    def test_wrong_buffer_type(self):
        with self.assertRaises(TypeError):
            read_uint16("not bytes")

    def test_buffer_error_is_value_error(self):
        # BufferError subclasses ValueError so callers can catch either.
        self.assertTrue(issubclass(BufferError, ValueError))


class TestWriteUnsigned(unittest.TestCase):
    def test_write_uint16_allocates(self):
        buf, n = write_uint16(0x1234)
        self.assertEqual(bytes(buf), b"\x12\x34")
        self.assertEqual(n, 2)

    def test_write_uint32_allocates(self):
        buf, n = write_uint32(0xDEADBEEF)
        self.assertEqual(bytes(buf), b"\xde\xad\xbe\xef")
        self.assertEqual(n, 4)

    def test_write_uint64_max(self):
        buf, n = write_uint64(0xFFFFFFFFFFFFFFFF)
        self.assertEqual(bytes(buf), b"\xff" * 8)
        self.assertEqual(n, 8)

    def test_write_into_existing_buffer_at_offset(self):
        target = bytearray(4)
        returned, n = write_uint16(0x0102, target, offset=1)
        self.assertIs(returned, target)
        self.assertEqual(n, 2)
        self.assertEqual(bytes(target), b"\x00\x01\x02\x00")

    def test_write_into_memoryview(self):
        backing = bytearray(2)
        mv = memoryview(backing)
        write_uint16(0xABCD, mv)
        self.assertEqual(bytes(backing), b"\xab\xcd")


class TestWriteSigned(unittest.TestCase):
    def test_write_int16_negative(self):
        buf, n = write_int16(-1)
        self.assertEqual(bytes(buf), b"\xff\xff")
        self.assertEqual(n, 2)

    def test_write_int32_min(self):
        buf, n = write_int32(-2147483648)
        self.assertEqual(bytes(buf), b"\x80\x00\x00\x00")
        self.assertEqual(n, 4)

    def test_write_int64_negative(self):
        buf, n = write_int64(-2)
        self.assertEqual(bytes(buf), b"\xff\xff\xff\xff\xff\xff\xff\xfe")
        self.assertEqual(n, 8)


class TestWriteErrors(unittest.TestCase):
    def test_uint16_overflow(self):
        with self.assertRaises(ValueError):
            write_uint16(0x10000)

    def test_uint16_negative(self):
        with self.assertRaises(ValueError):
            write_uint16(-1)

    def test_int16_overflow(self):
        with self.assertRaises(ValueError):
            write_int16(0x8000)

    def test_int16_underflow(self):
        with self.assertRaises(ValueError):
            write_int16(-0x8001)

    def test_bool_rejected(self):
        # bool is an int subclass; reject it explicitly so callers do not
        # accidentally write 0/1 when they meant an integer field.
        with self.assertRaises(TypeError):
            write_uint16(True)

    def test_non_int_rejected(self):
        with self.assertRaises(TypeError):
            write_uint16(1.5)

    def test_write_into_short_buffer(self):
        with self.assertRaises(BufferError):
            write_uint32(1, bytearray(3))

    def test_write_negative_offset(self):
        with self.assertRaises(ValueError):
            write_uint16(1, bytearray(2), offset=-1)

    def test_write_wrong_buffer_type(self):
        with self.assertRaises(TypeError):
            write_uint16(1, b"\x00\x00")


class TestRoundTrip(unittest.TestCase):
    def test_round_trip_all_widths(self):
        cases = [
            (write_uint16, read_uint16, 0xABCD),
            (write_uint32, read_uint32, 0x01020304),
            (write_uint64, read_uint64, 0x0102030405060708),
            (write_int16, read_int16, -12345),
            (write_int32, read_int32, -123456789),
            (write_int64, read_int64, -1234567890123456789),
        ]
        for writer, reader, value in cases:
            with self.subTest(value=value):
                buf, n = writer(value)
                got, used = reader(buf)
                self.assertEqual(got, value)
                self.assertEqual(used, n)

    def test_sequential_writes_are_big_endian(self):
        buf = bytearray(14)
        write_uint16(0x0001, buf, offset=0)
        write_uint32(0x00000002, buf, offset=2)
        write_uint64(0x0000000000000003, buf, offset=6)
        self.assertEqual(
            bytes(buf),
            b"\x00\x01\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03",
        )


if __name__ == "__main__":
    unittest.main()
