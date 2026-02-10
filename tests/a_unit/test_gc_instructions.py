"""Unit tests for GC instructions (WASM GC proposal)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_struct_new_wasm() -> bytes:
    """Create WASM with struct.new instruction.

    Defines a struct type and creates an instance.
    """
    # Type section: struct type with one i32 field
    # 0x5F = struct, 0x01 = 1 field, 0x7F = i32, 0x01 = mutable
    type_section = bytes([
        0x02,  # 2 types
        # Type 0: struct with one i32 field
        0x5F,  # struct
        0x01,  # 1 field
        0x7F,  # i32
        0x01,  # mutable
        # Type 1: () -> (structref)
        0x60,
        0x00,
        0x01,
        0x6B,  # func () -> (structref)
    ])

    # Function section
    func_section = bytes([0x01, 0x01])  # 1 function using type 1

    # Export section
    export_section = bytes([0x01, 0x0A]) + b"struct_new" + bytes([0x00, 0x00])

    # Code section: struct.new
    func_body = bytes([
        0x00,  # 0 locals
        0x41,
        0x2A,  # i32.const 42
        0xFB,
        0x00,
        0x00,  # struct.new 0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_struct_get_set_wasm() -> bytes:
    """Create WASM with struct.get and struct.set instructions."""
    # Type section: struct type with one i32 field + function type
    type_section = bytes([
        0x02,
        # Type 0: struct with one i32 field
        0x5F,
        0x01,
        0x7F,
        0x01,
        # Type 1: (structref) -> (i32)
        0x60,
        0x01,
        0x6B,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x0A]) + b"struct_get" + bytes([0x00, 0x00])

    # Code: get field 0 from struct
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0xFB,
        0x02,
        0x00,
        0x00,  # struct.get 0 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_array_new_wasm() -> bytes:
    """Create WASM with array.new instruction."""
    # Type section: array type with i32 elements
    type_section = bytes([
        0x02,
        # Type 0: array of i32
        0x5E,
        0x7F,
        0x01,  # array, i32, mutable
        # Type 1: (i32, i32) -> (arrayref)
        0x60,
        0x02,
        0x7F,
        0x7F,
        0x01,
        0x6A,  # func (i32, i32) -> (arrayref)
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x09]) + b"array_new" + bytes([0x00, 0x00])

    # Code: array.new(init_value, length)
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0 (init value)
        0x20,
        0x01,  # local.get 1 (length)
        0xFB,
        0x06,
        0x00,  # array.new 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_array_len_wasm() -> bytes:
    """Create WASM with array.len instruction."""
    type_section = bytes([
        0x02,
        # Type 0: array of i32
        0x5E,
        0x7F,
        0x01,
        # Type 1: (arrayref) -> (i32)
        0x60,
        0x01,
        0x6A,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x09]) + b"array_len" + bytes([0x00, 0x00])

    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0xFB,
        0x0F,  # array.len
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_i31_wasm() -> bytes:
    """Create WASM with i31ref instructions."""
    type_section = bytes([
        0x01,
        # Type 0: (i32) -> (i32)
        0x60,
        0x01,
        0x7F,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x00])

    export_section = bytes([0x01, 0x09]) + b"i31_round" + bytes([0x00, 0x00])

    # Code: ref.i31 then i31.get_s
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0xFB,
        0x1C,  # ref.i31
        0xFB,
        0x1D,  # i31.get_s
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestStructInstructions:
    """Tests for struct instructions."""

    def test_struct_new_compiles(self):
        """Test that struct.new compiles."""
        wasm = make_struct_new_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_struct_new" in output

    def test_struct_get_compiles(self):
        """Test that struct.get compiles."""
        wasm = make_struct_get_set_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have load instruction for field access
        assert "loadl" in output or "load" in output.lower()


class TestArrayInstructions:
    """Tests for array instructions."""

    def test_array_new_compiles(self):
        """Test that array.new compiles."""
        wasm = make_array_new_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_array_new" in output

    def test_array_len_compiles(self):
        """Test that array.len compiles."""
        wasm = make_array_len_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # array.len loads from array header
        assert "loadw" in output or "load" in output.lower()


class TestI31Instructions:
    """Tests for i31ref instructions."""

    def test_i31_roundtrip_compiles(self):
        """Test that ref.i31 and i31.get_s compile."""
        wasm = make_i31_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_ref_i31" in output
        assert "__wasm_i31_get_s" in output


def make_i31_get_u_wasm() -> bytes:
    """Create WASM with i31.get_u instruction."""
    type_section = bytes([
        0x01,
        # Type 0: (i32) -> (i32)
        0x60,
        0x01,
        0x7F,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x00])

    export_section = bytes([0x01, 0x09]) + b"i31_get_u" + bytes([0x00, 0x00])

    # Code: ref.i31 then i31.get_u
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0xFB,
        0x1C,  # ref.i31
        0xFB,
        0x1E,  # i31.get_u
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_struct_new_default_wasm() -> bytes:
    """Create WASM with struct.new_default instruction."""
    type_section = bytes([
        0x02,
        # Type 0: struct with one i32 field
        0x5F,
        0x01,
        0x7F,
        0x01,
        # Type 1: () -> (structref)
        0x60,
        0x00,
        0x01,
        0x6B,
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x12]) + b"struct_new_default" + bytes([0x00, 0x00])

    # Code: struct.new_default 0
    func_body = bytes([
        0x00,
        0xFB,
        0x01,
        0x00,  # struct.new_default 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_struct_set_wasm() -> bytes:
    """Create WASM with struct.set instruction."""
    type_section = bytes([
        0x02,
        # Type 0: struct with one i32 field
        0x5F,
        0x01,
        0x7F,
        0x01,
        # Type 1: (structref, i32) -> ()
        0x60,
        0x02,
        0x6B,
        0x7F,
        0x00,
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x0A]) + b"struct_set" + bytes([0x00, 0x00])

    # Code: struct.set 0 0
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0 (structref)
        0x20,
        0x01,  # local.get 1 (value)
        0xFB,
        0x05,
        0x00,
        0x00,  # struct.set 0 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_array_new_default_wasm() -> bytes:
    """Create WASM with array.new_default instruction."""
    type_section = bytes([
        0x02,
        # Type 0: array of i32
        0x5E,
        0x7F,
        0x01,
        # Type 1: (i32) -> (arrayref)
        0x60,
        0x01,
        0x7F,
        0x01,
        0x6A,
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x11]) + b"array_new_default" + bytes([0x00, 0x00])

    # Code: array.new_default(length)
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0 (length)
        0xFB,
        0x07,
        0x00,  # array.new_default 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_array_get_set_wasm() -> bytes:
    """Create WASM with array.get and array.set instructions."""
    type_section = bytes([
        0x02,
        # Type 0: array of i32
        0x5E,
        0x7F,
        0x01,
        # Type 1: (arrayref, i32, i32) -> (i32)
        0x60,
        0x03,
        0x6A,
        0x7F,
        0x7F,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x0D]) + b"array_get_set" + bytes([0x00, 0x00])

    # Code: set element, then get it
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0 (arrayref)
        0x20,
        0x01,  # local.get 1 (index)
        0x20,
        0x02,  # local.get 2 (value)
        0xFB,
        0x0E,
        0x00,  # array.set 0
        0x20,
        0x00,  # local.get 0 (arrayref)
        0x20,
        0x01,  # local.get 1 (index)
        0xFB,
        0x0B,
        0x00,  # array.get 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_ref_test_wasm() -> bytes:
    """Create WASM with ref.test instruction."""
    type_section = bytes([
        0x02,
        # Type 0: struct
        0x5F,
        0x01,
        0x7F,
        0x01,
        # Type 1: (structref) -> (i32)
        0x60,
        0x01,
        0x6B,
        0x01,
        0x7F,
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x08]) + b"ref_test" + bytes([0x00, 0x00])

    # Code: ref.test type 0
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0xFB,
        0x14,
        0x00,  # ref.test 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_ref_cast_wasm() -> bytes:
    """Create WASM with ref.cast instruction."""
    type_section = bytes([
        0x02,
        # Type 0: struct
        0x5F,
        0x01,
        0x7F,
        0x01,
        # Type 1: (structref) -> (structref)
        0x60,
        0x01,
        0x6B,
        0x01,
        0x6B,
    ])

    func_section = bytes([0x01, 0x01])

    export_section = bytes([0x01, 0x08]) + b"ref_cast" + bytes([0x00, 0x00])

    # Code: ref.cast type 0
    func_body = bytes([
        0x00,
        0x20,
        0x00,  # local.get 0
        0xFB,
        0x16,
        0x00,  # ref.cast 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestMoreStructInstructions:
    """Additional tests for struct instructions."""

    def test_struct_new_default_compiles(self):
        """Test that struct.new_default compiles."""
        wasm = make_struct_new_default_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_struct_new_default" in output

    def test_struct_set_compiles(self):
        """Test that struct.set compiles."""
        wasm = make_struct_set_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should store to struct field
        assert "store" in output.lower()


class TestMoreArrayInstructions:
    """Additional tests for array instructions."""

    def test_array_new_default_compiles(self):
        """Test that array.new_default compiles."""
        wasm = make_array_new_default_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_array_new_default" in output

    def test_array_get_set_compiles(self):
        """Test that array.get and array.set compile."""
        wasm = make_array_get_set_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have store and load operations
        assert "store" in output.lower()
        assert "load" in output.lower()


class TestMoreI31Instructions:
    """Additional tests for i31 instructions."""

    def test_i31_get_u_compiles(self):
        """Test that i31.get_u compiles."""
        wasm = make_i31_get_u_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_i31_get_u" in output


class TestRefInstructions:
    """Tests for reference type testing and casting."""

    def test_ref_test_compiles(self):
        """Test that ref.test compiles."""
        wasm = make_ref_test_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_ref_test" in output

    def test_ref_cast_compiles(self):
        """Test that ref.cast compiles."""
        wasm = make_ref_cast_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_ref_cast" in output
