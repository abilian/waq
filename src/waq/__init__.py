"""WAQ: WebAssembly to Native Code via QBE.

A compiler that translates WebAssembly binary modules into native machine code
using QBE as the backend.
"""

from __future__ import annotations

from waq.cli import main
from waq.compiler import compile_module
from waq.parser.module import WasmModule, parse_module

__version__ = "0.1.1"

__all__ = [
    "WasmModule",
    "compile_module",
    "main",
    "parse_module",
]
