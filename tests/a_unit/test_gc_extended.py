"""Extended tests for GC instructions - cover additional variants."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_struct_get_s_wasm() -> bytes:
    """Create WASM with struct.get_s instruction (signed get for packed fields)."""
    # Type section: struct with i8 field (packed)
    type_section = bytes([
        0x02,
        # Type 0: struct with one i8 field (packed)
        0x5F,
        0x01,
        0x78,  # i8 (packed)
        0x01,  # mutable
        # Type 1: (structref) -> (i32)
        0x60,
        0x01,
        0x6B,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x01])
    export_section = bytes([0x01, 0x0C]) + b"struct_get_s" + bytes([0x00, 0x00])

    # Code: struct.get_s 0 0
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0xFB,
        0x03,
        0x00,
        0x00,  # struct.get_s 0 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    return wasm


def make_struct_get_u_wasm() -> bytes:
    """Create WASM with struct.get_u instruction (unsigned get for packed fields)."""
    type_section = bytes([
        0x02,
        # Type 0: struct with one i8 field (packed)
        0x5F,
        0x01,
        0x78,
        0x01,
        # Type 1: (structref) -> (i32)
        0x60,
        0x01,
        0x6B,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x01])
    export_section = bytes([0x01, 0x0C]) + b"struct_get_u" + bytes([0x00, 0x00])

    # Code: struct.get_u 0 0
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0xFB,
        0x04,
        0x00,
        0x00,  # struct.get_u 0 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    return wasm


def make_array_get_s_wasm() -> bytes:
    """Create WASM with array.get_s instruction."""
    type_section = bytes([
        0x02,
        # Type 0: array of i8
        0x5E,
        0x78,
        0x01,  # array, i8, mutable
        # Type 1: (arrayref, i32) -> (i32)
        0x60,
        0x02,
        0x6A,
        0x7F,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x01])
    export_section = bytes([0x01, 0x0B]) + b"array_get_s" + bytes([0x00, 0x00])

    # Code: array.get_s 0
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0 (arrayref)
        0x20,
        0x01,  # local.get 1 (index)
        0xFB,
        0x0C,
        0x00,  # array.get_s 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    return wasm


def make_array_get_u_wasm() -> bytes:
    """Create WASM with array.get_u instruction."""
    type_section = bytes([
        0x02,
        # Type 0: array of i8
        0x5E,
        0x78,
        0x01,
        # Type 1: (arrayref, i32) -> (i32)
        0x60,
        0x02,
        0x6A,
        0x7F,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x01])
    export_section = bytes([0x01, 0x0B]) + b"array_get_u" + bytes([0x00, 0x00])

    # Code: array.get_u 0
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0x20,
        0x01,  # local.get 1
        0xFB,
        0x0D,
        0x00,  # array.get_u 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    return wasm


class TestPackedStructAccess:
    """Tests for packed struct field access."""

    def test_struct_get_s_compiles(self):
        """Test that struct.get_s compiles."""
        wasm = make_struct_get_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Signed load with extension
        assert "load" in output.lower()

    def test_struct_get_u_compiles(self):
        """Test that struct.get_u compiles."""
        wasm = make_struct_get_u_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Unsigned load with extension
        assert "load" in output.lower()


class TestPackedArrayAccess:
    """Tests for packed array element access."""

    def test_array_get_s_compiles(self):
        """Test that array.get_s compiles."""
        wasm = make_array_get_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "load" in output.lower()

    def test_array_get_u_compiles(self):
        """Test that array.get_u compiles."""
        wasm = make_array_get_u_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "load" in output.lower()
