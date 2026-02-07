"""Unit tests for numeric instruction compilation."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_i32_binary_wasm(opcode: int) -> bytes:
    """Create WASM for: (i32, i32) -> i32 { a op b }"""
    # Body: 0 locals (1), get 0 (2), get 1 (2), opcode (1), end (1) = 7 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (i32, i32) -> (i32)
        0x01,
        0x07,
        0x01,
        0x60,
        0x02,
        0x7F,
        0x7F,
        0x01,
        0x7F,
        # Function section
        0x03,
        0x02,
        0x01,
        0x00,
        # Code section
        0x0A,
        0x09,
        0x01,
        0x07,
        0x00,
        0x20,
        0x00,  # local.get 0
        0x20,
        0x01,  # local.get 1
        opcode,  # binary operation
        0x0B,  # end
    ])


def make_i32_unary_wasm(opcode: int) -> bytes:
    """Create WASM for: (i32) -> i32 { op a }"""
    # Body: 0 locals (1), get 0 (2), opcode (1), end (1) = 5 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (i32) -> (i32)
        0x01,
        0x06,
        0x01,
        0x60,
        0x01,
        0x7F,
        0x01,
        0x7F,
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
        opcode,  # unary operation
        0x0B,  # end
    ])


def make_i64_binary_wasm(opcode: int) -> bytes:
    """Create WASM for: (i64, i64) -> i64 { a op b }"""
    # Body: 0 locals (1), get 0 (2), get 1 (2), opcode (1), end (1) = 7 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (i64, i64) -> (i64)
        0x01,
        0x07,
        0x01,
        0x60,
        0x02,
        0x7E,
        0x7E,
        0x01,
        0x7E,
        # Function section
        0x03,
        0x02,
        0x01,
        0x00,
        # Code section
        0x0A,
        0x09,
        0x01,
        0x07,
        0x00,
        0x20,
        0x00,  # local.get 0
        0x20,
        0x01,  # local.get 1
        opcode,  # binary operation
        0x0B,  # end
    ])


def make_i64_unary_wasm(opcode: int) -> bytes:
    """Create WASM for: (i64) -> i64 { op a }"""
    # Body: 0 locals (1), get 0 (2), opcode (1), end (1) = 5 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (i64) -> (i64)
        0x01,
        0x06,
        0x01,
        0x60,
        0x01,
        0x7E,
        0x01,
        0x7E,
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
        opcode,  # unary operation
        0x0B,  # end
    ])


def make_i64_cmp_binary_wasm(opcode: int) -> bytes:
    """Create WASM for: (i64, i64) -> i32 { a cmp b }"""
    # Body: 0 locals (1), get 0 (2), get 1 (2), opcode (1), end (1) = 7 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (i64, i64) -> (i32)
        0x01,
        0x07,
        0x01,
        0x60,
        0x02,
        0x7E,
        0x7E,
        0x01,
        0x7F,
        # Function section
        0x03,
        0x02,
        0x01,
        0x00,
        # Code section
        0x0A,
        0x09,
        0x01,
        0x07,
        0x00,
        0x20,
        0x00,  # local.get 0
        0x20,
        0x01,  # local.get 1
        opcode,  # comparison
        0x0B,  # end
    ])


def make_i64_cmp_unary_wasm(opcode: int) -> bytes:
    """Create WASM for: (i64) -> i32 { op a }"""
    # Body: 0 locals (1), get 0 (2), opcode (1), end (1) = 5 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (i64) -> (i32)
        0x01,
        0x06,
        0x01,
        0x60,
        0x01,
        0x7E,
        0x01,
        0x7F,
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
        opcode,  # comparison
        0x0B,  # end
    ])


class TestI32Arithmetic:
    """Tests for i32 arithmetic operations."""

    def test_i32_add(self):
        """Test i32.add instruction."""
        wasm = make_i32_binary_wasm(0x6A)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "add" in output

    def test_i32_sub(self):
        """Test i32.sub instruction."""
        wasm = make_i32_binary_wasm(0x6B)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "sub" in output

    def test_i32_mul(self):
        """Test i32.mul instruction."""
        wasm = make_i32_binary_wasm(0x6C)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "mul" in output

    def test_i32_div_s(self):
        """Test i32.div_s instruction."""
        wasm = make_i32_binary_wasm(0x6D)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "div" in output

    def test_i32_div_u(self):
        """Test i32.div_u instruction."""
        wasm = make_i32_binary_wasm(0x6E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "udiv" in output

    def test_i32_rem_s(self):
        """Test i32.rem_s instruction."""
        wasm = make_i32_binary_wasm(0x6F)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "rem" in output

    def test_i32_rem_u(self):
        """Test i32.rem_u instruction."""
        wasm = make_i32_binary_wasm(0x70)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "urem" in output


class TestI32Bitwise:
    """Tests for i32 bitwise operations."""

    def test_i32_and(self):
        """Test i32.and instruction."""
        wasm = make_i32_binary_wasm(0x71)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "and" in output

    def test_i32_or(self):
        """Test i32.or instruction."""
        wasm = make_i32_binary_wasm(0x72)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert " or " in output

    def test_i32_xor(self):
        """Test i32.xor instruction."""
        wasm = make_i32_binary_wasm(0x73)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "xor" in output

    def test_i32_shl(self):
        """Test i32.shl instruction."""
        wasm = make_i32_binary_wasm(0x74)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "shl" in output

    def test_i32_shr_s(self):
        """Test i32.shr_s instruction."""
        wasm = make_i32_binary_wasm(0x75)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "sar" in output

    def test_i32_shr_u(self):
        """Test i32.shr_u instruction."""
        wasm = make_i32_binary_wasm(0x76)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "shr" in output

    def test_i32_rotl(self):
        """Test i32.rotl instruction."""
        wasm = make_i32_binary_wasm(0x77)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i32_rotl" in output

    def test_i32_rotr(self):
        """Test i32.rotr instruction."""
        wasm = make_i32_binary_wasm(0x78)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i32_rotr" in output


class TestI32Comparisons:
    """Tests for i32 comparison operations."""

    def test_i32_eqz(self):
        """Test i32.eqz instruction."""
        wasm = make_i32_unary_wasm(0x45)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "ceqw" in output

    def test_i32_eq(self):
        """Test i32.eq instruction."""
        wasm = make_i32_binary_wasm(0x46)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "ceqw" in output

    def test_i32_ne(self):
        """Test i32.ne instruction."""
        wasm = make_i32_binary_wasm(0x47)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cnew" in output

    def test_i32_lt_s(self):
        """Test i32.lt_s instruction."""
        wasm = make_i32_binary_wasm(0x48)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "csltw" in output

    def test_i32_lt_u(self):
        """Test i32.lt_u instruction."""
        wasm = make_i32_binary_wasm(0x49)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cultw" in output

    def test_i32_gt_s(self):
        """Test i32.gt_s instruction."""
        wasm = make_i32_binary_wasm(0x4A)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "csgtw" in output

    def test_i32_gt_u(self):
        """Test i32.gt_u instruction."""
        wasm = make_i32_binary_wasm(0x4B)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cugtw" in output

    def test_i32_le_s(self):
        """Test i32.le_s instruction."""
        wasm = make_i32_binary_wasm(0x4C)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cslew" in output

    def test_i32_le_u(self):
        """Test i32.le_u instruction."""
        wasm = make_i32_binary_wasm(0x4D)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "culew" in output

    def test_i32_ge_s(self):
        """Test i32.ge_s instruction."""
        wasm = make_i32_binary_wasm(0x4E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "csgew" in output

    def test_i32_ge_u(self):
        """Test i32.ge_u instruction."""
        wasm = make_i32_binary_wasm(0x4F)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cugew" in output


class TestI32Unary:
    """Tests for i32 unary operations that need runtime."""

    def test_i32_clz(self):
        """Test i32.clz instruction."""
        wasm = make_i32_unary_wasm(0x67)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i32_clz" in output

    def test_i32_ctz(self):
        """Test i32.ctz instruction."""
        wasm = make_i32_unary_wasm(0x68)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i32_ctz" in output

    def test_i32_popcnt(self):
        """Test i32.popcnt instruction."""
        wasm = make_i32_unary_wasm(0x69)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i32_popcnt" in output


class TestI64Operations:
    """Tests for i64 operations."""

    def test_i64_add(self):
        """Test i64.add instruction."""
        wasm = make_i64_binary_wasm(0x7C)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "add" in output

    def test_i64_sub(self):
        """Test i64.sub instruction."""
        wasm = make_i64_binary_wasm(0x7D)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "sub" in output

    def test_i64_mul(self):
        """Test i64.mul instruction."""
        wasm = make_i64_binary_wasm(0x7E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "mul" in output

    def test_i64_eqz(self):
        """Test i64.eqz instruction."""
        wasm = make_i64_cmp_unary_wasm(0x50)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "ceql" in output

    def test_i64_eq(self):
        """Test i64.eq instruction."""
        wasm = make_i64_cmp_binary_wasm(0x51)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "ceql" in output

    def test_i64_ne(self):
        """Test i64.ne instruction."""
        wasm = make_i64_cmp_binary_wasm(0x52)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "cnel" in output


class TestI64Unary:
    """Tests for i64 unary operations that need runtime."""

    def test_i64_clz(self):
        """Test i64.clz instruction."""
        wasm = make_i64_unary_wasm(0x79)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i64_clz" in output

    def test_i64_ctz(self):
        """Test i64.ctz instruction."""
        wasm = make_i64_unary_wasm(0x7A)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i64_ctz" in output

    def test_i64_popcnt(self):
        """Test i64.popcnt instruction."""
        wasm = make_i64_unary_wasm(0x7B)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i64_popcnt" in output

    def test_i64_rotl(self):
        """Test i64.rotl instruction."""
        wasm = make_i64_binary_wasm(0x89)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i64_rotl" in output

    def test_i64_rotr(self):
        """Test i64.rotr instruction."""
        wasm = make_i64_binary_wasm(0x8A)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i64_rotr" in output


class TestConstants:
    """Tests for constant instructions."""

    def test_i32_const(self):
        """Test i32.const instruction."""
        # Body: 0 locals (1), const 42 (2), end (1) = 4 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> (i32)
            0x01,
            0x05,
            0x01,
            0x60,
            0x00,
            0x01,
            0x7F,
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x06,
            0x01,
            0x04,
            0x00,
            0x41,
            0x2A,  # i32.const 42
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "42" in output
        assert "copy" in output

    def test_i64_const(self):
        """Test i64.const instruction."""
        # Body: 0 locals (1), const 100 (3 bytes in signed LEB128), end (1) = 5 bytes
        # 100 in signed LEB128 = 0xE4, 0x00 (need 2 bytes because bit 6 must be 0 for positive)
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> (i64)
            0x01,
            0x05,
            0x01,
            0x60,
            0x00,
            0x01,
            0x7E,
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
            0x42,
            0xE4,
            0x00,  # i64.const 100 (signed LEB128: 0xE4=100+128, 0x00 terminates)
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "100" in output

    def test_i32_const_negative(self):
        """Test i32.const with negative value."""
        # Body: 0 locals (1), const -1 (2 bytes), end (1) = 4 bytes
        # Section: num_funcs (1) + body_size (1) + body (4) = 6 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> (i32)
            0x01,
            0x05,
            0x01,
            0x60,
            0x00,
            0x01,
            0x7F,
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x06,
            0x01,
            0x04,
            0x00,
            0x41,
            0x7F,  # i32.const -1 (0x7F in signed LEB128)
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "-1" in output
