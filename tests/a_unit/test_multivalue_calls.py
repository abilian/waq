"""Tests for multi-value function calls and returns."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_call_multivalue_wasm() -> bytes:
    """Create WASM with call returning multiple values."""
    # fmt: off
    # Type section: two types
    type_section = bytes([
        0x02,
        # Type 0: () -> (i32, i32) - returns two values
        0x60, 0x00, 0x02, 0x7F, 0x7F,
        # Type 1: () -> (i32) - caller returns single value
        0x60, 0x00, 0x01, 0x7F,
    ])

    # Function section: 2 functions
    func_section = bytes([0x02, 0x00, 0x01])

    # Export section
    export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

    # Code section
    # Function 0: returns (10, 20)
    func0_body = bytes([
        0x00,
        0x41, 0x0A,  # i32.const 10
        0x41, 0x14,  # i32.const 20
        0x0B,
    ])

    # Function 1: calls func0 and adds results
    func1_body = bytes([
        0x00,
        0x10, 0x00,  # call func 0
        0x6A,        # i32.add (10 + 20 = 30)
        0x0B,
    ])

    code_section = bytes([
        0x02,  # 2 functions
        len(func0_body),
    ]) + func0_body + bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_call_indirect_multivalue_wasm() -> bytes:
    """Create WASM with call_indirect returning multiple values."""
    # fmt: off
    type_section = bytes([
        0x02,
        # Type 0: () -> (i32, i32)
        0x60, 0x00, 0x02, 0x7F, 0x7F,
        # Type 1: (i32) -> (i32)
        0x60, 0x01, 0x7F, 0x01, 0x7F,
    ])

    func_section = bytes([0x02, 0x00, 0x01])

    # Table section: 1 funcref table
    table_section = bytes([0x01, 0x70, 0x00, 0x01])

    # Element section: init table[0] = func 0
    elem_section = bytes([
        0x01,  # 1 element
        0x00,  # flags
        0x41, 0x00, 0x0B,  # offset: i32.const 0
        0x01, 0x00,  # 1 func index: func 0
    ])

    export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

    # Function 0: returns (10, 20)
    func0_body = bytes([
        0x00,
        0x41, 0x0A,  # i32.const 10
        0x41, 0x14,  # i32.const 20
        0x0B,
    ])

    # Function 1: call_indirect type 0, add results
    func1_body = bytes([
        0x00,
        0x20, 0x00,  # local.get 0 (table index)
        0x11, 0x00, 0x00,  # call_indirect type 0, table 0
        0x6A,        # i32.add
        0x0B,
    ])

    code_section = bytes([
        0x02,
        len(func0_body),
    ]) + func0_body + bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x09, len(elem_section)]) + elem_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_return_call_multivalue_wasm() -> bytes:
    """Create WASM with return_call to multi-value function."""
    # fmt: off
    type_section = bytes([
        0x02,
        # Type 0: (i32) -> (i32, i32)
        0x60, 0x01, 0x7F, 0x02, 0x7F, 0x7F,
        # Type 1: (i32) -> (i32, i32) - same as type 0
        0x60, 0x01, 0x7F, 0x02, 0x7F, 0x7F,
    ])

    func_section = bytes([0x02, 0x00, 0x01])

    export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

    # Function 0: returns (x, x+1)
    func0_body = bytes([
        0x00,
        0x20, 0x00,  # local.get 0
        0x20, 0x00,  # local.get 0
        0x41, 0x01,  # i32.const 1
        0x6A,        # i32.add
        0x0B,
    ])

    # Function 1: return_call func 0
    func1_body = bytes([
        0x00,
        0x20, 0x00,  # local.get 0
        0x12, 0x00,  # return_call func 0
        0x0B,
    ])

    code_section = bytes([
        0x02,
        len(func0_body),
    ]) + func0_body + bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_return_call_indirect_multivalue_wasm() -> bytes:
    """Create WASM with return_call_indirect to multi-value function."""
    # fmt: off
    type_section = bytes([
        0x02,
        # Type 0: () -> (i32, i32)
        0x60, 0x00, 0x02, 0x7F, 0x7F,
        # Type 1: (i32) -> (i32, i32)
        0x60, 0x01, 0x7F, 0x02, 0x7F, 0x7F,
    ])

    func_section = bytes([0x02, 0x00, 0x01])

    table_section = bytes([0x01, 0x70, 0x00, 0x01])

    elem_section = bytes([
        0x01, 0x00,
        0x41, 0x00, 0x0B,
        0x01, 0x00,
    ])

    export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

    # Function 0: returns (10, 20)
    func0_body = bytes([
        0x00,
        0x41, 0x0A,
        0x41, 0x14,
        0x0B,
    ])

    # Function 1: return_call_indirect type 0
    func1_body = bytes([
        0x00,
        0x20, 0x00,  # local.get 0 (table index)
        0x13, 0x00, 0x00,  # return_call_indirect type 0, table 0
        0x0B,
    ])

    code_section = bytes([
        0x02,
        len(func0_body),
    ]) + func0_body + bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x09, len(elem_section)]) + elem_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_br_table_wasm() -> bytes:
    """Create WASM with br_table instruction."""
    # fmt: off
    type_section = bytes([
        0x01,
        # Type 0: (i32) -> (i32)
        0x60, 0x01, 0x7F, 0x01, 0x7F,
    ])

    func_section = bytes([0x01, 0x00])

    export_section = bytes([0x01, 0x08]) + b"br_table" + bytes([0x00, 0x00])

    # Simple br_table: jump based on index
    # (block (result i32)
    #   (block
    #     (block
    #       (br_table 0 1 2 (local.get 0)))  ; 0->exit inner, 1->exit middle, 2->exit outer
    #     (return (i32.const 10)))            ; case 0
    #   (return (i32.const 20)))              ; case 1
    #   (i32.const 30))                       ; default (case 2)
    func_body = bytes([
        0x00,
        0x02, 0x7F,  # block (result i32) - outer (depth 0 from inner)
        0x02, 0x40,  # block (void) - middle (depth 1 from inner)
        0x02, 0x40,  # block (void) - inner (depth 2 from inner)
        0x20, 0x00,  # local.get 0
        0x0E, 0x02, 0x00, 0x01, 0x02,  # br_table [0, 1] default=2
        0x0B,  # end inner
        0x41, 0x0A,  # i32.const 10
        0x0F,        # return
        0x0B,  # end middle
        0x41, 0x14,  # i32.const 20
        0x0F,        # return
        0x0B,  # end outer
        0x41, 0x1E,  # i32.const 30 (default)
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_return_void_wasm() -> bytes:
    """Create WASM with return from void function."""
    # fmt: off
    type_section = bytes([
        0x01,
        # Type 0: () -> ()
        0x60, 0x00, 0x00,
    ])

    func_section = bytes([0x01, 0x00])

    export_section = bytes([0x01, 0x04]) + b"noop" + bytes([0x00, 0x00])

    func_body = bytes([
        0x00,
        0x0F,  # return
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_return_multivalue_wasm() -> bytes:
    """Create WASM with return of multiple values."""
    # fmt: off
    type_section = bytes([
        0x01,
        # Type 0: (i32) -> (i32, i32)
        0x60, 0x01, 0x7F, 0x02, 0x7F, 0x7F,
    ])

    func_section = bytes([0x01, 0x00])

    export_section = bytes([0x01, 0x09]) + b"multi_ret" + bytes([0x00, 0x00])

    # Return (x, x*2) using explicit return
    func_body = bytes([
        0x00,
        0x20, 0x00,  # local.get 0
        0x20, 0x00,  # local.get 0
        0x41, 0x02,  # i32.const 2
        0x6C,        # i32.mul
        0x0F,        # return
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_call_void_wasm() -> bytes:
    """Create WASM calling a void function."""
    # fmt: off
    type_section = bytes([
        0x02,
        # Type 0: () -> ()
        0x60, 0x00, 0x00,
        # Type 1: () -> (i32)
        0x60, 0x00, 0x01, 0x7F,
    ])

    func_section = bytes([0x02, 0x00, 0x01])

    export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

    # Function 0: void function
    func0_body = bytes([
        0x00,
        0x0B,
    ])

    # Function 1: calls void function, returns 42
    func1_body = bytes([
        0x00,
        0x10, 0x00,  # call func 0
        0x41, 0x2A,  # i32.const 42
        0x0B,
    ])

    code_section = bytes([
        0x02,
        len(func0_body),
    ]) + func0_body + bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_call_ref_multivalue_wasm() -> bytes:
    """Create WASM with call_ref returning multiple values."""
    # fmt: off
    type_section = bytes([
        0x02,
        # Type 0: () -> (i32, i32) - returns two values
        0x60, 0x00, 0x02, 0x7F, 0x7F,
        # Type 1: () -> (i32) - caller
        0x60, 0x00, 0x01, 0x7F,
    ])

    func_section = bytes([0x02, 0x00, 0x01])

    export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

    # Function 0: returns (10, 20)
    func0_body = bytes([
        0x00,
        0x41, 0x0A,
        0x41, 0x14,
        0x0B,
    ])

    # Function 1: ref.func 0, then call_ref type 0, add results
    func1_body = bytes([
        0x00,
        0xD2, 0x00,  # ref.func 0
        0x14, 0x00,  # call_ref type 0
        0x6A,        # i32.add
        0x0B,
    ])

    code_section = bytes([
        0x02,
        len(func0_body),
    ]) + func0_body + bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


def make_return_call_ref_multivalue_wasm() -> bytes:
    """Create WASM with return_call_ref to multi-value function."""
    # fmt: off
    type_section = bytes([
        0x01,
        # Type 0: () -> (i32, i32)
        0x60, 0x00, 0x02, 0x7F, 0x7F,
    ])

    func_section = bytes([0x02, 0x00, 0x00])

    export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

    # Function 0: returns (10, 20)
    func0_body = bytes([
        0x00,
        0x41, 0x0A,
        0x41, 0x14,
        0x0B,
    ])

    # Function 1: ref.func 0, then return_call_ref type 0
    func1_body = bytes([
        0x00,
        0xD2, 0x00,  # ref.func 0
        0x15, 0x00,  # return_call_ref type 0
        0x0B,
    ])

    code_section = bytes([
        0x02,
        len(func0_body),
    ]) + func0_body + bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on
    return wasm


class TestMultiValueCalls:
    """Tests for multi-value function calls."""

    def test_call_multivalue_compiles(self):
        """Test that call returning multiple values compiles."""
        wasm = make_call_multivalue_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have alloc for out-param
        assert "alloc" in output.lower() or "call" in output

    def test_call_indirect_multivalue_compiles(self):
        """Test that call_indirect with multi-value compiles."""
        wasm = make_call_indirect_multivalue_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_table" in output

    def test_call_void_compiles(self):
        """Test that calling void function compiles."""
        wasm = make_call_void_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "call" in output

    def test_call_ref_multivalue_compiles(self):
        """Test that call_ref with multi-value compiles."""
        wasm = make_call_ref_multivalue_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "call" in output


class TestMultiValueReturnCalls:
    """Tests for multi-value tail calls."""

    def test_return_call_multivalue_compiles(self):
        """Test that return_call to multi-value function compiles."""
        wasm = make_return_call_multivalue_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "call" in output or "ret" in output

    def test_return_call_indirect_multivalue_compiles(self):
        """Test that return_call_indirect with multi-value compiles."""
        wasm = make_return_call_indirect_multivalue_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_table" in output

    def test_return_call_ref_multivalue_compiles(self):
        """Test that return_call_ref with multi-value compiles."""
        wasm = make_return_call_ref_multivalue_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "call" in output or "ret" in output


class TestBrTable:
    """Tests for br_table instruction."""

    def test_br_table_compiles(self):
        """Test that br_table compiles."""
        wasm = make_br_table_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have multiple conditional jumps
        assert "jnz" in output or "jmp" in output


class TestReturns:
    """Tests for return instruction variants."""

    def test_return_void_compiles(self):
        """Test that return from void function compiles."""
        wasm = make_return_void_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "ret" in output

    def test_return_multivalue_compiles(self):
        """Test that multi-value return compiles."""
        wasm = make_return_multivalue_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have store for out-param
        assert "store" in output.lower() or "ret" in output
