"""WASM binary parser."""

from __future__ import annotations

from .binary import BinaryReader
from .module import parse_module
from .types import (
    FuncType,
    GlobalType,
    Limits,
    MemoryType,
    TableType,
    ValueType,
)

__all__ = [
    "BinaryReader",
    "FuncType",
    "GlobalType",
    "Limits",
    "MemoryType",
    "TableType",
    "ValueType",
    "parse_module",
]
