"""Unit tests for table operations (WASM 2.0)."""

from __future__ import annotations

from waq.compiler import compile_module
from waq.parser.module import parse_module


def make_table_get_wasm() -> bytes:
    """Create WASM with table.get instruction.

    (idx: i32) -> (ref: i64)
    """
    # Type section: (i32) -> (i64) - ref is returned as i64 pointer
    type_section = bytes([0x01, 0x60, 0x01, 0x7F, 0x01, 0x7E])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Table section: 1 funcref table, min 10, max 100
    table_section = bytes([0x01, 0x70, 0x01, 0x0A, 0x64])

    # Export section
    export_section = bytes([0x01, 0x03]) + b"get" + bytes([0x00, 0x00])

    # Code section: table.get
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (idx)
        0x25,
        0x00,  # table.get table_idx=0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_table_set_wasm() -> bytes:
    """Create WASM with table.set instruction.

    (idx: i32, ref: i64) -> ()
    """
    # Type section: (i32, i64) -> ()
    type_section = bytes([0x01, 0x60, 0x02, 0x7F, 0x7E, 0x00])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Table section: 1 funcref table, min 10
    table_section = bytes([0x01, 0x70, 0x00, 0x0A])

    # Export section
    export_section = bytes([0x01, 0x03]) + b"set" + bytes([0x00, 0x00])

    # Code section: table.set
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (idx)
        0x20,
        0x01,  # local.get 1 (ref)
        0x26,
        0x00,  # table.set table_idx=0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_table_size_wasm() -> bytes:
    """Create WASM with table.size instruction.

    () -> (size: i32)
    """
    # Type section: () -> (i32)
    type_section = bytes([0x01, 0x60, 0x00, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Table section: 1 funcref table, min 10
    table_section = bytes([0x01, 0x70, 0x00, 0x0A])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"size" + bytes([0x00, 0x00])

    # Code section: table.size
    func_body = bytes([
        0x00,  # 0 locals
        0xFC,
        0x10,
        0x00,  # table.size table_idx=0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_table_grow_wasm() -> bytes:
    """Create WASM with table.grow instruction.

    (ref: i64, delta: i32) -> (old_size: i32)
    """
    # Type section: (i64, i32) -> (i32)
    type_section = bytes([0x01, 0x60, 0x02, 0x7E, 0x7F, 0x01, 0x7F])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Table section: 1 funcref table, min 10
    table_section = bytes([0x01, 0x70, 0x00, 0x0A])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"grow" + bytes([0x00, 0x00])

    # Code section: table.grow
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (ref)
        0x20,
        0x01,  # local.get 1 (delta)
        0xFC,
        0x0F,
        0x00,  # table.grow table_idx=0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


def make_table_fill_wasm() -> bytes:
    """Create WASM with table.fill instruction.

    (dest: i32, ref: i64, len: i32) -> ()
    """
    # Type section: (i32, i64, i32) -> ()
    type_section = bytes([0x01, 0x60, 0x03, 0x7F, 0x7E, 0x7F, 0x00])

    # Function section
    func_section = bytes([0x01, 0x00])

    # Table section: 1 funcref table, min 10
    table_section = bytes([0x01, 0x70, 0x00, 0x0A])

    # Export section
    export_section = bytes([0x01, 0x04]) + b"fill" + bytes([0x00, 0x00])

    # Code section: table.fill
    func_body = bytes([
        0x00,  # 0 locals
        0x20,
        0x00,  # local.get 0 (dest)
        0x20,
        0x01,  # local.get 1 (ref)
        0x20,
        0x02,  # local.get 2 (len)
        0xFC,
        0x11,
        0x00,  # table.fill table_idx=0
        0x0B,  # end
    ])
    code_section = bytes([0x01, len(func_body)]) + func_body

    wasm = bytes([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
    wasm += bytes([0x01, len(type_section)]) + type_section
    wasm += bytes([0x03, len(func_section)]) + func_section
    wasm += bytes([0x04, len(table_section)]) + table_section
    wasm += bytes([0x07, len(export_section)]) + export_section
    wasm += bytes([0x0A, len(code_section)]) + code_section

    return wasm


class TestTableGet:
    """Tests for table.get instruction."""

    def test_table_get_compiles(self):
        """Test that table.get instruction compiles."""
        wasm = make_table_get_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_table_get" in output


class TestTableSet:
    """Tests for table.set instruction."""

    def test_table_set_compiles(self):
        """Test that table.set instruction compiles."""
        wasm = make_table_set_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_table_set" in output


class TestTableSize:
    """Tests for table.size instruction."""

    def test_table_size_compiles(self):
        """Test that table.size instruction compiles."""
        wasm = make_table_size_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_table_size" in output


class TestTableGrow:
    """Tests for table.grow instruction."""

    def test_table_grow_compiles(self):
        """Test that table.grow instruction compiles."""
        wasm = make_table_grow_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_table_grow" in output


class TestTableFill:
    """Tests for table.fill instruction."""

    def test_table_fill_compiles(self):
        """Test that table.fill instruction compiles."""
        wasm = make_table_fill_wasm()
        module = parse_module(wasm)
        qbe = compile_module(module)
        output = qbe.emit()
        assert "__wasm_table_fill" in output
