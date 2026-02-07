"""Unit tests for sign extension operations (WASM 2.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_i32_extend8_s_wasm() -> bytes:
    """Create WASM with i32.extend8_s instruction.

    (x: i32) -> (i32)
    """
    # Type section: (i32) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x7F, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x07]) + b"extend8" + bytes([0x00, 0x00])

    # Code section: i32.extend8_s
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xC0,  # i32.extend8_s
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_i32_extend16_s_wasm() -> bytes:
    """Create WASM with i32.extend16_s instruction.

    (x: i32) -> (i32)
    """
    # Type section: (i32) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x7F, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x08]) + b"extend16" + bytes([0x00, 0x00])

    # Code section: i32.extend16_s
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xC1,  # i32.extend16_s
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_i64_extend8_s_wasm() -> bytes:
    """Create WASM with i64.extend8_s instruction.

    (x: i64) -> (i64)
    """
    # Type section: (i64) -> (i64)
    type_section = bytes([0x01, 0x60, 0x01, 0x7E, 0x01, 0x7E])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x09]) + b"extend8_l" + bytes([0x00, 0x00])

    # Code section: i64.extend8_s
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xC2,  # i64.extend8_s
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_i64_extend16_s_wasm() -> bytes:
    """Create WASM with i64.extend16_s instruction.

    (x: i64) -> (i64)
    """
    # Type section: (i64) -> (i64)
    type_section = bytes([0x01, 0x60, 0x01, 0x7E, 0x01, 0x7E])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x0A]) + b"extend16_l" + bytes([0x00, 0x00])

    # Code section: i64.extend16_s
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xC3,  # i64.extend16_s
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_i64_extend32_s_wasm() -> bytes:
    """Create WASM with i64.extend32_s instruction.

    (x: i64) -> (i64)
    """
    # Type section: (i64) -> (i64)
    type_section = bytes([0x01, 0x60, 0x01, 0x7E, 0x01, 0x7E])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x0A]) + b"extend32_l" + bytes([0x00, 0x00])

    # Code section: i64.extend32_s
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xC4,  # i64.extend32_s
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestI32SignExtension:
    """Tests for i32 sign extension instructions."""

    def test_i32_extend8_s_compiles(self):
        """Test that i32.extend8_s compiles."""
        wasm = make_i32_extend8_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "extsb" in output

    def test_i32_extend16_s_compiles(self):
        """Test that i32.extend16_s compiles."""
        wasm = make_i32_extend16_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "extsh" in output


class TestI64SignExtension:
    """Tests for i64 sign extension instructions."""

    def test_i64_extend8_s_compiles(self):
        """Test that i64.extend8_s compiles."""
        wasm = make_i64_extend8_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "extsb" in output

    def test_i64_extend16_s_compiles(self):
        """Test that i64.extend16_s compiles."""
        wasm = make_i64_extend16_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "extsh" in output

    def test_i64_extend32_s_compiles(self):
        """Test that i64.extend32_s compiles."""
        wasm = make_i64_extend32_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "extsw" in output
