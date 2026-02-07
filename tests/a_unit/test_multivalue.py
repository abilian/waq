"""Unit tests for multi-value support (WASM 2.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_block_multivalue_wasm() -> bytes:
    """Create WASM with a block that returns two values.

    () -> (i32, i32)
    Block type uses type index 0 which is () -> (i32, i32)
    """
    # Type section: two types
    # Type 0: () -> (i32, i32) - for the block
    # Type 1: () -> (i64) - for the function (returns both values as i64 pair)
    type_section = bytes([
        0x02,  # 2 types
        0x60,
        0x00,
        0x02,
        0x7F,
        0x7F,  # () -> (i32, i32)
        0x60,
        0x00,
        0x01,
        0x7E,  # () -> (i64) - function type
    ])

    # Function section: one function using type 1
    func_section = bytes([0x01, 0x01])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"test" + bytes([0x00, 0x00])

    # Code section: block with type index, return values packed
    func_body = bytes([
        0x00,  # 0 locals
        # block (type 0) - returns two i32
        0x02,
        0x00,  # block type_idx=0
        0x41,
        0x01,  # i32.const 1
        0x41,
        0x02,  # i32.const 2
        0x0B,  # end block
        # Now we have two i32 on stack, need to pack into i64
        # For now, just drop one and extend the other
        0x1A,  # drop
        0xAD,  # i64.extend_i32_u
        0x0B,  # end function
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_simple_multivalue_return_wasm() -> bytes:
    """Create WASM with a function that returns two values.

    () -> (i32, i32)
    """
    # Type section: () -> (i32, i32)
    type_section = bytes([0x01, 0x60, 0x00, 0x02, 0x7F, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"pair" + bytes([0x00, 0x00])

    # Code section: return two constants
    func_body = bytes([
        0x00,  # 0 locals
        0x41,
        0x01,  # i32.const 1
        0x41,
        0x02,  # i32.const 2
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestMultiValueBlocks:
    """Tests for multi-value block types."""

    def test_block_with_type_index_parses(self):
        """Test that a block with type index parses correctly."""
        wasm = make_block_multivalue_wasm()
        module = parse_module(wasm)
        # Check that we have 2 types
        assert len(module.types) == 2
        # Check type 0 has 2 results
        assert len(module.types[0].results) == 2

    def test_block_with_type_index_compiles(self):
        """Test that a block with type index compiles."""
        wasm = make_block_multivalue_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have a function definition (export and function are on separate lines)
        assert "export" in output
        assert "function" in output
        assert "test" in output


class TestMultiValueReturn:
    """Tests for multi-value function returns."""

    def test_multivalue_function_parses(self):
        """Test that multi-value function parses correctly."""
        wasm = make_simple_multivalue_return_wasm()
        module = parse_module(wasm)
        # Check that function type has 2 results
        func_type = module.types[0]
        assert len(func_type.results) == 2
