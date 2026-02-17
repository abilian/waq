"""Integration tests for the WASM to QBE compiler."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.compiler.context import FunctionContext, ModuleContext
from waq.parser.module import ExportKind, WasmModule, parse_module
from waq.parser.types import FuncType, ValueType


class TestCompileEmptyModule:
    """Tests for compiling minimal modules."""

    def test_empty_module(self):
        """Compile a module with no functions."""
        wasm = b"\x00asm\x01\x00\x00\x00"
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert output is not None

    def test_empty_function(self):
        """Compile a module with one empty function."""
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
            # Export section: export "f"
            0x07,
            0x05,
            0x01,
            0x01,
            0x66,
            0x00,
            0x00,
            # Code section
            0x0A,
            0x04,
            0x01,
            0x02,
            0x00,
            0x0B,
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "export" in output
        assert "function" in output
        assert "$wasm_f" in output  # Exported functions get wasm_ prefix


class TestCompileConstants:
    """Tests for compiling constant instructions."""

    def test_i32_const_return(self):
        """Function that returns i32.const 42."""
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
            # Export section
            0x07,
            0x09,
            0x01,
            0x05,
            0x63,
            0x6F,
            0x6E,
            0x73,
            0x74,
            0x00,
            0x00,  # "const"
            # Code section: i32.const 42; end
            0x0A,
            0x06,
            0x01,
            0x04,
            0x00,
            0x41,
            0x2A,
            0x0B,
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "42" in output
        assert "ret" in output

    def test_i64_const(self):
        """Function that returns i64.const."""
        # 100 in signed LEB128 = 0xE4, 0x00 (2 bytes)
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
            # Code section: i64.const 100; end (body = 5 bytes, section = 7 bytes)
            0x0A,
            0x07,
            0x01,
            0x05,
            0x00,
            0x42,
            0xE4,
            0x00,
            0x0B,
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "100" in output


class TestCompileArithmetic:
    """Tests for compiling arithmetic operations."""

    def test_i32_add(self):
        """Function: (i32, i32) -> i32 { a + b }"""
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,
            0x01,
            0x00,
            0x00,
            0x00,
            # Type: (i32, i32) -> (i32)
            0x01,
            0x07,
            0x01,
            0x60,
            0x02,
            0x7F,
            0x7F,
            0x01,
            0x7F,
            # Function
            0x03,
            0x02,
            0x01,
            0x00,
            # Export "add"
            0x07,
            0x07,
            0x01,
            0x03,
            0x61,
            0x64,
            0x64,
            0x00,
            0x00,
            # Code: local.get 0; local.get 1; i32.add; end
            0x0A,
            0x09,
            0x01,
            0x07,
            0x00,
            0x20,
            0x00,  # local.get 0
            0x20,
            0x01,  # local.get 1
            0x6A,  # i32.add
            0x0B,
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "add" in output
        assert "%p0" in output  # First parameter
        assert "%p1" in output  # Second parameter

    def test_i32_sub(self):
        """Test i32.sub instruction."""
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,
            0x07,
            0x01,
            0x60,
            0x02,
            0x7F,
            0x7F,
            0x01,
            0x7F,
            0x03,
            0x02,
            0x01,
            0x00,
            0x07,
            0x07,
            0x01,
            0x03,
            0x73,
            0x75,
            0x62,
            0x00,
            0x00,  # "sub"
            0x0A,
            0x09,
            0x01,
            0x07,
            0x00,
            0x20,
            0x00,
            0x20,
            0x01,
            0x6B,
            0x0B,  # local.get 0; local.get 1; i32.sub; end
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "sub" in output

    def test_i32_mul(self):
        """Test i32.mul instruction."""
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,
            0x07,
            0x01,
            0x60,
            0x02,
            0x7F,
            0x7F,
            0x01,
            0x7F,
            0x03,
            0x02,
            0x01,
            0x00,
            0x07,
            0x07,
            0x01,
            0x03,
            0x6D,
            0x75,
            0x6C,
            0x00,
            0x00,  # "mul"
            0x0A,
            0x09,
            0x01,
            0x07,
            0x00,
            0x20,
            0x00,
            0x20,
            0x01,
            0x6C,
            0x0B,  # local.get 0; local.get 1; i32.mul; end
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "mul" in output


class TestCompileComparisons:
    """Tests for comparison operations."""

    def test_i32_eq(self):
        """Test i32.eq instruction."""
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,
            0x07,
            0x01,
            0x60,
            0x02,
            0x7F,
            0x7F,
            0x01,
            0x7F,
            0x03,
            0x02,
            0x01,
            0x00,
            0x07,
            0x06,
            0x01,
            0x02,
            0x65,
            0x71,
            0x00,
            0x00,  # "eq"
            0x0A,
            0x09,
            0x01,
            0x07,
            0x00,
            0x20,
            0x00,
            0x20,
            0x01,
            0x46,
            0x0B,  # local.get 0; local.get 1; i32.eq; end
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "ceqw" in output

    def test_i32_lt_s(self):
        """Test i32.lt_s instruction."""
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,
            0x07,
            0x01,
            0x60,
            0x02,
            0x7F,
            0x7F,
            0x01,
            0x7F,
            0x03,
            0x02,
            0x01,
            0x00,
            0x07,
            0x07,
            0x01,
            0x03,
            0x6C,
            0x74,
            0x73,
            0x00,
            0x00,  # "lts"
            0x0A,
            0x09,
            0x01,
            0x07,
            0x00,
            0x20,
            0x00,
            0x20,
            0x01,
            0x48,
            0x0B,  # local.get 0; local.get 1; i32.lt_s; end
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "csltw" in output

    def test_i32_eqz(self):
        """Test i32.eqz instruction."""
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,
            0x06,
            0x01,
            0x60,
            0x01,
            0x7F,
            0x01,
            0x7F,  # (i32) -> (i32)
            0x03,
            0x02,
            0x01,
            0x00,
            0x07,
            0x07,
            0x01,
            0x03,
            0x65,
            0x71,
            0x7A,
            0x00,
            0x00,  # "eqz"
            0x0A,
            0x07,
            0x01,
            0x05,
            0x00,
            0x20,
            0x00,
            0x45,
            0x0B,  # local.get 0; i32.eqz; end
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        assert "ceqw" in output


class TestCompileLocals:
    """Tests for local variable operations."""

    def test_local_get_set(self):
        """Test local.get and local.set."""
        # Body: 1 local decl (3) + local.get 0 (2) + local.set 1 (2) + local.get 1 (2) + end (1) = 10 bytes
        # Section: num_funcs (1) + body_size (1) + body (10) = 12 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,
            0x06,
            0x01,
            0x60,
            0x01,
            0x7F,
            0x01,
            0x7F,  # (i32) -> (i32)
            0x03,
            0x02,
            0x01,
            0x00,
            0x07,
            0x06,
            0x01,
            0x02,
            0x69,
            0x64,
            0x00,
            0x00,  # "id"
            # Code section
            0x0A,
            0x0C,
            0x01,
            0x0A,
            0x01,
            0x01,
            0x7F,
            0x20,
            0x00,  # local.get 0
            0x21,
            0x01,  # local.set 1
            0x20,
            0x01,  # local.get 1
            0x0B,
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        # With stack-allocated locals, we use load/store instead of copy
        assert "loadw" in output
        assert "storew" in output

    def test_local_tee(self):
        """Test local.tee instruction."""
        # Body: 1 local decl (3) + local.get 0 (2) + local.tee 1 (2) + end (1) = 8 bytes
        # Section: num_funcs (1) + body_size (1) + body (8) = 10 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,
            0x06,
            0x01,
            0x60,
            0x01,
            0x7F,
            0x01,
            0x7F,  # (i32) -> (i32)
            0x03,
            0x02,
            0x01,
            0x00,
            0x07,
            0x07,
            0x01,
            0x03,
            0x74,
            0x65,
            0x65,
            0x00,
            0x00,  # "tee"
            # Code section
            0x0A,
            0x0A,
            0x01,
            0x08,
            0x01,
            0x01,
            0x7F,
            0x20,
            0x00,  # local.get 0
            0x22,
            0x01,  # local.tee 1
            0x0B,
        ])
        module = parse_module(wasm)
        qbe_module = compile_module(module)
        output = qbe_module.emit()
        # With stack-allocated locals, we use load/store instead of copy
        assert "loadw" in output
        assert "storew" in output


class TestModuleContext:
    """Tests for ModuleContext."""

    def test_get_func_name_exported(self):
        """Test getting name for exported function."""
        from waq.parser.module import Export

        module = WasmModule()
        module.exports = [Export("my_exported_func", ExportKind.FUNC, 0)]

        ctx = ModuleContext(module=module)
        name = ctx.get_func_name(0)
        # Exported functions get wasm_ prefix to avoid C symbol conflicts
        # No $ prefix - qbepy adds it
        assert name == "wasm_my_exported_func"

    def test_get_func_name_internal(self):
        """Test getting name for internal function."""
        module = WasmModule()
        ctx = ModuleContext(module=module)
        name = ctx.get_func_name(5)
        # No $ prefix - qbepy adds it
        assert name == "__wasm_func_5"

    def test_get_global_name(self):
        """Test getting global variable names."""
        module = WasmModule()
        ctx = ModuleContext(module=module)
        name = ctx.get_global_name(0)
        # No $ prefix - qbepy adds it
        assert name == "__wasm_global_0"

    def test_get_func_name_imported(self):
        """Test getting name for imported function."""
        from waq.parser.module import Import, ImportKind

        module = WasmModule()
        module.imports = [Import("env", "add_numbers", ImportKind.FUNC, 0)]

        ctx = ModuleContext(module=module)
        name = ctx.get_func_name(0)
        # Imported functions use their import name
        assert name == "add_numbers"

    def test_get_func_name_after_import(self):
        """Test function index offset for functions after imports."""
        from waq.parser.module import Export, Import, ImportKind

        module = WasmModule()
        module.imports = [Import("env", "add_numbers", ImportKind.FUNC, 0)]
        module.exports = [Export("my_func", ExportKind.FUNC, 1)]  # After import

        ctx = ModuleContext(module=module)
        # First function is imported
        assert ctx.get_func_name(0) == "add_numbers"
        # Second function is exported (gets wasm_ prefix)
        assert ctx.get_func_name(1) == "wasm_my_func"


class TestFunctionContext:
    """Tests for FunctionContext."""

    def test_new_label(self):
        """Test label generation."""
        module = WasmModule()
        ctx = FunctionContext(
            module=module,
            func_idx=0,
            func_type=FuncType((), ()),
        )
        label1 = ctx.new_label("test")
        label2 = ctx.new_label("test")
        # No @ prefix - qbepy adds it
        assert label1 == "test0"
        assert label2 == "test1"

    def test_get_local_type(self):
        """Test getting local variable types."""
        module = WasmModule()
        ctx = FunctionContext(
            module=module,
            func_idx=0,
            func_type=FuncType((ValueType.I32, ValueType.I64), ()),
            locals=[ValueType.I32, ValueType.I64, ValueType.F32],
        )
        assert ctx.get_local_type(0) == ValueType.I32
        assert ctx.get_local_type(1) == ValueType.I64
        assert ctx.get_local_type(2) == ValueType.F32

    def test_local_addrs(self):
        """Test local address management (stack-allocated locals)."""
        module = WasmModule()
        ctx = FunctionContext(
            module=module,
            func_idx=0,
            func_type=FuncType((), ()),
            locals=[ValueType.I32],
        )
        # With stack-allocated locals, we use addresses instead of temps
        ctx.set_local_addr(0, "local_addr0")
        assert ctx.get_local_addr(0) == "local_addr0"
