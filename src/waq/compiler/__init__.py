"""WASM to QBE compiler."""

from __future__ import annotations

from .codegen import compile_module

__all__ = ["compile_module"]
