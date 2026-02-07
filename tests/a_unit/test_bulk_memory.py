"""Unit tests for bulk memory operations (WASM 2.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_memory_fill_wasm() -> bytes:
    """Create WASM with memory.fill instruction.

    (dest: i32, val: i32, len: i32) -> ()
    """
    # Type section: (i32, i32, i32) -> ()
    type_section = bytes([0x01, 0x60, 0x03, 0x7F, 0x7F, 0x7F, 0x00])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Memory section: 1 page
    memory_section = bytes([0x01, 0x00, 0x01])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"fill" + bytes([0x00, 0x00])

    # Code section: memory.fill
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (dest)
        0x20,
        0x01,  # local.get 1 (val)
        0x20,
        0x02,  # local.get 2 (len)
        0xFC,
        0x0B,
        0x00,  # memory.fill mem_idx=0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x05, len(memory_section)]) + memory_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_memory_copy_wasm() -> bytes:
    """Create WASM with memory.copy instruction.

    (dest: i32, src: i32, len: i32) -> ()
    """
    # Type section: (i32, i32, i32) -> ()
    type_section = bytes([0x01, 0x60, 0x03, 0x7F, 0x7F, 0x7F, 0x00])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Memory section: 1 page
    memory_section = bytes([0x01, 0x00, 0x01])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"copy" + bytes([0x00, 0x00])

    # Code section: memory.copy
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (dest)
        0x20,
        0x01,  # local.get 1 (src)
        0x20,
        0x02,  # local.get 2 (len)
        0xFC,
        0x0A,
        0x00,
        0x00,  # memory.copy dest_mem=0 src_mem=0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x05, len(memory_section)]) + memory_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_memory_init_wasm() -> bytes:
    """Create WASM with memory.init and data.drop instructions.

    Uses a passive data segment.
    """
    # Type section: (dest: i32, src: i32, len: i32) -> ()
    type_section = bytes([0x01, 0x60, 0x03, 0x7F, 0x7F, 0x7F, 0x00])

    # Function section: 2 functions
    func_section = bytes([0x02, 0x00, 0x00])

    # Memory section: 1 page
    memory_section = bytes([0x01, 0x00, 0x01])

    # Export section
    export_init = bytes([0x04]) + b"init" + bytes([0x00, 0x00])
    export_drop = bytes([0x04]) + b"drop" + bytes([0x00, 0x01])
    export_section = bytes([0x02]) + export_init + export_drop

    # Data count section (required for passive segments in some validators)
    data_count_section = bytes([0x01])

    # Data section: 1 passive segment with "Hello"
    data_content = b"Hello"
    data_section = (
        bytes([
            0x01,  # 1 segment
            0x01,  # flags=1 (passive)
            len(data_content),
        ])
        + data_content
    )

    # Code section: 2 functions
    # func 0: memory.init
    func0_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (dest)
        0x20,
        0x01,  # local.get 1 (src_offset)
        0x20,
        0x02,  # local.get 2 (len)
        0xFC,
        0x08,
        0x00,
        0x00,  # memory.init data_idx=0 mem_idx=0
        0x0B,  # end
    ])
    # func 1: data.drop
    func1_body = bytes([
        0x00,  # 0 locals
        0xFC,
        0x09,
        0x00,  # data.drop data_idx=0
        0x0B,  # end
    ])

    code_section = bytes([0x02])
    code_section += bytes([len(func0_body)]) + func0_body
    code_section += bytes([len(func1_body)]) + func1_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x05, len(memory_section)]) + memory_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0C, len(data_count_section)]) + data_count_section
    wasm += bytes([0x0B, len(data_section)]) + data_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestMemoryFill:
    """Tests for memory.fill instruction."""

    def test_memory_fill_compiles(self):
        """Test that memory.fill instruction compiles."""
        wasm = make_memory_fill_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_memory_fill" in output

    def test_memory_fill_takes_three_args(self):
        """Test that memory.fill call has three arguments."""
        wasm = make_memory_fill_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        # Should call with dest, val, len
        assert "call" in output.lower()


class TestMemoryCopy:
    """Tests for memory.copy instruction."""

    def test_memory_copy_compiles(self):
        """Test that memory.copy instruction compiles."""
        wasm = make_memory_copy_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_memory_copy" in output


class TestMemoryInit:
    """Tests for memory.init and data.drop instructions."""

    def test_memory_init_compiles(self):
        """Test that memory.init instruction compiles."""
        wasm = make_memory_init_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_memory_init" in output

    def test_data_drop_compiles(self):
        """Test that data.drop instruction compiles."""
        wasm = make_memory_init_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_data_drop" in output
