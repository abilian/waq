"""Unit tests for variable instruction compilation."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


class TestLocalGet:
    """Tests for local.get instruction."""

    def test_local_get_param(self):
        """Test local.get on function parameter."""
        # Body: 0 locals (1), get 0 (2), end (1) = 4 bytes
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
            0x20,
            0x00,  # local.get 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "%p0" in output  # Parameter 0

    def test_local_get_multiple_params(self):
        """Test local.get on multiple parameters."""
        # Body: 0 locals (1), get 1 (2), end (1) = 4 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: (i32, i64) -> (i64)
            0x01,
            0x07,
            0x01,
            0x60,
            0x02,
            0x7F,
            0x7E,
            0x01,
            0x7E,
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
            0x20,
            0x01,  # local.get 1
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "%p1" in output  # Parameter 1


class TestLocalSet:
    """Tests for local.set instruction."""

    def test_local_set(self):
        """Test local.set instruction."""
        # Body: 1 local decl (3 bytes: count=1, type=1, value=i32), const 42 (2), set 0 (2), end (1) = 8 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> ()
            0x01,
            0x04,
            0x01,
            0x60,
            0x00,
            0x00,
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x0A,
            0x01,
            0x08,
            0x01,
            0x01,
            0x7F,  # 1 local of type i32
            0x41,
            0x2A,  # i32.const 42
            0x21,
            0x00,  # local.set 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "42" in output
        assert "copy" in output


class TestLocalTee:
    """Tests for local.tee instruction."""

    def test_local_tee(self):
        """Test local.tee instruction."""
        # Body: 1 local decl (3 bytes), const 42 (2), tee 0 (2), end (1) = 8 bytes
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
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x0A,
            0x01,
            0x08,
            0x01,
            0x01,
            0x7F,  # 1 local of type i32
            0x41,
            0x2A,  # i32.const 42
            0x22,
            0x00,  # local.tee 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "42" in output
        assert "copy" in output
        # The value should still be on stack (returned)
        assert "ret" in output


class TestGlobals:
    """Tests for global variable instructions."""

    def test_global_get(self):
        """Test global.get instruction."""
        # Body: 0 locals (1), global.get 0 (2), end (1) = 4 bytes
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
            # Global section: 1 immutable i32 = 100
            0x06,
            0x06,
            0x01,
            0x7F,
            0x00,
            0x41,
            0x64,
            0x0B,
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
            0x23,
            0x00,  # global.get 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_global_0" in output
        assert "loadw" in output  # Load word for i32

    def test_global_set(self):
        """Test global.set instruction."""
        # Body: 0 locals (1), const 42 (2), global.set 0 (2), end (1) = 6 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> ()
            0x01,
            0x04,
            0x01,
            0x60,
            0x00,
            0x00,
            # Global section: 1 mutable i32 = 0
            0x06,
            0x06,
            0x01,
            0x7F,
            0x01,
            0x41,
            0x00,
            0x0B,
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
            0x41,
            0x2A,  # i32.const 42
            0x24,
            0x00,  # global.set 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_global_0" in output
        assert "storew" in output  # Store word for i32

    def test_global_i64(self):
        """Test global with i64 type."""
        # Body: 0 locals (1), global.get 0 (2), end (1) = 4 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> (i64)
            0x01,
            0x05,
            0x01,
            0x60,
            0x00,
            0x01,
            0x7E,
            # Global section: 1 immutable i64 = 1000 (0xE8 0x07 in LEB128)
            0x06,
            0x07,
            0x01,
            0x7E,
            0x00,
            0x42,
            0xE8,
            0x07,
            0x0B,
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
            0x23,
            0x00,  # global.get 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_global_0" in output
        assert "loadl" in output  # Load long for i64


class TestLocalsWithDifferentTypes:
    """Tests for locals with different value types."""

    def test_i32_local(self):
        """Test i32 local variable."""
        # Body: 1 local (3), const 5 (2), set 0 (2), get 0 (2), end (1) = 10 bytes
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
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x0C,
            0x01,
            0x0A,
            0x01,
            0x01,
            0x7F,  # 1 i32 local
            0x41,
            0x05,  # i32.const 5
            0x21,
            0x00,  # local.set 0
            0x20,
            0x00,  # local.get 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "5" in output or "copy" in output

    def test_i64_local(self):
        """Test i64 local variable."""
        # Body: 1 local (3), const 100 (3 with proper LEB128), set 0 (2), get 0 (2), end (1) = 11 bytes
        # Section: num_funcs (1) + body_size (1) + body (11) = 13 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> (i64)
            0x01,
            0x05,
            0x01,
            0x60,
            0x00,
            0x01,
            0x7E,
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x0D,
            0x01,
            0x0B,
            0x01,
            0x01,
            0x7E,  # 1 i64 local
            0x42,
            0xE4,
            0x00,  # i64.const 100 (proper signed LEB128)
            0x21,
            0x00,  # local.set 0
            0x20,
            0x00,  # local.get 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "100" in output

    def test_multiple_locals(self):
        """Test multiple local variables."""
        # Body: 1 local decl for 3 i32s (3), const 1 (2), set 0 (2), const 2 (2), set 1 (2),
        #       get 0 (2), get 1 (2), add (1), end (1) = 17 bytes
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
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x13,
            0x01,
            0x11,
            0x01,
            0x03,
            0x7F,  # 3 i32 locals
            0x41,
            0x01,  # i32.const 1
            0x21,
            0x00,  # local.set 0
            0x41,
            0x02,  # i32.const 2
            0x21,
            0x01,  # local.set 1
            0x20,
            0x00,  # local.get 0
            0x20,
            0x01,  # local.get 1
            0x6A,  # i32.add
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "add" in output
