"""Unit tests for br_table instruction compilation."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_br_table_3_targets_wasm() -> bytes:
    """Create WASM with br_table with 3 branch targets.

    (i32) -> (i32): returns different values based on input
    """
    # Type section: (i32) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x7F, 0x01, 0x7F])

    # Function section: 1 function, type 0
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x06]) + b"select" + bytes([0x00, 0x00])

    # Code: block with br_table having 3 targets (0, 1, 2) + default
    # Similar structure to the simple case but with one more branch
    func_body = bytes([
        0x00,  # 0 locals
        0x02,
        0x7F,  # block result i32
        0x02,
        0x40,  # block
        0x02,
        0x40,  # block
        0x02,
        0x40,  # block
        0x20,
        0x00,  # local.get 0
        # br_table: 3 targets [0, 1, 2] + default 3
        0x0E,
        0x03,
        0x00,
        0x01,
        0x02,
        0x03,
        0x0B,  # end (innermost)
        0x41,
        0x01,  # i32.const 1
        0x0C,
        0x02,  # br 2
        0x0B,  # end
        0x41,
        0x02,  # i32.const 2
        0x0C,
        0x01,  # br 1
        0x0B,  # end
        0x41,
        0x03,  # i32.const 3
        0x0C,
        0x00,  # br 0
        0x0B,  # end (outer)
        0x41,
        0x00,  # i32.const 0 (default)
        0x0B,  # end function
    ])

    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([
        0x00,
        0x61,
        0x73,
        0x6D,
        0x01,
        0x00,
        0x00,
        0x00,
    ])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_simple_br_table_wasm() -> bytes:
    """Create simpler WASM with br_table for basic testing.

    (i32) -> (i32): uses br_table with 2 targets + default
    Returns 1 if param==0, 2 if param==1, 0 otherwise
    """
    # Type section: (i32) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x7F, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"test" + bytes([0x00, 0x00])

    # Simpler function: just br_table to return a constant
    # block (result i32)
    #   block
    #     block
    #       local.get 0
    #       br_table 0 1 2
    #     end (inner: idx=0) -> return 1
    #     i32.const 1
    #     br 1
    #   end (middle: idx=1) -> return 2
    #   i32.const 2
    #   br 0
    # end (outer: default) -> return 0
    # i32.const 0
    func_body = bytes([
        0x00,  # 0 locals
        0x02,
        0x7F,  # block result i32
        0x02,
        0x40,  # block
        0x02,
        0x40,  # block
        0x20,
        0x00,  # local.get 0
        0x0E,
        0x02,
        0x00,
        0x01,
        0x02,  # br_table 2 targets: 0, 1, default 2
        0x0B,  # end
        0x41,
        0x01,  # i32.const 1
        0x0C,
        0x01,  # br 1
        0x0B,  # end
        0x41,
        0x02,  # i32.const 2
        0x0C,
        0x00,  # br 0
        0x0B,  # end
        0x41,
        0x00,  # i32.const 0 (default)
        0x0B,  # end function
    ])

    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([
        0x00,
        0x61,
        0x73,
        0x6D,
        0x01,
        0x00,
        0x00,
        0x00,
    ])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestBrTable:
    """Tests for br_table instruction compilation."""

    def test_br_table_compiles(self):
        """Test that br_table instruction compiles."""
        wasm = make_simple_br_table_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have multiple comparison blocks
        assert "ceqw" in output  # comparison for each case
        # Should have multiple jumps
        assert "jnz" in output or "jmp" in output

    def test_br_table_generates_comparisons(self):
        """Test that br_table generates comparison for each case."""
        wasm = make_simple_br_table_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # br_table with 2 targets should generate at least 2 comparisons
        assert output.count("ceqw") >= 2

    def test_br_table_with_more_targets(self):
        """Test br_table with more branch targets."""
        wasm = make_br_table_3_targets_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # br_table with 3 targets should generate at least 3 comparisons
        assert output.count("ceqw") >= 3
