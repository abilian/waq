"""Unit tests for type conversion instruction compilation."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_conversion_wasm(
    opcode: int,
    input_type: int,
    output_type: int,
) -> bytes:
    """Create WASM for a function that does a conversion.

    (input_type) -> output_type { convert(a) }
    """
    # Body: 0 locals (1), get 0 (2), convert (1), end (1) = 5 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (input_type) -> (output_type)
        0x01,
        0x06,
        0x01,
        0x60,
        0x01,
        input_type,
        0x01,
        output_type,
        # Function section
        0x03,
        0x02,
        0x01,
        0x00,
        # Code section
        0x0A,
        0x07,
        0x01,
        0x05,
        0x00,
        0x20,
        0x00,  # local.get 0
        opcode,  # conversion
        0x0B,  # end
    ])


class TestIntWrapExtend:
    """Tests for i32.wrap and i64.extend."""

    def test_i32_wrap_i64(self):
        """Test i32.wrap_i64 instruction."""
        wasm = make_conversion_wasm(0xA7, 0x7E, 0x7F)  # i64 -> i32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Wrapping is just copying with w type
        assert "copy" in output.lower() or "%" in output

    def test_i64_extend_i32_s(self):
        """Test i64.extend_i32_s instruction."""
        wasm = make_conversion_wasm(0xAC, 0x7F, 0x7E)  # i32 -> i64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "extsw" in output

    def test_i64_extend_i32_u(self):
        """Test i64.extend_i32_u instruction."""
        wasm = make_conversion_wasm(0xAD, 0x7F, 0x7E)  # i32 -> i64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "extuw" in output


class TestIntTruncFloat:
    """Tests for i32/i64 truncation from floats."""

    def test_i32_trunc_f32_s(self):
        """Test i32.trunc_f32_s instruction."""
        wasm = make_conversion_wasm(0xA8, 0x7D, 0x7F)  # f32 -> i32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "stosi" in output

    def test_i32_trunc_f32_u(self):
        """Test i32.trunc_f32_u instruction."""
        wasm = make_conversion_wasm(0xA9, 0x7D, 0x7F)  # f32 -> i32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "stoui" in output

    def test_i32_trunc_f64_s(self):
        """Test i32.trunc_f64_s instruction."""
        wasm = make_conversion_wasm(0xAA, 0x7C, 0x7F)  # f64 -> i32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "dtosi" in output

    def test_i32_trunc_f64_u(self):
        """Test i32.trunc_f64_u instruction."""
        wasm = make_conversion_wasm(0xAB, 0x7C, 0x7F)  # f64 -> i32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "dtoui" in output

    def test_i64_trunc_f32_s(self):
        """Test i64.trunc_f32_s instruction."""
        wasm = make_conversion_wasm(0xAE, 0x7D, 0x7E)  # f32 -> i64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "stosi" in output

    def test_i64_trunc_f64_s(self):
        """Test i64.trunc_f64_s instruction."""
        wasm = make_conversion_wasm(0xB0, 0x7C, 0x7E)  # f64 -> i64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "dtosi" in output

    def test_i64_trunc_f32_u(self):
        """Test i64.trunc_f32_u instruction."""
        wasm = make_conversion_wasm(0xAF, 0x7D, 0x7E)  # f32 -> i64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "stoui" in output

    def test_i64_trunc_f64_u(self):
        """Test i64.trunc_f64_u instruction."""
        wasm = make_conversion_wasm(0xB1, 0x7C, 0x7E)  # f64 -> i64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "dtoui" in output


class TestFloatConvertInt:
    """Tests for float conversion from ints."""

    def test_f32_convert_i32_s(self):
        """Test f32.convert_i32_s instruction."""
        wasm = make_conversion_wasm(0xB2, 0x7F, 0x7D)  # i32 -> f32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "swtof" in output

    def test_f32_convert_i32_u(self):
        """Test f32.convert_i32_u instruction."""
        wasm = make_conversion_wasm(0xB3, 0x7F, 0x7D)  # i32 -> f32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "uwtof" in output

    def test_f32_convert_i64_s(self):
        """Test f32.convert_i64_s instruction."""
        wasm = make_conversion_wasm(0xB4, 0x7E, 0x7D)  # i64 -> f32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "sltof" in output

    def test_f64_convert_i32_s(self):
        """Test f64.convert_i32_s instruction."""
        wasm = make_conversion_wasm(0xB7, 0x7F, 0x7C)  # i32 -> f64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "swtof" in output

    def test_f64_convert_i64_s(self):
        """Test f64.convert_i64_s instruction."""
        wasm = make_conversion_wasm(0xB9, 0x7E, 0x7C)  # i64 -> f64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "sltof" in output

    def test_f32_convert_i64_u(self):
        """Test f32.convert_i64_u instruction."""
        wasm = make_conversion_wasm(0xB5, 0x7E, 0x7D)  # i64 -> f32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "ultof" in output

    def test_f64_convert_i32_u(self):
        """Test f64.convert_i32_u instruction."""
        wasm = make_conversion_wasm(0xB8, 0x7F, 0x7C)  # i32 -> f64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "uwtof" in output

    def test_f64_convert_i64_u(self):
        """Test f64.convert_i64_u instruction."""
        wasm = make_conversion_wasm(0xBA, 0x7E, 0x7C)  # i64 -> f64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "ultof" in output


class TestFloatPromoteDemote:
    """Tests for float promotion and demotion."""

    def test_f32_demote_f64(self):
        """Test f32.demote_f64 instruction."""
        wasm = make_conversion_wasm(0xB6, 0x7C, 0x7D)  # f64 -> f32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "truncd" in output

    def test_f64_promote_f32(self):
        """Test f64.promote_f32 instruction."""
        wasm = make_conversion_wasm(0xBB, 0x7D, 0x7C)  # f32 -> f64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "exts" in output


class TestReinterpret:
    """Tests for reinterpret instructions."""

    def test_i32_reinterpret_f32(self):
        """Test i32.reinterpret_f32 instruction."""
        wasm = make_conversion_wasm(0xBC, 0x7D, 0x7F)  # f32 -> i32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cast" in output

    def test_i64_reinterpret_f64(self):
        """Test i64.reinterpret_f64 instruction."""
        wasm = make_conversion_wasm(0xBD, 0x7C, 0x7E)  # f64 -> i64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cast" in output

    def test_f32_reinterpret_i32(self):
        """Test f32.reinterpret_i32 instruction."""
        wasm = make_conversion_wasm(0xBE, 0x7F, 0x7D)  # i32 -> f32
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cast" in output

    def test_f64_reinterpret_i64(self):
        """Test f64.reinterpret_i64 instruction."""
        wasm = make_conversion_wasm(0xBF, 0x7E, 0x7C)  # i64 -> f64
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cast" in output
