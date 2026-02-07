"""WASM instruction compilation."""

from __future__ import annotations

from .control import compile_control_instruction
from .numeric import compile_numeric_instruction
from .variable import compile_variable_instruction

__all__ = [
    "compile_control_instruction",
    "compile_numeric_instruction",
    "compile_variable_instruction",
]
