"""Unit tests for memory instruction compilation."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_load_wasm(load_opcode: int, value_type: int = 0x7F) -> bytes:
    """Create WASM for a function that loads from memory.

    (i32) -> value_type { load(addr) }
    """
    # Body: 0 locals (1), get 0 (2), load (3 - opcode + align + offset), end (1) = 7 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (i32) -> (value_type)
        0x01,
        0x06,
        0x01,
        0x60,
        0x01,
        0x7F,
        0x01,
        value_type,
        # Memory section: 1 page min, no max
        0x05,
        0x03,
        0x01,
        0x00,
        0x01,
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
        load_opcode,
        0x02,
        0x00,  # align=2, offset=0
        0x0B,  # end
    ])


def make_store_wasm(store_opcode: int, value_type: int = 0x7F) -> bytes:
    """Create WASM for a function that stores to memory.

    (i32, value_type) -> () { store(addr, value) }
    """
    # Body: 0 locals (1), get 0 (2), get 1 (2), store (3), end (1) = 9 bytes
    return bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
        # Type section: (i32, value_type) -> ()
        0x01,
        0x06,
        0x01,
        0x60,
        0x02,
        0x7F,
        value_type,
        0x00,
        # Memory section: 1 page min, no max
        0x05,
        0x03,
        0x01,
        0x00,
        0x01,
        # Function section
        0x03,
        0x02,
        0x01,
        0x00,
        # Code section
        0x0A,
        0x0B,
        0x01,
        0x09,
        0x00,
        0x20,
        0x00,  # local.get 0 (address)
        0x20,
        0x01,  # local.get 1 (value)
        store_opcode,
        0x02,
        0x00,  # align=2, offset=0
        0x0B,  # end
    ])


class TestI32Load:
    """Tests for i32 load instructions."""

    def test_i32_load(self):
        """Test i32.load instruction."""
        wasm = make_load_wasm(0x28)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loadw" in output
        assert "__wasm_memory" in output

    def test_i32_load8_s(self):
        """Test i32.load8_s instruction."""
        wasm = make_load_wasm(0x2C)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loadsb" in output

    def test_i32_load8_u(self):
        """Test i32.load8_u instruction."""
        wasm = make_load_wasm(0x2D)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loadub" in output

    def test_i32_load16_s(self):
        """Test i32.load16_s instruction."""
        wasm = make_load_wasm(0x2E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loadsh" in output

    def test_i32_load16_u(self):
        """Test i32.load16_u instruction."""
        wasm = make_load_wasm(0x2F)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loaduh" in output


class TestI64Load:
    """Tests for i64 load instructions."""

    def test_i64_load(self):
        """Test i64.load instruction."""
        wasm = make_load_wasm(0x29, value_type=0x7E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loadl" in output

    def test_i64_load32_s(self):
        """Test i64.load32_s instruction."""
        wasm = make_load_wasm(0x34, value_type=0x7E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loadsw" in output

    def test_i64_load32_u(self):
        """Test i64.load32_u instruction."""
        wasm = make_load_wasm(0x35, value_type=0x7E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loaduw" in output


class TestFloatLoad:
    """Tests for float load instructions."""

    def test_f32_load(self):
        """Test f32.load instruction."""
        wasm = make_load_wasm(0x2A, value_type=0x7D)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loads" in output

    def test_f64_load(self):
        """Test f64.load instruction."""
        wasm = make_load_wasm(0x2B, value_type=0x7C)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loadd" in output


class TestI32Store:
    """Tests for i32 store instructions."""

    def test_i32_store(self):
        """Test i32.store instruction."""
        wasm = make_store_wasm(0x36)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "storew" in output
        assert "__wasm_memory" in output

    def test_i32_store8(self):
        """Test i32.store8 instruction."""
        wasm = make_store_wasm(0x3A)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "storeb" in output

    def test_i32_store16(self):
        """Test i32.store16 instruction."""
        wasm = make_store_wasm(0x3B)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "storeh" in output


class TestI64Store:
    """Tests for i64 store instructions."""

    def test_i64_store(self):
        """Test i64.store instruction."""
        wasm = make_store_wasm(0x37, value_type=0x7E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "storel" in output

    def test_i64_store32(self):
        """Test i64.store32 instruction."""
        wasm = make_store_wasm(0x3E, value_type=0x7E)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "storew" in output


class TestFloatStore:
    """Tests for float store instructions."""

    def test_f32_store(self):
        """Test f32.store instruction."""
        wasm = make_store_wasm(0x38, value_type=0x7D)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "stores" in output

    def test_f64_store(self):
        """Test f64.store instruction."""
        wasm = make_store_wasm(0x39, value_type=0x7C)
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "stored" in output


class TestMemorySizeGrow:
    """Tests for memory.size and memory.grow instructions."""

    def test_memory_size(self):
        """Test memory.size instruction."""
        # () -> i32 { memory.size }
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
            # Memory section: 1 page min
            0x05,
            0x03,
            0x01,
            0x00,
            0x01,
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
            0x3F,
            0x00,  # memory.size 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_memory_size_pages" in output

    def test_memory_grow(self):
        """Test memory.grow instruction."""
        # (i32) -> i32 { memory.grow(pages) }
        wasm = bytes([
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
            # Memory section: 1 page min
            0x05,
            0x03,
            0x01,
            0x00,
            0x01,
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x08,
            0x01,
            0x06,
            0x00,
            0x20,
            0x00,  # local.get 0
            0x40,
            0x00,  # memory.grow 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_memory_grow" in output
