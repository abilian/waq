"""Unit tests for WASM module parsing."""

from __future__ import annotations

import pytest

from waq.errors import ParseError
from waq.parser.module import (
    ExportKind,
    ImportKind,
    WasmModule,
    parse_module,
)
from waq.parser.types import FuncType, ValueType


class TestModuleValidation:
    """Tests for module header validation."""

    def test_valid_magic(self):
        # Minimal valid WASM module (just header)
        wasm = b"\x00asm\x01\x00\x00\x00"
        module = parse_module(wasm)
        assert isinstance(module, WasmModule)

    def test_invalid_magic(self):
        wasm = b"\x00bad\x01\x00\x00\x00"
        with pytest.raises(ParseError, match="invalid magic"):
            parse_module(wasm)

    def test_invalid_version(self):
        wasm = b"\x00asm\x02\x00\x00\x00"
        with pytest.raises(ParseError, match="unsupported version"):
            parse_module(wasm)


class TestTypeSection:
    """Tests for type section parsing."""

    def test_empty_func_type(self):
        # Type section with one function type: () -> ()
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            0x01,  # type section
            0x04,  # section size
            0x01,  # one type
            0x60,  # func type
            0x00,  # 0 params
            0x00,  # 0 results
        ])
        module = parse_module(wasm)
        assert len(module.types) == 1
        assert module.types[0] == FuncType((), ())

    def test_func_type_with_params_and_results(self):
        # Type: (i32, i64) -> (i32)
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            0x01,  # type section
            0x07,  # section size
            0x01,  # one type
            0x60,  # func type
            0x02,  # 2 params
            0x7F,  # i32
            0x7E,  # i64
            0x01,  # 1 result
            0x7F,  # i32
        ])
        module = parse_module(wasm)
        assert len(module.types) == 1
        assert module.types[0] == FuncType(
            (ValueType.I32, ValueType.I64),
            (ValueType.I32,),
        )

    def test_multiple_func_types(self):
        # Two types: () -> () and (i32) -> (i32)
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            0x01,  # type section
            0x09,  # section size
            0x02,  # two types
            0x60,
            0x00,
            0x00,  # () -> ()
            0x60,
            0x01,
            0x7F,
            0x01,
            0x7F,  # (i32) -> (i32)
        ])
        module = parse_module(wasm)
        assert len(module.types) == 2
        assert module.types[0] == FuncType((), ())
        assert module.types[1] == FuncType((ValueType.I32,), (ValueType.I32,))


class TestFunctionSection:
    """Tests for function section parsing."""

    def test_function_section(self):
        # Type section + function section
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section
            0x01,
            0x04,
            0x01,
            0x60,
            0x00,
            0x00,
            # Function section
            0x03,  # function section
            0x02,  # section size
            0x01,  # one function
            0x00,  # type index 0
        ])
        module = parse_module(wasm)
        assert len(module.func_types) == 1
        assert module.func_types[0] == 0


class TestExportSection:
    """Tests for export section parsing."""

    def test_function_export(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section
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
            # Export section
            0x07,  # export section
            0x08,  # section size
            0x01,  # one export
            0x04,  # name length
            0x6D,
            0x61,
            0x69,
            0x6E,  # "main"
            0x00,  # export kind: func
            0x00,  # function index
        ])
        module = parse_module(wasm)
        assert len(module.exports) == 1
        assert module.exports[0].name == "main"
        assert module.exports[0].kind == ExportKind.FUNC
        assert module.exports[0].index == 0

    def test_memory_export(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Memory section
            0x05,
            0x03,
            0x01,
            0x00,
            0x01,  # memory: min=1, no max
            # Export section
            0x07,  # export section
            0x0A,  # section size
            0x01,  # one export
            0x06,  # name length
            0x6D,
            0x65,
            0x6D,
            0x6F,
            0x72,
            0x79,  # "memory"
            0x02,  # export kind: memory
            0x00,  # memory index
        ])
        module = parse_module(wasm)
        assert len(module.exports) == 1
        assert module.exports[0].name == "memory"
        assert module.exports[0].kind == ExportKind.MEMORY


class TestMemorySection:
    """Tests for memory section parsing."""

    def test_memory_min_only(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Memory section
            0x05,  # memory section
            0x03,  # section size
            0x01,  # one memory
            0x00,  # flags: no max
            0x01,  # min: 1 page
        ])
        module = parse_module(wasm)
        assert len(module.memories) == 1
        assert module.memories[0].limits.min == 1
        assert module.memories[0].limits.max is None

    def test_memory_with_max(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Memory section
            0x05,  # memory section
            0x04,  # section size
            0x01,  # one memory
            0x01,  # flags: has max
            0x01,  # min: 1 page
            0x10,  # max: 16 pages
        ])
        module = parse_module(wasm)
        assert len(module.memories) == 1
        assert module.memories[0].limits.min == 1
        assert module.memories[0].limits.max == 16


class TestImportSection:
    """Tests for import section parsing."""

    def test_function_import(self):
        # Section content: 1 import (1), mod name len 3 (1), "env" (3), field name len 4 (1),
        # "puts" (4), kind func (1), type idx 0 (1) = 12 bytes
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section
            0x01,
            0x05,
            0x01,
            0x60,
            0x01,
            0x7F,
            0x00,  # (i32) -> ()
            # Import section
            0x02,  # import section
            0x0C,  # section size = 12 bytes
            0x01,  # one import
            0x03,  # module name length
            0x65,
            0x6E,
            0x76,  # "env"
            0x04,  # field name length
            0x70,
            0x75,
            0x74,
            0x73,  # "puts"
            0x00,  # import kind: func
            0x00,  # type index
        ])
        module = parse_module(wasm)
        assert len(module.imports) == 1
        assert module.imports[0].module == "env"
        assert module.imports[0].name == "puts"
        assert module.imports[0].kind == ImportKind.FUNC
        assert module.imports[0].desc == 0


class TestCodeSection:
    """Tests for code section parsing."""

    def test_empty_function_body(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section
            0x01,
            0x04,
            0x01,
            0x60,
            0x00,
            0x00,  # () -> ()
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,  # code section
            0x04,  # section size
            0x01,  # one function
            0x02,  # body size
            0x00,  # no locals
            0x0B,  # end
        ])
        module = parse_module(wasm)
        assert len(module.code) == 1
        assert module.code[0].locals == []
        assert module.code[0].code == b"\x0b"

    def test_function_with_locals(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section
            0x01,
            0x04,
            0x01,
            0x60,
            0x00,
            0x00,  # () -> ()
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Code section
            0x0A,  # code section
            0x06,  # section size
            0x01,  # one function
            0x04,  # body size
            0x01,  # one local declaration
            0x02,  # 2 locals
            0x7F,  # of type i32
            0x0B,  # end
        ])
        module = parse_module(wasm)
        assert len(module.code) == 1
        assert module.code[0].locals == [(2, ValueType.I32)]
        assert module.code[0].all_locals() == [ValueType.I32, ValueType.I32]


class TestGlobalSection:
    """Tests for global section parsing."""

    def test_immutable_global(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Global section
            0x06,  # global section
            0x06,  # section size
            0x01,  # one global
            0x7F,  # i32
            0x00,  # immutable
            0x41,
            0x2A,  # i32.const 42
            0x0B,  # end
        ])
        module = parse_module(wasm)
        assert len(module.globals) == 1
        assert module.globals[0].type.value_type == ValueType.I32
        assert module.globals[0].type.mutable is False

    def test_mutable_global(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Global section
            0x06,  # global section
            0x06,  # section size
            0x01,  # one global
            0x7E,  # i64
            0x01,  # mutable
            0x42,
            0x00,  # i64.const 0
            0x0B,  # end
        ])
        module = parse_module(wasm)
        assert len(module.globals) == 1
        assert module.globals[0].type.value_type == ValueType.I64
        assert module.globals[0].type.mutable is True


class TestTableSection:
    """Tests for table section parsing."""

    def test_funcref_table(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Table section
            0x04,  # table section
            0x04,  # section size
            0x01,  # one table
            0x70,  # funcref
            0x00,  # flags: no max
            0x01,  # min: 1
        ])
        module = parse_module(wasm)
        assert len(module.tables) == 1
        assert module.tables[0].elem_type == ValueType.FUNCREF
        assert module.tables[0].limits.min == 1


class TestStartSection:
    """Tests for start section parsing."""

    def test_start_function(self):
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section
            0x01,
            0x04,
            0x01,
            0x60,
            0x00,
            0x00,  # () -> ()
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Start section
            0x08,  # start section
            0x01,  # section size
            0x00,  # function index 0
            # Code section
            0x0A,
            0x04,
            0x01,
            0x02,
            0x00,
            0x0B,
        ])
        module = parse_module(wasm)
        assert module.start == 0


class TestModuleMethods:
    """Tests for WasmModule methods."""

    def test_num_imported_funcs(self):
        module = WasmModule()
        assert module.num_imported_funcs() == 0

    def test_get_func_type(self):
        module = WasmModule()
        module.types = [FuncType((ValueType.I32,), (ValueType.I32,))]
        module.func_types = [0]

        func_type = module.get_func_type(0)
        assert func_type == FuncType((ValueType.I32,), (ValueType.I32,))

    def test_get_func_name_from_export(self):
        module = WasmModule()
        from waq.parser.module import Export

        module.exports = [Export("my_func", ExportKind.FUNC, 0)]

        name = module.get_func_name(0)
        assert name == "my_func"

    def test_get_func_name_generated(self):
        module = WasmModule()
        name = module.get_func_name(5)
        assert name == "func_5"
