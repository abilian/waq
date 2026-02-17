"""Negative tests for WASM parser.

These tests verify that the parser correctly rejects malformed inputs
with appropriate error messages.

Tests marked with @pytest.mark.xfail indicate validation gaps that
should be addressed in future improvements.
"""

from __future__ import annotations

import pytest

from waq.errors import ParseError
from waq.parser.module import parse_module


class TestMalformedHeader:
    """Tests for malformed WASM headers."""

    def test_empty_input(self):
        """Empty input should raise ParseError."""
        with pytest.raises(ParseError):
            parse_module(b"")

    def test_truncated_magic(self):
        """Truncated magic number should raise ParseError."""
        with pytest.raises(ParseError):
            parse_module(b"\x00as")

    def test_wrong_magic(self):
        """Wrong magic number should raise ParseError."""
        with pytest.raises(ParseError, match="magic"):
            parse_module(b"\x00bsm\x01\x00\x00\x00")

    def test_truncated_version(self):
        """Truncated version should raise ParseError."""
        with pytest.raises(ParseError):
            parse_module(b"\x00asm\x01\x00")

    def test_wrong_version(self):
        """Wrong version should raise ParseError."""
        with pytest.raises(ParseError, match="version"):
            parse_module(b"\x00asm\x02\x00\x00\x00")

    def test_version_zero(self):
        """Version 0 should raise ParseError."""
        with pytest.raises(ParseError, match="version"):
            parse_module(b"\x00asm\x00\x00\x00\x00")


class TestTruncatedSections:
    """Tests for truncated section data."""

    def test_truncated_section_id(self):
        """Truncated section ID should raise ParseError."""
        # Valid header but no complete section
        with pytest.raises(ParseError):
            parse_module(b"\x00asm\x01\x00\x00\x00\x01")

    def test_truncated_section_length(self):
        """Truncated section length should raise ParseError."""
        # Section ID 0x01 (type) but incomplete LEB128 length
        with pytest.raises(ParseError):
            parse_module(b"\x00asm\x01\x00\x00\x00\x01\x80")

    def test_section_length_exceeds_data(self):
        """Section claiming more data than available should raise ParseError."""
        # Type section claiming 10 bytes but only 1 available
        with pytest.raises(ParseError):
            parse_module(b"\x00asm\x01\x00\x00\x00\x01\x0a\x00")

    def test_truncated_type_section(self):
        """Truncated type section should raise ParseError."""
        # Type section with 1 type but no type data
        with pytest.raises(ParseError):
            parse_module(b"\x00asm\x01\x00\x00\x00\x01\x01\x01")


class TestInvalidSectionOrder:
    """Tests for invalid section ordering."""

    @pytest.mark.xfail(reason="Parser doesn't validate duplicate sections yet")
    def test_duplicate_type_section(self):
        """Duplicate type section should raise ParseError."""
        # Two type sections
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # First type section: empty
            0x01, 0x01, 0x00,
            # Second type section: empty
            0x01, 0x01, 0x00,
        ])
        with pytest.raises(ParseError, match="(?i)(duplicate|already|multiple)"):
            parse_module(wasm)

    @pytest.mark.xfail(reason="Parser doesn't validate section ordering yet")
    def test_function_section_before_type(self):
        """Function section before type section should raise ParseError."""
        # Function section (0x03) before type section (0x01)
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Function section (should come after type)
            0x03, 0x01, 0x00,
            # Type section
            0x01, 0x01, 0x00,
        ])
        with pytest.raises(ParseError, match="(?i)(order|sequence|before)"):
            parse_module(wasm)


class TestInvalidTypeSection:
    """Tests for invalid type section data."""

    def test_invalid_func_type_marker(self):
        """Invalid function type marker should raise ParseError."""
        # Type section with wrong type marker (0x61 instead of 0x60)
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: 1 type, marker 0x61 (wrong)
            0x01, 0x04, 0x01, 0x61, 0x00, 0x00,
        ])
        with pytest.raises(ParseError, match="(?i)(type|func|0x60)"):
            parse_module(wasm)

    def test_invalid_value_type(self):
        """Invalid value type should raise ParseError."""
        # Type section with invalid value type 0xFF
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: 1 type, () -> (invalid)
            0x01, 0x04, 0x01, 0x60, 0x00, 0x01, 0xFF,
        ])
        # This should fail due to invalid value type
        with pytest.raises((ParseError, ValueError)):
            parse_module(wasm)


class TestInvalidFunctionSection:
    """Tests for invalid function section data."""

    @pytest.mark.xfail(reason="Parser doesn't validate type index bounds yet")
    def test_function_index_out_of_bounds(self):
        """Function referencing non-existent type should raise ParseError."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: 1 type () -> ()
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section: references type index 5 (doesn't exist)
            0x03, 0x02, 0x01, 0x05,
        ])
        # Should fail during parsing or validation
        with pytest.raises((ParseError, ValueError)):
            parse_module(wasm)


class TestInvalidCodeSection:
    """Tests for invalid code section data."""

    @pytest.mark.xfail(reason="Parser doesn't validate code/function count mismatch yet")
    def test_code_count_mismatch(self):
        """Code count not matching function count should raise ParseError."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: 1 type
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section: 2 functions
            0x03, 0x03, 0x02, 0x00, 0x00,
            # Code section: only 1 code entry
            0x0A, 0x04, 0x01, 0x02, 0x00, 0x0B,
        ])
        with pytest.raises(ParseError, match="(?i)(count|mismatch|function)"):
            parse_module(wasm)

    def test_truncated_function_body(self):
        """Truncated function body should raise ParseError."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section: claims 10 bytes for body but section is shorter
            0x0A, 0x03, 0x01, 0x0A,
        ])
        with pytest.raises(ParseError):
            parse_module(wasm)


class TestInvalidLEB128:
    """Tests for malformed LEB128 encoded values."""

    def test_leb128_too_long(self):
        """LEB128 value with too many bytes should raise ParseError."""
        # More than 5 bytes for u32 LEB128 (continuation bits all set)
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section with malformed count (too many LEB128 bytes)
            0x01, 0x0A, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x00,
        ])
        with pytest.raises(ParseError):
            parse_module(wasm)


class TestMemoryLimits:
    """Tests for memory limit validation."""

    @pytest.mark.xfail(reason="Parser doesn't validate memory min/max limits yet")
    def test_memory_max_less_than_min(self):
        """Memory max < min should raise ParseError."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Memory section: 1 memory with limits flag=1, min=10, max=5
            0x05, 0x04, 0x01, 0x01, 0x0A, 0x05,
        ])
        with pytest.raises((ParseError, ValueError), match="(?i)(limit|max|min)"):
            parse_module(wasm)


class TestTableLimits:
    """Tests for table limit validation."""

    @pytest.mark.xfail(reason="Parser doesn't validate table min/max limits yet")
    def test_table_max_less_than_min(self):
        """Table max < min should raise ParseError."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Table section: 1 table funcref with limits flag=1, min=10, max=5
            0x04, 0x05, 0x01, 0x70, 0x01, 0x0A, 0x05,
        ])
        with pytest.raises((ParseError, ValueError), match="(?i)(limit|max|min)"):
            parse_module(wasm)


class TestExportSection:
    """Tests for invalid export section."""

    def test_export_invalid_kind(self):
        """Export with invalid kind should raise ParseError."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Export section: 1 export, name "f", kind 0xFF (invalid), index 0
            0x07, 0x05, 0x01, 0x01, 0x66, 0xFF, 0x00,
        ])
        with pytest.raises((ParseError, ValueError), match="(?i)(kind|export)"):
            parse_module(wasm)

    @pytest.mark.xfail(reason="Parser doesn't validate export index bounds yet")
    def test_export_index_out_of_bounds(self):
        """Export referencing non-existent function should raise ParseError."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Export section: export "f" as function index 5 (doesn't exist)
            0x07, 0x05, 0x01, 0x01, 0x66, 0x00, 0x05,
        ])
        # Should fail during parsing or validation
        with pytest.raises((ParseError, ValueError)):
            parse_module(wasm)


class TestImportSection:
    """Tests for invalid import section."""

    def test_import_empty_module_name(self):
        """Import with empty module name should be accepted."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Import section: module="", name="f", kind=func, index=0
            0x02, 0x06, 0x01, 0x00, 0x01, 0x66, 0x00, 0x00,
        ])
        # Empty module name is valid per spec
        module = parse_module(wasm)
        assert len(module.imports) == 1

    def test_import_invalid_kind(self):
        """Import with invalid kind should raise ParseError."""
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Import section: module="m", name="n", kind=0xFF (invalid)
            0x02, 0x07, 0x01, 0x01, 0x6D, 0x01, 0x6E, 0xFF,
        ])
        with pytest.raises((ParseError, ValueError)):
            parse_module(wasm)
