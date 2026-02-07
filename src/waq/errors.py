"""Error definitions for the WASM-to-QBE compiler."""

from __future__ import annotations


class WasmError(Exception):
    """Base class for all WASM compiler errors."""


class ParseError(WasmError):
    """Error during WASM binary parsing."""

    def __init__(self, message: str, offset: int | None = None) -> None:
        self.offset = offset
        if offset is not None:
            message = f"at offset 0x{offset:x}: {message}"
        super().__init__(message)


class ValidationError(WasmError):
    """Error during WASM module validation."""


class CompileError(WasmError):
    """Error during compilation to QBE."""


class TrapError(WasmError):
    """Runtime trap condition detected at compile time."""

    def __init__(self, trap_type: str, message: str = "") -> None:
        self.trap_type = trap_type
        super().__init__(f"{trap_type}: {message}" if message else trap_type)
