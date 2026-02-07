"""Unit tests for control flow instruction compilation."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


class TestBlock:
    """Tests for block instruction."""

    def test_empty_block(self):
        """Test empty block."""
        # Code body: 0 locals (1 byte), block void (2 bytes), end (1 byte), end (1 byte) = 5 bytes
        # Section: 1 func (1 byte), body size 5 (1 byte), body (5 bytes) = 7 bytes
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
            0x07,
            0x01,
            0x05,
            0x00,
            0x02,
            0x40,  # block (void)
            0x0B,  # end (block)
            0x0B,  # end (function)
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "block_end" in output

    def test_block_with_result(self):
        """Test block with result type."""
        # Body: 0 locals (1), block i32 (2), const 1 (2), end (1), end (1) = 7 bytes
        # Section: 1 func (1), size 7 (1), body (7) = 9 bytes
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
            0x09,
            0x01,
            0x07,
            0x00,
            0x02,
            0x7F,  # block (result i32)
            0x41,
            0x01,  # i32.const 1
            0x0B,  # end (block)
            0x0B,  # end (function)
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "1" in output


class TestLoop:
    """Tests for loop instruction."""

    def test_simple_loop(self):
        """Test simple loop structure."""
        # Body: 0 locals (1), loop void (2), end (1), end (1) = 5 bytes
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
            0x07,
            0x01,
            0x05,
            0x00,
            0x03,
            0x40,  # loop (void)
            0x0B,  # end (loop)
            0x0B,  # end (function)
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "loop" in output
        assert "jmp" in output


class TestIf:
    """Tests for if/else instructions."""

    def test_if_only(self):
        """Test if without else."""
        # Body: 0 locals (1), get 0 (2), if void (2), end (1), end (1) = 7 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: (i32) -> ()
            0x01,
            0x05,
            0x01,
            0x60,
            0x01,
            0x7F,
            0x00,
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x09,
            0x01,
            0x07,
            0x00,
            0x20,
            0x00,  # local.get 0
            0x04,
            0x40,  # if (void)
            0x0B,  # end (if)
            0x0B,  # end (function)
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "jnz" in output
        assert "then" in output

    def test_if_else(self):
        """Test if with else."""
        # Body: 0 locals (1), get 0 (2), if i32 (2), const 1 (2), else (1), const 0 (2), end (1), end (1) = 12 bytes
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
            0x0E,
            0x01,
            0x0C,
            0x00,
            0x20,
            0x00,  # local.get 0
            0x04,
            0x7F,  # if (result i32)
            0x41,
            0x01,  # i32.const 1
            0x05,  # else
            0x41,
            0x00,  # i32.const 0
            0x0B,  # end (if)
            0x0B,  # end (function)
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "jnz" in output
        assert "then" in output
        assert "else" in output


class TestBranch:
    """Tests for branch instructions."""

    def test_br(self):
        """Test br instruction."""
        # Body: 0 locals (1), block void (2), br 0 (2), end (1), end (1) = 7 bytes
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
            0x09,
            0x01,
            0x07,
            0x00,
            0x02,
            0x40,  # block (void)
            0x0C,
            0x00,  # br 0
            0x0B,  # end (block)
            0x0B,  # end (function)
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "jmp" in output

    def test_br_if(self):
        """Test br_if instruction."""
        # Body: 0 locals (1), block void (2), get 0 (2), br_if 0 (2), end (1), end (1) = 9 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: (i32) -> ()
            0x01,
            0x05,
            0x01,
            0x60,
            0x01,
            0x7F,
            0x00,
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,
            0x0B,
            0x01,
            0x09,
            0x00,
            0x02,
            0x40,  # block (void)
            0x20,
            0x00,  # local.get 0
            0x0D,
            0x00,  # br_if 0
            0x0B,  # end (block)
            0x0B,  # end (function)
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "jnz" in output
        assert "br_if" in output


class TestReturn:
    """Tests for return instruction."""

    def test_return_void(self):
        """Test return from void function."""
        # Body: 0 locals (1), return (1), end (1) = 3 bytes
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
            0x05,
            0x01,
            0x03,
            0x00,
            0x0F,  # return
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "ret" in output

    def test_return_value(self):
        """Test return with value."""
        # Body: 0 locals (1), const 42 (2), return (1), end (1) = 5 bytes
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
            0x07,
            0x01,
            0x05,
            0x00,
            0x41,
            0x2A,  # i32.const 42
            0x0F,  # return
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "42" in output
        assert "ret" in output


class TestCall:
    """Tests for call instruction."""

    def test_call_simple(self):
        """Test simple function call."""
        # Func 1 body: 0 locals (1), call 1 (2), end (1) = 4 bytes
        # Func 2 body: 0 locals (1), end (1) = 2 bytes
        # Section: 2 funcs (1), size 4 (1), body1 (4), size 2 (1), body2 (2) = 9 bytes
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
            # Function section: two functions
            0x03,
            0x03,
            0x02,
            0x00,
            0x00,
            # Code section
            0x0A,
            0x09,
            0x02,
            # First function: call 1; end
            0x04,
            0x00,
            0x10,
            0x01,
            0x0B,
            # Second function: end
            0x02,
            0x00,
            0x0B,
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "call" in output

    def test_call_with_args(self):
        """Test function call with arguments."""
        # Type section: count (1) + type0 (3) + type1 (4) = 8 bytes
        # Code section: count (1) + func1 (1+6=7) + func2 (1+2=3) = 11 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> (), (i32) -> ()
            0x01,
            0x08,
            0x02,  # section=1, size=8, count=2
            0x60,
            0x00,
            0x00,  # () -> ()
            0x60,
            0x01,
            0x7F,
            0x00,  # (i32) -> ()
            # Function section: two functions
            0x03,
            0x03,
            0x02,
            0x00,
            0x01,
            # Code section
            0x0A,
            0x0B,
            0x02,
            # First function: i32.const 42; call 1; end
            0x06,
            0x00,
            0x41,
            0x2A,
            0x10,
            0x01,
            0x0B,
            # Second function (takes i32): end
            0x02,
            0x00,
            0x0B,
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "call" in output
        assert "42" in output


class TestNop:
    """Tests for nop instruction."""

    def test_nop(self):
        """Test nop instruction does nothing."""
        # Body: 0 locals (1), nop (1), nop (1), nop (1), end (1) = 5 bytes
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
            0x07,
            0x01,
            0x05,
            0x00,
            0x01,  # nop
            0x01,  # nop
            0x01,  # nop
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should compile without error
        assert output is not None


class TestUnreachable:
    """Tests for unreachable instruction."""

    def test_unreachable(self):
        """Test unreachable instruction generates trap."""
        # Body: 0 locals (1), unreachable (1), end (1) = 3 bytes
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
            0x05,
            0x01,
            0x03,
            0x00,
            0x00,  # unreachable
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "trap" in output or "hlt" in output


class TestDrop:
    """Tests for drop instruction."""

    def test_drop(self):
        """Test drop instruction removes value from stack."""
        # Body: 0 locals (1), const 1 (2), drop (1), end (1) = 5 bytes
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
            0x07,
            0x01,
            0x05,
            0x00,
            0x41,
            0x01,  # i32.const 1
            0x1A,  # drop
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should compile without error - the dropped value is just not used
        assert output is not None


class TestSelect:
    """Tests for select instruction."""

    def test_select(self):
        """Test select instruction."""
        # Body: 0 locals (1), const 1 (2), const 2 (2), get 0 (2), select (1), end (1) = 9 bytes
        # Section: count (1) + body_size (1) + body (9) = 11 bytes
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
            0x0B,
            0x01,
            0x09,
            0x00,
            0x41,
            0x01,  # i32.const 1
            0x41,
            0x02,  # i32.const 2
            0x20,
            0x00,  # local.get 0
            0x1B,  # select
            0x0B,  # end
        ])
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # select uses conditional branching (jnz)
        assert "jnz" in output or "phi" in output
