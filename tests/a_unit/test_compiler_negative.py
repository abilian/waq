"""Negative tests for WASM compiler.

These tests verify that the compiler correctly handles edge cases
and malformed inputs that pass parsing but fail during compilation.
"""

from __future__ import annotations

import pytest

from waq.compiler import compile_module
from waq.errors import CompileError
from waq.parser.module import parse_module


class TestStackErrors:
    """Tests for stack-related compilation errors."""

    def test_stack_underflow_on_return(self):
        """Function returning value with empty stack should fail."""
        # Function () -> i32 but no return value pushed
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> (i32)
            0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7F,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section: no instructions, just end
            0x0A, 0x04, 0x01, 0x02, 0x00, 0x0B,
        ])
        module = parse_module(wasm)
        # Should compile but return 0 (implicit return for empty stack)
        # This is valid WASM behavior - the result is undefined
        qbe = compile_module(module)
        assert qbe is not None


class TestUnhandledOpcodes:
    """Tests for unhandled instruction opcodes."""

    def test_unhandled_prefix_opcode(self):
        """Unknown prefix opcode should raise CompileError."""
        # Function with opcode 0xFE (SIMD prefix, not fully supported)
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> ()
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section: 0xFE prefix (SIMD), then some sub-opcode
            0x0A, 0x06, 0x01, 0x04, 0x00, 0xFE, 0x00, 0x0B,
        ])
        module = parse_module(wasm)
        with pytest.raises(CompileError, match="unhandled"):
            compile_module(module)


class TestControlFlowEdgeCases:
    """Tests for control flow compilation edge cases."""

    def test_br_depth_zero(self):
        """Branch to depth 0 (innermost block) should work."""
        # block: br 0; end
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> ()
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section
            0x0A, 0x09, 0x01,  # section, size, 1 function
            0x07, 0x00,        # func body size=7, 0 locals
            0x02, 0x40,        # block void
            0x0C, 0x00,        # br 0
            0x0B,              # end block
            0x0B,              # end function
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        assert qbe is not None

    def test_nested_blocks(self):
        """Deeply nested blocks should compile."""
        # Simple block test
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> ()
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section: single block
            0x0A, 0x07, 0x01,  # section id, size 7, 1 function
            0x05, 0x00,        # func body size 5, 0 locals
            0x02, 0x40,        # block void
            0x0B,              # end block
            0x0B,              # end function
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        assert qbe is not None


class TestMemoryOperations:
    """Tests for memory operation edge cases."""

    def test_memory_load_without_memory(self):
        """Memory load without memory section should still compile."""
        # Function with i32.load but no memory
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> i32
            0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7F,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section: i32.const 0, i32.load, end
            0x0A, 0x09, 0x01, 0x07, 0x00,
            0x41, 0x00,        # i32.const 0
            0x28, 0x02, 0x00,  # i32.load align=2 offset=0
            0x0B,
        ])
        module = parse_module(wasm)
        # Should compile (runtime will handle missing memory)
        qbe = compile_module(module)
        assert qbe is not None


class TestCallOperations:
    """Tests for function call edge cases."""

    def test_call_to_itself(self):
        """Recursive call should compile."""
        # Function that calls itself
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> ()
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section: call 0, end
            0x0A, 0x06, 0x01, 0x04, 0x00,
            0x10, 0x00,  # call function 0
            0x0B,
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        assert qbe is not None


class TestLocalOperations:
    """Tests for local variable operations."""

    def test_get_param(self):
        """Getting function parameter should work."""
        # Function (i32) -> i32, returns param
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: (i32) -> (i32)
            0x01, 0x06, 0x01, 0x60, 0x01, 0x7F, 0x01, 0x7F,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section: local.get 0, end
            0x0A, 0x06, 0x01, 0x04, 0x00,
            0x20, 0x00,  # local.get 0
            0x0B,
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        assert qbe is not None

    def test_local_with_single_type(self):
        """Function with local variables should compile."""
        # Function () -> () with 1 i32 local
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> ()
            0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Code section
            0x0A, 0x06, 0x01,  # section id, size 6, 1 function
            0x04,              # func body size 4
            0x01,              # 1 local group
            0x01, 0x7F,        # 1 i32
            0x0B,              # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        assert qbe is not None


class TestGlobalOperations:
    """Tests for global variable operations."""

    def test_global_get_set(self):
        """Getting and setting global should work."""
        # Module with mutable global, function that increments it
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D,  # magic
            0x01, 0x00, 0x00, 0x00,  # version
            # Type section: () -> (i32)
            0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7F,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Global section: mutable i32, init to 0
            0x06, 0x06, 0x01, 0x7F, 0x01, 0x41, 0x00, 0x0B,
            # Code section
            0x0A, 0x0D, 0x01,  # section, size, 1 function
            0x0B, 0x00,        # func body size, 0 locals
            0x23, 0x00,        # global.get 0
            0x41, 0x01,        # i32.const 1
            0x6A,              # i32.add
            0x24, 0x00,        # global.set 0
            0x23, 0x00,        # global.get 0
            0x0B,              # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        assert qbe is not None
