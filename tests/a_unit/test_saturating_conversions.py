"""Unit tests for saturating float-to-int conversions (WASM 2.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_i32_trunc_sat_f32_s_wasm() -> bytes:
    """Create WASM with i32.trunc_sat_f32_s instruction.

    (x: f32) -> (i32)
    """
    # Type section: (f32) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x7D, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"conv" + bytes([0x00, 0x00])

    # Code section: i32.trunc_sat_f32_s
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xFC,
        0x00,  # i32.trunc_sat_f32_s
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_i32_trunc_sat_f64_u_wasm() -> bytes:
    """Create WASM with i32.trunc_sat_f64_u instruction.

    (x: f64) -> (i32)
    """
    # Type section: (f64) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x7C, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"conv" + bytes([0x00, 0x00])

    # Code section: i32.trunc_sat_f64_u
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xFC,
        0x03,  # i32.trunc_sat_f64_u
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_i64_trunc_sat_f32_s_wasm() -> bytes:
    """Create WASM with i64.trunc_sat_f32_s instruction.

    (x: f32) -> (i64)
    """
    # Type section: (f32) -> (i64)
    type_section = bytes([0x01, 0x60, 0x01, 0x7D, 0x01, 0x7E])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"conv" + bytes([0x00, 0x00])

    # Code section: i64.trunc_sat_f32_s
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xFC,
        0x04,  # i64.trunc_sat_f32_s
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_i64_trunc_sat_f64_u_wasm() -> bytes:
    """Create WASM with i64.trunc_sat_f64_u instruction.

    (x: f64) -> (i64)
    """
    # Type section: (f64) -> (i64)
    type_section = bytes([0x01, 0x60, 0x01, 0x7C, 0x01, 0x7E])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"conv" + bytes([0x00, 0x00])

    # Code section: i64.trunc_sat_f64_u
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0
        0xFC,
        0x07,  # i64.trunc_sat_f64_u
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestI32SaturatingConversions:
    """Tests for i32 saturating conversions."""

    def test_i32_trunc_sat_f32_s_compiles(self):
        """Test that i32.trunc_sat_f32_s compiles."""
        wasm = make_i32_trunc_sat_f32_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i32_trunc_sat_f32_s" in output

    def test_i32_trunc_sat_f64_u_compiles(self):
        """Test that i32.trunc_sat_f64_u compiles."""
        wasm = make_i32_trunc_sat_f64_u_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i32_trunc_sat_f64_u" in output


class TestI64SaturatingConversions:
    """Tests for i64 saturating conversions."""

    def test_i64_trunc_sat_f32_s_compiles(self):
        """Test that i64.trunc_sat_f32_s compiles."""
        wasm = make_i64_trunc_sat_f32_s_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i64_trunc_sat_f32_s" in output

    def test_i64_trunc_sat_f64_u_compiles(self):
        """Test that i64.trunc_sat_f64_u compiles."""
        wasm = make_i64_trunc_sat_f64_u_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i64_trunc_sat_f64_u" in output
