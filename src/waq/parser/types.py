"""WASM type definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ValueType(IntEnum):
    """WASM value types.

    Binary encoding matches WASM specification.
    """

    I32 = 0x7F
    I64 = 0x7E
    F32 = 0x7D
    F64 = 0x7C
    # Reference types (WASM 2.0+)
    FUNCREF = 0x70
    EXTERNREF = 0x6F
    # SIMD (not supported in QBE)
    V128 = 0x7B
    # GC reference types (WASM GC proposal)
    ANYREF = 0x6E
    EQREF = 0x6D
    I31REF = 0x6C
    STRUCTREF = 0x6B
    ARRAYREF = 0x6A
    NULLFUNCREF = 0x73
    NULLEXTERNREF = 0x72
    NULLREF = 0x71
    # Packed types for struct/array fields
    I8 = 0x78
    I16 = 0x77

    def to_qbe(self) -> str:
        """Convert to QBE type letter."""
        match self:
            case ValueType.I32:
                return "w"
            case ValueType.I64:
                return "l"
            case ValueType.F32:
                return "s"
            case ValueType.F64:
                return "d"
            case (
                ValueType.FUNCREF
                | ValueType.EXTERNREF
                | ValueType.ANYREF
                | ValueType.EQREF
                | ValueType.I31REF
                | ValueType.STRUCTREF
                | ValueType.ARRAYREF
                | ValueType.NULLFUNCREF
                | ValueType.NULLEXTERNREF
                | ValueType.NULLREF
            ):
                return "l"  # All reference types are pointers
            case ValueType.I8:
                return "b"  # byte
            case ValueType.I16:
                return "h"  # halfword
            case _:
                msg = f"Unsupported type: {self.name}"
                raise ValueError(msg)

    def is_reference(self) -> bool:
        """Check if this is a reference type."""
        return self in (
            ValueType.FUNCREF,
            ValueType.EXTERNREF,
            ValueType.ANYREF,
            ValueType.EQREF,
            ValueType.I31REF,
            ValueType.STRUCTREF,
            ValueType.ARRAYREF,
            ValueType.NULLFUNCREF,
            ValueType.NULLEXTERNREF,
            ValueType.NULLREF,
        )

    def __str__(self) -> str:
        return self.name.lower()


@dataclass(frozen=True, slots=True)
class FuncType:
    """Function signature."""

    params: tuple[ValueType, ...]
    results: tuple[ValueType, ...]

    def __str__(self) -> str:
        params = ", ".join(str(t) for t in self.params)
        results = ", ".join(str(t) for t in self.results)
        return f"({params}) -> ({results})"


@dataclass(frozen=True, slots=True)
class Limits:
    """Memory or table size limits."""

    min: int
    max: int | None = None

    def __str__(self) -> str:
        if self.max is None:
            return f"{self.min}.."
        return f"{self.min}..{self.max}"


@dataclass(frozen=True, slots=True)
class MemoryType:
    """Memory type."""

    limits: Limits
    is_memory64: bool = False  # WASM 3.0

    def __str__(self) -> str:
        suffix = " (memory64)" if self.is_memory64 else ""
        return f"memory {self.limits}{suffix}"


@dataclass(frozen=True, slots=True)
class TableType:
    """Table type."""

    limits: Limits
    elem_type: ValueType  # FUNCREF or EXTERNREF

    def __str__(self) -> str:
        return f"table {self.limits} {self.elem_type}"


@dataclass(frozen=True, slots=True)
class GlobalType:
    """Global variable type."""

    value_type: ValueType
    mutable: bool

    def __str__(self) -> str:
        mut = "mut " if self.mutable else ""
        return f"{mut}{self.value_type}"


# Block type can be:
# - Empty (0x40)
# - A value type (single result)
# - A type index (function type, for multi-value)
BlockType = None | ValueType | int


# ============================================================================
# GC Types (WASM GC Proposal)
# ============================================================================


@dataclass(frozen=True, slots=True)
class FieldType:
    """Field type for struct/array elements.

    Contains a storage type (value type or packed type) and mutability.
    """

    storage_type: ValueType | int  # ValueType or type index for ref types
    mutable: bool

    def __str__(self) -> str:
        mut = "mut " if self.mutable else ""
        return f"{mut}{self.storage_type}"


@dataclass(frozen=True, slots=True)
class StructType:
    """GC struct type definition.

    A struct is a fixed-size collection of heterogeneous fields.
    """

    fields: tuple[FieldType, ...]

    def __str__(self) -> str:
        fields = ", ".join(str(f) for f in self.fields)
        return f"(struct {fields})"


@dataclass(frozen=True, slots=True)
class ArrayType:
    """GC array type definition.

    An array is a variable-size collection of homogeneous elements.
    """

    element_type: FieldType

    def __str__(self) -> str:
        return f"(array {self.element_type})"


@dataclass(frozen=True, slots=True)
class RefType:
    """Reference type with heap type and nullability.

    Represents (ref null? heaptype) in the WASM GC spec.
    """

    heap_type: ValueType | int  # ValueType for abstract, int for concrete type index
    nullable: bool = True

    def __str__(self) -> str:
        null = "null " if self.nullable else ""
        return f"(ref {null}{self.heap_type})"

    def to_qbe(self) -> str:
        """All reference types are pointers in QBE."""
        return "l"


# A composite type can be a function, struct, or array type
CompositeType = FuncType | StructType | ArrayType
