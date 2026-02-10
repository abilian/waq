"""Unit tests for tail call instructions (WASM 3.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_self_tail_call_wasm() -> bytes:
    """Create WASM with self-recursive tail call (simple countdown).

    (func $countdown (param $n i32) (param $acc i32) (result i32)
      (if (i32.le_s (local.get $n) (i32.const 0))
        (then (return (local.get $acc))))
      (return_call $countdown
        (i32.sub (local.get $n) (i32.const 1))
        (i32.add (local.get $acc) (local.get $n))))
    """
    # fmt: off
    # Type section: (i32, i32) -> (i32)
    type_section = bytes([
        0x01, 0x60,  # 1 func type, func marker
        0x02, 0x7F, 0x7F,  # 2 params: i32, i32
        0x01, 0x7F,  # 1 result: i32
    ])

    # Function section: func uses type 0
    func_section = bytes([0x01, 0x00])

    # Export section: export "countdown" as func 0
    export_section = bytes([0x01, 0x09]) + b"countdown" + bytes([0x00, 0x00])

    # Code section: simple self-recursive countdown with return_call
    func_body = bytes([
        0x00,  # 0 locals
        # if (n <= 0) return acc
        0x20, 0x00,  # local.get 0 (n)
        0x41, 0x00,  # i32.const 0
        0x4C,        # i32.le_s
        0x04, 0x40,  # if (void)
        0x20, 0x01,  # local.get 1 (acc)
        0x0F,        # return
        0x0B,        # end if
        # return_call $countdown(n-1, acc+n)
        0x20, 0x00,  # local.get 0 (n)
        0x41, 0x01,  # i32.const 1
        0x6B,        # i32.sub -> n-1
        0x20, 0x01,  # local.get 1 (acc)
        0x20, 0x00,  # local.get 0 (n)
        0x6A,        # i32.add -> acc+n
        0x12, 0x00,  # return_call func 0 (self)
        0x0B,        # end function
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])  # magic + version
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on

    return wasm


def make_non_self_tail_call_wasm() -> bytes:
    """Create WASM with tail call to a different function.

    (func $helper (param $x i32) (result i32)
      (i32.add (local.get $x) (i32.const 10)))

    (func $caller (param $x i32) (result i32)
      (return_call $helper (i32.add (local.get $x) (i32.const 5))))
    """
    # fmt: off
    # Type section: (i32) -> (i32)
    type_section = bytes([
        0x01, 0x60,
        0x01, 0x7F,  # 1 param: i32
        0x01, 0x7F,  # 1 result: i32
    ])

    # Function section: 2 funcs, both use type 0
    func_section = bytes([0x02, 0x00, 0x00])

    # Export section: export "caller" as func 1
    export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

    # Code section: two functions
    # Helper function: x + 10
    helper_body = bytes([
        0x00,  # 0 locals
        0x20, 0x00,  # local.get 0
        0x41, 0x0A,  # i32.const 10
        0x6A,        # i32.add
        0x0B,        # end
    ])

    # Caller function: return_call helper(x + 5)
    caller_body = bytes([
        0x00,  # 0 locals
        0x20, 0x00,  # local.get 0
        0x41, 0x05,  # i32.const 5
        0x6A,        # i32.add
        0x12, 0x00,  # return_call func 0 (helper)
        0x0B,        # end
    ])

    code_section = bytes([
        0x02,  # 2 functions
        len(helper_body),
    ]) + helper_body + bytes([len(caller_body)]) + caller_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on

    return wasm


def make_return_call_indirect_wasm() -> bytes:
    """Create WASM with return_call_indirect.

    Type 0: (i32) -> (i32)
    Type 1: (i32, i32) -> (i32)

    (func $impl (param $x i32) (result i32)
      (i32.add (local.get $x) (i32.const 1)))

    (func $dispatcher (param $idx i32) (param $x i32) (result i32)
      (return_call_indirect (type 0) (local.get $x) (local.get $idx)))
    """
    # fmt: off
    # Type section: 2 types
    # Type 0: (i32) -> (i32)
    # Type 1: (i32, i32) -> (i32)
    type_section = bytes([
        0x02,  # 2 types
        0x60, 0x01, 0x7F, 0x01, 0x7F,  # type 0: (i32) -> (i32)
        0x60, 0x02, 0x7F, 0x7F, 0x01, 0x7F,  # type 1: (i32, i32) -> (i32)
    ])

    # Function section: 2 funcs - impl uses type 0, dispatcher uses type 1
    func_section = bytes([0x02, 0x00, 0x01])

    # Table section: 1 funcref table with min 1
    table_section = bytes([
        0x01,  # 1 table
        0x70,  # funcref
        0x00, 0x01,  # limits: min 1
    ])

    # Element section: init table[0] = func 0
    elem_section = bytes([
        0x01,  # 1 element
        0x00,  # flags: active, table 0
        0x41, 0x00, 0x0B,  # offset: i32.const 0, end
        0x01, 0x00,  # 1 func index: func 0
    ])

    # Export section: export "dispatch" as func 1
    export_section = bytes([0x01, 0x08]) + b"dispatch" + bytes([0x00, 0x01])

    # Code section
    # Impl function: x + 1
    impl_body = bytes([
        0x00,  # 0 locals
        0x20, 0x00,  # local.get 0
        0x41, 0x01,  # i32.const 1
        0x6A,        # i32.add
        0x0B,        # end
    ])

    # Dispatcher: return_call_indirect type 0
    dispatch_body = bytes([
        0x00,  # 0 locals
        0x20, 0x01,  # local.get 1 (x)
        0x20, 0x00,  # local.get 0 (idx)
        0x13, 0x00, 0x00,  # return_call_indirect type 0, table 0
        0x0B,        # end
    ])

    code_section = bytes([
        0x02,  # 2 functions
        len(impl_body),
    ]) + impl_body + bytes([len(dispatch_body)]) + dispatch_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x09, len(elem_section)]) + elem_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on

    return wasm


class TestReturnCall:
    """Tests for return_call instruction (0x12)."""

    def test_self_tail_call_compiles(self):
        """Test that self-recursive tail call compiles to a loop."""
        wasm = make_self_tail_call_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Self-tail-call should optimize to a loop (jmp @entry)
        assert "jmp @entry" in output
        # Should NOT have a recursive call to the same function
        assert output.count("call $countdown") == 0

    def test_non_self_tail_call_compiles(self):
        """Test that tail call to different function uses call + ret."""
        wasm = make_non_self_tail_call_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Non-self tail call should use regular call + ret
        assert "call $" in output
        assert "ret" in output


class TestReturnCallIndirect:
    """Tests for return_call_indirect instruction (0x13)."""

    def test_return_call_indirect_compiles(self):
        """Test that return_call_indirect compiles."""
        wasm = make_return_call_indirect_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should load from table and do indirect call
        assert "__wasm_table" in output
        assert "ret" in output


class TestReturnCallRef:
    """Tests for return_call_ref instruction (0x14)."""

    def test_return_call_ref_basic(self):
        """Test return_call_ref with function reference."""
        # fmt: off
        # Build WASM with return_call_ref
        # Type section: (i32) -> (i32)
        type_section = bytes([
            0x01, 0x60,
            0x01, 0x7F,  # 1 param: i32
            0x01, 0x7F,  # 1 result: i32
        ])

        # Function section: 2 funcs
        func_section = bytes([0x02, 0x00, 0x00])

        # Export section
        export_section = bytes([0x01, 0x06]) + b"caller" + bytes([0x00, 0x01])

        # Code section
        # Target function: x + 1
        target_body = bytes([
            0x00,
            0x20, 0x00,  # local.get 0
            0x41, 0x01,  # i32.const 1
            0x6A,        # i32.add
            0x0B,
        ])

        # Caller: ref.func 0, then return_call_ref
        caller_body = bytes([
            0x00,
            0x20, 0x00,  # local.get 0 (arg)
            0xD2, 0x00,  # ref.func 0
            0x14, 0x00,  # return_call_ref type 0
            0x0B,
        ])

        code_section = bytes([
            0x02,
            len(target_body),
        ]) + target_body + bytes([len(caller_body)]) + caller_body

        wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
        wasm += bytes([0x01, len(type_section)]) + type_section
        wasm += bytes([0x03, len(func_section)]) + func_section
        wasm += bytes([0x07, len(export_section)]) + export_section
        wasm += bytes([0x0A, len(code_section)]) + code_section
        # fmt: on

        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have indirect call via function reference
        assert "ret" in output
