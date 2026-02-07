"""Binary reader utilities for WASM parsing."""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, TypeVar

from waq.errors import ParseError

T = TypeVar("T")

from .types import (
    ArrayType,
    BlockType,
    CompositeType,
    FieldType,
    FuncType,
    GlobalType,
    Limits,
    MemoryType,
    StructType,
    TableType,
    ValueType,
)

if TYPE_CHECKING:
    from collections.abc import Callable

# WASM magic number and version
WASM_MAGIC = b"\x00asm"
WASM_VERSION = 1


class BinaryReader:
    """Reader for WASM binary format with LEB128 support."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    @property
    def remaining(self) -> int:
        """Bytes remaining to read."""
        return len(self.data) - self.pos

    @property
    def at_end(self) -> bool:
        """True if no more bytes to read."""
        return self.pos >= len(self.data)

    def read_bytes(self, n: int) -> bytes:
        """Read exactly n bytes."""
        if self.pos + n > len(self.data):
            raise ParseError(f"unexpected end of data (need {n} bytes)", self.pos)
        result = self.data[self.pos : self.pos + n]
        self.pos += n
        return result

    def read_byte(self) -> int:
        """Read a single byte."""
        if self.pos >= len(self.data):
            raise ParseError("unexpected end of data", self.pos)
        result = self.data[self.pos]
        self.pos += 1
        return result

    def peek_byte(self) -> int:
        """Peek at the next byte without consuming it."""
        if self.pos >= len(self.data):
            raise ParseError("unexpected end of data", self.pos)
        return self.data[self.pos]

    def read_u32_leb128(self) -> int:
        """Read an unsigned 32-bit LEB128 integer."""
        result = 0
        shift = 0
        while True:
            byte = self.read_byte()
            result |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7
            if shift >= 35:
                raise ParseError("LEB128 integer too large", self.pos)
        return result

    def read_s32_leb128(self) -> int:
        """Read a signed 32-bit LEB128 integer."""
        result = 0
        shift = 0
        while True:
            byte = self.read_byte()
            result |= (byte & 0x7F) << shift
            shift += 7
            if (byte & 0x80) == 0:
                # Sign extend if negative
                if shift < 32 and (byte & 0x40):
                    result |= ~0 << shift
                break
            if shift >= 35:
                raise ParseError("LEB128 integer too large", self.pos)
        # Convert to signed 32-bit
        if result >= 0x80000000:
            result -= 0x100000000
        return result

    def read_s64_leb128(self) -> int:
        """Read a signed 64-bit LEB128 integer."""
        result = 0
        shift = 0
        while True:
            byte = self.read_byte()
            result |= (byte & 0x7F) << shift
            shift += 7
            if (byte & 0x80) == 0:
                # Sign extend if negative
                if shift < 64 and (byte & 0x40):
                    result |= ~0 << shift
                break
            if shift >= 70:
                raise ParseError("LEB128 integer too large", self.pos)
        return result

    def read_f32(self) -> float:
        """Read a 32-bit float."""
        data = self.read_bytes(4)
        return struct.unpack("<f", data)[0]

    def read_f64(self) -> float:
        """Read a 64-bit float."""
        data = self.read_bytes(8)
        return struct.unpack("<d", data)[0]

    def read_name(self) -> str:
        """Read a UTF-8 name (length-prefixed)."""
        length = self.read_u32_leb128()
        data = self.read_bytes(length)
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ParseError(f"invalid UTF-8 in name: {e}", self.pos - length) from e

    def read_value_type(self) -> ValueType:
        """Read a value type."""
        byte = self.read_byte()
        try:
            return ValueType(byte)
        except ValueError:
            raise ParseError(
                f"invalid value type: 0x{byte:02x}", self.pos - 1
            ) from None

    def read_block_type(self) -> BlockType:
        """Read a block type (empty, value type, or type index)."""
        byte = self.peek_byte()
        if byte == 0x40:
            self.read_byte()
            return None
        if byte in (0x7F, 0x7E, 0x7D, 0x7C, 0x70, 0x6F):
            return self.read_value_type()
        # Type index (signed LEB128 for negative values)
        return self.read_s32_leb128()

    def read_limits(self) -> Limits:
        """Read memory/table limits."""
        flags = self.read_byte()
        min_val = self.read_u32_leb128()
        max_val = self.read_u32_leb128() if flags & 0x01 else None
        return Limits(min_val, max_val)

    def read_memory_type(self) -> MemoryType:
        """Read a memory type."""
        limits = self.read_limits()
        return MemoryType(limits)

    def read_table_type(self) -> TableType:
        """Read a table type."""
        elem_type = self.read_value_type()
        if elem_type not in (ValueType.FUNCREF, ValueType.EXTERNREF):
            raise ParseError(f"invalid table element type: {elem_type}", self.pos)
        limits = self.read_limits()
        return TableType(limits, elem_type)

    def read_global_type(self) -> GlobalType:
        """Read a global type."""
        value_type = self.read_value_type()
        mutable = self.read_byte() == 0x01
        return GlobalType(value_type, mutable)

    def read_func_type(self) -> FuncType:
        """Read a function type."""
        tag = self.read_byte()
        if tag != 0x60:
            raise ParseError(
                f"expected function type (0x60), got 0x{tag:02x}", self.pos - 1
            )

        # Read parameter types
        num_params = self.read_u32_leb128()
        params = tuple(self.read_value_type() for _ in range(num_params))

        # Read result types
        num_results = self.read_u32_leb128()
        results = tuple(self.read_value_type() for _ in range(num_results))

        return FuncType(params, results)

    def read_composite_type(self) -> CompositeType:
        """Read a composite type (function, struct, or array).

        WASM GC type constructors:
        - 0x60: function type
        - 0x5F: struct type
        - 0x5E: array type
        """
        tag = self.read_byte()

        if tag == 0x60:
            # Function type - read params and results
            num_params = self.read_u32_leb128()
            params = tuple(self.read_value_type() for _ in range(num_params))
            num_results = self.read_u32_leb128()
            results = tuple(self.read_value_type() for _ in range(num_results))
            return FuncType(params, results)

        if tag == 0x5F:
            # Struct type - read fields
            num_fields = self.read_u32_leb128()
            fields = tuple(self.read_field_type() for _ in range(num_fields))
            return StructType(fields)

        if tag == 0x5E:
            # Array type - read element type
            element_type = self.read_field_type()
            return ArrayType(element_type)

        raise ParseError(
            f"expected composite type (0x60/0x5F/0x5E), got 0x{tag:02x}",
            self.pos - 1,
        )

    def read_field_type(self) -> FieldType:
        """Read a field type (storage type + mutability)."""
        storage_type = self.read_storage_type()
        mutable = self.read_byte() == 0x01
        return FieldType(storage_type, mutable)

    def read_storage_type(self) -> ValueType | int:
        """Read a storage type (value type, packed type, or reference type).

        Storage types can be:
        - Value types (i32, i64, f32, f64)
        - Packed types (i8=0x78, i16=0x77)
        - Reference types (encoded as heap type)
        """
        byte = self.read_byte()

        # Check for packed types first
        if byte == 0x78:
            return ValueType.I8
        if byte == 0x77:
            return ValueType.I16

        # Check for value types
        try:
            return ValueType(byte)
        except ValueError:
            pass

        # For reference types, the byte is a heap type indicator
        # 0x6A-0x70 are abstract heap types, others are type indices
        if byte in (0x63, 0x64):
            # 0x63 = (ref null ht), 0x64 = (ref ht)
            # Read the heap type index
            return self.read_s32_leb128()

        raise ParseError(f"invalid storage type: 0x{byte:02x}", self.pos - 1)

    def read_vector(self, read_elem: Callable[[], T]) -> list[T]:
        """Read a vector of elements."""
        count = self.read_u32_leb128()
        return [read_elem() for _ in range(count)]

    def skip(self, n: int) -> None:
        """Skip n bytes."""
        if self.pos + n > len(self.data):
            raise ParseError(f"cannot skip {n} bytes", self.pos)
        self.pos += n

    def slice(self, length: int) -> BinaryReader:
        """Create a new reader for a slice of the data."""
        data = self.read_bytes(length)
        return BinaryReader(data)
