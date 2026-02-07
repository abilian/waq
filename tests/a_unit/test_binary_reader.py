"""Unit tests for the binary reader and LEB128 decoding."""

from __future__ import annotations

import pytest

from waq.errors import ParseError
from waq.parser.binary import BinaryReader


class TestBinaryReader:
    """Tests for BinaryReader basic operations."""

    def test_read_bytes(self):
        reader = BinaryReader(b"\x01\x02\x03\x04")
        assert reader.read_bytes(2) == b"\x01\x02"
        assert reader.read_bytes(2) == b"\x03\x04"

    def test_read_bytes_insufficient(self):
        reader = BinaryReader(b"\x01\x02")
        with pytest.raises(ParseError, match="unexpected end"):
            reader.read_bytes(5)

    def test_read_byte(self):
        reader = BinaryReader(b"\x42\x43")
        assert reader.read_byte() == 0x42
        assert reader.read_byte() == 0x43

    def test_peek_byte(self):
        reader = BinaryReader(b"\x42\x43")
        assert reader.peek_byte() == 0x42
        assert reader.peek_byte() == 0x42  # Still the same
        reader.read_byte()
        assert reader.peek_byte() == 0x43

    def test_at_end(self):
        reader = BinaryReader(b"\x01")
        assert not reader.at_end
        reader.read_byte()
        assert reader.at_end


class TestLEB128:
    """Tests for LEB128 integer decoding."""

    def test_u32_single_byte(self):
        # Values 0-127 use single byte
        reader = BinaryReader(b"\x00")
        assert reader.read_u32_leb128() == 0

        reader = BinaryReader(b"\x01")
        assert reader.read_u32_leb128() == 1

        reader = BinaryReader(b"\x7f")
        assert reader.read_u32_leb128() == 127

    def test_u32_multi_byte(self):
        # 128 = 0x80 0x01
        reader = BinaryReader(b"\x80\x01")
        assert reader.read_u32_leb128() == 128

        # 624485 = 0xE5 0x8E 0x26
        reader = BinaryReader(b"\xe5\x8e\x26")
        assert reader.read_u32_leb128() == 624485

    def test_s32_positive(self):
        reader = BinaryReader(b"\x00")
        assert reader.read_s32_leb128() == 0

        reader = BinaryReader(b"\x3f")
        assert reader.read_s32_leb128() == 63

    def test_s32_negative(self):
        # -1 = 0x7f
        reader = BinaryReader(b"\x7f")
        assert reader.read_s32_leb128() == -1

        # -128 = 0x80 0x7f
        reader = BinaryReader(b"\x80\x7f")
        assert reader.read_s32_leb128() == -128

    def test_s64_large(self):
        # Large positive value
        reader = BinaryReader(b"\xff\xff\xff\xff\x07")
        assert reader.read_s64_leb128() == 0x7FFFFFFF


class TestFloats:
    """Tests for float reading."""

    def test_f32(self):
        # IEEE 754 single: 1.0 = 0x3f800000
        reader = BinaryReader(b"\x00\x00\x80\x3f")
        assert reader.read_f32() == 1.0

    def test_f64(self):
        # IEEE 754 double: 1.0 = 0x3ff0000000000000
        reader = BinaryReader(b"\x00\x00\x00\x00\x00\x00\xf0\x3f")
        assert reader.read_f64() == 1.0


class TestNames:
    """Tests for name reading."""

    def test_read_name(self):
        # Length-prefixed UTF-8: 5 bytes "hello"
        reader = BinaryReader(b"\x05hello")
        assert reader.read_name() == "hello"

    def test_read_empty_name(self):
        reader = BinaryReader(b"\x00")
        assert reader.read_name() == ""
