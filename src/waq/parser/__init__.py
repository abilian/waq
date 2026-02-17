"""WASM binary parser."""

from __future__ import annotations

from .binary import DEFAULT_LIMITS, BinaryReader, ParserLimits
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
    "DEFAULT_LIMITS",
    "BinaryReader",
    "FuncType",
    "GlobalType",
    "Limits",
    "MemoryType",
    "ParserLimits",
    "TableType",
    "ValueType",
    "parse_module",
]
