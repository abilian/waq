"""Unit tests for Memory64 (WASM 3.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_memory64_size_wasm() -> bytes:
    """Create WASM with Memory64 and memory.size.

    (memory (;0;) i64 1)  ; Memory64 with 1 page
    (func (export "size") (result i64)
      memory.size)
    """
    # fmt: off
    # Type section: () -> (i64)
    type_section = bytes([
        0x01, 0x60,
        0x00,  # 0 params
        0x01, 0x7E,  # 1 result: i64
    ])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Memory section: Memory64 with min=1, no max
    # Flag 0x04 = memory64, no max
    memory_section = bytes([
        0x01,  # 1 memory
        0x04,  # flags: memory64, no max
        0x01,  # min = 1 page
    ])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"size" + bytes([0x00, 0x00])

    # Code section: memory.size
    func_body = bytes([
        0x00,  # 0 locals
        0x3F, 0x00,  # memory.size mem 0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x05, len(memory_section)]) + memory_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on

    return wasm


def make_memory64_grow_wasm() -> bytes:
    """Create WASM with Memory64 and memory.grow.

    (memory (;0;) i64 1)
    (func (export "grow") (param i64) (result i64)
      local.get 0
      memory.grow)
    """
    # fmt: off
    # Type section: (i64) -> (i64)
    type_section = bytes([
        0x01, 0x60,
        0x01, 0x7E,  # 1 param: i64
        0x01, 0x7E,  # 1 result: i64
    ])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Memory section: Memory64
    memory_section = bytes([
        0x01,
        0x04,  # memory64, no max
        0x01,  # min = 1
    ])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"grow" + bytes([0x00, 0x00])

    # Code section
    func_body = bytes([
        0x00,  # 0 locals
        0x20, 0x00,  # local.get 0
        0x40, 0x00,  # memory.grow mem 0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x05, len(memory_section)]) + memory_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on

    return wasm


def make_memory64_load_store_wasm() -> bytes:
    """Create WASM with Memory64 load/store.

    (memory (;0;) i64 1)
    (func (export "store_load") (param $addr i64) (param $val i32) (result i32)
      local.get 0
      local.get 1
      i32.store
      local.get 0
      i32.load)
    """
    # fmt: off
    # Type section: (i64, i32) -> (i32)
    type_section = bytes([
        0x01, 0x60,
        0x02, 0x7E, 0x7F,  # 2 params: i64, i32
        0x01, 0x7F,  # 1 result: i32
    ])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Memory section: Memory64
    memory_section = bytes([
        0x01,
        0x04,  # memory64
        0x01,  # min = 1
    ])

    # Export section
    export_section = bytes([0x01, 0x0A]) + b"store_load" + bytes([0x00, 0x00])

    # Code section
    func_body = bytes([
        0x00,  # 0 locals
        0x20, 0x00,  # local.get 0 (addr i64)
        0x20, 0x01,  # local.get 1 (val i32)
        0x36, 0x02, 0x00,  # i32.store align=2, offset=0
        0x20, 0x00,  # local.get 0 (addr i64)
        0x28, 0x02, 0x00,  # i32.load align=2, offset=0
        0x0B,
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x05, len(memory_section)]) + memory_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on

    return wasm


def make_memory64_with_max_wasm() -> bytes:
    """Create WASM with Memory64 with max limit.

    (memory (;0;) i64 1 10)  ; Memory64 with min=1, max=10
    """
    # fmt: off
    # Type section: () -> ()
    type_section = bytes([0x01, 0x60, 0x00, 0x00])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Memory section: Memory64 with min=1, max=10
    # Flag 0x05 = memory64 with max
    memory_section = bytes([
        0x01,  # 1 memory
        0x05,  # flags: memory64 with max
        0x01,  # min = 1
        0x0A,  # max = 10
    ])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"test" + bytes([0x00, 0x00])

    # Code section
    func_body = bytes([0x00, 0x0B])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x05, len(memory_section)]) + memory_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on

    return wasm


class TestMemory64Parsing:
    """Tests for Memory64 parsing."""

    def test_memory64_flag_parsed(self):
        """Test that memory64 flag is correctly parsed."""
        wasm = make_memory64_size_wasm()
        module = parse_module(wasm)
        assert len(module.memories) == 1
        assert module.memories[0].is_memory64 is True
        assert module.memories[0].limits.min == 1

    def test_memory64_with_max_parsed(self):
        """Test that memory64 with max limit is correctly parsed."""
        wasm = make_memory64_with_max_wasm()
        module = parse_module(wasm)
        assert len(module.memories) == 1
        assert module.memories[0].is_memory64 is True
        assert module.memories[0].limits.min == 1
        assert module.memories[0].limits.max == 10


class TestMemory64Compilation:
    """Tests for Memory64 code generation."""

    def test_memory64_size_returns_i64(self):
        """Test that memory.size returns i64 for memory64."""
        wasm = make_memory64_size_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should call memory64 size function
        assert "__wasm_memory_size_pages64" in output

    def test_memory64_grow_uses_i64(self):
        """Test that memory.grow uses i64 for memory64."""
        wasm = make_memory64_grow_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should call memory64 grow function
        assert "__wasm_memory_grow64" in output

    def test_memory64_load_store_compiles(self):
        """Test that memory64 load/store compiles without address conversion."""
        wasm = make_memory64_load_store_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should have load and store operations
        assert "loadw" in output
        assert "storew" in output
        # Memory64 should not use extuw for address conversion
        # (the address is already i64)
        # Count occurrences - for memory32, we'd have 2 extuw (one per load/store)
        # For memory64, we should have 0
        assert output.count("extuw") == 0


class TestMemory32Unchanged:
    """Tests to verify Memory32 still works correctly."""

    def test_memory32_size_returns_i32(self):
        """Test that memory.size still returns i32 for memory32."""
        # fmt: off
        # Standard memory32 module
        wasm = bytes([
            0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00,
            # Type section: () -> (i32)
            0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7F,
            # Function section
            0x03, 0x02, 0x01, 0x00,
            # Memory section: Memory32 with min=1
            0x05, 0x03, 0x01, 0x00, 0x01,
            # Export section
            0x07, 0x08, 0x01, 0x04,
        ]) + b"size" + bytes([
            0x00, 0x00,
            # Code section
            0x0A, 0x06, 0x01, 0x04, 0x00, 0x3F, 0x00, 0x0B,
        ])
        # fmt: on
        module = parse_module(wasm)
        assert module.memories[0].is_memory64 is False
        qbe = compile_module(module)
        output = qbe.emit()
        # Should call memory32 size function
        assert "__wasm_memory_size_pages" in output
        assert "__wasm_memory_size_pages64" not in output
