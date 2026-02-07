"""Tests for extended WASM 2.0 opcodes."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_select_with_type_wasm() -> bytes:
    """Create WASM with select with type instruction.

    (a: i32, b: i32, cond: i32) -> (i32)
    """
    # Type section: (i32, i32, i32) -> (i32)
    type_section = bytes([0x01, 0x60, 0x03, 0x7F, 0x7F, 0x7F, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x06]) + b"select" + bytes([0x00, 0x00])

    # Code section: select with type
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (a)
        0x20,
        0x01,  # local.get 1 (b)
        0x20,
        0x02,  # local.get 2 (cond)
        0x1C,
        0x01,
        0x7F,  # select (type) with 1 type: i32
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_ref_eq_wasm() -> bytes:
    """Create WASM with ref.eq instruction.

    (ref1: funcref, ref2: funcref) -> (i32)
    """
    # Type section: (funcref, funcref) -> (i32)
    type_section = bytes([0x01, 0x60, 0x02, 0x70, 0x70, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x06]) + b"ref_eq" + bytes([0x00, 0x00])

    # Code section: ref.eq
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (ref1)
        0x20,
        0x01,  # local.get 1 (ref2)
        0xD3,  # ref.eq
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_ref_as_non_null_wasm() -> bytes:
    """Create WASM with ref.as_non_null instruction.

    (ref: funcref) -> (funcref)
    """
    # Type section: (funcref) -> (funcref)
    type_section = bytes([0x01, 0x60, 0x01, 0x70, 0x01, 0x70])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x08]) + b"non_null" + bytes([0x00, 0x00])

    # Code section: ref.as_non_null
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (ref)
        0xD4,  # ref.as_non_null
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_br_on_null_wasm() -> bytes:
    """Create WASM with br_on_null instruction.

    (ref: funcref) -> (i32)
    Returns 1 if ref is null, 0 otherwise.
    """
    # Type section: (funcref) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x70, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x0A]) + b"br_on_null" + bytes([0x00, 0x00])

    # Code section: block with br_on_null
    func_body = bytes([
        0x00,  # 0 locals
        0x02,
        0x40,  # block (void)
        0x20,
        0x00,  # local.get 0 (ref)
        0xD5,
        0x00,  # br_on_null 0 (to block end)
        0x1A,  # drop (the non-null ref)
        0x41,
        0x00,  # i32.const 0 (not null)
        0x0F,  # return
        0x0B,  # end block
        0x41,
        0x01,  # i32.const 1 (was null)
        0x0B,  # end function
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_br_on_non_null_wasm() -> bytes:
    """Create WASM with br_on_non_null instruction.

    (ref: funcref) -> (i32)
    Returns 0 if ref is null, 1 otherwise.
    """
    # Type section: (funcref) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x70, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x0E]) + b"br_on_non_null" + bytes([0x00, 0x00])

    # Code section: block with br_on_non_null
    func_body = bytes([
        0x00,  # 0 locals
        0x02,
        0x40,  # block (void)
        0x20,
        0x00,  # local.get 0 (ref)
        0xD6,
        0x00,  # br_on_non_null 0 (to block end if non-null)
        0x41,
        0x00,  # i32.const 0 (was null)
        0x0F,  # return
        0x0B,  # end block
        0x41,
        0x01,  # i32.const 1 (was non-null)
        0x0B,  # end function
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestSelectWithType:
    """Tests for select with type instruction."""

    def test_select_with_type_compiles(self):
        """Test that select with type compiles."""
        wasm = make_select_with_type_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "select" in output


class TestRefEq:
    """Tests for ref.eq instruction."""

    def test_ref_eq_compiles(self):
        """Test that ref.eq compiles."""
        wasm = make_ref_eq_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should contain ceql comparison
        assert "ceql" in output


class TestRefAsNonNull:
    """Tests for ref.as_non_null instruction."""

    def test_ref_as_non_null_compiles(self):
        """Test that ref.as_non_null compiles."""
        wasm = make_ref_as_non_null_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should contain trap function call
        assert "__wasm_trap_null_reference" in output


class TestBrOnNull:
    """Tests for br_on_null instruction."""

    def test_br_on_null_compiles(self):
        """Test that br_on_null compiles."""
        wasm = make_br_on_null_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "br_on_null" in output


class TestBrOnNonNull:
    """Tests for br_on_non_null instruction."""

    def test_br_on_non_null_compiles(self):
        """Test that br_on_non_null compiles."""
        wasm = make_br_on_non_null_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "br_on_non_null" in output
