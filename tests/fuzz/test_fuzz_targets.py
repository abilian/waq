"""Tests for fuzzing targets.

These tests verify that the fuzzing targets handle various inputs
correctly without crashing.
"""

from __future__ import annotations

import pytest

from .fuzz_compiler import fuzz_compiler
from .fuzz_parser import fuzz_parser


class TestFuzzParser:
    """Test the parser fuzzing target."""

    def test_empty_input(self):
        """Empty input should not crash."""
        fuzz_parser(b"")

    def test_random_bytes(self):
        """Random bytes should not crash."""
        fuzz_parser(b"\x00\x01\x02\x03\x04\x05")

    def test_valid_magic(self):
        """Valid magic but truncated should not crash."""
        fuzz_parser(b"\x00asm")

    def test_valid_header(self):
        """Valid header should parse (minimal module)."""
        fuzz_parser(b"\x00asm\x01\x00\x00\x00")

    def test_wrong_magic(self):
        """Wrong magic should not crash."""
        fuzz_parser(b"\x00bsm\x01\x00\x00\x00")

    def test_wrong_version(self):
        """Wrong version should not crash."""
        fuzz_parser(b"\x00asm\x02\x00\x00\x00")

    def test_truncated_section(self):
        """Truncated section should not crash."""
        fuzz_parser(b"\x00asm\x01\x00\x00\x00\x01\xff")

    def test_very_large_section_count(self):
        """Large section count should be limited and not crash."""
        # Section 0x01 with count 0xffffffff (LEB128)
        fuzz_parser(b"\x00asm\x01\x00\x00\x00\x01\x05\xff\xff\xff\xff\x0f")

    @pytest.mark.parametrize("byte_val", range(0, 256, 17))
    def test_single_bytes(self, byte_val: int):
        """Single byte inputs should not crash."""
        fuzz_parser(bytes([byte_val]))


class TestFuzzCompiler:
    """Test the compiler fuzzing target."""

    def test_empty_input(self):
        """Empty input should not crash."""
        fuzz_compiler(b"")

    def test_minimal_module(self):
        """Minimal valid module should compile."""
        fuzz_compiler(b"\x00asm\x01\x00\x00\x00")

    def test_invalid_wasm(self):
        """Invalid WASM should not crash the compiler."""
        fuzz_compiler(b"not wasm at all")

    def test_truncated_header(self):
        """Truncated header should not crash."""
        fuzz_compiler(b"\x00asm\x01\x00")

    def test_malformed_type_section(self):
        """Malformed type section should not crash."""
        # Type section with bad data
        fuzz_compiler(b"\x00asm\x01\x00\x00\x00\x01\x03\x01\xff\xff")

    def test_module_with_empty_function(self):
        """Module with empty function should compile."""
        # Module with type () -> (), function index 0, and code section
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> ()
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section
            0x0A, 0x04, 0x01, 0x02, 0x00, 0x0B,
        ])
        fuzz_compiler(wasm)
