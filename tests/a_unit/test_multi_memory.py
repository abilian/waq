"""Unit tests for Multiple Memories (WASM 3.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_multi_memory_wasm() -> bytes:
    """Create WASM with multiple memories.

    (memory (;0;) 1)    ; First memory: 1 page
    (memory (;1;) 2)    ; Second memory: 2 pages

    (func (export "size0") (result i32)
      memory.size 0)

    (func (export "size1") (result i32)
      memory.size 1)
    """
    # fmt: off
    # Type section: () -> (i32)
    type_section = bytes([
        0x01, 0x60,
        0x00,  # 0 params
        0x01, 0x7F,  # 1 result: i32
    ])

    # Function section: 2 functions of type 0
    func_section = bytes([0x02, 0x00, 0x00])

    # Memory section: 2 memories
    memory_section = bytes([
        0x02,  # 2 memories
        0x00, 0x01,  # memory 0: min=1, no max
        0x00, 0x02,  # memory 1: min=2, no max
    ])

    # Export section: export both functions
    export_section = bytes([
        0x02,  # 2 exports
        0x05,  # name length
    ]) + b"size0" + bytes([
        0x00, 0x00,  # func 0
        0x05,  # name length
    ]) + b"size1" + bytes([
        0x00, 0x01,  # func 1
    ])

    # Code section: two functions
    func0_body = bytes([
        0x00,  # 0 locals
        0x3F, 0x00,  # memory.size 0
        0x0B,
    ])
    func1_body = bytes([
        0x00,  # 0 locals
        0x3F, 0x01,  # memory.size 1
        0x0B,
    ])
    code_section = bytes([
        0x02,  # 2 functions
        len(func0_body),
    ]) + func0_body + bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x05, len(memory_section)]) + memory_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section
    # fmt: on

    return wasm


def make_multi_memory_grow_wasm() -> bytes:
    """Create WASM with memory.grow for multiple memories.

    (memory (;0;) 1)
    (memory (;1;) 1)

    (func (export "grow1") (param i32) (result i32)
      local.get 0
      memory.grow 1)  ; Grow memory 1
    """
    # fmt: off
    # Type section: (i32) -> (i32)
    type_section = bytes([
        0x01, 0x60,
        0x01, 0x7F,  # 1 param: i32
        0x01, 0x7F,  # 1 result: i32
    ])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Memory section: 2 memories
    memory_section = bytes([
        0x02,  # 2 memories
        0x00, 0x01,  # memory 0: min=1
        0x00, 0x01,  # memory 1: min=1
    ])

    # Export section
    export_section = bytes([0x01, 0x05]) + b"grow1" + bytes([0x00, 0x00])

    # Code section
    func_body = bytes([
        0x00,  # 0 locals
        0x20, 0x00,  # local.get 0
        0x40, 0x01,  # memory.grow 1 (memory index 1)
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


class TestMultiMemoryParsing:
    """Tests for multiple memories parsing."""

    def test_multiple_memories_parsed(self):
        """Test that multiple memories are correctly parsed."""
        wasm = make_multi_memory_wasm()
        module = parse_module(wasm)
        assert len(module.memories) == 2
        assert module.memories[0].limits.min == 1
        assert module.memories[1].limits.min == 2


class TestMultiMemoryCompilation:
    """Tests for multiple memories code generation."""

    def test_memory_size_with_index(self):
        """Test that memory.size passes memory index to runtime."""
        wasm = make_multi_memory_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should call __wasm_memory_size_pages with memory index
        assert "__wasm_memory_size_pages" in output
        # The memory index should be passed as an argument
        # For memory 0: first call
        # For memory 1: should also be present
        # Check that both functions compile
        assert "size0" in output
        assert "size1" in output

    def test_memory_grow_with_index(self):
        """Test that memory.grow passes memory index to runtime."""
        wasm = make_multi_memory_grow_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should call __wasm_memory_grow with memory index 1
        assert "__wasm_memory_grow" in output
        # The output should contain the memory index (1)
        assert "w 1" in output  # Memory index as argument


class TestSingleMemoryOptimization:
    """Tests to verify single memory still uses optimized path."""

    def test_single_memory_uses_direct_global(self):
        """Test that single memory uses direct __wasm_memory global."""
        # fmt: off
        # Standard single memory module
        # Type section: (i32) -> (i32)
        type_section = bytes([0x01, 0x60, 0x01, 0x7F, 0x01, 0x7F])

        # Function section: 1 function of type 0
        func_section = bytes([0x01, 0x00])

        # Memory section: single memory
        memory_section = bytes([0x01, 0x00, 0x01])  # 1 memory, min=1

        # Export section
        export_section = bytes([0x01, 0x04]) + b"load" + bytes([0x00, 0x00])

        # Code section
        func_body = bytes([
            0x00,  # 0 locals
            0x20, 0x00,  # local.get 0
            0x28, 0x02, 0x00,  # i32.load
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

        module = parse_module(wasm)
        assert len(module.memories) == 1
        qbe = compile_module(module)
        output = qbe.emit()
        # Single memory should use direct load from __wasm_memory
        assert "$__wasm_memory" in output
        # Should NOT call __wasm_memory_base (that's for multi-memory)
        assert "__wasm_memory_base" not in output
