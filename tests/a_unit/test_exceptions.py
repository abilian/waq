"""Unit tests for exception handling instructions (WASM 3.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_try_catch_wasm() -> bytes:
    """Create WASM with try/catch.

    () -> (i32)
    Returns 1 if exception caught, 0 otherwise.
    """
    # Type section: () -> (i32)
    type_section = bytes([0x01, 0x60, 0x00, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x09]) + b"try_catch" + bytes([0x00, 0x00])

    # Code section: try/catch
    func_body = bytes([
        0x00,  # 0 locals
        0x06,
        0x40,  # try (void)
        0x41,
        0x00,  # i32.const 0
        0x0F,  # return (no exception)
        0x07,
        0x00,  # catch tag 0
        0x1A,  # drop (exception value)
        0x41,
        0x01,  # i32.const 1
        0x0F,  # return (caught exception)
        0x0B,  # end try
        0x41,
        0x00,  # i32.const 0 (fallback)
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_throw_wasm() -> bytes:
    """Create WASM with throw instruction.

    () -> ()
    Throws exception with tag 0.
    """
    # Type section: () -> ()
    type_section = bytes([0x01, 0x60, 0x00, 0x00])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x05]) + b"throw" + bytes([0x00, 0x00])

    # Code section: throw
    func_body = bytes([
        0x00,  # 0 locals
        0x08,
        0x00,  # throw tag 0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_catch_all_wasm() -> bytes:
    """Create WASM with catch_all.

    () -> (i32)
    Returns 1 if any exception caught.
    """
    # Type section: () -> (i32)
    type_section = bytes([0x01, 0x60, 0x00, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x09]) + b"catch_all" + bytes([0x00, 0x00])

    # Code section: try/catch_all
    func_body = bytes([
        0x00,  # 0 locals
        0x06,
        0x40,  # try (void)
        0x41,
        0x00,  # i32.const 0
        0x0F,  # return
        0x19,  # catch_all
        0x41,
        0x01,  # i32.const 1
        0x0F,  # return
        0x0B,  # end try
        0x41,
        0x00,  # i32.const 0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestTryCatch:
    """Tests for try/catch instructions."""

    def test_try_catch_compiles(self):
        """Test that try/catch compiles."""
        wasm = make_try_catch_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should contain exception handler calls
        assert "__wasm_push_exception_handler" in output
        assert "__wasm_get_exception" in output


class TestThrow:
    """Tests for throw instruction."""

    def test_throw_compiles(self):
        """Test that throw compiles."""
        wasm = make_throw_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should contain throw call
        assert "__wasm_throw" in output


class TestCatchAll:
    """Tests for catch_all instruction."""

    def test_catch_all_compiles(self):
        """Test that catch_all compiles."""
        wasm = make_catch_all_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should contain exception handler setup
        assert "__wasm_push_exception_handler" in output


def make_rethrow_wasm() -> bytes:
    """Create WASM with rethrow instruction.

    () -> ()
    Rethrows the exception from catch block.
    """
    # Type section: () -> ()
    type_section = bytes([0x01, 0x60, 0x00, 0x00])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section
    export_section = bytes([0x01, 0x07]) + b"rethrow" + bytes([0x00, 0x00])

    # Code section: try/catch with rethrow
    func_body = bytes([
        0x00,  # 0 locals
        0x06,
        0x40,  # try (void)
        0x00,  # nop
        0x07,
        0x00,  # catch tag 0
        0x09,
        0x00,  # rethrow depth 0
        0x0B,  # end try
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_delegate_wasm() -> bytes:
    """Create WASM with delegate instruction.

    () -> ()
    Delegates exception handling to outer try block.
    """
    # Type section: () -> ()
    type_section = bytes([0x01, 0x60, 0x00, 0x00])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Export section: name length = 8 for "delegate"
    export_name = b"delegate"
    export_section = bytes([0x01, len(export_name)]) + export_name + bytes([0x00, 0x00])

    # Code section: try with delegate
    func_body = bytes([
        0x00,  # 0 locals
        0x06,
        0x40,  # try (void)
        0x00,  # nop
        0x18,
        0x00,  # delegate depth 0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestRethrow:
    """Tests for rethrow instruction."""

    def test_rethrow_compiles(self):
        """Test that rethrow compiles."""
        wasm = make_rethrow_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_rethrow" in output


class TestDelegate:
    """Tests for delegate instruction."""

    def test_delegate_compiles(self):
        """Test that delegate compiles."""
        wasm = make_delegate_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Delegate uses try body label and pushes exception handler
        assert "__wasm_push_exception_handler" in output
        assert "try" in output
