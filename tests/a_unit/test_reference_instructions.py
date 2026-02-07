"""Unit tests for reference instructions (WASM 2.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_ref_null_funcref_wasm() -> bytes:
    """Create WASM with ref.null funcref instruction.

    () -> (funcref)
    """
    # Type section: () -> (funcref)
    type_section = bytes([0x01, 0x60, 0x00, 0x01, 0x70])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"null" + bytes([0x00, 0x00])

    # Code section: ref.null funcref
    func_body = bytes([
        0x00,  # 0 locals
        0xD0,
        0x70,  # ref.null funcref
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_ref_null_externref_wasm() -> bytes:
    """Create WASM with ref.null externref instruction.

    () -> (externref)
    """
    # Type section: () -> (externref)
    type_section = bytes([0x01, 0x60, 0x00, 0x01, 0x6F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"null" + bytes([0x00, 0x00])

    # Code section: ref.null externref
    func_body = bytes([
        0x00,  # 0 locals
        0xD0,
        0x6F,  # ref.null externref
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_ref_is_null_wasm() -> bytes:
    """Create WASM with ref.is_null instruction.

    (funcref) -> (i32)
    """
    # Type section: (funcref) -> (i32)
    type_section = bytes([0x01, 0x60, 0x01, 0x70, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x06]) + b"isnull" + bytes([0x00, 0x00])

    # Code section: ref.is_null
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (the funcref)
        0xD1,  # ref.is_null
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_ref_func_wasm() -> bytes:
    """Create WASM with ref.func instruction.

    () -> (funcref)

    References the function itself.
    """
    # Type section: () -> (funcref)
    type_section = bytes([0x01, 0x60, 0x00, 0x01, 0x70])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x07]) + b"getfunc" + bytes([0x00, 0x00])

    # Code section: ref.func (self-reference)
    func_body = bytes([
        0x00,  # 0 locals
        0xD2,
        0x00,  # ref.func func_idx=0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestRefNull:
    """Tests for ref.null instruction."""

    def test_ref_null_funcref_compiles(self):
        """Test that ref.null funcref compiles."""
        wasm = make_ref_null_funcref_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # ref.null produces 0 (null pointer)
        assert "copy" in output.lower() or "0" in output

    def test_ref_null_externref_compiles(self):
        """Test that ref.null externref compiles."""
        wasm = make_ref_null_externref_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # ref.null produces 0 (null pointer)
        assert "copy" in output.lower() or "0" in output


class TestRefIsNull:
    """Tests for ref.is_null instruction."""

    def test_ref_is_null_compiles(self):
        """Test that ref.is_null compiles."""
        wasm = make_ref_is_null_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # ref.is_null uses comparison
        assert "ceql" in output


class TestRefFunc:
    """Tests for ref.func instruction."""

    def test_ref_func_compiles(self):
        """Test that ref.func compiles."""
        wasm = make_ref_func_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should reference the function
        assert "getfunc" in output
