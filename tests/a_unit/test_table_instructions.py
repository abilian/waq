"""Unit tests for table and call_indirect instruction compilation."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_simple_call_indirect_wasm() -> bytes:
    """Create simpler WASM for call_indirect test.

    Module with:
    - type 0: (i32) -> i32
    - func 0: identity function
    - func 1: calls func 0 indirectly via table
    - table with func 0 at index 0
    """
    # Build sections with correct sizes
    # Type section content: 1 type, functype (0x60), 1 param (i32), 1 result (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x7F, 0x01, 0x7F])

    # Function section content: 2 functions, both type 0
    func_section = bytes([0x02, 0x00, 0x00])

    # Table section content: 1 table, funcref (0x70), limits (min=1, no max)
    table_section = bytes([0x01, 0x70, 0x00, 0x01])

    # Export section content: 1 export, name "test", func, index 1
    export_section = bytes([0x01, 0x04]) + b"test" + bytes([0x00, 0x01])

    # Element section content: 1 segment, flags=0, offset i32.const 0, 1 func idx
    element_section = bytes([
        0x01,  # 1 segment
        0x00,  # flags=0 (active, table 0)
        0x41,
        0x00,
        0x0B,  # offset: i32.const 0, end
        0x01,
        0x00,  # 1 element: func 0
    ])

    # Code section content: 2 functions
    # func 0: identity - 3 bytes body: local.get 0, end
    func0_body = bytes([0x00, 0x20, 0x00, 0x0B])  # 0 locals, local.get 0, end
    func0 = bytes([len(func0_body)]) + func0_body

    # func 1: call_indirect - local.get 0, i32.const 0, call_indirect 0 0, end
    func1_body = bytes([0x00, 0x20, 0x00, 0x41, 0x00, 0x11, 0x00, 0x00, 0x0B])
    func1 = bytes([len(func1_body)]) + func1_body

    code_section = bytes([0x02]) + func0 + func1

    # Combine all sections
    wasm = bytes([
        0x00,
        0x61,
        0x73,
        0x6D,  # magic
        0x01,
        0x00,
        0x00,
        0x00,  # version
    ])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x09, len(element_section)]) + element_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestCallIndirect:
    """Tests for call_indirect instruction."""

    def test_call_indirect_compiles(self):
        """Test that call_indirect instruction compiles."""
        wasm = make_simple_call_indirect_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have table access
        assert "__wasm_table" in output
        # Should have an indirect call (loading function pointer)
        assert "call" in output.lower()

    def test_call_indirect_loads_from_table(self):
        """Test that call_indirect generates table load."""
        wasm = make_simple_call_indirect_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should multiply index by 8 (pointer size)
        assert "mul" in output.lower() or "8" in output


class TestElementSection:
    """Tests for element section parsing."""

    def test_element_section_parsed(self):
        """Test that element section is parsed correctly."""
        wasm = make_simple_call_indirect_wasm()
        module = parse_module(wasm)
        # Should have 1 element segment
        assert len(module.elements) == 1
        elem = module.elements[0]
        assert elem.table_idx == 0
        assert elem.func_indices == [0]

    def test_table_section_parsed(self):
        """Test that table section is parsed correctly."""
        wasm = make_simple_call_indirect_wasm()
        module = parse_module(wasm)
        # Should have 1 table
        assert len(module.tables) == 1
        table = module.tables[0]
        assert table.limits.min == 1
