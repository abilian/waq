"""WASM module validation.

This module provides validation for WASM modules before compilation,
including type checking, stack depth verification, and index validation.
"""

from __future__ import annotations

from .module import validate_module
from .types import ValidationContext, ValidationResult

__all__ = [
    "ValidationContext",
    "ValidationResult",
    "validate_module",
]
